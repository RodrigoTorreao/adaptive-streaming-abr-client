import sys
import os

# 1. Descobre o caminho da pasta raiz (um nível acima da pasta 'test')
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 2. Garante que a raiz do projeto seja a PRIMEIRA prioridade na busca do Python
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Agora o Python vai direto na raiz buscar o downloader.py verdadeiro!
from downloader import download_segment, SegmentResult
from config import SERVER_A

#Selecione aqui a qualidade [240, 360, 480, 720, 1080]
quality = 240

def test_downloader_real():
    print(f"--- Teste Downloader: {SERVER_A} ---\n")
    
    # Simulamos exatamente o bloco de 200 kbps que veio no manifesto do professor
    fake_quality = {
        "quality": f"{quality}p",
        "bitrate_kbps": 200,
        "segment_bytes": 25000,
        "url_path": "/segment/240p"
    }
    segment_num = 1
    
    try:
        print(f"1. Enviando requisição para o Segmento {segment_num} (Qualidade: {fake_quality['quality']})...")
        result = download_segment(SERVER_A, fake_quality, segment_num)
        
        print("✓ Resposta recebida")
        print("-" * 50)
        print(f" -> Bytes baixados: {result.bytes_total} Bytes")
        print(f" -> Tempo gasto:   {result.download_time_s:.4f} segundos")
        print(f" -> Vazão medida:  {result.throughput_kbps:.2f} kbps")
        print(f" -> Jitter (Rede): {result.jitter_network_ms:.4f} ms")
        print("-" * 50)
        
        assert isinstance(result, SegmentResult)
        assert result.bytes_total > 0
        assert result.throughput_kbps > 0
        assert result.jitter_network_ms >= 0
        
        print("\nDeu certo")

    except Exception as e:
        print(f"\nFalha no teste do downloader: {e}")

if __name__ == "__main__":
    test_downloader_real()