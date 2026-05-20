import sys
import os

# 1. Ajusta o caminho para o Python encontrar os arquivos da raiz
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Importa direto o MetricsLogger e a função de gráficos do seu arquivo real
from metrics import MetricsLogger, generate_graphs

def test_metrics_and_graphs():
    print("--- Iniciando Testes do MetricsLogger e Geração de Gráficos ---\n")
    
    csv_teste = "test_simulation_metrics.csv"
    
    # Apaga resíduos de testes anteriores
    for arquivo in [csv_teste, 'graph_throughput_quality.png', 'graph_buffer.png']:
        if os.path.exists(arquivo):
            os.remove(arquivo)

    try:
        print("1. Inicializando MetricsLogger e simulando gravação de dados...")
        logger = MetricsLogger(csv_teste)
        
        # 2. ADAPTAÇÃO IMPORTANTE: Use exatamente os nomes das colunas que você escreveu 
        # dentro do seu arquivo 'metrics.py' (df['vazao_kbps'], df['bitrate_kbps'], etc.)
        dados_simulados = [
            {"segment": 1, "vazao_kbps": 2500, "bitrate_kbps": 400,  "buffer_level_s": 4.0,  "rebuffer_event": 0},
            {"segment": 2, "vazao_kbps": 3200, "bitrate_kbps": 1500, "buffer_level_s": 6.0,  "rebuffer_event": 0},
            {"segment": 3, "vazao_kbps": 300,  "bitrate_kbps": 1500, "buffer_level_s": 2.0,  "rebuffer_event": 0},
            {"segment": 4, "vazao_kbps": 150,  "bitrate_kbps": 700,  "buffer_level_s": 0.0,  "rebuffer_event": 1},
            {"segment": 5, "vazao_kbps": 1200, "bitrate_kbps": 200,  "buffer_level_s": 3.5,  "rebuffer_event": 0},
        ]
        
        # Grava linha por linha simulando o loop da main
        for linha in dados_simulados:
            logger.log_segment(linha)
            
        logger.close()
        
        assert os.path.exists(csv_teste), "Erro: O arquivo CSV de teste não foi criado no disco."
        print("✓ Arquivo CSV gerado e preenchido perfeitamente.")

        # Teste 2: Geração de Gráficos
        print("\n2. Processando o CSV e gerando os gráficos automáticos...")
        generate_graphs(csv_teste)
        
        assert os.path.exists('graph_throughput_quality.png'), "Erro: Gráfico 1 não foi salvo."
        assert os.path.exists('graph_buffer.png'), "Erro: Gráfico 2 não foi salvo."
        
        print("✓ Gráficos criados com sucesso na raiz do projeto!")
        print("\n--- TUDO CERTINHO! Todos os testes de métricas passaram. ---")

    except Exception as e:
        print(f"\n Falha no teste de métricas: {e}")
        

if __name__ == "__main__":
    test_metrics_and_graphs()