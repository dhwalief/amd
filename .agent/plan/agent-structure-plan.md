# Arsitektur Multi-Agent System — Revisi v5
## Perencanaan Model, Dependency, dan Estimasi GPU

> **Dokumen ini adalah revisi v5**, mencakup penggantian seluruh model berlisensi terbatas (Llama, Mistral) dengan model Apache 2.0 yang kuat untuk Bahasa Inggris dan Bahasa Indonesia, sesuai kebutuhan lomba internasional.

---

## 1. Ringkasan Arsitektur

```
┌─────────────────────────────────────────────────────────┐
│                    EXECUTIVE LAYER                       │
│   Orchestrator → Critic → Risk Manager                  │
└─────────────────────────────────────────────────────────┘
              ↓ (setelah Executive selesai)
┌─────────────────────────────────────────────────────────┐
│                     ANALYST LAYER                        │
│  Geo Analyst | Competitor Scout | Growth Hacker          │
│  CFO | Pricing Strategist                               │
└─────────────────────────────────────────────────────────┘
              ↓ (setelah Analyst selesai)
┌─────────────────────────────────────────────────────────┐
│                      WORKER LAYER                        │
│  Inquisitor | Legal | Product Architect | HR Planner     │
│  Supply Planner | SOP Designer                          │
└─────────────────────────────────────────────────────────┘
              ↓ (kapan saja, deterministik)
┌─────────────────────────────────────────────────────────┐
│                     UTILITY LAYER                        │
│   BEP Calc | Cashflow Sim | Dependency Checker           │
│   Schema Validator  ← Python functions, tanpa LLM       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Detail Model Per Agent — Revisi v5

### 2.1 Executive Layer

| Agent | Model Lama | Model Baru | Status | Justifikasi |
|-------|-----------|-----------|--------|-------------|
| **Orchestrator** | DeepSeek V3 671B | **Qwen2.5-72B** | 🔄 Diganti | DeepSeek V3 OOM di 1× MI300X (BF16 ~720GB, FP8 gagal load). Qwen2.5-72B (~144GB BF16) muat nyaman, pengetahuan luas untuk routing dan state management kompleks. |
| **Critic / Gap Finder** | Qwen3-32B | Qwen3-32B | ✅ Tetap | Deteksi kontradiksi antar output agent — butuh abstract reasoning kuat. Qwen3-32B punya thinking mode built-in. |
| **Risk Manager** | DeepSeek R1 671B (full) | **DeepSeek R1 Distill Llama-70B** | 🔄 Diganti | DeepSeek R1 full OOM di 1× MI300X. R1 Distill Llama-70B (~140GB BF16) masih keluarga R1, ditraining khusus untuk reasoning, muat di 1× MI300X. Varian Qwen-70B tidak tersedia di HuggingFace — varian Llama-70B adalah pilihan tertinggi yang ada. |

### 2.2 Analyst Layer

| Agent | Model | Lisensi | Status | Justifikasi |
|-------|-------|---------|--------|-------------|
| **Geo Analyst** | Qwen2.5-14B | Apache 2.0 | ✅ Tetap | Interpretasi demografi dan socio-economic reasoning. Kuat untuk EN + ID. |
| **Competitor Scout** | ~~Llama 3.1 8B~~ → **Qwen2.5-7B** | Apache 2.0 | 🔄 Diganti | Llama bermasalah lisensi dan lemah Bahasa Indonesia. Qwen2.5-7B Apache 2.0, kuat EN + ID, sudah loaded di GPU 3 bersama Inquisitor — nol VRAM tambahan. |
| **Growth Hacker / Marketing Planner** | Qwen2.5-14B | Apache 2.0 | ✅ Tetap | Marketing creativity dan campaign ideation. Kuat EN + ID. |
| **CFO** | DeepSeek R1 Distill Qwen-14B | MIT | ✅ Tetap | Financial reasoning terstruktur. Benchmark dulu — fallback ke R1 Distill Qwen-32B jika perlu. |
| **Pricing Strategist** | ~~Mistral Small 3~~ → **Qwen2.5-14B** | Apache 2.0 | 🔄 Diganti | Mistral lemah Bahasa Indonesia. Qwen2.5-14B Apache 2.0, konsisten untuk EN + ID, sudah loaded di GPU 3 — nol VRAM tambahan. |

### 2.3 Worker Layer

| Agent | Model Lama | Model Baru | Lisensi | Status | Justifikasi Perubahan |
|-------|-----------|-----------|---------|--------|----------------------|
| **Inquisitor** | Qwen2.5-7B | Qwen2.5-7B | Apache 2.0 | ✅ Tetap | Conversational interview. Kuat EN + ID. |
| **Legal & Compliance** | Mistral 7B | **Qwen2.5-14B** | Apache 2.0 | 🔄 Diganti + 🌐 Global | Skala global, multi-jurisdiction. Web search + RAG dinamis + graceful fallback. |
| **Product Architect** | Llama 3.2 3B | **Qwen2.5-3B** | Apache 2.0 | 🔄 Diganti | Llama bermasalah lisensi. Qwen2.5-3B lebih kuat structured text EN + ID. |
| **HR Planner** | Phi-3 Mini | **Qwen2.5-3B** | Apache 2.0 | 🔄 Diganti | Phi-3 Mini lemah Bahasa Indonesia. Qwen2.5-3B lebih tepat dan lebih ringan. |
| **Supply Planner** | Gemma 2 2B | **Python Function** | — | 🔄 Utility Layer | Logic deterministik, tidak perlu LLM. |
| **SOP Designer** | Qwen2.5-3B | Qwen2.5-3B | Apache 2.0 | ✅ Tetap | Procedural generation dengan template konsisten. |

### 2.4 Utility Layer — Tanpa LLM

| Komponen | Implementasi |
|----------|-------------|
| **BEP Calculator** | Python function murni |
| **Cashflow Simulator** | Python function murni |
| **Supply Planner** | Python function murni ← **dipindah dari Worker Layer** |
| **Dependency Checker** | Python function murni |
| **Schema Validator** | Python function murni |

> ✅ Deterministik, tidak bisa halusinasi, nol biaya compute LLM.

---

## 3. Ringkasan Seluruh Perubahan Model (v1 → v5)

| Agent | v1 (Awal) | v2 | v3 | v4 | v5 (Sekarang) | Alasan |
|-------|-----------|-----|-----|-----|----------------|--------|
| **Orchestrator** | DeepSeek V3 671B | DeepSeek V3 671B | Qwen2.5-72B | Qwen2.5-72B | Qwen2.5-72B | OOM di MI300X |
| **Risk Manager** | DeepSeek R1 671B | DeepSeek R1 671B | R1 Distill Llama-70B | R1 Distill Llama-70B | R1 Distill Llama-70B | OOM di MI300X; varian Qwen-70B tidak tersedia di HuggingFace |
| **Competitor Scout** | Llama 3.1 8B | Llama 3.1 8B | Llama 3.1 8B | Llama 3.1 8B | **Qwen2.5-7B** | Lisensi Llama + lemah Bahasa Indonesia |
| **Pricing Strategist** | Mistral Small 3 | Mistral Small 3 | Mistral Small 3 | Mistral Small 3 | **Qwen2.5-14B** | Mistral lemah Bahasa Indonesia |
| **Legal & Compliance** | Mistral 7B | Mistral 7B + RAG statis | Mistral 7B + RAG statis | Qwen2.5-14B + Web Search + RAG | Qwen2.5-14B + Web Search + RAG | Skala global, multi-jurisdiction |
| **Product Architect** | Llama 3.2 3B | Qwen2.5-3B | Qwen2.5-3B | Qwen2.5-3B | Qwen2.5-3B | Lisensi Llama + lemah ID |
| **HR Planner** | Phi-3 Mini | Qwen2.5-3B | Qwen2.5-3B | Qwen2.5-3B | Qwen2.5-3B | Lemah Bahasa Indonesia |
| **Supply Planner** | Gemma 2 2B | Python Function | Python Function | Python Function | Python Function | Logic deterministik |
| Semua lainnya | — | Tidak berubah | Tidak berubah | Tidak berubah | Tidak berubah | Sudah tepat |

### Lisensi Seluruh Model Final (v5)

| Model | Lisensi | Bebas Komersial? |
|-------|---------|-----------------|
| Qwen2.5-72B | Apache 2.0 | ✅ Ya |
| R1 Distill Llama-70B | MIT | ✅ Ya |
| Qwen3-32B | Apache 2.0 | ✅ Ya |
| R1 Distill Qwen-14B | MIT | ✅ Ya |
| Qwen2.5-14B | Apache 2.0 | ✅ Ya |
| Qwen2.5-7B | Apache 2.0 | ✅ Ya |
| Qwen2.5-3B | Apache 2.0 | ✅ Ya |

> ✅ Seluruh model di v5 menggunakan lisensi Apache 2.0 atau MIT — bebas untuk penggunaan komersial dan lomba internasional tanpa batasan.

---

## 4. Dependency Graph

### 4.1 Aturan Eksekusi

```
Dependency Engine (kode Python/asyncio) yang mengatur ini — bukan Orchestrator LLM.
Orchestrator LLM hanya dipanggil untuk ambiguitas dan edge cases.
```

### 4.2 Graph Per Agent (Revisi v5)

```
[START]
   │
   ├──► Inquisitor (Qwen2.5-7B)                    ← tidak ada dependency
   │         │
   │         ▼ output: business_context.md
   │
   ├──► Geo Analyst (Qwen2.5-14B)                  ← depends: Inquisitor ✓
   ├──► Competitor Scout (Qwen2.5-7B)              ← depends: Inquisitor ✓
   │
   │    [Geo Analyst + Competitor Scout selesai]
   │         │
   │         ▼
   ├──► Growth Hacker (Qwen2.5-14B)                ← depends: Geo Analyst, Competitor Scout
   ├──► Pricing Strategist (Qwen2.5-14B)           ← depends: Geo Analyst, Competitor Scout
   │
   │    [Growth Hacker + Pricing Strategist selesai]
   │         │
   │         ▼
   ├──► CFO (DeepSeek R1 Distill Qwen-14B)         ← depends: Growth Hacker, Pricing Strategist
   │
   │    [CFO selesai]
   │         │
   │         ▼
   ├──► Legal & Compliance (Qwen2.5-14B)           ← depends: CFO, Pricing Strategist  🔄 model + arsitektur
   │         └── Web Search (global, prioritized sources)
   │         └── RAG dinamis per yurisdiksi (graceful fallback jika tidak ada)
   ├──► Product Architect (Qwen2.5-3B)             ← depends: Growth Hacker
   ├──► HR Planner (Qwen2.5-3B)                    ← depends: CFO
   ├──► Supply Planner (Python Function)            ← depends: CFO
   │
   │    [Semua Worker selesai]
   │         │
   │         ▼
   ├──► SOP Designer (Qwen2.5-3B)                  ← depends: Product Architect, HR Planner, Supply Planner
   │
   │    [Semua Analyst + Worker selesai]
   │         │
   │         ▼
   ├──► Critic / Gap Finder (Qwen3-32B)            ← depends: SEMUA layer selesai
   ├──► Risk Manager (R1 Distill Llama-70B)        ← depends: SEMUA layer selesai
   │
   │    [Critic + Risk Manager selesai]
   │         │
   │         ▼
   └──► Orchestrator Final Review (Qwen2.5-72B)    ← depends: Critic, Risk Manager
              │
              ▼
           [OUTPUT]
