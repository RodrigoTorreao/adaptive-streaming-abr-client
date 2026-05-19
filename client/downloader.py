"""
Downloads a single video segment from the server and measures network metrics.

Reads the HTTP response in chunks (config.CHUNK_SIZE bytes each), recording the
arrival time of each chunk to compute intra-segment jitter.
"""

from dataclasses import dataclass

import time
import urllib.request

import numpy as np

from config import CHUNK_SIZE, IDENTIFY_HEADER


@dataclass
class SegmentResult:
    bytes_total: int          # Tamanho total do segmento
    download_time_s: float    # Quantos segundos demorou a transferência
    throughput_kbps: float    # Vazão da rede
    jitter_network_ms: float  # Jitter (instabilidade)


def download_segment(server_url: str, quality: dict, segment_num: int) -> SegmentResult:
    """
    Download one segment at the given quality from server_url.

    URL pattern expected: GET /segment?quality=<quality>&n=<segment_num>
    (adjust if the actual server API differs after reading the manifest).

    Steps:
    1. Open HTTP connection to server_url/segment endpoint
    2. Read response in CHUNK_SIZE chunks, recording time of each chunk arrival
    3. Compute throughput = bytes_total / download_time_s (convert to kbps)
    4. Compute jitter_network = std-dev of intervals between consecutive chunk arrivals (ms)
    5. Return SegmentResult
    """

    path = quality['url_path'].lstrip('/')
    url = f"{server_url.rstrip('/')}/{path}?n={segment_num}"
    req = urllib.request.Request(url, headers={'User-Agent': IDENTIFY_HEADER})

    chunk_timestamps = [] # Registro do instante em que cada chunk foi recebido

    bytes_total = 0 # Tamanho total do arquivo

    t_start = time.time() # Tempo inicial

    with urllib.request.urlopen(req, timeout=5.0) as response:
        """
        Inicia a conexão com limite de espera em 5 segundos
        """
        while True:
            # Baixa os dados em tamanho fixo (CHUNK_SIZE = 4096).
            chunk = response.read(CHUNK_SIZE)
            
            # Se o chunk for vazio, arquivo terminou de baixar.
            if not chunk:
                break
            
            # Registra o instante em que terminou de ser recebido
            chunk_timestamps.append(time.time())
            # Soma a quantidade de bytes recebida neste bloco ao total acumulado
            bytes_total += len(chunk)
            
    # Marca o tempo final após o encerramento do download
    t_end = time.time()

    # Tempo de download total em segundos
    download_time_s = t_end - t_start
    if download_time_s <= 0:
        # Evita erro matemático da divisão por 0
        download_time_s = 0.001

    # CÁLCULO DA VAZÃO (THROUGHPUT):
    throughput_kbps = ((bytes_total * 8) / 1000.0) / download_time_s

    # CÁLCULO Do JITTER:
    jitter_network_ms = 0.0

    # Só faz sentido calcular a variação se tivermos recebido pelo menos 2 pedaços de dados
    if len(chunk_timestamps) > 1:
        
        # Calcula os intervalos de recebimento e 1000.0 para converter esses intervalos de
        # segundos para milissegundos.
        intervals_ms = np.diff(chunk_timestamps) * 1000.0
        
        # Define os Graus de Liberdade (ddof) para o cálculo estatístico.
        # Se houver mais de um intervalo, usamos o Desvio Padrão Amostral (ddof=1).
        ddof_val = 1 if len(intervals_ms) > 1 else 0

        # Desvio padrão da oscilação de tempo de chegada dos pacotes é o Jitter
        jitter_network_ms = float(np.std(intervals_ms, ddof=ddof_val))

    return SegmentResult(
        bytes_total=bytes_total,
        download_time_s=download_time_s,
        throughput_kbps=throughput_kbps,
        jitter_network_ms=jitter_network_ms
    )

    pass
