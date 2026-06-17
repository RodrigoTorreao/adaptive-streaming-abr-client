SERVER_A = "http://137.131.178.229:8080"
SERVER_B = "http://137.131.178.229:8081"

# ── Entrega selector ──────────────────────────────────────────────────────────
# Change this value to switch which ABR policy and features are active:
#   1 → Rate-Based baseline only          (Entrega 1)
#   2 → Policy 2 + failover               (Entrega 2)
#   3 → Policy 3 (statistical/heuristic)  (Apresentação Final)
ACTIVE_POLICY = 2
# ─────────────────────────────────────────────────────────────────────────────

SAFETY_FACTOR = 0.92
SEGMENT_DURATION = 4.0      # seconds of video per segment
MIN_BUFFER_TO_PLAY = 4.0    # seconds needed for continuous play
NUM_SEGMENTS = 20
THROUGHPUT_WINDOW = 3       # number of past segments used for avg throughput
CHUNK_SIZE = 4096           # bytes per HTTP read chunk
IDENTIFY_HEADER = 'GRUPO 6' # identificador do grupo
OUTPUT_CSV = "metrics.csv"

# ── Buffer-Based ABR (Policy 2) ─────────────────────────────────────────────
BUFFER_CRITICAL_S = 1.0   # Abaixo disso: rebuffering iminente
BUFFER_MIN_S      = 4.0   # Abaixo disso: qualidade mínima (emergência)
BUFFER_LOW_S      = 8.0  # Abaixo disso: desce um nível (conservador)
BUFFER_TARGET_S   = 15.0  # Ponto de equilíbrio e alvo do ABR
BUFFER_HIGH_S     = 12.0  # Abaixo disso: mantém qualidade atual
BUFFER_MAX_S      = 15.0  # Acima disso: pede qualidade máxima
BUFFER_CAP_S      = 15.0  # Teto absoluto — loop pausa (sleep) só se ultrapassar isso
# ─────────────────────────────────────────────────────────────────────────────