```

### 4.3 Tabel Dependency Formal (Revisi v5)

```python
DAG = {
    "inquisitor":          [],
    "geo_analyst":         ["inquisitor"],
    "competitor_scout":    ["inquisitor"],
    "growth_hacker":       ["geo_analyst", "competitor_scout"],
    "pricing_strategist":  ["geo_analyst", "competitor_scout"],
    "cfo":                 ["growth_hacker", "pricing_strategist"],
    "legal_compliance":    ["cfo", "pricing_strategist"],
    "product_architect":   ["growth_hacker"],
    "hr_planner":          ["cfo"],
    "supply_planner":      ["cfo"],          # ← sekarang Python function, bukan LLM
    "sop_designer":        ["product_architect", "hr_planner", "supply_planner"],
    "critic":              ["geo_analyst", "competitor_scout", "growth_hacker",
                            "pricing_strategist", "cfo", "legal_compliance",
                            "product_architect", "hr_planner", "supply_planner",
                            "sop_designer"],
    "risk_manager":        ["critic"],
    "orchestrator_review": ["critic", "risk_manager"],
}
```

> Dependency graph tidak berubah strukturnya. Supply Planner tetap ada sebagai node, hanya implementasinya yang berubah dari LLM menjadi Python function.

---

## 5. Estimasi VRAM dan Alokasi GPU (Revisi v5)

**Hardware yang digunakan: AMD Instinct MI300X — 192 GB HBM3 per GPU**

### 5.1 Spesifikasi MI300X yang Relevan

| Spesifikasi | Detail |
|-------------|--------|
| VRAM per GPU | 192 GB HBM3 |
| Memory Bandwidth | 5.2 TB/s per GPU |
| Interconnect | Infinity Fabric 3.0 |
| Compute | FP8 dan BF16 native |
| Framework support | ROCm — vLLM, SGLang, Ollama, HuggingFace TGI |

### 5.2 Tabel VRAM Per Model di MI300X (Revisi v5)

| Model | Agent | Lisensi | Params | VRAM (BF16) | Muat di 1× MI300X? |
|-------|-------|---------|--------|-------------|---------------------|
| ~~DeepSeek V3~~ | ~~Orchestrator~~ | — | 671B MoE | ~720 GB | ❌ OOM — diganti |
| ~~DeepSeek R1 (full)~~ | ~~Risk Manager~~ | — | 671B MoE | ~720 GB | ❌ OOM — diganti |
| ~~Mistral Small 3~~ | ~~Pricing Strategist~~ | — | ~22B | ~44 GB | ❌ Diganti — lemah Bahasa Indonesia |
| ~~Llama 3.1 8B~~ | ~~Competitor Scout~~ | — | 8B | ~16 GB | ❌ Diganti — lisensi + lemah Bahasa Indonesia |
| ~~Mistral 7B~~ | ~~Legal & Compliance~~ | — | 7B | ~14 GB | ❌ Diganti — skala global |
| **Qwen2.5-72B** | Orchestrator | Apache 2.0 | 72B | ~144 GB | ✅ Muat dengan headroom |
| **R1 Distill Llama-70B** | Risk Manager | MIT | 70B | ~140 GB | ✅ Muat dengan headroom |
| **Qwen3-32B** | Critic | Apache 2.0 | 32B | ~64 GB | ✅ Nyaman |
| **R1 Distill Qwen-14B** | CFO | MIT | 14B | ~28 GB | ✅ Nyaman |
| **Qwen2.5-14B** | Geo Analyst, Growth Hacker, Legal, Pricing Strategist | Apache 2.0 | 14B | ~28 GB | ✅ Nyaman |
| **Qwen2.5-7B** | Inquisitor, Competitor Scout | Apache 2.0 | 7B | ~14 GB | ✅ Nyaman |
| **Qwen2.5-3B** | Product Architect, HR Planner, SOP Designer | Apache 2.0 | 3B | ~6 GB | ✅ Nyaman |

### 5.3 Contoh Docker Deploy (BF16, Tanpa Quantization)

**Orchestrator — Qwen2.5-72B (GPU 0 / Mesin Dhiwa):**
```bash
docker run -d --name orchestrator-72b \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  --ipc=host --shm-size 32G \
  -p 8000:8000 \
  -e HIP_VISIBLE_DEVICES=0 \
  -e VLLM_USE_V1=0 \
  --entrypoint python3 \
  vllm/vllm-openai-rocm:v0.17.1 \
  -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-72B-Instruct \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  --enforce-eager \
  --host 0.0.0.0 --dtype bfloat16
