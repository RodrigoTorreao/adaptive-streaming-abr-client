import csv
import sys

# Mapping qualities to indices 0-4 (assuming these are the 5 qualities)
quality_map = {
    '240p': 0,
    '360p': 1,
    '480p': 2,
    '720p': 3,
    '1080p': 4
}

def process(filename):
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return

    # Quantity of rebuffering events
    rebuffer_events = sum(1 for row in data if int(row['rebuffer_event']) == 1)
    
    # Total stall time
    total_stall_duration = sum(float(row['stall_duration_s']) for row in data)
    
    # Quality stability (number of switches)
    switches = 0
    prev_quality = None
    qualities = []
    buffers = []
    
    failover_buffer_can_play_1 = True
    failover_occurred = False
    
    for i, row in enumerate(data):
        quality = row['quality']
        if quality in quality_map:
            qualities.append(quality_map[quality])
        else:
            # fallback if unknown quality
            qualities.append(0)
            
        if prev_quality is not None and quality != prev_quality:
            switches += 1
        prev_quality = quality
        
        # Buffer min pós-aquecimento (we can define pós-aquecimento as after segment 2, or just the min overall?)
        # Let's track buffer after the first few segments that had rebuffering (usually 1 and 2)
        if int(row['rebuffer_event']) == 0:
            buffers.append(float(row['buffer_level_s']))
        
        # Failover check
        if float(row['failover_total']) > 0 or row['server_id'] != data[0]['server_id']:
            failover_occurred = True
            if int(row['buffer_can_play']) == 0:
                failover_buffer_can_play_1 = False

    avg_quality = sum(qualities) / len(qualities) if qualities else 0
    min_buffer = min(buffers) if buffers else 0
                
    print(f"--- {filename} ---")
    print(f"Eventos de rebuffering: {rebuffer_events}")
    print(f"Tempo total de stall (s): {total_stall_duration:.3f}")
    print(f"Número de trocas de qualidade: {switches}")
    print(f"Qualidade média (índice 0-4): {avg_quality:.2f}")
    print(f"Buffer mínimo pós-aquecimento (s): {min_buffer:.2f}")
    
    if failover_occurred:
        print(f"buffer_can_play no failover: {'1' if failover_buffer_can_play_1 else '0'}")
    else:
        print("buffer_can_play no failover: N/A")
    print()

for p in ['metrics_policy1.csv', 'metrics_policy2.csv', 'metrics_policy3.csv']:
    process(p)
