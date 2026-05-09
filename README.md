# Go to America — Multi-Agent System (v5)

Proyek ini adalah implementasi **Sistem Multi-Agent** berkinerja tinggi yang dirancang untuk merencanakan strategi bisnis "Go to America" secara otomatis. Sistem ini menggunakan berbagai agen terspesialisasi yang ditenagai oleh model bahasa berlisensi terbuka (Apache 2.0 & MIT) seperti keluarga Qwen2.5 dan DeepSeek R1 Distill Llama, dioptimalkan untuk berjalan pada infrastruktur 4× AMD Instinct MI300X GPUs.

## Arsitektur Layered Agent

Sistem ini terbagi ke dalam 4 layer utama yang bekerja secara asinkron dengan dependensi berbasis Directed Acyclic Graph (DAG):

1. **Executive Layer**
   - Orchestrator (Qwen2.5-72B): Pengendali utama dan perutean tugas kompleks.
   - Critic / Gap Finder (Qwen3-32B): Mendeteksi kontradiksi antar output agen.
   - Risk Manager (R1 Distill Llama-70B): Analisis skenario risiko bisnis kompleks.

2. **Analyst Layer**
   - Terdiri dari Geo Analyst, Competitor Scout, Growth Hacker, CFO, dan Pricing Strategist.
   - Didukung oleh model keluarga Qwen2.5 (7B–14B) & R1 Distill Qwen-14B untuk penalaran analisis spesifik domain.

3. **Worker Layer**
   - Terdiri dari Inquisitor, Legal & Compliance, Product Architect, HR Planner, dan SOP Designer.
   - Berjalan pada model Qwen2.5 (3B–14B) dengan tugas memproduksi standar operasional dan validasi praktis.

4. **Utility Layer**
   - Fungsi deterministik Python murni tanpa LLM untuk akurasi tinggi dan tanpa halusinasi (contoh: BEP Calculator, Cashflow Simulator, Supply Planner, Schema Validator).

## Struktur Direktori Utama

- `.agent/` : Dokumen panduan, blueprint (*plan*), dan *rules* untuk agen *AI Assistant*.
- `.env` : Konfigurasi *endpoint* vLLM (MI300X) & API Keys.
- `app/` : Antarmuka *Frontend* (Streamlit).
- `core/` : *Backend Engine*, manajemen *state* asinkron (*Shared Memory*), skema Pydantic, dan konektor LLM.
- `agents/` : Kumpulan logika internal tiap *agent* (Executive, Analyst, Worker, Utility).
- `data/` : Basis pengetahuan lokal, basis data *RAG* dasar, dokumen legal, dan *template* laporan.
- `pyproject.toml` / `poetry.lock` : File pengelola *dependency*.

## Infrastruktur & Model

Sistem mengadopsi arsitektur pemisahan *container*:
- **Model Container:** Menjalankan mesin *inference* (seperti vLLM) yang memuat *weights* ke dalam GPU (1 *container* per model independen).
- **Agent Container:** Menjalankan logika bisnis (prompt, tool) dan saling berkomunikasi lewat API HTTP, tanpa saling menumpuk dan mencampur konteks.

Model telah direvisi penuh (v5) untuk mengatasi isu *Out of Memory* (OOM), memprioritaskan kemampuan Bahasa Indonesia & Inggris, dan kepatuhan penuh lisensi komersial bebas (Apache 2.0/MIT).

## Prasyarat & Instalasi

Disarankan untuk menjalankan secara penuh menggunakan 4× AMD Instinct MI300X 192GB. 

1. **Persiapan Repositori**
   ```bash
   git clone <repo-url>
   cd goto-america
   ```

2. **Instalasi Dependencies (Untuk Pengembangan Lokal)**
   Pastikan Anda menggunakan Python 3.11+ dan [Poetry](https://python-poetry.org/):
   ```bash
   poetry install
   ```

3. **Menjalankan Sistem**
   Untuk menginisialisasi eksekusi model (baik secara kontainer terpisah atau *development server*), Anda dapat menyesuaikan konfigurasi `.env` dan menjalankannya melalui perintah skrip atau *docker-compose*.
   Contoh:
   ```bash
   poetry run python app/main.py
   ```
   *(Catatan: Lihat dokumen di dalam `.agent/plan/` untuk melihat `docker run` command lengkap bagi model-model spesifik).*

## Aturan & Dokumentasi Pengembangan

Untuk memahami detail pengembangan lebih dalam, silakan baca dokumentasi *blueprint*:
- **[Agent Structure Plan](./.agent/plan/agent-structure-plan.md)**: Detail lengkap VRAM, alokasi GPU, model, dan alur DAG.
- **[Project Structure Plan](./.agent/plan/project-structure.md)**: Gambaran arsitektur direktori.

> **PERHATIAN (Sesuai `.agent/rules.md`)**:
> 1. JANGAN UBAH `config.py` secara sembarangan.
> 2. SELALU BACA `plan.md` di direktori `.agent/plan/` sebelum memulai tugas pengembangan apa pun.
