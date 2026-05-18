"""
Política 2 — (Entrega 2, a definir pelo grupo).

Sugestões:
  - Buffer-Based ABR: decide qualidade com base no nível do buffer
  - Rate-Based com histerese: só muda qualidade após N segmentos consecutivos
  - Conservador com slow-start: começa em 240p e sobe gradualmente

Deve também integrar o failover (ver failover.py).
"""

from abr.base import ABRPolicy


class Policy2(ABRPolicy):
    def select_quality(self, throughput_kbps, buffer_level_s, qualities):
        raise NotImplementedError
