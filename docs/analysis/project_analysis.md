# Analisis Proyek: Go to America (LangChain Test)

## 1. Arsitektur Proyek
Proyek ini merupakan implementasi sederhana dari **Retrieval-Augmented Generation (RAG)** menggunakan ekosistem **LangChain**. Proyek ini tidak menggunakan arsitektur web framework atau layer kompleks, melainkan script prosedural yang menghubungkan berbagai komponen:
- **Search Engine:** DuckDuckGo Search
- **Web Scraper:** BeautifulSoup & lxml
- **Text Splitter:** RecursiveCharacterTextSplitter (LangChain)
- **Vector Store:** FAISS (CPU)
- **Embeddings:** `nomic-embed-text` (dilayani melalui instance server Ollama eksternal)
- **LLM:** `qwen2.5:3b` (dilayani melalui interface OpenAI compatible API pada instance Ollama eksternal)

## 2. Flow Aplikasi (`app/agent.py`)
1. **Input:** Pengguna memasukkan sebuah topik (kueri).
2. **Pencarian (Web Search):** Aplikasi menggunakan `duckduckgo_search` untuk mencari 3 hasil teratas berdasarkan topik.
3. **Ekstraksi (Scraping):** Aplikasi mengunduh konten dari ketiga URL hasil pencarian menggunakan `requests` dan mengekstrak teksnya dengan `BeautifulSoup`.
4. **Pemrosesan Teks (Chunking):** Teks dari halaman web digabungkan dan dipotong menjadi *chunk* (ukuran 1000 karakter dengan *overlap* 200 karakter).
5. **Vektorisasi (Embedding):** Chunk tersebut diubah menjadi vektor menggunakan model `nomic-embed-text` dan disimpan di memory lokal menggunakan **FAISS**.
6. **Retrieval:** Top 5 chunk paling relevan dengan topik ditarik dari vektor store (FAISS).
7. **Generasi (LLM):** Konteks dokumen yang ditarik beserta topik diberikan ke prompt LLM (`qwen2.5:3b`), yang kemudian menghasilkan dan mencetak jawaban secara terstruktur.

## 3. Struktur Module / Service
Struktur saat ini sangat minimalis:
- `/app/agent.py`: Merupakan modul utama / *core service* yang menjalankan seluruh flow RAG di atas.
- `/app/test1.py`: Skrip pengujian koneksi dan inferensi ke endpoint LLM (`ChatOpenAI`).
- `/app/test2.py`: Skrip pengujian koneksi dan embedding ke endpoint embeddings (`OllamaEmbeddings`).
- `/pyproject.toml`: Konfigurasi *dependency* dan *environment* menggunakan **Poetry**.

## 4. Dependency Penting
- `langchain`, `langchain-openai`, `langchain-ollama`, `langgraph`: Ekosistem framework LLM utama.
- `faiss-cpu`: Pustaka pencarian kemiripan vektor efisien dari Meta.
- `duckduckgo-search`: Untuk integrasi pencarian web.
- `beautifulsoup4`, `lxml`, `requests`: Untuk web scraping dan HTTP requests.

## 5. Konfigurasi Utama
- **Dependency Manager**: Menggunakan `poetry`.
- **LLM Base URL**: Hardcoded ke `http://43.134.132.230:11434/v1` (di `agent.py`) dan `http://134.199.206.176:11434/v1` (di file test).
- **Embeddings Base URL**: Hardcoded ke instance yang sama dengan LLM.

## 6. Catatan Teknis Penting & Temuan
- **Inkonsistensi IP Endpoint:** File `/app/agent.py` menggunakan IP `43.134.132.230` untuk server LLM dan Embeddings. Sementara `/app/test1.py` dan `/app/test2.py` menggunakan IP `134.199.206.176`. Hal ini berpotensi membingungkan jika server berubah.
- **Hardcoded Configuration:** Konfigurasi API Base URL dan API Key (*dummy*) saat ini di-*hardcode* di dalam kode. Sebaiknya konfigurasi ini dipindahkan ke *environment variables* (misal `.env`).
- **Error Handling:** Error handling pada proses *request* web scraping sudah diterapkan dengan `try-except`, yang cukup baik untuk mencegah seluruh proses RAG gagal jika satu *website* gagal diakses atau terdapat pembatasan (seperti *timeout*).
