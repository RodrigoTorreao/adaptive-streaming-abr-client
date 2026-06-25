import pandas as pd
import matplotlib.pyplot as plt
import os

def gerar_grafico_vazao_qualidade(csv_path, output_img="grafico_politica1.png"):
    if not os.path.exists(csv_path):
        print(f"Erro: O arquivo {csv_path} não foi encontrado.")
        print("Certifique-se de rodar a Política 1 primeiro para gerar o CSV.")
        return

    # Carrega os dados do CSV
    df = pd.read_csv(csv_path)

    # Cria a figura e o eixo principal
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Plota a Vazão Medida no eixo Y principal (esquerda)
    ax1.plot(df['segment'], df['vazao_kbps'], color='blue', marker='o', label='Vazão Medida (kbps)')
    ax1.set_xlabel('Segmento')
    ax1.set_ylabel('Vazão (kbps)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Cria um segundo eixo Y compartilhando o mesmo eixo X (direita)
    ax2 = ax1.twinx()

    # Plota a Qualidade Selecionada (Bitrate) como degraus
    ax2.step(df['segment'], df['bitrate_kbps'], color='orange', where='mid', label='Qualidade Selecionada (kbps)', linewidth=2.5)
    ax2.set_ylabel('Bitrate Nominal (kbps)', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # Adiciona título e grid
    plt.title('Política 1 (Baseline) - Vazão Medida vs Qualidade Selecionada')
    plt.grid(True, linestyle='--', alpha=0.6)

    # Ajusta o layout para não cortar textos
    fig.tight_layout()

    # Salva o gráfico
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico gerado com sucesso e salvo como: {output_img}")
    plt.close()

if __name__ == "__main__":
    # Nome do arquivo CSV gerado pela Política 1 (Entrega 1)
    # No config.py atual, ele salva como metrics_policy1.csv se ACTIVE_POLICY for 1
    arquivo_csv = "metrics_policy1.csv"
    
    gerar_grafico_vazao_qualidade(arquivo_csv)
