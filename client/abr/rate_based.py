"""
Política 1 — Rate-Based ABR (Entrega 1 / Baseline).

Seleciona a maior qualidade cujo bitrate caiba dentro da banda estimada
disponível, aplicando um fator de segurança para evitar superestimar a rede.
"""

from config import SAFETY_FACTOR, THROUGHPUT_WINDOW
from abr.base import ABRPolicy


class RateBasedPolicy(ABRPolicy):
    def __init__(self, safety_factor: float = SAFETY_FACTOR, window: int = THROUGHPUT_WINDOW):
        self.safety_factor = safety_factor
        self.window = window
        self._throughput_history: list[float] = []

    def update_throughput(self, measured_kbps: float) -> None:
        """Registra uma nova medição de vazão (após cada download)."""
        self._throughput_history.append(measured_kbps)
        if len(self._throughput_history) > self.window:
            self._throughput_history.pop(0)

    def _estimated_throughput(self) -> float:
        """Retorna a média das últimas medições de vazão da janela."""
        if not self._throughput_history:
            return 0.0  
        
        # Média aritmética simples dos valores salvos no histórico
        return sum(self._throughput_history) / len(self._throughput_history)

    def select_quality(
        self,
        throughput_kbps: float,
        buffer_level_s: float,
        qualities: list[dict],
    ) -> dict:
        """
        Algoritmo:
          vazao_efetiva = media(ultimas N medicoes) * fator_seguranca
          escolhe a maior qualidade onde bitrate_kbps <= vazao_efetiva
          retorna a menor qualidade (fallback) se nenhuma couber
        """
        # Aplica o fator de segurança
        effective_throughput = throughput_kbps * self.safety_factor
        
        # Como 'qualities' já vem ordenada do menor para o maior, percorremos a 
        # lista de trás para frente para achar a maior qualidade que cabe.
        for q in reversed(qualities):
            if q['bitrate_kbps'] <= effective_throughput:
                return q
                
        # Fallback: se a rede não for o suficiente para nenhuma qualidade pega a
        #  menor disponível
        return qualities[0]
