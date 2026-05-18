"""
Política 3 — Componente estatístico ou heurístico (Entrega Final).

Deve incorporar ao menos um dos seguintes:
  - EWMA: throughput recente tem peso maior que o passado distante
  - Detecção de tendência: antecipar redução se vazão está caindo
  - Desvio padrão: usar vazao_media - k * std como estimativa conservadora
  - Política híbrida: combinar nível de buffer e vazão com pesos ajustáveis
  - Penalidade de jitter: reduzir estimativa de vazão proporcionalmente ao jitter

Deve tratar explicitamente o cenário de jitter alto.
"""

from abr.base import ABRPolicy


class Policy3(ABRPolicy):
    def select_quality(self, throughput_kbps, buffer_level_s, qualities):
        raise NotImplementedError