```

**Risk Manager — R1 Distill Llama-70B (GPU 1 / Mesin Amitha):**
```bash
docker run -d --name DeepSeek-R1-Distill-Llama-70B \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --group-add render \
  --ipc=host --shm-size 32G \
  -p 8000:8000 \
  -e HIP_VISIBLE_DEVICES=0 \
  -e VLLM_USE_V1=0 \
  --entrypoint python3 \
  vllm/vllm-openai-rocm:v0.17.1 \
  -m vllm.entrypoints.openai.api_server \
  --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 32768 \
  --enforce-eager \
  --host 0.0.0.0 --dtype bfloat16
```

> ✅ Tidak ada `--quantization`, tidak ada drama FP8. Standard BF16 deployment.

### 5.4 Alokasi Agent ke GPU (Revisi v5 — 4× MI300X)

**Konfigurasi minimum yang direkomendasikan: 4× MI300X 192GB**

| GPU | Model | Agent | VRAM | Sisa |
|-----|-------|-------|------|------|
| **GPU 0** (192GB) | Qwen2.5-72B | Orchestrator | ~144GB | ~48GB |
| **GPU 1** (192GB) | R1 Distill Llama-70B | Risk Manager | ~140GB | ~52GB |
| **GPU 2** (192GB) | Qwen3-32B | Critic | ~64GB | |
| | R1 Distill Qwen-14B | CFO | ~28GB | **~100GB sisa** ✓ |
| **GPU 3** (192GB) | Qwen2.5-14B | Geo Analyst | ~28GB | |
| | Qwen2.5-14B | Growth Hacker | ~28GB | |
| | Qwen2.5-14B | Legal & Compliance | ~28GB | |
| | Qwen2.5-14B | Pricing Strategist | ~28GB | |
| | Qwen2.5-7B | Inquisitor | ~14GB | |
| | Qwen2.5-7B | Competitor Scout | ~14GB | |
| | Qwen2.5-3B | Product Architect | ~6GB | |
| | Qwen2.5-3B | HR Planner | ~6GB | |
| | Qwen2.5-3B | SOP Designer | ~6GB | **~34GB sisa** ✓ |

**Total VRAM terpakai per GPU:**
```
GPU 0: ~144GB / 192GB  (75%) — headroom KV cache ~48GB
GPU 1: ~140GB / 192GB  (73%) — headroom KV cache ~52GB
GPU 2:  ~92GB / 192GB  (48%) — headroom lega
GPU 3: ~158GB / 192GB  (82%) — headroom KV cache ~34GB, paling padat
```

> ⚠️ GPU 3 adalah yang paling padat (82%). Pantau KV cache usage terutama saat Legal & Compliance melakukan web search dengan context panjang.
> ✅ Seluruh model menggunakan lisensi Apache 2.0 atau MIT — tidak ada model berlisensi terbatas.

### 5.5 Perbandingan Skenario GPU

| Konfigurasi | Total VRAM | Status | Catatan |
|-------------|-----------|--------|---------|
| **4× MI300X 192GB** | 768 GB | ✅ **Minimum recommended** | Semua model muat paralel, headroom 25–30% per GPU |
| 6× MI300X 192GB | 1.152 TB | ✅ Optimal | Lebih banyak ruang untuk context panjang dan concurrent requests |
| 2× MI300X 192GB | 384 GB | ⚠️ Terbatas | GPU 0 & 1 habis untuk 72B + 70B; model lain harus sharing dan antri |
| 1× MI300X 192GB | 192 GB | ❌ Tidak feasible | Hanya cukup untuk 1 model besar, sistem tidak bisa jalan paralel |
| 8× A100 80GB | 640 GB | ⚠️ Lebih kompleks | Butuh tensor parallel untuk 72B dan 70B; setup lebih rumit |

---

## 6. State Management

### 6.1 Struktur Shared Memory (Markdown + JSON)

```markdown
# Shared State — [Session ID]

