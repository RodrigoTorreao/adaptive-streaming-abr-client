import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from manifest import (fetch_manifest, parse_qualities, parse_servers)
from config import SERVER_A, ACTIVE_POLICY

def test_manifest():
    print(f"--- Iniciando Cliente ABR (Política Ativa: {ACTIVE_POLICY}) ---")
    
    # 1. Obter e processar o manifesto do servidor inicial (SERVER_A)
    try:
        print(f"Baixando manifesto de: {SERVER_A}")
        manifest = fetch_manifest(SERVER_A)
        
        # Ordena os servidores por prioridade e as qualidades por bitrate
        available_servers = parse_servers(manifest)
        available_qualities = parse_qualities(manifest)
        
        print(f"✓ Servidores encontrados: {available_servers}")
        print(f"✓ Qualidades disponíveis (bitrates): {[q['bitrate_kbps'] for q in available_qualities]} kbps")
    except Exception as e:
        print(f"Erro no manifesto: {e}")
        return
    

if __name__ == "__main__":
    test_manifest()