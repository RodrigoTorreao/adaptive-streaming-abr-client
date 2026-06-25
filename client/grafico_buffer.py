import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def gerar_grafico_buffer(csv_path, output_img="grafico_buffer_nivel.png"):
    if not os.path.exists(csv_path):
        print(f"Erro: O arquivo {csv_path} não foi encontrado.")
        return

    # Carrega os dados do CSV
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(12, 6))

    # Plota a evolução do Buffer
    plt.plot(df['segment'], df['buffer_level_s'], color='green', linewidth=2.5, 
             label='Nível do Buffer (s)')

    # Marcações de Rebuffering (quando buffer chega a zero e trava)
    if 'rebuffer_event' in df.columns:
        rebuffer_segments = df[df['rebuffer_event'] == 1]['segment']
        for i, seg in enumerate(rebuffer_segments):
            plt.axvline(x=seg, color='red', linestyle=':', linewidth=2, 
                        label='Rebuffering' if i == 0 else "")

    # Marcações de Failover (queda do servidor)
    if 'failover_total' in df.columns:
        failover_segments = df[df['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
        for i, seg in enumerate(failover_segments):
            plt.axvline(x=seg, color='purple', linestyle='--', linewidth=2, 
                        label='Failover' if i == 0 else "")

    # Linhas de referência para facilitar a leitura do gráfico
    plt.axhline(y=30, color='gray', linestyle='-.', alpha=0.5, label='Cap Máximo (30s)')
    plt.axhline(y=4, color='orange', linestyle='-.', alpha=0.5, label='Buffer Mínimo (4s)')

    plt.xlabel('Número do Segmento', fontsize=12)
    plt.ylabel('Tamanho do Buffer (segundos)', fontsize=12)
    plt.title('Evolução do Nível do Buffer ao Longo do Tempo', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Coloca a legenda no canto superior esquerdo ou direito
    plt.legend(loc='upper right', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico do buffer gerado com sucesso e salvo como: {output_img}")
    plt.close()

if __name__ == "__main__":
    # Permite passar o CSV como argumento. Por padrão, usa a Política 2 (que tem Failover configurado).
    csv_file = "metrics_policy2.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    # Se metrics_policy2.csv não existir, tenta policy3 ou policy1
    if not os.path.exists(csv_file):
        if os.path.exists("metrics_policy3.csv"):
            csv_file = "metrics_policy3.csv"
        elif os.path.exists("metrics_policy1.csv"):
            csv_file = "metrics_policy1.csv"

    gerar_grafico_buffer(csv_file)