## Status
```json
{
  "inquisitor":         { "status": "done",    "completed_at": "..." },
  "geo_analyst":        { "status": "running", "started_at": "..."   },
  "competitor_scout":   { "status": "pending"                        },
  "growth_hacker":      { "status": "locked"                         }
}
```

## Outputs
### inquisitor
[output bebas di sini]

### geo_analyst
[output bebas di sini]
```

### 6.2 Status Lifecycle

```
pending → running → done
                 → failed → retry → done / abort
locked  (dependency belum terpenuhi, tidak bisa dijalankan)
```

---

## 7. Catatan Risiko (Revisi v5)

| Agent | Risiko | Mitigasi | Priority |
|-------|--------|----------|----------|
| **Legal & Compliance** | Web search ke sumber tidak resmi bisa hasilkan informasi hukum yang salah | Source prioritization — tier 1 (gov sites) diprioritaskan; output wajib sertakan URL + tanggal sumber; confidence level per yurisdiksi | 🔴 Tinggi |
| **Legal & Compliance** | RAG tidak tersedia untuk yurisdiksi tertentu | Graceful fallback — sistem tetap jalan dengan web search only; output diberi flag "RAG unavailable, web-only" | 🟡 Sedang |
| **GPU 3** | Paling padat (82%) — 4 agent memanggil `model-qwen14b` secara bersamaan | Set `--max-num-seqs` sesuai kebutuhan; monitor queue latency; jika bottleneck, pertimbangkan pindah Pricing ke GPU 2 | 🟡 Sedang |
| **Orchestrator (Qwen2.5-72B)** | Lebih kecil dari V3 untuk routing edge cases sangat kompleks | Benchmark dengan skenario multi-agent routing kompleks sebelum production | 🟡 Sedang |
| **Risk Manager (R1 Distill Llama-70B)** | Distill version bisa kehilangan depth reasoning vs R1 full; base model Llama berbeda dari seri Qwen | Prompt Chain-of-Thought eksplisit; evaluasi kualitas output risk scenario | 🟡 Sedang |
| **CFO (R1 Distill Qwen-14B)** | Edge cases finansial kompleks | Prompt terstruktur + output format rigid. Fallback ke R1 Distill Qwen-32B jika perlu | 🟡 Sedang |
| **Qwen2.5-3B** (PA, HR, SOP) | Model kecil, output bisa dangkal untuk dokumen kompleks | Template sangat rigid; benchmark dengan dokumen bisnis nyata EN + ID | 🟢 Rendah |

---

## 8. Arsitektur Container

### 8.1 Prinsip: Model Container vs Agent Container

Ada dua jenis container yang berbeda peran dan tidak boleh dicampur:

- **Model container** — menjalankan inference engine (vLLM) dan memuat weights model ke GPU. Satu container per model unik.
- **Agent container** — menjalankan logika bisnis agent (system prompt, state, tools). Satu container per agent. Tidak memuat model — hanya memanggil model container via HTTP.

Konteks setiap agent **tidak pernah tercampur** meskipun berbagi model container yang sama, karena setiap request membawa full context window-nya sendiri (system prompt + conversation history + output agent sebelumnya) dikirim ulang di setiap API call.

```
agent-geo-analyst  ──┐
agent-growth-hacker──┼──► model-qwen14b (GPU 3) ← setiap request isolated
agent-legal        ──┘
```

### 8.2 Daftar Semua Container

#### Model Containers (per model unik)

| Container | Model | GPU | Port | VRAM |
|-----------|-------|-----|------|------|
| `model-qwen72b` | Qwen2.5-72B | GPU 0 | 8000 | ~144GB |
| `DeepSeek-R1-Distill-Llama-70B` | R1 Distill Llama-70B | GPU 1 | 8001 | ~140GB |
| `model-qwen3-32b` | Qwen3-32B | GPU 2 | 8002 | ~64GB |
| `model-r1-14b` | R1 Distill Qwen-14B | GPU 2 | 8003 | ~28GB |
| `model-qwen14b` | Qwen2.5-14B | GPU 3 | 8004 | ~28GB |
| `model-qwen7b` | Qwen2.5-7B | GPU 3 | 8005 | ~14GB |
| `model-qwen3b` | Qwen2.5-3B | GPU 3 | 8006 | ~6GB |

#### Agent Containers (per agent, tidak ada GPU)

| Container | Agent | Memanggil Model Container |
|-----------|-------|--------------------------|
| `agent-orchestrator` | Orchestrator | `model-qwen72b:8000` |
| `agent-critic` | Critic | `model-qwen3-32b:8002` |
| `agent-risk-manager` | Risk Manager | `DeepSeek-R1-Distill-Llama-70B:8001` |
| `agent-geo-analyst` | Geo Analyst | `model-qwen14b:8004` |
| `agent-competitor-scout` | Competitor Scout | `model-qwen7b:8005` |
| `agent-growth-hacker` | Growth Hacker | `model-qwen14b:8004` |
| `agent-pricing-strategist` | Pricing Strategist | `model-qwen14b:8004` |
| `agent-cfo` | CFO | `model-r1-14b:8003` |
| `agent-inquisitor` | Inquisitor | `model-qwen7b:8005` |
| `agent-legal` | Legal & Compliance | `model-qwen14b:8004` |
| `agent-product-architect` | Product Architect | `model-qwen3b:8006` |
| `agent-hr-planner` | HR Planner | `model-qwen3b:8006` |
| `agent-sop-designer` | SOP Designer | `model-qwen3b:8006` |
| `agent-supply-planner` | Supply Planner | — (Python function) |
| `shared-memory` | State Manager | — (Redis) |

### 8.3 Contoh Docker Compose (Skeleton)

```yaml
services:

  # ── MODEL CONTAINERS ──────────────────────────────────────

  model-qwen72b:
    image: vllm/vllm-openai-rocm:v0.17.1
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    environment:
      HIP_VISIBLE_DEVICES: "0"
      VLLM_USE_V1: "0"
    entrypoint: python3
    command: >
      -m vllm.entrypoints.openai.api_server
      --model Qwen/Qwen2.5-72B-Instruct
      --dtype bfloat16
      --gpu-memory-utilization 0.90
      --max-model-len 32768
      --enforce-eager
      --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    ipc: host
    shm_size: 32g

  DeepSeek-R1-Distill-Llama-70B:
    image: vllm/vllm-openai-rocm:v0.17.1
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    environment:
      HIP_VISIBLE_DEVICES: "0"
      VLLM_USE_V1: "0"
    entrypoint: python3
    command: >
      -m vllm.entrypoints.openai.api_server
      --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B
      --dtype bfloat16
      --gpu-memory-utilization 0.90
      --max-model-len 32768
      --enforce-eager
      --host 0.0.0.0 --port 8001
    ports: ["8001:8001"]
    ipc: host
    shm_size: 32g

  model-qwen14b:
    image: vllm/vllm-openai-rocm:v0.17.1
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["video", "render"]
    environment:
      HIP_VISIBLE_DEVICES: "0"
      VLLM_USE_V1: "0"
    entrypoint: python3
    command: >
      -m vllm.entrypoints.openai.api_server
      --model Qwen/Qwen2.5-14B-Instruct
      --dtype bfloat16
      --gpu-memory-utilization 0.60
      --max-model-len 32768
      --enforce-eager
      --host 0.0.0.0 --port 8004
    ports: ["8004:8004"]
    ipc: host
    shm_size: 16g

  # (model-qwen3-32b, model-r1-14b, model-qwen7b, model-qwen3b — pola sama)

  # ── AGENT CONTAINERS ──────────────────────────────────────

  agent-geo-analyst:
    build: ./agents/geo_analyst
    environment:
      MODEL_URL: "http://model-qwen14b:8004/v1"
      SHARED_MEMORY_URL: "http://shared-memory:6379"
    depends_on: [model-qwen14b, shared-memory]

  agent-growth-hacker:
    build: ./agents/growth_hacker
    environment:
      MODEL_URL: "http://model-qwen14b:8004/v1"
      SHARED_MEMORY_URL: "http://shared-memory:6379"
    depends_on: [model-qwen14b, shared-memory]

  agent-legal:
    build: ./agents/legal_compliance
    environment:
      MODEL_URL: "http://model-qwen14b:8004/v1"
      SHARED_MEMORY_URL: "http://shared-memory:6379"
      RAG_URL: "http://rag-service:9000"
      WEB_SEARCH_ENABLED: "true"
    depends_on: [model-qwen14b, shared-memory]

  # (agent lainnya — pola sama)

  # ── INFRASTRUKTUR ─────────────────────────────────────────

  shared-memory:
    image: redis:7-alpine
    ports: ["6379:6379"]

  rag-service:                                   # opsional
    build: ./rag
    ports: ["9000:9000"]
