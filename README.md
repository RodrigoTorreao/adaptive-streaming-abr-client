# TR2 — Projeto Final: DASH Client Adaptativo

**Disciplina:** Teleinformática e Redes 2 (CIC0236) — UnB 2026.1  
**Grupo:** 3 alunos  
**Servidor:** fornecido pelo professor (não implementado pelo grupo)

---

## Visão Geral

O projeto implementa um **cliente de streaming adaptativo (DASH)** em Python puro.
O cliente baixa segmentos de vídeo via HTTP, mede as condições de rede em tempo real e
decide dinamicamente qual qualidade pedir a cada segmento — exatamente como fazem
YouTube e Netflix internamente.

```
┌──────────────────────────────────────────────────────────┐
│                        CLIENTE                           │
│                                                          │
│  manifest.py ──► main.py ──► downloader.py              │
│                    │              │                      │
│                 buffer.py    (vazão + jitter)            │
│                    │                                     │
│                 abr/          metrics.py                 │
│              (decisão ABR)   (CSV + gráficos)            │
└──────────────────────────────────────────────────────────┘
         │ HTTP                          │ HTTP
         ▼                              ▼
  Servidor A :8080              Servidor B :8081
  (principal)                    (fallback)
```

---

## Arquitetura de Módulos

```
client/
├── main.py           # Orquestra o loop principal de download
├── manifest.py       # Fetch e parse do manifest JSON
├── downloader.py     # Download de segmento + medição de vazão e jitter
├── buffer.py         # Gerenciamento do buffer em segundos
├── metrics.py        # Escrita do CSV e geração de gráficos
├── config.py         # Constantes e parâmetros globais
└── abr/
    ├── base.py        # Interface ABRPolicy (classe abstrata)
    ├── rate_based.py  # Política 1 — Rate-Based puro (Entrega 1)
    ├── policy2.py     # Política 2 (Entrega 2)
    └── policy3.py     # Política 3 — componente estatístico (Entrega Final)
```

---

## Fluxo de Dados

### Inicialização

```
main.py
  └─► manifest.py: GET /manifest
        └─► retorna: lista de servidores + lista de representações (qualidades)
  └─► instancia: ABRPolicy, BufferManager, MetricsLogger
```

### Loop por segmento (repetido NUM_SEGMENTS vezes)

```
1. ABRPolicy.select_quality(throughput_médio, buffer_level, qualities)
       └─► retorna: qualidade escolhida (ex: "720p", bitrate 1000 kbps)

2. downloader.download_segment(server_url, quality, segment_num)
       └─► abre conexão HTTP com o servidor
       └─► lê resposta em chunks de 4 KB
       └─► mede tempo entre chegadas de chunks → jitter_network_ms
       └─► ao final: calcula vazão = bytes_totais / tempo_download
       └─► retorna: SegmentResult(bytes, download_time_s, throughput_kbps, jitter_network_ms)

3. BufferManager.consume(tempo_desde_último_segmento)
       └─► desconta o tempo real decorrido do buffer
       └─► detecta rebuffering (buffer chegou a 0)

4. BufferManager.add_segment(SEGMENT_DURATION)
       └─► acrescenta 4s ao buffer

5. metrics.log_segment(row)
       └─► grava linha no CSV com todos os 14 campos obrigatórios
```

### Finalização

```
metrics.generate_graphs(csv_path)
  └─► gráfico 1: vazão (kbps) + qualidade ao longo dos segmentos
  └─► gráfico 2: nível do buffer ao longo do tempo (com eventos de rebuffer marcados)
```

---

## Manifest (formato esperado do servidor)

```json
{
  "servers": [
    { "id": "A", "url": "http://137.131.178.229:8080", "priority": 1 },
    { "id": "B", "url": "http://137.131.178.229:8081", "priority": 2 }
  ],
  "representations": [
    { "quality": "240p",  "bitrate_kbps": 200,  "segment_size_kb": 25  },
    { "quality": "360p",  "bitrate_kbps": 400,  "segment_size_kb": 50  },
    { "quality": "480p",  "bitrate_kbps": 600,  "segment_size_kb": 75  },
    { "quality": "720p",  "bitrate_kbps": 1000, "segment_size_kb": 125 },
    { "quality": "1080p", "bitrate_kbps": 1200, "segment_size_kb": 150 }
  ]
}
```

