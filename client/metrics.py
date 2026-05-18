"""
Handles CSV logging of per-segment metrics and matplotlib graph generation.

CSV fields (in order):
  segment, timestamp, server_id, quality, bitrate_kbps, vazao_kbps,
  download_time_s, jitter_network_ms, jitter_ewma_ms, buffer_level_s,
  buffer_can_play, rebuffer_event, stall_duration_s, failover_total
"""

CSV_FIELDS = [
    "segment", "timestamp", "server_id", "quality", "bitrate_kbps",
    "vazao_kbps", "download_time_s", "jitter_network_ms", "jitter_ewma_ms",
    "buffer_level_s", "buffer_can_play", "rebuffer_event",
    "stall_duration_s", "failover_total",
]


class MetricsLogger:
    def __init__(self, output_file: str):
        """Open output_file for writing and write the CSV header row."""
        self.output_file = output_file
        self._file = None
        self._writer = None
        pass

    def log_segment(self, row: dict) -> None:
        """Write one CSV row for a single segment. row keys must match CSV_FIELDS."""
        pass

    def close(self) -> None:
        """Flush and close the CSV file."""
        pass


def generate_graphs(csv_path: str) -> None:
    """
    Read the CSV at csv_path and produce two PNG files:

    1. graph_throughput_quality.png
       - Primary axis: vazao_kbps per segment (line)
       - Secondary axis: quality as a step plot (or numeric bitrate)

    2. graph_buffer.png
       - buffer_level_s over time
       - Vertical markers where rebuffer_event == 1
    """
    pass
