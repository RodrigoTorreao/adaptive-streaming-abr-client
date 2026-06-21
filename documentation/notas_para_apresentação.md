# Visão Geral do Projeto — Cliente DASH Adaptativo
**TR2 2026.1 · UnB · Grupo 6**

---

## O que o projeto faz

Implementamos um **cliente de streaming adaptativo (DASH)** em Python. Ele baixa segmentos de vídeo via HTTP e decide, a cada segmento, qual qualidade pedir — exatamente como YouTube e Netflix fazem internamente.

O desafio central é equilibrar dois objetivos conflitantes:
- **Qualidade máxima** — usar o máximo de banda disponível
- **Continuidade** — nunca deixar o buffer esvaziar e o vídeo travar

Para isso implementamos **três políticas ABR** progressivas, uma por entrega.

---

## Infraestrutura

| Componente | Endereço |
|---|---|
| Servidor A (principal) | `http://137.131.178.229:8080` |
| Servidor B (failover) | `http://137.131.178.229:8081` |
| Manifest | `GET /manifest` |
| Health check | `GET /health` |

**Qualidades disponíveis** (do manifest real):

| Qualidade | Bitrate | Tamanho do segmento |
|---|---|---|
| 240p | 200 kbps | 25 KB |
| 360p | 400 kbps | 50 KB |
| 480p | 600 kbps | 75 KB |
| 720p | 900 kbps | 112 KB |
| 1080p | 1200 kbps | 150 KB |

Cada segmento representa **2 segundos** de vídeo (`segment_duration_s: 2`).

---

## Como trocar de política

Editar `client/config.py`:

```python
ACTIVE_POLICY = 1   # Entrega 1 — Rate-Based baseline
ACTIVE_POLICY = 2   # Entrega 2 — Buffer-Based + failover
ACTIVE_POLICY = 3   # Final     — Estatístico/heurístico
```

Depois rodar:
```bash
cd client
python3 main.py
```

Saídas: `metrics.csv`, `graph_throughput_quality.png`, `graph_buffer.png`

---

## Política 1 — Rate-Based (Entrega 1)

**Ideia:** Mede a banda das últimas 3 amostras, aplica um fator de segurança de 8%, e pede a maior qualidade que couber nessa banda.

```
vazao_efetiva = média(últimas 3 medições) × 0.92
→ maior qualidade com bitrate ≤ vazao_efetiva
```

**Problema identificado com dados reais:** oscila entre qualidades porque reage imediatamente a variações momentâneas de banda. No nosso teste, alternnou 6 vezes entre qualidades mesmo com condições estáveis.

---

## Política 2 — Buffer-Based (Entrega 2)

**Ideia:** Ignora throughput. Decide qualidade **só pelo nível do buffer** — se o buffer está cheio, pede mais qualidade; se está vazio, pede menos.

| Buffer | Decisão |
|---|---|
| < 4s | Qualidade mínima (emergência) |
| 4–8s | Desce 1 nível |
| 8–12s | Mantém qualidade atual |
| 12–15s | Sobe 1 nível |
| ≥ 15s | Qualidade máxima |

**Melhoria sobre P1:** muito mais estável — o buffer muda devagar, então as decisões também. Apenas 4 mudanças de qualidade no teste vs. 6 da P1.

**Problema residual:** cega à banda real. Se a rede cair de repente com o buffer cheio, a política não percebe até o buffer começar a esvaziar.

**Failover (também entrega 2):** em caso de erro de download, o sistema verifica a saúde dos servidores via `GET /health` e migra automaticamente para o próximo disponível.

---

## Política 3 — Estatístico/Heurístico (Apresentação Final)

**Ideia central:** combinar o melhor das duas políticas anteriores, adicionando consciência de jitter. A P3 sabe tanto a banda disponível (via EWMA) quanto o estado do buffer, e penaliza automaticamente cenários de alto jitter.

### Os quatro mecanismos

**1. EWMA de Throughput** — substitui a média simples de 3 amostras por uma média exponencial que dá mais peso ao histórico recente sem ser tão volátil quanto a janela pequena da P1.

```
T_ewma = 0.3 × T_medido + 0.7 × T_ewma_anterior
```

**2. EWMA de Jitter** — acompanha a variação de latência entre chunks ao longo do tempo com o mesmo mecanismo de suavização.

```
J_ewma = 0.3 × J_medido + 0.7 × J_ewma_anterior
```

**3. Penalidade de Jitter** — reduz a banda efetiva proporcionalmente ao jitter acumulado. Jitter alto indica entrega irregular de dados — mesmo que a banda nominal seja alta, segmentos podem chegar de forma fragmentada e causar stalls.

```
Penalidade = min(50%, jitter_ewma / 1000)
```

| Jitter EWMA | Penalidade | O que acontece |
|---|---|---|
| 100 ms | 10% | Banda reduzida em 10% |
| 300 ms | 30% | Banda reduzida em 30% |
| ≥ 500 ms | 50% (teto) | Banda reduzida à metade |

**4. Fator de Buffer** — ajusta a agressividade com base na segurança do buffer atual.

| Buffer | Fator | Modo |
|---|---|---|
| < 4s | 0.5 | Crítico — muito conservador |
| 4–8s | 0.7 | Baixo — conservador |
| 8–12s | 0.9 | Alerta — levemente conservador |
| ≥ 12s | 1.0 | Confortável — sem penalidade extra |

