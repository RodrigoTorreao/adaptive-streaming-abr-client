"""
Fetches and parses the manifest JSON from the server.

Manifest format (v2.0):
{
  "servers": [{"id": "A", "url": "...", "priority": 1}, ...],
  "representations": [{"quality": "240p", "bitrate_kbps": 200, "segment_size_kb": 25}, ...]
}
"""
import urllib.request
import json


def fetch_manifest(server_url: str) -> dict:
    """
    Faz a requisição HTTP GET para o servidor e baixa o arquivo de manifesto JSON.
    """

    # Ajusta o url removendo '/' duplicada se houver.
    url = f"{server_url.rstrip('/')}/manifest"

    # Cria requisição com cabeçalho de identificação do nosso grupo.
    req = urllib.request.Request(url, headers={'User-Agent': 'GRUPO 6'})

    # Abre conexão com timeout de 5 segundos.
    # A conexão é fechada automaticamente após o término
    with urllib.request.urlopen(req, timeout=5.0) as response:
        # 1. response.read() baixa os bytes do servidor.
        # 2. .decode('utf-8') transforma os bytes em uma string.
        # 3. json.loads() converte a string de texto contendo o JSON em um dicionário.
        return json.loads(response.read().decode('utf-8'))


def parse_servers(manifest: dict) -> list[str]:
    """
    Extrai a lista de servidores disponíveis e os ordena por prioridade (menor valor = maior prioridade).
    """
    # sorted() varre a lista que está na chave 'servers'.
    # key utiliza a função lambda para dizer como comparar os servidores:
    # x.get('priority', 1) tenta pegar o valor de 'priority'. 
    # Se o servidor não tiver essa chave, ele assume o valor padrão 1.
    sorted_servers = sorted(manifest['servers'], key=lambda x: x.get('priority', 1))
    return [srv['url'] for srv in sorted_servers]


def parse_qualities(manifest: dict) -> list[dict]:
    """
    Extrai as representações de vídeo do manifesto v2.0 e as ordena por taxa de bits (bitrate).
    """

    # Acessa a lista de perfis de vídeo dentro da chave 'representations'.
    # Ordena a lista usando o 'bitrate_kbps'.
    # Por padrão, a ordenação é crescente (ex. 200, 400, 700, 1500, 3000).
    # Começa a simulação na qualidade mais baixa e melhora com o tempo.

    return sorted(manifest['representations'], key=lambda x: x['bitrate_kbps'])