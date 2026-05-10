# Changelog - Branch: dhwalief

Semua perubahan dan aktivitas signifikan pada branch `dhwalief` akan didokumentasikan di sini.

## [2026-05-10]
### Added
- Membuat file `dhwalief-plan.md` untuk mencatat target pekerjaan pada branch ini sesuai dengan mandat dari `rules.md`.
- Membuat file `dhwalief-changelog.md` sebagai log perubahan operasional dan kode di branch ini.
- Melakukan analisis mendalam terhadap keseluruhan proyek berdasarkan arsitektur v5 (MI300X, DAG pipeline, Model & Agent Containers) dan menyajikannya dalam sebuah artifact terpisah.
- Melakukan tinjauan arsitektur terhadap konsep "Business Co-Pilot" dari file `.agent/plan/user-flow-plan.md` dan memvalidasi kelayakannya untuk diterapkan ke dalam arsitektur v5.
- Mengimplementasikan fitur **Business Co-Pilot** ke *core engine*:
  - Memisahkan DAG ke file mandiri (`core/dag.py`) dengan menginjeksi node *virtual* (`USER_REVIEW_1`, `USER_REVIEW_2`) dan peta `RERUN_MAP`.
  - Melakukan ekspansi pada memori terpusat (`core/shared_memory.py`) untuk mendukung sesi berfase, penyimpanan *user prefs*, dan fungsi *invalidate* (*Partial Re-run*).
  - Menyelaraskan *schema* (`core/schemas.py`) dengan struktur *virtual node*.
  - Melakukan perombakan logika jeda (`DAG Pausing`) pada pelaksana tugas asinkron (`core/engine.py`).
  - Memperbaiki pengujian (*unit tests*) di `test_shared_memory.py` agar sinkron dengan referensi *import* DAG yang baru.
- Menghubungkan logika *pause* dengan Antarmuka Pengguna (Tahap 2):
  - Memperbaiki `setup_and_run` di `agents/executive/orchestrator.py` agar tidak memaksa eksekusi final saat sedang *paused*, sekaligus meregistrasikan *mock* `PROPOSAL_GENERATOR` dan agen utama `ORCHESTRATOR` ke dalam *engine*.
  - Menanamkan kerangka MVP interaktif di Streamlit (`app/dashboard.py`) untuk memantau status `USER_REVIEW`. Dashboard kini memunculkan *banner* "Tinjau & Setujui" secara dinamis dan mampu memantik kembali *background thread* AI saat pengguna menyetujui opsi.
- Mengembangkan agen fungsional **PROPOSAL_GENERATOR**:
  - Mengonfigurasi skema Pydantic (`ProposalOption` dan `ProposalGeneratorOutput`) di `core/schemas.py`.
  - Menulis logika *prompt engineering* menggunakan kelas `ChatOpenAI` Qwen2.5 di dalam file `agents/executive/proposal_generator.py` yang mensintesis data riset (*Geo, Competitor, Growth, Pricing*).
  - Menyingkirkan *mock* fungsi dari Orchestrator dan mengintegrasikan agen asli ini ke dalam sistem.
  - Memperbarui komponen Dashboard untuk menampilkan opsi strategi yang dihasilkan LLM secara interaktif (*Radio buttons* dan *Details*).
- **Integrasi *Worker Layer* (Source of Truth Sentralisasi):**
  - Menanamkan *helper function* `get_selected_proposal()` di dalam `core/shared_memory.py` untuk secara absolut mengambil opsi bisnis yang diklik oleh *user*.
  - Menyelaraskan agen hilir/operasional (`CFO`, `Product Architect`, `HR Planner`, `Legal`, `SOP Designer`) agar menggunakan proposal terpilih tersebut sebagai jangkar *prompt*-nya, menggantikan data lama (*Growth Hacker* / *Inquisitor*) untuk menjaga relevansi yang solid antara desain strategis dan operasional.
- **Implementasi *Partial Re-run* (Invalidasi Selektif):**
  - Memodifikasi UI Sidebar di `app/dashboard.py` untuk mendeteksi secara *real-time* perubahan input dari pengguna (seperti `budget` atau `location`) setelah eksekusi pertama berjalan.
  - Memanfaatkan peta dependensi `RERUN_MAP` di `core/dag.py` untuk memanggil `memory.invalidate_agents()`.
  - Jika `budget` berubah, sistem membatalkan CFO ke bawah tanpa mengusik riset pasar. Jika `location` berubah, hampir seluruh jaringan diruntuhkan dan dibangun ulang secara efisien. Tombol otomatis berubah menjadi "Update Configuration & Rerun".