**Fórmula final:**
```
T_efetiva = T_ewma × (1 − Penalidade) × FatorBuffer
→ maior qualidade com bitrate ≤ T_efetiva
```

**5. Histerese** — evita oscilar entre qualidades próximas do limiar:
- **Subida:** máximo +1 nível por segmento (não pula direto para 1080p)
- **Descida:** imediata — cai quantos níveis forem necessários para evitar stall

---

## Resultados Reais (testes online — 2026-06-21)

Condições: Servidor A a 2000 kbps, Servidor B a 1000 kbps, jitter natural baixo (~8ms).

| Cenário | Bitrate médio | Mudanças de qualidade | Rebuffers | Stall total |
|---|---|---|---|---|
| P1 Rate-Based | 865 kbps | 6 | 2 | 0.821s |
| P2 Buffer-Based | 765 kbps | 4 | 2 | 0.360s |
| **P3 Rede estável** | **915 kbps** | **4** | **2** | **0.355s** |
| P3 + Failover (srv A cai no seg 10) | 645 kbps | 6 | 2 | 0.354s |
| P3 + Jitter 400ms (a partir do seg 8) | 630 kbps | 4 | 2 | 0.353s |

**Interpretação:**
- P3 em rede estável superou todas as políticas: maior bitrate médio (915 kbps) com a mesma estabilidade da P2 (4 mudanças).
- P2 ficou presa em 240p por 7 segmentos esperando o buffer encher; P3 começou a subir no segmento 3.
- No cenário de jitter 400ms, a P3 caiu de 720p para 480p a partir do segmento 12 — **sem rebuffering adicional** — enquanto o stall de 0.353s veio apenas do arranque inicial (buffer zerado no começo).

---

## Cenário de Failover — O que acontece

**Sequência observada no teste:**

1. Segmentos 1–9: Servidor A, buffer sobe até 14.1s
2. **Segmento 10:** Servidor A cai → sistema detecta erro → chama `GET /health` no Servidor B → migra em ~5s
3. Como o buffer estava em 14.1s, os 5s de timeout de failover foram absorvidos **sem rebuffering visível**
4. Segmentos 10–20: Servidor B (800 kbps disponíveis) → P3 ajusta qualidade para 480p via EWMA

**Onde no código:** `failover.py:handle_failure()` → `main.py` linhas 85–94.

---

## Cenário de Jitter Alto — O que acontece

**Sequência observada no teste (jitter +400ms a partir do seg 8):**

1. Segmentos 1–7: jitter natural ~8ms, qualidade sobe normalmente até 720p
2. **Segmento 8:** professor injeta jitter → `jitter_network_ms` sobe para ~407ms
3. `J_ewma` sobe gradualmente (β=0.3): não reage ao primeiro spike
4. **Segmento 12:** J_ewma acumulado aplica penalidade de ~40% → `T_efetiva` cai abaixo do limiar de 900 kbps para 720p → sistema desce para 480p
5. Resultado: **zero rebuffering adicional** — a penalidade antecipou o risco antes do buffer esvaziar

**Por que não reagiu imediatamente no seg 8?** O EWMA suaviza a entrada do jitter (β=0.3 = 30% de peso para a nova amostra). Isso é intencional: um único spike não causa troca de qualidade desnecessária.

---

## Para a Apresentação — Respostas Rápidas

**"Onde no código a decisão ABR é tomada?"**
→ `client/abr/policy3.py`, método `select_quality()` (linha ~50)

**"Por que 480p e não 720p com o jitter alto?"**
→ T_ewma ≈ 1300 kbps; penalidade ≈ 40% (J_ewma ≈ 400ms); T_efetiva ≈ 780 kbps — abaixo do bitrate de 900 kbps da 720p.

**"Como o failover foi detectado?"**
→ `download_segment()` levantou `TimeoutError`; `main.py` capturou, chamou `FailoverManager.handle_failure()`, que fez `GET /health` no Servidor B e migrou.

**"O buffer foi suficiente durante o failover?"**
→ Sim. Buffer estava em 14.1s quando o Servidor A caiu. O timeout de failover consumiu ~5s. Restaram ~9s de buffer — bem acima do mínimo de 4s para `buffer_can_play = 1`.

**"Qual política se saiu melhor?"**
→ P3 em rede estável (915 kbps médios, 4 mudanças de qualidade). P2 é mais previsível mas desperdiça banda. P1 tem mais bitrate momentâneo mas oscila. P3 equilibra os dois.

---

## Arquivos Gerados nos Testes

| Arquivo | Conteúdo |
|---|---|
| `client/metrics.csv` | CSV principal da última execução de `main.py` |
| `client/graph_throughput_quality.png` | Vazão vs qualidade ao longo dos segmentos |
| `client/graph_buffer.png` | Buffer com marcadores de rebuffer e failover |
| `client/test_results/policy1_stable.csv` | Teste online P1 |
| `client/test_results/policy2_stable.csv` | Teste online P2 |
| `client/test_results/policy3_stable.csv` | Teste online P3 rede estável |
| `client/test_results/policy3_failover.csv` | Teste online P3 + failover no seg 10 |
| `client/test_results/policy3_high_jitter.csv` | Teste online P3 + jitter 400ms |
| `client/test_results/comparativo_cenarios.csv` | Tabela comparativa de todos os cenários |
