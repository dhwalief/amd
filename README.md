# Go to America (LangChain RAG Agent)

Proyek ini merupakan implementasi sederhana dari **Retrieval-Augmented Generation (RAG)** menggunakan ekosistem Python, LangChain, dan model dari server Ollama. Aplikasi ini memungkinkan pencarian otomatis ke internet (DuckDuckGo Search) untuk merangkum dan menjawab pertanyaan berdasarkan topik yang dimasukkan oleh pengguna.

## Arsitektur

Proyek ini dibangun dengan komponen utama sebagai berikut:
- **Bahasa Pemrograman:** Python 3.11+
- **Manajemen Dependency:** Poetry
- **Framework Utama:** LangChain
- **Pencarian Web (Search):** DuckDuckGo Search API
- **Web Scraping:** BeautifulSoup4 & lxml
- **Vector Store:** FAISS (Memory-based, CPU)
- **Embeddings Model:** `nomic-embed-text` (via instance server Ollama eksternal)
- **Large Language Model (LLM):** `qwen2.5:3b` (via ChatOpenAI wrapper ke instance server Ollama eksternal)

## Struktur Direktori Utama

- `app/agent.py`: Modul utama / aplikasi RAG. Berisi *pipeline* lengkap dari menerima input, mencari ke web, memotong dokumen, membuat representasi vektor, mengambil konteks, hingga membuat jawaban menggunakan LLM.
- `app/test1.py`: Skrip pengujian konektivitas LLM.
- `app/test2.py`: Skrip pengujian konektivitas Embeddings.
- `docs/analysis/`: Dokumentasi hasil analisa struktur dan arsitektur aplikasi.
- `docs/work/`: Dokumentasi *changelog* pekerjaan dan keputusan teknis harian.

## Prasyarat & Instalasi

Pastikan sistem Anda sudah terinstal [Poetry](https://python-poetry.org/) dan Python versi 3.11+.

1. Clone repositori ini dan masuk ke dalam folder proyek.
2. Install seluruh *dependencies* menggunakan Poetry:
   ```bash
   poetry install
   ```

## Konfigurasi

Saat ini, aplikasi mengarah ke server Ollama eksternal yang URL-nya ditulis langsung (*hardcode*) di dalam *source code*. Jika Anda perlu menghubungkan aplikasi ke *endpoint* atau *instance* server Ollama yang berbeda, silakan lakukan konfigurasi manual berikut:

1. **Ubah Konfigurasi LLM**
   Buka file `app/agent.py` dan temukan bagian inisialisasi `ChatOpenAI`. Ubah nilai `base_url` ke *endpoint* API Anda:
   ```python
   llm = ChatOpenAI(
       base_url="http://<IP_ANDA>:11434/v1",
       ...
   )
   ```

2. **Ubah Konfigurasi Embeddings**
   Masih di dalam `app/agent.py`, temukan inisialisasi `OllamaEmbeddings`. Sesuaikan nilai `base_url`:
   ```python
   embeddings = OllamaEmbeddings(
       base_url="http://<IP_ANDA>:11434",
       ...
   )
   ```

*(Catatan: Anda juga dapat melakukan penyesuaian yang sama pada skrip pengujian di `app/test1.py` dan `app/test2.py` apabila diperlukan).*

## Cara Menjalankan

Jalankan agen RAG utama dengan perintah berikut:

```bash
poetry run python app/agent.py
```

Setelah aplikasi berjalan, program akan meminta Anda untuk memasukkan topik. Program kemudian akan melakukan pencarian artikel web, memproses teks tersebut, dan menyusun jawaban menggunakan Qwen2.5.

## Dokumentasi Proyek

Untuk memahami lebih lanjut mengenai desain, arsitektur, dan rekam jejak pekerjaan, silakan lihat folder dokumentasi berikut:
- **[Analisis Proyek & Arsitektur](./docs/analysis/project_analysis.md)**
- **[Catatan Pekerjaan](./docs/work/)**
