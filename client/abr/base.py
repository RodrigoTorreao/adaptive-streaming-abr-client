"""
Abstract base class for all ABR (Adaptive Bitrate) policies.

Each policy receives the current network estimate and buffer level, and
returns the quality dict (from the manifest) to request for the next segment.
"""


class ABRPolicy:
    def select_quality(
        self,
        throughput_kbps: float,
        buffer_level_s: float,
        qualities: list[dict],
    ) -> dict:
        """
        Choose a quality representation for the next segment.

        Args:
            throughput_kbps: estimated available bandwidth (kbps)
            buffer_level_s:  current buffer level in seconds
            qualities:       list of dicts from manifest, sorted by bitrate ascending

        Returns:
            One dict from qualities (e.g. {"quality": "720p", "bitrate_kbps": 1000, ...})
        """
        raise NotImplementedError
