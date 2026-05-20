import sys
import os

# Ajusta o caminho para o Python encontrar os módulos da raiz
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Importa a política do arquivo que estamos testando
from abr.rate_based import RateBasedPolicy

def test_rate_based_policy():
    print("--- Teste da Política Rate-Based ---\n")

    # 1. Instanciamos a política com parâmetros conhecidos:
    # Fator de segurança de 0.80 (significa usar apenas 80% da banda informada)
    policy = RateBasedPolicy(safety_factor=0.80, window=3)

    # 2. Copiamos exatamente a lista de representações reais do manifesto do professor
    gabarito_qualidades = [
        {"quality": "240p",  "bitrate_kbps": 200,  "url_path": "/segment/240p"},
        {"quality": "360p",  "bitrate_kbps": 400,  "url_path": "/segment/360p"},
        {"quality": "480p",  "bitrate_kbps": 700,  "url_path": "/segment/480p"},
        {"quality": "720p",  "bitrate_kbps": 1500, "url_path": "/segment/720p"},
        {"quality": "1080p", "bitrate_kbps": 3000, "url_path": "/segment/1080p"}
    ]

    # -------------------------------------------------------------------------
    # Cenário A: Internet de Alta Performance (Banda de 4000 kbps)
    # -------------------------------------------------------------------------
    print("Cenário A: Internet Excelente (4000 kbps)...")
    # Banda efetiva calculada pelo algoritmo: 4000 * 0.8 = 3200 kbps.
    # O maior bitrate que cabe em 3200 kbps é o de 3000 kbps (1080p).
    decisao_A = policy.select_quality(throughput_kbps=4000.0, buffer_level_s=5.0, qualities=gabarito_qualidades)
    print(f" -> Banda Efetiva: 3200 kbps | Qualidade Escolhida: {decisao_A['quality']} ({decisao_A['bitrate_kbps']} kbps)")
    assert decisao_A['quality'] == "1080p", "Erro no Cenário A: Deveria ter escolhido 1080p"
    print("✓ Cenário A passou!\n")

    # -------------------------------------------------------------------------
    # Cenário B: O Impacto do Fator de Segurança (Banda de 1600 kbps)
    # -------------------------------------------------------------------------
    print("Cenário B: O limite do Fator de Segurança (1600 kbps)...")
    # Banda de 1600 kbps parece suficiente para rodar 720p (1500 kbps).
    # MAS, banda efetiva: 1600 * 0.8 = 1280 kbps.
    # Como 1280 kbps NÃO suporta 1500 kbps, o algoritmo DEVE recuar para 480p (700 kbps).
    decisao_B = policy.select_quality(throughput_kbps=1600.0, buffer_level_s=5.0, qualities=gabarito_qualidades)
    print(f" -> Banda Efetiva: 1280 kbps | Qualidade Escolhida: {decisao_B['quality']} ({decisao_B['bitrate_kbps']} kbps)")
    assert decisao_B['quality'] == "480p", "Erro no Cenário B: O fator de segurança deveria ter forçado a queda para 480p"
    print("✓ Cenário B passou!\n")

    # -------------------------------------------------------------------------
    # Cenário C: Internet em Crise - Modo Fallback (Banda de 100 kbps)
    # -------------------------------------------------------------------------
    print("Cenário C: Internet Crítica (100 kbps)...")
    # Banda efetiva: 100 * 0.8 = 80 kbps.
    # 80 kbps é menor do que a qualidade mais baixa do servidor (200 kbps).
    # O algoritmo deve acionar o fallback e devolver o menor perfil (240p).
    decisao_C = policy.select_quality(throughput_kbps=100.0, buffer_level_s=2.0, qualities=gabarito_qualidades)
    print(f" -> Banda Efetiva: 80 kbps | Qualidade Escolhida: {decisao_C['quality']} ({decisao_C['bitrate_kbps']} kbps)")
    assert decisao_C['quality'] == "240p", "Erro no Cenário C: Deveria ter retornado a qualidade mínima de segurança (240p)"
    print("✓ Cenário C passou!\n")

    # -------------------------------------------------------------------------
    # Cenário D: Teste do Histórico e Janela Deslizante
    # -------------------------------------------------------------------------
    print("Cenário D: Testando histórico de média móvel...")
    policy.update_throughput(3000.0)
    policy.update_throughput(4000.0)
    policy.update_throughput(5000.0)
    
    media_calculada = policy._estimated_throughput()
    print(f" -> Média de [3000, 4000, 5000]: {media_calculada} kbps")
    assert media_calculada == 4000.0, "Erro: Média calculada incorretamente."

    # Adiciona mais uma medição para testar se estoura a janela (deve descartar o 3000)
    policy.update_throughput(6000.0)
    nova_media = policy._estimated_throughput()
    print(f" -> Média após janela deslizar [4000, 5000, 6000]: {nova_media} kbps")
    assert nova_media == 5000.0, "Erro: A janela não descartou o valor mais antigo."
    print("✓ Cenário D (Histórico) passou!\n")

    print("--- Tudo certo! ---")

if __name__ == "__main__":
    test_rate_based_policy()