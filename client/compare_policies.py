import os
import subprocess
import shutil
import pandas as pd
import matplotlib.pyplot as plt

def run_policy(policy_num, output_csv):
    print(f"--- Rodando Política {policy_num} ---")
    env = os.environ.copy()
    env["ACTIVE_POLICY"] = str(policy_num)
    # Roda o main.py usando o interpretador do ambiente virtual se existir
    python_exe = ".venv/bin/python" if os.path.exists(".venv/bin/python") else "python"
    
    subprocess.run([python_exe, "main.py"], env=env, check=True)
    
    # Renomeia o metrics.csv gerado
    if os.path.exists("metrics.csv"):
        shutil.move("metrics.csv", output_csv)

def generate_comparison_graph(csv_p1, csv_p2, csv_p3):
    df1 = pd.read_csv(csv_p1)
    df2 = pd.read_csv(csv_p2)
    df3 = pd.read_csv(csv_p3)
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 15), sharex=True, sharey=True)
    
    policies = [
        (df1, "Política 1 (Baseline)", axes[0]),
        (df2, "Política 2 (Buffer-aware)", axes[1]),
        (df3, "Política 3 (Estatística/Heurística)", axes[2])
    ]
    
    for df, title, ax in policies:
        ax.step(df['segment'], df['bitrate_kbps'], color='orange', where='mid', label='Bitrate (kbps)', linewidth=2)
        ax.plot(df['segment'], df['vazao_kbps'], color='blue', marker='.', alpha=0.5, label='Vazão Medida (kbps)')
        
        # Marcações de rebuffering
        rebuffer_segments = df[df['rebuffer_event'] == 1]['segment']
        for i, seg in enumerate(rebuffer_segments):
            ax.axvline(x=seg, color='red', linestyle=':', label='Rebuffering' if i == 0 else "")
            
        # Marcações de failover
        failover_segments = df[df['failover_total'].diff().fillna(0) > 0]['segment'].tolist()
        for i, seg in enumerate(failover_segments):
            ax.axvline(x=seg, color='purple', linestyle='--', linewidth=1.5, label='Failover' if i == 0 else "")
            
        ax.set_title(title)
        ax.set_ylabel("kbps")
        ax.grid(True, linestyle='--')
        ax.legend(loc='upper right')
        
    axes[2].set_xlabel("Segmento")
    
    plt.tight_layout()
    plt.savefig("graph_comparison.png")
    plt.close()
    print("Gráfico comparativo salvo como 'graph_comparison.png'")

if __name__ == "__main__":
    run_policy(1, "metrics_p1.csv")
    run_policy(2, "metrics_p2.csv")
    run_policy(3, "metrics_p3.csv")
    generate_comparison_graph("metrics_p1.csv", "metrics_p2.csv", "metrics_p3.csv")
