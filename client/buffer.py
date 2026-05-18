"""
Manages the playback buffer level in seconds of video content.

The buffer grows when a segment is received and shrinks in real time as
content is consumed. If the buffer reaches 0 while the next segment has
not arrived yet, a rebuffering (stall) event occurs.
"""

from config import MIN_BUFFER_TO_PLAY, SEGMENT_DURATION


class BufferManager:
    def __init__(self):
        self.buffer_level_s: float = 0.0

    def add_segment(self, duration_s: float = SEGMENT_DURATION) -> None:
        """Add duration_s seconds of content to the buffer after a successful download."""
        pass

    def consume(self, elapsed_s: float) -> None:
        """Subtract elapsed real time from the buffer (floor at 0)."""
        pass

    def can_play(self, min_buffer: float = MIN_BUFFER_TO_PLAY) -> bool:
        """Return True if buffer_level_s >= min_buffer (continuous play possible)."""
        pass

    def check_rebuffer(self) -> tuple[bool, float]:
        """
        Detect whether a rebuffering event just occurred.

        Returns (rebuffer_event: bool, stall_duration_s: float).
        stall_duration_s is 0.0 if no stall happened.
        """
        pass
