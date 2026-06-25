import pandas as pd
import matplotlib.pyplot as plt
import os

def gerar_grafico_comparacao(csv_p1, csv_p2, output_img="grafico_comparacao_p1_p2.png"):
    if not os.path.exists(csv_p1) or not os.path.exists(csv_p2):
        print(f"Erro: Arquivos não encontrados.")
        print(f"Verifique se {csv_p1} e {csv_p2} foram gerados rodando as respectivas políticas.")
        return

    # Carrega os dados dos dois CSVs
    df1 = pd.read_csv(csv_p1)
    df2 = pd.read_csv(csv_p2)

    # Mapeamento de bitrate para índice/string de qualidade
    bitrates = [200, 400, 600, 900, 1200]
    qualities = ['240p', '360p', '480p', '720p', '1080p']
    
    # Criar mapeamento de bitrate para índice
    df1['quality_idx'] = df1['bitrate_kbps'].apply(lambda x: bitrates.index(x) if x in bitrates else 0)
    df2['quality_idx'] = df2['bitrate_kbps'].apply(lambda x: bitrates.index(x) if x in bitrates else 0)

    plt.figure(figsize=(12, 6))

    # Plota a Qualidade da Política 1 (Baseline)
    plt.step(df1['segment'], df1['quality_idx'], color='blue', where='post', 
             label='Política 1 (Baseline)', linewidth=2.5, alpha=0.6)
    
    # Plota a Qualidade da Política 2 (Buffer-aware)
    # Adicionando um pequeno offset (+0.05) no y para as linhas não ficarem exatamente sobrepostas
    plt.step(df2['segment'], df2['quality_idx'] + 0.05, color='orange', where='post', 
             label='Política 2 (Buffer-aware)', linewidth=2.5, alpha=0.9)

    # Verifica se houve Failover na Política 2 e desenha uma linha vertical
    if 'failover_total' in df2.columns:
        failover_segments = df2[df2['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
        for i, seg in enumerate(failover_segments):
            plt.axvline(x=seg, color='red', linestyle='--', linewidth=2.0, 
                        label='Failover (Política 2)' if i == 0 else "")

    # Configurações de exibição do gráfico
    plt.xlabel('Segmento', fontsize=12)
    plt.ylabel('Qualidade Selecionada', fontsize=12)
    plt.yticks(range(len(qualities)), qualities) # Define as labels no eixo Y
    plt.title('Comparação de Qualidade: Baseline vs Política 2', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.4, axis='y')
    
    # Ajusta a legenda para um local que atrapalhe menos as linhas (ex: canto inferior direito)
    plt.legend(loc='lower right', fontsize=11)
    
    plt.tight_layout()

    # Salva e fecha
    plt.savefig(output_img, dpi=300)
    print(f"Gráfico gerado com sucesso e salvo como: {output_img}")
    plt.close()

if __name__ == "__main__":
    # Nomes dos arquivos de saída das duas políticas
    csv_baseline = "metrics_policy1.csv"
    csv_policy2 = "metrics_policy2.csv"
    
    gerar_grafico_comparacao(csv_baseline, csv_policy2)