```

### 8.4 Poin Penting

**`gpu-memory-utilization` untuk GPU 3** yang menjalankan 3 model berbeda:

```
model-qwen14b  → gpu-memory-utilization: 0.60  (~115GB dari 192GB)
model-qwen7b   → gpu-memory-utilization: 0.10  (~19GB)
model-qwen3b   → gpu-memory-utilization: 0.06  (~12GB)
                                          ──────────────
                                          total: ~146GB ✓ (sisa ~46GB untuk OS + overhead)
```

> ⚠️ `model-qwen14b` melayani 4 agent sekaligus (Geo, Growth, Legal, Pricing) — pastikan `--max-num-seqs` dikonfigurasi cukup tinggi untuk handle concurrent requests.

**`depends_on`** di agent container memastikan agent tidak start sebelum model container siap menerima request.

**RAG service** di `agent-legal` menggunakan environment variable terpisah dan bersifat opsional — jika container RAG tidak jalan, agent legal tetap bisa berjalan dengan web search only (graceful fallback).

---

## 9. Rencana Kolaborasi Tim

### 9.1 Prinsip Pembagian Kerja

> **Bagi berdasarkan layer, bukan berdasarkan agent.**
> Pembagian per agent menyebabkan semua developer blocking satu sama lain karena semua agent butuh infrastruktur yang sama sebelum bisa jalan.

### 9.2 Pembagian Per Developer

| Developer | Layer / Tanggung Jawab | Deliverable Utama |
|-----------|----------------------|-------------------|
| **Dev 1 — Ketua** | Fondasi sistem | `shared_memory.py`, `schemas.py`, `orchestrator.py` |
| **Dev 2** | Layer bisnis — hulu | `market_agent.py`, `ops_agent.py`, `app.py` |
| **Dev 3** | Layer bisnis — hilir | `finance_agent.py`, `critic_agent.py`, `output_formatter.py` |

### 9.3 Detail Tugas Per Developer

#### Dev 1 — Ketua (Kerjakan Hari Pertama, Paling Kritis)

Tiga file ini harus selesai sebelum Dev 2 dan Dev 3 bisa mulai:

**`shared_memory.py`** — Fondasi segalanya. Class `SharedMemory` dengan method:
```python
memory.set(key, value, status)   # tulis output agent
memory.get(key)                  # baca nilai + status
memory.emit_event(event)         # trigger dependency checker
```

**`schemas.py`** — Kontrak antar developer. Semua Pydantic model output tiap agent:
```python
class MarketOutput(BaseModel): ...
class OpsOutput(BaseModel): ...
class FinanceOutput(BaseModel): ...
class CriticOutput(BaseModel): ...
```

**`orchestrator.py`** — Logic routing dan dependency check. Tidak perlu sempurna di hari pertama, cukup bisa dispatch agent satu per satu.

#### Dev 2 — Layer Bisnis Hulu

**`market_agent.py`** — Market Analyst Agent
```
Input  : location, budget, skills
Output : MarketOutput → shared memory
Model  : Qwen2.5-14B + web search tool
Tugas  : analisis lokasi, target pasar, kompetitor
```

**`ops_agent.py`** — Operations Agent
```
Precondition : market_analysis selesai di memory
Output       : OpsOutput → shared memory
Model        : Qwen2.5-14B
Tugas        : alat, SOP, resource plan
```

**`app.py / main.py`** — User Input Interface
```
Implementasi : CLI atau Streamlit UI
Fungsi       : form input (modal, lokasi, skill) → kirim ke Orchestrator
```

#### Dev 3 — Layer Bisnis Hilir

**`finance_agent.py`** — Finance Agent (CFO)
```
Precondition : ops_output selesai di memory
Output       : FinanceOutput → shared memory
Model        : DeepSeek R1 Distill Qwen-14B
Tugas        : kalkulasi modal, BEP, cashflow
```

**`critic_agent.py`** — Critic Agent
```
Precondition : SEMUA agent selesai
Output       : CriticOutput → shared memory
Model        : Qwen3-32B
Tugas        : deteksi inkonsistensi, stress test asumsi
```

**`output_formatter.py`** — Output Formatter
```
Input  : baca semua key dari shared memory
Output : render ke Markdown / PDF
```

### 9.4 Timeline & Flow Kolaborasi

```
Hari 1
  Dev 1 ──► schemas.py (WAJIB selesai duluan)
         ──► shared_memory.py
         ──► orchestrator.py (draft)
                    │
                    ▼ schemas.py done → unlock Dev 2 & Dev 3
