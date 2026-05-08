# Dokumentasi Pengerjaan: Setup Analisis & README Proyek

**Tanggal:** 8 Mei 2026

## Ringkasan Tugas
Menjalankan Standar Operasional Prosedur (SOP) untuk mendokumentasikan hasil analisis arsitektur proyek `amd` dan menambahkan/memperbarui file `README.md` sesuai dengan hasil arsitektur yang dianalisis.

## Perubahan yang Dilakukan
1. **Analisis Arsitektur Proyek:**
   Melakukan pembacaan pada seluruh file `.py` di dalam struktur aplikasi dan `pyproject.toml` untuk menyusun dokumentasi teknis mengenai arsitektur, flow jalannya aplikasi (RAG menggunakan LangChain, DuckDuckGo, FAISS), struktur direktori yang digunakan, *dependency* (Poetry), dan *endpoint* spesifik (Ollama/OpenAI compatible backend).
   
2. **Memperbarui File README:**
   Menimpa file `README.md` lama (yang sebelumnya sangat sederhana) dengan versi yang lebih detail yang mencakup spesifikasi *tech stack*, arsitektur, prasyarat, cara instalasi, dan cara menjalankan aplikasi sesuai konteks skrip utama `app/agent.py`.
   
3. **Penyimpanan Dokumentasi Work Log:**
   Membuat file catatan pengerjaan (*work log*) di dalam direktori `/docs/work/` sesuai dengan instruksi yang tertera di SOP.

## Alasan Teknis (Rationale) & Keputusan Desain
- Pembuatan subdirektori dokumentasi `docs/analysis` dan `docs/work` sengaja dilakukan untuk menyesuaikan dengan perintah SOP yang wajib mendokumentasikan analisis awal serta pekerjaan yang telah diselesaikan.
- File dokumentasi dipisahkan secara modular: `project_analysis.md` berisi analisis mendalam (menjadi dasar arsitektur), sementara `README.md` berfokus pada informasi *on-boarding* (*how-to-run* dan komponen utama). Keputusan memisahkan keduanya ini agar pengembang atau pihak ketiga bisa lebih cepat memahami *level of detail* masing-masing dokumentasi.

## File yang Terdampak
- `[NEW]` `/docs/analysis/project_analysis.md`: Menyimpan hasil pendalaman arsitektur.
- `[MODIFY]` `/README.md`: Diperbarui agar lebih jelas dan informatif bagi *developer*.
- `[NEW]` `/docs/work/2026-05-08-generate-docs.md`: Log pengerjaan saat ini.
