SERVER_A = "http://137.131.178.229:8080"
SERVER_B = "http://137.131.178.229:8081"

# ── Entrega selector ──────────────────────────────────────────────────────────
# Change this value to switch which ABR policy and features are active:
#   1 → Rate-Based baseline only          (Entrega 1)
#   2 → Policy 2 + failover               (Entrega 2)
#   3 → Policy 3 (statistical/heuristic)  (Apresentação Final)
ACTIVE_POLICY = 1
# ─────────────────────────────────────────────────────────────────────────────

SAFETY_FACTOR = 0.85
SEGMENT_DURATION = 4.0      # seconds of video per segment
MIN_BUFFER_TO_PLAY = 4.0    # seconds needed for continuous play
NUM_SEGMENTS = 10
THROUGHPUT_WINDOW = 3       # number of past segments used for avg throughput
CHUNK_SIZE = 4096           # bytes per HTTP read chunk
IDENTIFY_HEADER = 'GRUPO 6' # identificador do grupo
OUTPUT_CSV = "metrics.csv"
