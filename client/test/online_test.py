"""
Testes online contra o servidor real do professor.

Cenários cobertos:
  1. Baseline (Policy 1) — Rate-Based, 20 segmentos, rede estável
  2. Policy 2 — Buffer-Based, 20 segmentos, rede estável
  3. Policy 3 — Estatístico, 20 segmentos, rede estável
  4. Policy 3 + Failover simulado — queda do Servidor A no segmento 10
  5. Policy 3 + Jitter alto simulado — injeta jitter artificial no downloader

Nota: o endpoint /control requer X-API-Key do professor e não está acessível
ao grupo. A simulação de mudança de banda e jitter é feita interceptando o
downloader localmente, reproduzindo os efeitos que o professor causaria ao vivo.
"""

import sys
import os
import csv
import datetime
import time
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from manifest import fetch_manifest, parse_servers, parse_qualities
from downloader import download_segment, SegmentResult
from buffer import BufferManager
from failover import build_failover_manager
from abr.rate_based import RateBasedPolicy
from abr.policy2 import Policy2
from abr.policy3 import Policy3
from config import (
    SERVER_A, SERVER_B, NUM_SEGMENTS, SEGMENT_DURATION,
    BUFFER_CAP_S, BUFFER_TARGET_S, MIN_BUFFER_TO_PLAY,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def _check_server(url: str) -> bool:
    try:
        req = urllib.request.Request(f"{url}/health", headers={"User-Agent": "GRUPO 6"})
        with urllib.request.urlopen(req, timeout=4) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def _run_session(
    abr,
    qualities: list[dict],
    seg_duration: float,
    num_segments: int,
    label: str,
    *,
    failover_at: int | None = None,
    jitter_inject_from: int | None = None,
    jitter_inject_ms: float = 0.0,
) -> list[dict]:
    """
    Loop de download genérico reutilizável por todos os cenários.
    Retorna lista de dicts com as 14 métricas por segmento.
    """
    manifest = fetch_manifest(SERVER_A)
    failover = build_failover_manager(manifest)
    buf = BufferManager()

    jitter_ewma = 0.0
    ewma_alpha  = 0.2
    failover_total = 0
    rows = []

    print(f"\n{'='*60}")
    print(f"  CENÁRIO: {label}")
    print(f"{'='*60}")

    for seg_num in range(1, num_segments + 1):
        buffer_can_play = 1 if buf.can_play() else 0

        chosen = abr.select_quality(
            throughput_kbps=abr._estimated_throughput(),
            buffer_level_s=buf.buffer_level_s,
            qualities=qualities,
        )

        # ── Download com lógica de failover e injeção de condições ───────────
        try:
            if failover_at and seg_num == failover_at:
                print(f"\n  [SIM] Segmento {seg_num}: Simulando queda do Servidor A!")
                raise TimeoutError("Simulação de queda do Servidor A")

            result = download_segment(failover.current_server, chosen, seg_num)

            # Simula jitter alto injetado pelo professor a partir de certo segmento
            if jitter_inject_from and seg_num >= jitter_inject_from:
                result = SegmentResult(
                    bytes_total=result.bytes_total,
                    download_time_s=result.download_time_s,
                    throughput_kbps=result.throughput_kbps,
                    jitter_network_ms=result.jitter_network_ms + jitter_inject_ms,
                )

        except Exception as e:
            t_failover = 5.0
            if buffer_can_play == 1:
                buf.consume(t_failover)
            failover.handle_failure()
            failover_total = failover.failover_count
            result = download_segment(failover.current_server, chosen, seg_num)

        current_server_id = failover.current_server_id
        abr.update_throughput(result.throughput_kbps, result.jitter_network_ms)
        jitter_ewma = ewma_alpha * result.jitter_network_ms + (1 - ewma_alpha) * jitter_ewma

        if buffer_can_play == 1:
            buf.consume(result.download_time_s)
        else:
            buf._had_stall = True
            buf._stall_duration = result.download_time_s

        rebuffer, stall_s = buf.check_rebuffer()
        buf.add_segment(seg_duration)

        # Pacing básico para não encher o buffer além do teto
        if buf.buffer_level_s >= BUFFER_TARGET_S:
            wait_s = max(0.0, seg_duration - result.download_time_s)
            if wait_s > 0:
                time.sleep(wait_s)
                buf.consume(wait_s)
        buf.wait_if_full(BUFFER_CAP_S)

        row = {
            "segment": seg_num,
            "timestamp": datetime.datetime.now().isoformat(),
            "server_id": current_server_id,
            "quality": chosen["quality"],
            "bitrate_kbps": chosen["bitrate_kbps"],
            "vazao_kbps": round(result.throughput_kbps, 2),
            "download_time_s": round(result.download_time_s, 4),
            "jitter_network_ms": round(result.jitter_network_ms, 2),
            "jitter_ewma_ms": round(jitter_ewma, 2),
            "buffer_level_s": round(buf.buffer_level_s, 2),
            "buffer_can_play": buffer_can_play,
            "rebuffer_event": 1 if rebuffer else 0,
            "stall_duration_s": round(stall_s, 3),
            "failover_total": failover_total,
        }
        rows.append(row)

        flag_fo  = " [FAILOVER]" if failover_total > 0 and seg_num == failover_at else ""
        flag_ji  = f" [JITTER+{jitter_inject_ms:.0f}ms]" if jitter_inject_from and seg_num >= jitter_inject_from else ""
        flag_rb  = " [REBUFFER]" if rebuffer else ""
        print(
            f"  [{seg_num:02d}] {chosen['quality']:5s} | "
            f"vazao={result.throughput_kbps:5.0f} kbps | "
            f"jitter={result.jitter_network_ms:5.1f}ms | "
            f"buffer={buf.buffer_level_s:.1f}s | "
            f"srv={current_server_id}"
            f"{flag_fo}{flag_ji}{flag_rb}"
        )

    return rows


def _summarize(rows: list[dict], label: str) -> dict:
    qualities_order = ["240p", "360p", "480p", "720p", "1080p"]
    bitrates = [r["bitrate_kbps"] for r in rows]
    rebuffers = sum(r["rebuffer_event"] for r in rows)
    stall_total = sum(r["stall_duration_s"] for r in rows)
    changes = sum(
        1 for i in range(1, len(rows)) if rows[i]["quality"] != rows[i-1]["quality"]
    )
    avg_quality_idx = sum(
        qualities_order.index(r["quality"]) for r in rows if r["quality"] in qualities_order
    ) / len(rows)
    failovers = rows[-1]["failover_total"] if rows else 0

    summary = {
        "cenario": label,
        "segmentos": len(rows),
        "bitrate_medio_kbps": round(sum(bitrates) / len(bitrates), 1),
        "qualidade_media_idx": round(avg_quality_idx, 2),
        "mudancas_qualidade": changes,
        "rebuffer_eventos": rebuffers,
        "stall_total_s": round(stall_total, 3),
        "failovers": failovers,
    }
    return summary


# ─── Cenários ────────────────────────────────────────────────────────────────

def run_all():
    if not _check_server(SERVER_A):
        print(f"[ERRO] Servidor A ({SERVER_A}) inacessível. Abortando testes online.")
        sys.exit(1)

    manifest = fetch_manifest(SERVER_A)
    qualities = parse_qualities(manifest)
    seg_duration = manifest.get("segment_duration_s", SEGMENT_DURATION)

    print(f"\nManifest: {len(qualities)} qualidades, {seg_duration}s por segmento")
    print(f"Servidor A: {SERVER_A}  |  Servidor B: {SERVER_B}")

    summaries = []

    # ── Cenário 1: Policy 1 — Rate-Based baseline ─────────────────────────────
    rows1 = _run_session(
        RateBasedPolicy(), qualities, seg_duration, NUM_SEGMENTS,
        "Policy 1 — Rate-Based (Baseline)"
    )
    _write_csv(os.path.join(OUTPUT_DIR, "policy1_stable.csv"), rows1)
    summaries.append(_summarize(rows1, "P1 Rate-Based"))

    # ── Cenário 2: Policy 2 — Buffer-Based ───────────────────────────────────
    rows2 = _run_session(
        Policy2(), qualities, seg_duration, NUM_SEGMENTS,
        "Policy 2 — Buffer-Based"
    )
    _write_csv(os.path.join(OUTPUT_DIR, "policy2_stable.csv"), rows2)
    summaries.append(_summarize(rows2, "P2 Buffer-Based"))

    # ── Cenário 3: Policy 3 — Estatístico, rede estável ──────────────────────
    rows3 = _run_session(
        Policy3(), qualities, seg_duration, NUM_SEGMENTS,
        "Policy 3 — Estatístico (rede estável)"
    )
    _write_csv(os.path.join(OUTPUT_DIR, "policy3_stable.csv"), rows3)
    summaries.append(_summarize(rows3, "P3 Estável"))

    # ── Cenário 4: Policy 3 + Failover no segmento 10 (simula queda Srv A) ───
    rows4 = _run_session(
        Policy3(), qualities, seg_duration, NUM_SEGMENTS,
        "Policy 3 + Failover (queda Servidor A no seg 10)",
        failover_at=10,
    )
    _write_csv(os.path.join(OUTPUT_DIR, "policy3_failover.csv"), rows4)
    summaries.append(_summarize(rows4, "P3 + Failover"))

    # ── Cenário 5: Policy 3 + Jitter alto a partir do segmento 8 ─────────────
    # Simula o professor injetando 400ms de jitter na rede a partir do seg 8
    rows5 = _run_session(
        Policy3(), qualities, seg_duration, NUM_SEGMENTS,
        "Policy 3 + Jitter alto a partir do seg 8 (simula professor: +400ms)",
        jitter_inject_from=8,
        jitter_inject_ms=400.0,
    )
    _write_csv(os.path.join(OUTPUT_DIR, "policy3_high_jitter.csv"), rows5)
    summaries.append(_summarize(rows5, "P3 + Jitter 400ms"))

    # ── Relatório final ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  RESUMO COMPARATIVO DOS CENÁRIOS")
    print(f"{'='*60}")
    print(f"{'Cenário':<28} {'Bitrate méd':>11} {'Qual.méd':>8} {'Mudanças':>8} "
          f"{'Rebuffers':>9} {'Stall(s)':>8} {'Failover':>8}")
    print("-" * 84)
    for s in summaries:
        print(
            f"{s['cenario']:<28} {s['bitrate_medio_kbps']:>10.0f}k "
            f"{s['qualidade_media_idx']:>8.2f} {s['mudancas_qualidade']:>8} "
            f"{s['rebuffer_eventos']:>9} {s['stall_total_s']:>8.3f} "
            f"{s['failovers']:>8}"
        )

    _write_csv(os.path.join(OUTPUT_DIR, "comparativo_cenarios.csv"), summaries)
    print(f"\nCSVs salvos em: {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_all()
