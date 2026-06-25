import pandas as pd
import matplotlib.pyplot as plt
import os

def gerar_grafico_vazao(csv_p1, csv_p2, output_img="grafico_comparacao_vazao_p1_p2.png"):
    if not os.path.exists(csv_p1) or not os.path.exists(csv_p2):
        print(f"Erro: Arquivos não encontrados.")
        print(f"Verifique se {csv_p1} e {csv_p2} existem.")
        return

    # Carrega os dados dos dois CSVs
    df1 = pd.read_csv(csv_p1)
    df2 = pd.read_csv(csv_p2)

    plt.figure(figsize=(12, 6))

    # Plota a Vazão Medida da Política 1
    plt.plot(df1['segment'], df1['vazao_kbps'], color='blue', marker='o', 
             label='Vazão Medida - Política 1 (Baseline)', linewidth=2, alpha=0.7)
    
    # Plota a Vazão Medida da Política 2
    plt.plot(df2['segment'], df2['vazao_kbps'], color='orange', marker='s', 
             label='Vazão Medida - Política 2 (Buffer-aware)', linewidth=2, alpha=0.8)

    # Verifica se houve Failover na Política 2 e desenha uma linha vertical
    if 'failover_total' in df2.columns:
        failover_segments = df2[df2['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
        for i, seg in enumerate(failover_segments):
            plt.axvline(x=seg, color='purple', linestyle='--', linewidth=1.5, 
                        label='Failover (Política 2)' if i == 0 else "")

    # Configurações de exibição do gráfico
    plt.xlabel('Segmento', fontsize=12)
    plt.ylabel('Vazão (kbps)', fontsize=12)
    plt.title('Comparação de Vazão: Baseline vs Política 2', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Coloca a legenda no canto superior direito
    plt.legend(loc='upper right', fontsize=11)
    
    plt.tight_layout()

    # Salva e fecha
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico gerado com sucesso e salvo como: {output_img}")
    plt.close()

if __name__ == "__main__":
    # Nomes dos arquivos de saída das duas políticas
    csv_baseline = "metrics_policy1.csv"
    csv_policy2 = "metrics_policy2.csv"
    
    gerar_grafico_vazao(csv_baseline, csv_policy2)
