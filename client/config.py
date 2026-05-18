SERVER_A = "http://137.131.178.229:8080"
SERVER_B = "http://137.131.178.229:8081"

SAFETY_FACTOR = 0.85
SEGMENT_DURATION = 4.0      # seconds of video per segment
MIN_BUFFER_TO_PLAY = 4.0    # seconds needed for continuous play
NUM_SEGMENTS = 10
THROUGHPUT_WINDOW = 3       # number of past segments used for avg throughput
CHUNK_SIZE = 4096           # bytes per HTTP read chunk
OUTPUT_CSV = "metrics.csv"
