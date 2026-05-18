"""
Downloads a single video segment from the server and measures network metrics.

Reads the HTTP response in chunks (config.CHUNK_SIZE bytes each), recording the
arrival time of each chunk to compute intra-segment jitter.
"""

from dataclasses import dataclass


@dataclass
class SegmentResult:
    bytes_total: int
    download_time_s: float
    throughput_kbps: float
    jitter_network_ms: float  # std-dev of inter-chunk arrival intervals


def download_segment(server_url: str, quality: dict, segment_num: int) -> SegmentResult:
    """
    Download one segment at the given quality from server_url.

    URL pattern expected: GET /segment?quality=<quality>&n=<segment_num>
    (adjust if the actual server API differs after reading the manifest).

    Steps:
    1. Open HTTP connection to server_url/segment endpoint
    2. Read response in CHUNK_SIZE chunks, recording time of each chunk arrival
    3. Compute throughput = bytes_total / download_time_s (convert to kbps)
    4. Compute jitter_network = std-dev of intervals between consecutive chunk arrivals (ms)
    5. Return SegmentResult
    """
    pass
