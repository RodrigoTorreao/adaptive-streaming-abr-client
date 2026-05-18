"""
Entry point — orchestrates the full download loop for Entrega 1.

Usage:
    python main.py

For Entrega 2+, extend with: --policy 2|3, --server-a <url>, --server-b <url>
"""

import time
from config import SERVER_A, NUM_SEGMENTS, OUTPUT_CSV, SEGMENT_DURATION
from manifest import fetch_manifest, parse_servers, parse_qualities
from downloader import download_segment
from buffer import BufferManager
from metrics import MetricsLogger, generate_graphs
from abr.rate_based import RateBasedPolicy


def main():
    # 1. Fetch manifest and extract server list + quality representations
    manifest = fetch_manifest(SERVER_A)
    servers = parse_servers(manifest)      # ordered by priority
    qualities = parse_qualities(manifest)  # ordered by bitrate ascending

    # 2. Instantiate components
    abr = RateBasedPolicy()
    buf = BufferManager()
    logger = MetricsLogger(OUTPUT_CSV)

    server_url = servers[0]   # Entrega 1: always Server A
    jitter_ewma = 0.0
    ewma_alpha = 0.2          # smoothing factor for jitter EWMA
    failover_total = 0
    last_segment_time = time.time()

    # 3. Download loop
    for seg_num in range(1, NUM_SEGMENTS + 1):

        # 3a. Update buffer with real time elapsed since last segment
        now = time.time()
        buf.consume(now - last_segment_time)
        last_segment_time = now

        # 3b. Record buffer state before the ABR decision
        buffer_can_play = 1 if buf.can_play() else 0

        # 3c. ABR decision (throughput = 0 on first segment → picks lowest quality)
        chosen = abr.select_quality(
            throughput_kbps=abr._estimated_throughput(),
            buffer_level_s=buf.buffer_level_s,
            qualities=qualities,
        )

        # 3d. Download segment
        result = download_segment(server_url, chosen, seg_num)

        # 3e. Update ABR throughput history
        abr.update_throughput(result.throughput_kbps)

        # 3f. Update jitter EWMA
        jitter_ewma = ewma_alpha * result.jitter_network_ms + (1 - ewma_alpha) * jitter_ewma

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
            f"vazao={result.throughput_kbps:7.0f} kbps  "
            f"buffer={buf.buffer_level_s:.1f}s  "
            f"can_play={buffer_can_play}"
        )

    # 4. Finalize
    logger.close()
    generate_graphs(OUTPUT_CSV)
    print(f"\nMetrics saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
