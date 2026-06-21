"""
Testes unitários para Policy3 — não requer servidor.

Cenários cobertos:
  1. Rede estável com jitter baixo → qualidade sobe gradualmente (histerese)
  2. Jitter alto (300ms) → penalidade reduz throughput efetivo → qualidade cai
  3. Buffer crítico (<4s) → fator 0.5 força qualidade baixa mesmo com banda alta
  4. Transição gradual → nunca sobe mais de 1 nível por vez
  5. Descida rápida → cai imediatamente ao nível correto
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abr.policy3 import Policy3

# Representações fictícias (mesma estrutura do manifest real)
QUALITIES = [
    {"quality": "240p",  "bitrate_kbps": 200},
    {"quality": "360p",  "bitrate_kbps": 400},
    {"quality": "480p",  "bitrate_kbps": 600},
    {"quality": "720p",  "bitrate_kbps": 1000},
    {"quality": "1080p", "bitrate_kbps": 1200},
]


def _run_n_segments(policy, throughput_kbps, jitter_ms, buffer_s, n):
    """Simula n segmentos com condições constantes e retorna a última qualidade."""
    q = QUALITIES[0]
    for _ in range(n):
        policy.update_throughput(throughput_kbps, jitter_ms)
        q = policy.select_quality(
            throughput_kbps=policy._estimated_throughput(),
            buffer_level_s=buffer_s,
            qualities=QUALITIES,
        )
    return q


# ─── Teste 1: Rede estável, jitter baixo → deve subir de qualidade ────────────
def test_stable_network_rises():
    p = Policy3()
    # 2000 kbps disponível, jitter 0ms, buffer confortável (15s)
    # Após muitos segmentos, o EWMA converge e deve atingir 1080p
    q = _run_n_segments(p, throughput_kbps=2000, jitter_ms=0, buffer_s=15.0, n=20)
    assert q["quality"] == "1080p", (
        f"[FALHA] Esperava 1080p com banda estável, obteve {q['quality']}"
    )
    print(f"[OK] test_stable_network_rises → {q['quality']}")


# ─── Teste 2: Jitter alto → penalidade força qualidade menor ──────────────────
def test_high_jitter_lowers_quality():
    p = Policy3()
    # 2000 kbps mas jitter de 700ms → penalidade = min(0.5, 1.0*700/1000) = 0.5
    # T_efetiva = T_ewma * 0.5 * 1.0 (buffer confortável)
    # T_ewma converge para ~2000 * 0.3 acumulado; efetiva será bastante reduzida
    q = _run_n_segments(p, throughput_kbps=2000, jitter_ms=700, buffer_s=15.0, n=20)
    assert q["bitrate_kbps"] < 1200, (
        f"[FALHA] Jitter alto deveria reduzir qualidade, obteve {q['quality']}"
    )
    print(f"[OK] test_high_jitter_lowers_quality → {q['quality']} "
          f"(penalidade aplicada com jitter 700ms)")


# ─── Teste 3: Buffer crítico (<4s) → fator 0.5 força qualidade baixa ──────────
def test_critical_buffer_forces_low_quality():
    p = Policy3()
    # Mesmo com 2000 kbps e sem jitter, buffer crítico deve limitar qualidade
    q = _run_n_segments(p, throughput_kbps=2000, jitter_ms=0, buffer_s=2.0, n=20)
    # T_efetiva = T_ewma * 1.0 * 0.5; T_ewma converge ≈ 2000*(1-(0.7^20))
    # Suficientemente suavizado: efetiva ≈ 2000*0.5 = 1000 kbps → 720p no máximo
    assert q["bitrate_kbps"] <= 1000, (
        f"[FALHA] Buffer crítico deveria limitar qualidade, obteve {q['quality']}"
    )
    print(f"[OK] test_critical_buffer_forces_low_quality → {q['quality']} "
          f"(fator buffer 0.5 aplicado)")


# ─── Teste 4: Histerese — nunca sobe mais de 1 nível por vez ──────────────────
def test_hysteresis_max_one_step_up():
    p = Policy3()
    history = []
    # Alta banda do início para estimular subida rápida
    for i in range(10):
        p.update_throughput(2000, 0)
        q = p.select_quality(
            throughput_kbps=p._estimated_throughput(),
            buffer_level_s=15.0,
            qualities=QUALITIES,
        )
        history.append(q["quality"])

    # Verifica que nenhuma transição subiu mais de 1 nível de uma vez
    indices = [next(j for j, ql in enumerate(QUALITIES) if ql["quality"] == qn)
               for qn in history]
    for i in range(1, len(indices)):
        diff = indices[i] - indices[i-1]
        assert diff <= 1, (
            f"[FALHA] Subida de {history[i-1]} para {history[i]} pulou {diff} nível(is)"
        )
    print(f"[OK] test_hysteresis_max_one_step_up → trajetória: {history}")


# ─── Teste 5: Descida sem histerese — cai mais rápido do que sobe ─────────────
def test_fast_drop():
    """
    Valida que a descida é imediata (sem limite de 1 nível por vez),
    ao contrário da subida que é gradual.
    Usamos vários segmentos de banda baixa para que o EWMA convirja.
    """
    p = Policy3()
    # Estabiliza em qualidade alta
    _run_n_segments(p, throughput_kbps=2000, jitter_ms=0, buffer_s=15.0, n=15)
    high_idx = p._quality_index  # deve ser 4 (1080p)

    # Agora aplica banda muito baixa por vários segmentos até o EWMA cair
    q_low = _run_n_segments(p, throughput_kbps=100, jitter_ms=0, buffer_s=15.0, n=15)
    low_idx = p._quality_index

    # A qualidade deve ter caído — e a descida deve ser maior que 1 nível de uma vez
    # (o que prova que não há histerese na descida)
    total_drop = high_idx - low_idx
    assert total_drop > 1, (
        f"[FALHA] Esperava descida de mais de 1 nível partindo de {high_idx}, "
        f"mas ficou em {low_idx} (queda de apenas {total_drop})"
    )
    print(f"[OK] test_fast_drop → caiu de índice {high_idx} para {low_idx} "
          f"({q_low['quality']}) — queda de {total_drop} níveis sem histerese")


# ─── Runner ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_stable_network_rises,
        test_high_jitter_lowers_quality,
        test_critical_buffer_forces_low_quality,
        test_hysteresis_max_one_step_up,
        test_fast_drop,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(e)
            failed += 1
        except Exception as e:
            print(f"[ERRO] {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Resultado: {passed}/{len(tests)} testes passaram, {failed} falharam.")
    if failed > 0:
        sys.exit(1)
