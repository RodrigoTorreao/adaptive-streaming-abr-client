"""
Manages the playback buffer level in seconds of video content.

The buffer grows when a segment is received and shrinks in real time as
content is consumed. If the buffer reaches 0 while the next segment has
not arrived yet, a rebuffering (stall) event occurs.
"""

from config import MIN_BUFFER_TO_PLAY, SEGMENT_DURATION


class BufferManager:
    def __init__(self):
        self.buffer_level_s: float = 0.0 # Quantos segundos de vídeo estão baixados, o buffer mínimo esta em 4
        self._had_stall: bool = False # Avisa se o vídeo travou, apenas uma flag
        self._stall_duration: float = 0.0 # Duração do travamento em segundos

    def add_segment(self, duration_s: float = SEGMENT_DURATION) -> None:
        self.buffer_level_s += duration_s # Adiciona no buffer a quantidade de tempo baixada
        pass

    def consume(self, elapsed_s: float) -> None:
        """
        Essa função tem como objetivo medir o buffer, possibilitando a visualização

        Na função, temos 3 possibilidades:
            1° - O buffer era suficiente e aguenta o tempo de download do proximo
            segmento (4s)
            2° - O buffer não era suficiente e acaba travando, nesse momento 
            contamos a quantidade de stall que tivemos
            3° - O buffer estava vazio, portanto todo o tempo decorrido é stall
        """
        if self.buffer_level_s > 0:
            if self.buffer_level_s >= elapsed_s:
                self.buffer_level_s -= elapsed_s
                self._had_stall = False
                self._stall_duration = 0.0
            else:
                # O tempo decorrido foi maior que o buffer restante: houve stall parcial
                remainder = elapsed_s - self.buffer_level_s
                self.buffer_level_s = 0.0
                self._had_stall = True
                self._stall_duration = remainder
        else:
            # O buffer já estava zerado, todo o tempo decorrido foi de stall
            self._had_stall = True
            self._stall_duration = elapsed_s
        pass

    def can_play(self, min_buffer: float = MIN_BUFFER_TO_PLAY) -> bool:
        """Return True if return self.buffer_level_s >= min_bufferreturn self.buffer_level_s >= min_buffer >= min_buffer (continuous play possible)."""
        return self.buffer_level_s >= min_buffer

    def check_rebuffer(self) -> tuple[bool, float]:
        """
        Detect whether a rebuffering event just occurred.

        Returns (rebuffer_event: bool, stall_duration_s: float).
        stall_duration_s is 0.0 if no stall happened.
        """
        return self._had_stall, self._stall_duration
