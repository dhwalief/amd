# Amitha Plan

## Status Saat Ini (Berdasarkan Evaluasi v5)
Ketua (Dev 1) telah menyelesaikan sebagian besar fondasi sistem:
- `core/schemas.py` (Kontrak output agent) - Selesai
- `core/shared_memory.py` (State management) - Selesai
- `app/main.py` (Streamlit frontend) - Selesai / Ada progress

**Namun, yang belum selesai dari tugas Dev 1 (Ketua) adalah:**
- `core/engine.py` (atau `orchestrator.py`): Logic routing dan dependency check.

## Rencana Pembagian Tugas (Untuk 2 Orang)

Karena kalian berdua (misal: Dev A dan Dev B) akan melanjutkan, berikut adalah langkah yang harus dilakukan:

### Tahap 1: Selesaikan Fondasi (Blocker)
**Siapa:** Salah satu dari kalian (Dev A)
**Tugas:** Membuat `core/engine.py`
**Deskripsi:**
- Membuat Orchestrator sederhana yang bisa membaca `shared_memory` dan men-dispatch agent berdasarkan Dependency Graph (DAG).
- Implementasi status: `pending` → `running` → `done`.
- Harus selesai sebelum kalian bisa menguji agen secara end-to-end.

### Tahap 2: Pembagian Tugas Pengembangan Agen (Sistem Mock-First)
Setelah (atau paralel dengan) Tahap 1, kalian bisa mulai membagi pengerjaan layer bisnis:

**Dev A (Layer Hulu / Ops):**
1. `agents/executive/orchestrator.py` (LLM prompt routing)
2. `agents/analyst/geo_analyst.py` & `competitor_scout.py`
3. `agents/worker/inquisitor.py`
4. Membangun Tooling pencarian web untuk `legal_compliance`.

**Dev B (Layer Hilir / Finance & Risk):**
1. `agents/analyst/growth_hacker.py`, `pricing_strategist.py`, `cfo.py`
2. `agents/executive/critic.py` & `risk_manager.py`
3. Pengembangan Layer Utilitas Python (BEP Calc, Cashflow Sim, dsb) tanpa LLM.
4. `output_formatter.py` untuk mengenerate laporan akhir ke `.md` atau `.pdf`.

### Tahap 3: Mock-First Validation
JANGAN langsung sambungkan ke model (LLM vLLM). Buat fungsi agent yang mengembalikan dummy data Pydantic (Mock) dan pastikan urutan eksekusi di `engine.py` berjalan sempurna (mengalir dari Inquisitor -> Geo/Competitor -> dst).

### Tahap 4: Integrasi LLM (MI300X vLLM)
Setelah sistem mock jalan, baru ubah fungsi agen untuk melakukan HTTP request ke endpoint model (Qwen2.5 / DeepSeek R1 Distill) seperti yang ada di `agent-structure-plan.md`.

## Langkah Selanjutnya Sekarang
Pilih siapa yang akan menjadi Dev A dan Dev B, lalu konfirmasikan untuk kita mulai menggarap `core/engine.py` (Tahap 1) terlebih dahulu.