Hari 2+
  Dev 2 ──► market_agent.py
         ──► ops_agent.py         (paralel dengan Dev 3)
         ──► app.py

  Dev 3 ──► finance_agent.py      (mock OpsOutput dulu)
         ──► critic_agent.py      (paralel dengan Dev 2)
         ──► output_formatter.py
```

### 9.5 Aturan Penting: Mock-First Development

> ⚠️ **Jangan sambungkan ke LLM sebelum alur data terbukti benar.**

```python
# Contoh mock untuk development awal
def market_agent_mock(input_data) -> MarketOutput:
    return MarketOutput(
        location="Jakarta Selatan",
        target_segment="UMKM F&B",
        top_competitors=["Warung A", "Warung B"],
        market_size_estimate=500_000_000
    )
```

Alurnya: hardcode semua return value → validasi data mengalir benar (`Market → Ops → Finance → Critic`) → pastikan schema tidak ada mismatch → baru sambungkan ke model asli.

### 9.6 Dependency File Antar Developer

```
schemas.py          ← dibuat Dev 1, dipakai SEMUA developer
shared_memory.py    ← dibuat Dev 1, dipakai SEMUA developer
orchestrator.py     ← dibuat Dev 1, dipakai Dev 2 & Dev 3 sebagai entry point
market_agent.py     ← dibuat Dev 2, dibutuhkan Dev 2 (ops) dan Dev 3 (via memory)
ops_agent.py        ← dibuat Dev 2, dibutuhkan Dev 3 (finance)
finance_agent.py    ← dibuat Dev 3, dibutuhkan Dev 3 (critic)
critic_agent.py     ← dibuat Dev 3, dibutuhkan Dev 3 (formatter)
output_formatter.py ← dibuat Dev 3, final output
app.py              ← dibuat Dev 2, entry point untuk user
```

---

## 10. Checklist Sebelum Production

- [ ] Validasi Docker deploy Qwen2.5-72B bisa load tanpa error
- [ ] Validasi Docker deploy R1 Distill Llama-70B bisa load tanpa error
- [ ] Validasi Docker deploy Qwen3-32B bisa load tanpa error
- [ ] Benchmark Orchestrator (Qwen2.5-72B) dengan skenario routing multi-agent kompleks
- [ ] Benchmark Risk Manager (R1 Distill Llama-70B) dengan skenario kegagalan bisnis edge cases
- [ ] Benchmark CFO (R1 Distill Qwen-14B) dengan skenario cashflow edge cases
- [ ] Test Legal & Compliance — web search dengan minimal 5 yurisdiksi berbeda
- [ ] Test Legal & Compliance — graceful fallback saat RAG tidak tersedia (output tetap jalan, ada flag warning)
- [ ] Validasi source prioritization legal berjalan dengan benar (gov sites > verified DB > open web)
- [ ] Benchmark HR Planner (Qwen2.5-3B) dengan data job description multi-bahasa
- [ ] Validasi template SOP Product Architect sebelum sambung ke model
- [ ] Test Supply Planner sebagai Python function dengan data inventory aktual
- [ ] Monitor KV cache usage saat context panjang di semua GPU
- [ ] Setup Docker health check + auto-restart untuk container model besar

---

*Dokumen ini adalah revisi v5. Perubahan dari v4: Legal & Compliance diupgrade ke Qwen2.5-14B dengan arsitektur global (web search open + RAG dinamis per yurisdiksi + graceful fallback). Alokasi GPU dikonsolidasi ke 4× MI300X. Arsitektur Container memisahkan model container dan agent container. Risk Manager menggunakan DeepSeek R1 Distill Llama-70B — varian Qwen-70B tidak tersedia di HuggingFace, varian Llama-70B adalah pilihan tertinggi yang ada dengan capability reasoning setara.*