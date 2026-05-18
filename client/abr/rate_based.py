"""
Política 1 — Rate-Based ABR (Entrega 1 / Baseline).

Selects the highest quality whose bitrate fits within the estimated
available bandwidth, applying a safety factor to avoid overestimation.

Known limitations (to be addressed in Entrega 2):
- Reacts to instantaneous throughput, causing quality oscillation on
  unstable networks.
- Does not consider buffer level in the decision.
- No hysteresis: can flip quality up/down between consecutive segments.
"""

from config import SAFETY_FACTOR, THROUGHPUT_WINDOW
from abr.base import ABRPolicy


class RateBasedPolicy(ABRPolicy):
    def __init__(self, safety_factor: float = SAFETY_FACTOR, window: int = THROUGHPUT_WINDOW):
        self.safety_factor = safety_factor
        self.window = window
        self._throughput_history: list[float] = []

    def update_throughput(self, measured_kbps: float) -> None:
        """Record a new throughput measurement (call after each download)."""
        pass

    def _estimated_throughput(self) -> float:
        """Return average of the last `window` throughput measurements."""
        pass

    def select_quality(
        self,
        throughput_kbps: float,
        buffer_level_s: float,
        qualities: list[dict],
    ) -> dict:
        """
        Algorithm:
          effective = avg(last WINDOW measurements) * safety_factor
          pick the highest quality where bitrate_kbps <= effective
          fallback to lowest quality if none fits
        """
        pass
