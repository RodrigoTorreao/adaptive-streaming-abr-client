"""
Gerencia o registro de dados em formato CSV e a geração de gráficos com o matplotlib.

CSV fields (in order):
  segment, timestamp, server_id, quality, bitrate_kbps, vazao_kbps,
  download_time_s, jitter_network_ms, jitter_ewma_ms, buffer_level_s,
  buffer_can_play, rebuffer_event, stall_duration_s, failover_total
"""

import csv

from matplotlib import pyplot as plt
import pandas as pd


CSV_FIELDS = [
    "segment", "timestamp", "server_id", "quality", "bitrate_kbps",
    "vazao_kbps", "download_time_s", "jitter_network_ms", "jitter_ewma_ms",
    "buffer_level_s", "buffer_can_play", "rebuffer_event",
    "stall_duration_s", "failover_total",
]


class MetricsLogger:
    def __init__(self, output_file: str):
        """
        Inicializa o registrador de métricas, criando ou limpando o arquivo CSV de saída.
        """
        self.output_file = output_file
        self._file = open(self.output_file, mode='w', newline='')
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS)
        self._writer.writeheader()

    def log_segment(self, row: dict) -> None:
        """
        Escreve uma linha de dados no CSV com as estatísticas do segmento atual.
        """
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        """
        Fecha o arquivo CSV de forma segura
        """
        if self._file:
            self._file.close()


def generate_graphs(csv_path: str) -> None:
    """
    Gera os dois gráficos obrigatórios da Entrega 1 a partir dos dados do CSV.
    """
    # Carrega os dados salvos usando a biblioteca Pandas, transformando o CSV em uma tabela.
    df = pd.read_csv(csv_path)
    
    # -------------------------------------------------------------------------
    # Gráfico 1: Vazão e Qualidade (Bitrate) por segmento
    # -------------------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    ax1.plot(df['segment'], df['vazao_kbps'], color='blue', marker='o', label='Vazão Medida')
    ax1.set_xlabel('Segmento')
    ax1.set_ylabel('Vazão (kbps)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    ax2 = ax1.twinx()  
    
    # O formato em escada é ideal porque o bitrate do vídeo muda de forma abrupta (degraus), nunca suave.
    ax2.step(df['segment'], df['bitrate_kbps'], color='orange', where='mid', label='Bitrate Selecionado', linewidth=2)
    ax2.set_ylabel('Bitrate Nominal (kbps)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    plt.title('Entrega 1 - Vazão vs Qualidade')
    plt.grid(True, linestyle='--')
    
    plt.savefig('graph_throughput_quality.png')
    plt.close() 

    # -------------------------------------------------------------------------
    # Gráfico 2: Nível do Buffer ao longo do tempo (ou segmentos)
    # -------------------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    plt.plot(df['segment'], df['buffer_level_s'], color='green', label='Nível do Buffer', linewidth=2)
    
    # Filtra no Pandas apenas as linhas onde houve um evento de travamento
    rebuffer_segments = df[df['rebuffer_event'] == 1]['segment']
    
    # Desenha marcadores verticais tracejados vermelhos em cada segmento que sofreu stall
    for seg in rebuffer_segments:
        plt.axvline(x=seg, color='red', linestyle=':', label='Rebuffering' if seg == rebuffer_segments.iloc[0] else "")
        
    plt.xlabel('Segmento')
    plt.ylabel('Buffer (segundos)')
    plt.title('Entrega 1 - Evolução do Buffer')
    plt.legend()
    plt.grid(True, linestyle='--')
    
    plt.savefig('graph_buffer.png')
    plt.close()