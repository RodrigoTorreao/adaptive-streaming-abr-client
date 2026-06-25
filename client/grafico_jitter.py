import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

def gerar_grafico_jitter(csv_path, output_img="grafico_jitter.png"):
    if not os.path.exists(csv_path):
        print(f"Erro: O arquivo {csv_path} não foi encontrado.")
        return

    # Carrega os dados do CSV
    df = pd.read_csv(csv_path)

    plt.figure(figsize=(10, 5))

    # Plota Jitter Medido
    plt.plot(df['segment'], df['jitter_network_ms'], color='lightgray', marker='.', 
             label='Jitter Medido (ms)', alpha=0.8)
    
    # Plota Jitter EWMA (Média Móvel)
    plt.plot(df['segment'], df['jitter_ewma_ms'], color='red', marker='o', 
             label='Jitter EWMA (ms)', linewidth=2.5)

    # Marcações de failover, se existirem
    if 'failover_total' in df.columns:
        failover_segments = df[df['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
        for i, seg in enumerate(failover_segments):
            plt.axvline(x=seg, color='purple', linestyle='--', linewidth=1.5,
                        label='Failover' if i == 0 else "")

    plt.xlabel('Segmento', fontsize=12)
    plt.ylabel('Jitter (ms)', fontsize=12)
    plt.title('Variação de Atraso: Jitter Medido vs Jitter EWMA', fontsize=14)
    plt.legend(loc='upper right', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico de Jitter gerado com sucesso e salvo como: {output_img}")
    plt.close()

if __name__ == "__main__":
    # Permite passar o CSV como argumento, ou usa o da Política 3 (onde o Jitter importa mais) por padrão
    csv_file = "metrics_policy3.csv"
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    # Se o csv da politica 3 não existir, tenta o da politica 1
    if not os.path.exists(csv_file):
        csv_file = "metrics_policy1.csv"
        
    gerar_grafico_jitter(csv_file)
