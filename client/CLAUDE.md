# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the client

```bash
cd client
pip install matplotlib
python main.py
```

Outputs: `metrics.csv`, `graph_throughput_quality.png`, `graph_buffer.png`

## Running tests

Tests live in `test/` and are standalone scripts — run them directly:

```bash
cd client
python test/abrTest.py
python test/bufferTest.py
python test/downloaderTest.py
python test/manisfetTest.py
python test/metricsTest.py
```

Each test adds its own parent directory to `sys.path`, so they must be run from `client/`.

## Switching delivery phases

Change `ACTIVE_POLICY` in `config.py` to select which ABR policy runs:

```python
ACTIVE_POLICY = 1  # Rate-Based baseline (Entrega 1)
ACTIVE_POLICY = 2  # Buffer-Based + failover (Entrega 2)
ACTIVE_POLICY = 3  # Statistical/heuristic (Apresentação Final)
```

`main.py` uses this value to instantiate the right policy and optionally wire up `FailoverManager`. **No other file changes are needed between deliveries.**

## Architecture

The download loop in `main.py` drives everything:

1. `manifest.py` fetches the JSON manifest from the server → returns server list (priority-ordered) and quality representations (bitrate-ascending).
2. `ABRPolicy.select_quality()` is called **before** the download using the estimated throughput and current buffer level.
3. `downloader.download_segment()` performs the HTTP fetch in 4 KB chunks, measuring throughput (`bytes / time`) and jitter (inter-chunk arrival variance).
4. `BufferManager` tracks playback buffer in seconds. `consume(download_time_s)` is only called when `buffer_can_play == 1`; otherwise the download time is counted as stall.
5. `MetricsLogger` appends a CSV row with all 14 required fields after each segment.

## ABR policy interface

All policies subclass `abr/base.py:ABRPolicy` and must implement:
- `select_quality(throughput_kbps, buffer_level_s, qualities) → dict`
- `update_throughput(measured_kbps)` — called by `main.py` after every download
- `_estimated_throughput() → float` — called by `main.py` to pass into `select_quality`

The `qualities` list is always sorted **bitrate ascending** (240p → 1080p). `qualities[0]` is the safe fallback.

## Key configuration values (`config.py`)

| Constant | Purpose |
|---|---|
| `SAFETY_FACTOR = 0.85` | Applied to estimated throughput in Rate-Based policy |
| `SEGMENT_DURATION = 4.0` | Seconds of video per segment |
| `MIN_BUFFER_TO_PLAY = 4.0` | Threshold for `BufferManager.can_play()` |
| `THROUGHPUT_WINDOW = 3` | Moving average window for all policies |
| `BUFFER_{MIN,LOW,HIGH,MAX}_S` | Thresholds for Policy 2's buffer-state machine |

## Server infrastructure

- Server A: `http://137.131.178.229:8080` (primary)
- Server B: `http://137.131.178.229:8081` (fallback)
- Manifest: `GET /manifest` — JSON with `servers[]` and `representations[]`
- Health check: `GET /health` — used by `FailoverManager` (Entrega 2+)
- All requests include `X-Group: GRUPO 6` header (`IDENTIFY_HEADER` in config).
