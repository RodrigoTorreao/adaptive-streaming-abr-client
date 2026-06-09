"""
Entry point — orchestrates the full download loop for Entrega 1.

Usage:
    python main.py

For Entrega 2+, extend with: --policy 2|3, --server-a <url>, --server-b <url>
"""

import time
from config import SERVER_A, NUM_SEGMENTS, OUTPUT_CSV, SEGMENT_DURATION, ACTIVE_POLICY
from manifest import fetch_manifest, parse_servers, parse_qualities
from downloader import download_segment
from buffer import BufferManager
from metrics import MetricsLogger, generate_graphs
from abr.rate_based import RateBasedPolicy


def _build_abr():
    if ACTIVE_POLICY == 1:
        from abr.rate_based import RateBasedPolicy
        return RateBasedPolicy()
    elif ACTIVE_POLICY == 2:
        from abr.policy2 import Policy2
        return Policy2()
    elif ACTIVE_POLICY == 3:
        from abr.policy3 import Policy3
        return Policy3()
    raise ValueError(f"Unknown ACTIVE_POLICY: {ACTIVE_POLICY}")


def _build_failover(servers):
    """Return a FailoverManager for Entrega 2+, or None for Entrega 1."""
    if ACTIVE_POLICY >= 2:
        from failover import FailoverManager
        return FailoverManager(servers)
    return None


def main():
    # 1. Fetch manifest and extract server list + quality representations
    manifest = fetch_manifest(SERVER_A)
    servers = parse_servers(manifest)      # ordered by priority
    qualities = parse_qualities(manifest)  # ordered by bitrate ascending

    # 2. Instantiate components
    abr = _build_abr()
    buf = BufferManager()
    logger = MetricsLogger(OUTPUT_CSV)
    failover = _build_failover(servers)

    # Entrega 1: always Server A. Entrega 2+: managed by FailoverManager.
    server_url = failover.current_server if failover else servers[0]
    jitter_ewma = 0.0
    ewma_alpha = 0.2          # smoothing factor for jitter EWMA
    failover_total = 0

    # 3. Download loop
    for seg_num in range(1, NUM_SEGMENTS + 1):

        # 3a. Record buffer state before the ABR decision.
        # buffer_can_play determines whether the player is playing or stalled
        # during the upcoming download, so it must be checked here — before
        # the segment is fetched — to correctly drive the consume step below.
        buffer_can_play = 1 if buf.can_play() else 0

        # 3b. ABR decision (throughput = 0 on first segment → picks lowest quality)
        chosen = abr.select_quality(
            throughput_kbps=abr._estimated_throughput(),
            buffer_level_s=buf.buffer_level_s,
            qualities=qualities,
        )

        # 3c. Download segment (with failover on error for Entrega 2+)
        try:
            result = download_segment(server_url, chosen, seg_num)
        except Exception:
            if failover:
                server_url = failover.handle_failure()
                failover_total = failover.failover_count
                result = download_segment(server_url, chosen, seg_num)
            else:
                raise

        # 3d. Update ABR throughput history
        abr.update_throughput(result.throughput_kbps)

        # 3e. Update jitter EWMA
        jitter_ewma = ewma_alpha * result.jitter_network_ms + (1 - ewma_alpha) * jitter_ewma

        # 3f. Consume buffer only while the player is actually playing.
        # The exact time to deduct is result.download_time_s: that is how long
        # the download took, which is precisely the real-time interval during
        # which the player would have been consuming content.
        # When buffer_can_play == 0 the player is stalled; no content is consumed
        # but the full download time counts as stall duration.
        if buffer_can_play == 1:
            buf.consume(result.download_time_s)
        else:
            buf._had_stall = True
            buf._stall_duration = result.download_time_s

        # 3g. Update buffer and detect rebuffering
        rebuffer, stall_s = buf.check_rebuffer()
        buf.add_segment(SEGMENT_DURATION)

        # 3h. Log metrics
        import datetime
        logger.log_segment({
            "segment": seg_num,
            "timestamp": datetime.datetime.now().isoformat(),
            "server_id": "A",
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
        })

        print(
            f"[seg {seg_num:02d}] quality={chosen['quality']:5s}  "
            f"vazao={result.throughput_kbps:4.0f} kbps  "
            f"buffer={buf.buffer_level_s:.1f}s  "
            f"can_play={True if buffer_can_play == 1 else False}"        
            )

    # 4. Finalize
    logger.close()
    generate_graphs(OUTPUT_CSV)
    print(f"\nMetrics saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
