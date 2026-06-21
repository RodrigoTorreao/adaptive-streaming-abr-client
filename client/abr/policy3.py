"""
Política 3 — ABR Estatístico/Heurístico (Apresentação Final).

Combina quatro mecanismos para decisões mais robustas em cenários de alto jitter:

  1. EWMA de throughput  — suaviza picos/quedas momentâneas de banda
  2. EWMA de jitter      — acompanha tendência de variação de latência
  3. Penalidade de jitter — reduz a banda efetiva proporcionalmente ao jitter acumulado
  4. Fator de buffer     — ajusta agressividade conforme segurança do buffer
  5. Histerese           — sobe no máximo 1 nível por segmento; desce imediatamente

Fórmulas (ver documentation/implementation_plan.md para derivação):
    T_ewma(n)    = α × T_medido(n)  + (1-α) × T_ewma(n-1)         α = 0.3
    J_ewma(n)    = β × J_medido(n)  + (1-β) × J_ewma(n-1)         β = 0.3
    Penalidade   = min(0.5, γ × J_ewma / 1000)                     γ = 1.0
    FatorBuffer  = 0.5 (<4s) | 0.7 (<8s) | 0.9 (<12s) | 1.0 (≥12s)
    T_efetiva    = T_ewma × (1 - Penalidade) × FatorBuffer
"""

from abr.base import ABRPolicy

_ALPHA = 0.3   # suavização do throughput EWMA
_BETA  = 0.3   # suavização do jitter EWMA
_GAMMA = 1.0   # coeficiente de penalidade de jitter


class Policy3(ABRPolicy):
    def __init__(self):
        self._throughput_ewma: float = 0.0
        self._jitter_ewma: float = 0.0
        self._quality_index: int = 0

    # ── Throughput e jitter tracking ─────────────────────────────────────────

    def update_throughput(self, measured_kbps: float, jitter_ms: float = 0.0) -> None:
        self._throughput_ewma = _ALPHA * measured_kbps + (1 - _ALPHA) * self._throughput_ewma
        self._jitter_ewma     = _BETA  * jitter_ms     + (1 - _BETA)  * self._jitter_ewma

    def _estimated_throughput(self) -> float:
        return self._throughput_ewma

    # ── Cálculos internos ────────────────────────────────────────────────────

    def _jitter_penalty(self) -> float:
        return min(0.5, _GAMMA * self._jitter_ewma / 1000.0)

    def _buffer_factor(self, buffer_level_s: float) -> float:
        if buffer_level_s < 4.0:
            return 0.5   # crítico: muito conservador
        if buffer_level_s < 8.0:
            return 0.7   # baixo: conservador
        if buffer_level_s < 12.0:
            return 0.9   # alerta: levemente conservador
        return 1.0        # confortável: sem penalidade de buffer

    # ── Decisão de qualidade ─────────────────────────────────────────────────

    def select_quality(
        self,
        throughput_kbps: float,
        buffer_level_s: float,
        qualities: list[dict],
    ) -> dict:
        penalty  = self._jitter_penalty()
        factor   = self._buffer_factor(buffer_level_s)
        effective = self._throughput_ewma * (1 - penalty) * factor

        max_index = len(qualities) - 1

        # Maior qualidade que cabe dentro da banda efetiva
        target_index = 0
        for i, q in enumerate(qualities):
            if q["bitrate_kbps"] <= effective:
                target_index = i

        # Histerese: sobe no máximo 1 nível, desce imediatamente
        if target_index > self._quality_index:
            self._quality_index = self._quality_index + 1
        else:
            self._quality_index = target_index

        self._quality_index = max(0, min(max_index, self._quality_index))
        return qualities[self._quality_index]