---

## CSV de Métricas (campos obrigatórios)

| Campo | Tipo | Descrição |
|---|---|---|
| `segment` | int | Número sequencial do segmento |
| `timestamp` | ISO 8601 | Horário do download |
| `server_id` | str | Servidor que atendeu (A ou B) |
| `quality` | str | Qualidade selecionada pelo ABR |
| `bitrate_kbps` | int | Bitrate nominal da representação |
| `vazao_kbps` | float | Vazão medida neste segmento |
| `download_time_s` | float | Tempo de download do segmento |
| `jitter_network_ms` | float | Variação de latência entre chunks |
| `jitter_ewma_ms` | float | EWMA do jitter entre segmentos consecutivos |
| `buffer_level_s` | float | Nível do buffer em segundos |
| `buffer_can_play` | 0/1 | 1 se buffer ≥ MIN_BUFFER no momento da decisão |
| `rebuffer_event` | 0/1 | 1 se ocorreu rebuffering neste segmento |
| `stall_duration_s` | float | Tempo de stall (0 se não houve) |
| `failover_total` | int | Número acumulado de failovers |

---

## Algoritmo ABR — Política 1: Rate-Based (Entrega 1)

```
throughput_estimado = média(últimas 3 vazões medidas)
capacidade_efetiva  = throughput_estimado × SAFETY_FACTOR (0.85)

para cada qualidade (ordem decrescente de bitrate):
    se qualidade.bitrate_kbps ≤ capacidade_efetiva:
        retorna esta qualidade

fallback: retorna a menor qualidade (240p)
```

**Deficiência conhecida (base para Entrega 2):** o Rate-Based puro oscila em redes
instáveis porque reage imediatamente a variações momentâneas, sem considerar o
nível do buffer nem tendências de longo prazo.

---

## Entregas e Cronograma

> **Importante:** cada entrega é uma demo **ao vivo**, com o sistema rodando contra o servidor do professor.
> Não é entrega de código parcial — o cliente precisa funcionar de ponta a ponta em cada semana.
> Cada entrega acumula o que foi feito anteriormente.

| Entrega | Semana | Peso | O que deve rodar ao vivo |
|---|---|---|---|
| **Entrega 1** | Semana 4 | 15% | Baixar 10 segmentos, mostrar CSV gerado e gráfico de vazão |
| **Entrega 2** | Semana 7 | 20% | Baseline vs Política 2 com mudança de banda; derrubar Servidor A e mostrar failover automático para B |
| **Apresentação Final** | Semana 10 | 65% | Cenário surpresa: professor altera banda, introduz jitter e derruba Servidor A ao vivo; grupo explica decisões do código em tempo real |

### O que cada entrega acrescenta ao código

| Entrega | Módulos novos / alterados |
|---|---|
| Entrega 1 | `manifest.py`, `downloader.py`, `buffer.py`, `metrics.py`, `abr/rate_based.py` |
| Entrega 2 | `abr/policy2.py`, `failover.py` |
| Final | `abr/policy3.py`, análise Wireshark no relatório |

---

## Como Executar

```bash
# Instalar dependência de gráficos (única dependência externa)
pip install matplotlib

# Rodar o cliente (Entrega 1)
cd client
python main.py
```

Saída esperada:
- `metrics.csv` com uma linha por segmento
- `graph_throughput_quality.png`
- `graph_buffer.png`

---

## Infraestrutura (fornecida pelo professor)

- **Servidor A:** `http://137.131.178.229:8080`
- **Servidor B:** `http://137.131.178.229:8081`
- **Manifest:** `GET http://137.131.178.229:8080/manifest`
- **Controle ao vivo:** endpoint `/control` (banda e jitter programáticos)
- **Health check:** `GET /health` (usado no failover — Entrega 2)

O código do servidor **não é disponibilizado**. O grupo implementa somente o cliente.
