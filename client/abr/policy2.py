"""
Política 2 — Buffer-Based ABR (Entrega 2).

Seleciona a qualidade do próximo segmento com base no nível atual do buffer,
ignorando throughput instantâneo. Isso produz decisões mais estáveis, pois o
buffer absorve variações momentâneas de rede.

Lógica de decisão (limiares definidos em config.py):
    buffer < BUFFER_MIN_S  → qualidade mínima (modo emergência)
    buffer < BUFFER_LOW_S  → desce um nível
    buffer < BUFFER_HIGH_S → mantém qualidade atual
    buffer < BUFFER_MAX_S  → sobe um nível
    buffer >= BUFFER_MAX_S → qualidade máxima
"""

from config import BUFFER_MIN_S, BUFFER_LOW_S, BUFFER_HIGH_S, BUFFER_MAX_S, THROUGHPUT_WINDOW
from abr.base import ABRPolicy


class Policy2(ABRPolicy):
    def __init__(self):
        self._quality_index: int = 0               # índice atual em qualities[]
        self._throughput_history: list[float] = [] # mantido para compatibilidade com main.py

    # ── Throughput tracking (exigido por main.py) ─────────────────────────────

    def update_throughput(self, measured_kbps: float, jitter_ms: float = 0.0) -> None:
        self._throughput_history.append(measured_kbps)
        if len(self._throughput_history) > THROUGHPUT_WINDOW:
            self._throughput_history.pop(0)

    def _estimated_throughput(self) -> float:
        if not self._throughput_history:
            return 0.0
        return sum(self._throughput_history) / len(self._throughput_history)

    # ── Decisão de qualidade ──────────────────────────────────────────────────

    def select_quality(
        self,
        throughput_kbps: float,
        buffer_level_s: float,
        qualities: list[dict],
    ) -> dict:
        max_index = len(qualities) - 1

        if buffer_level_s < BUFFER_MIN_S:
            # Emergência: buffer crítico, pede o mínimo independente do histórico
            self._quality_index = 0

        elif buffer_level_s < BUFFER_LOW_S:
            # Buffer baixo: desce um nível
            self._quality_index = max(0, self._quality_index - 1)

        elif buffer_level_s <= BUFFER_HIGH_S:
            # Zona neutra: mantém qualidade atual
            pass

        elif buffer_level_s < BUFFER_MAX_S:
            # Buffer confortável: sobe um nível
            self._quality_index = min(max_index, self._quality_index + 1)

        else:
            # Buffer cheio: qualidade máxima disponível
            self._quality_index = max_index

        return qualities[self._quality_index]
