import pandas as pd
import matplotlib.pyplot as plt
import os

def gerar_grafico_3_politicas(csv_p1, csv_p2, csv_p3, output_img="grafico_comparacao_3_politicas.png"):
    # Verifica se os 3 CSVs existem
    csvs = [csv_p1, csv_p2, csv_p3]
    missing = [c for c in csvs if not os.path.exists(c)]
    
    if missing:
        print(f"Erro: Os seguintes arquivos não foram encontrados: {', '.join(missing)}")
        print("Certifique-se de rodar as 3 políticas para gerar todos os CSVs antes de gerar o gráfico.")
        return

    # Carrega os dados
    df1 = pd.read_csv(csv_p1)
    df2 = pd.read_csv(csv_p2)
    df3 = pd.read_csv(csv_p3)

    # Cria uma figura com 3 subgráficos (linhas) compartilhando os mesmos eixos X e Y
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True, sharey=True)

    policies = [
        (df1, "Política 1 (Baseline - Rate-Based)", axes[0]),
        (df2, "Política 2 (Buffer-Aware)", axes[1]),
        (df3, "Política 3 (Heurística c/ Jitter Penalty)", axes[2])
    ]

    for df, title, ax in policies:
        # Plota Bitrate (Qualidade Selecionada)
        ax.step(df['segment'], df['bitrate_kbps'], color='orange', where='mid', label='Bitrate Selecionado', linewidth=2.5)
        
        # Plota Vazão Medida para contexto
        ax.plot(df['segment'], df['vazao_kbps'], color='blue', marker='.', alpha=0.5, label='Vazão Medida da Rede')
        
        # Marcações de rebuffering
        if 'rebuffer_event' in df.columns:
            rebuffer_segments = df[df['rebuffer_event'] == 1]['segment']
            for i, seg in enumerate(rebuffer_segments):
                ax.axvline(x=seg, color='red', linestyle=':', linewidth=2, label='Rebuffering' if i == 0 else "")
                
        # Marcações de failover
        if 'failover_total' in df.columns:
            failover_segments = df[df['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
            for i, seg in enumerate(failover_segments):
                ax.axvline(x=seg, color='purple', linestyle='--', linewidth=2, label='Failover' if i == 0 else "")
                
        # Estilização do subplot atual
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.set_ylabel("Largura de Banda (kbps)", fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Ajuste de legenda para não cobrir o gráfico
        ax.legend(loc='upper right', fontsize=10)
        
    # Título principal e label do eixo X (apenas no último subplot)
    axes[2].set_xlabel("Número do Segmento", fontsize=12)
    plt.suptitle("Comparação Lado a Lado das 3 Políticas ABR (Mesma Escala e Cenário)", fontsize=16, y=0.98)
    
    # Ajusta espaçamento
    plt.tight_layout()
    
    # Salva
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico comparativo das 3 políticas salvo com sucesso como: {output_img}")
    plt.close()

if __name__ == "__main__":
    gerar_grafico_3_politicas("metrics_policy1.csv", "metrics_policy2.csv", "metrics_policy3.csv")
