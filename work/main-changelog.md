# Changelog: Branch `main` / `afiqa`

## Perbaikan Infrastruktur Core & Multi-Agent (Testing Phase)

1. **Bugfix pada Pengujian Shared Memory:**
   - Memperbaiki tipe data pemanggilan (*argument passing*) pada fungsi uji sehingga `pytest core/test_shared_memory.py -v` berhasil dilalui 100% (4 test passed).
   
2. **Implementasi `core/factory.py`:**
   - Mengekstrak fungsionalitas pembuatan sesi LLM (*Factory Pattern*) menggunakan `langchain_openai.ChatOpenAI` dari `app/main.py`.
   - Mengatasi isu kompatibilitas argumen `request_timeout` yang dikirim dari klien *LangChain* pada *Inquisitor Agent*.

3. **Implementasi `core/engine.py`:**
   - Membangun `DependencyEngine` untuk memfasilitasi eksekusi agen yang asinkron dengan kontrol ketat dari `SharedMemory` (menghormati DAG agen yang berjalan, misal `GEO_ANALYST` menunggu `INQUISITOR`).
   - Orkestrator dapat berjalan mulus dan melakukan mekanisme validasi apakah semua pra-syaratnya sudah berstatus `DONE` sebelum *Orchestrator* melakukan keputusan akhir.

**Status Keseluruhan:**
Proyek sekarang dalam keadaan stabil (Lulus unit test dan test eksekusi lokal dengan model-model LLM pada vLLM port 8000/8001/8002). Siap dilanjutkan pada tahap interaksi melalui Dashboard UI (Streamlit).
