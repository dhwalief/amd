# Dokumentasi Pengerjaan: Merapikan Dokumentasi Konfigurasi README

**Tanggal:** 9 Mei 2026

## Ringkasan Tugas
Melengkapi dan merapikan dokumentasi konfigurasi di `README.md` guna memberikan petunjuk yang lebih jelas kepada developer terkait cara mengubah *endpoint* IP server Ollama (LLM dan Embeddings) yang masih di-*hardcode* di dalam sistem. Tugas ini dikerjakan dengan tetap mengikuti Standar Operasional Prosedur (SOP) proyek.

## Perubahan yang Dilakukan
1. **Pembaruan File `README.md`:**
   Menyisipkan seksi baru berjudul **"Konfigurasi"** tepat sebelum seksi **"Cara Menjalankan"**. Seksi ini berisi panduan manual tentang cara mencari baris `base_url` di `app/agent.py` dan cara menyesuaikannya dengan IP instance Ollama yang digunakan (*custom endpoint*). Hal yang sama juga berlaku sebagai catatan tambahan untuk file pengujian `app/test1.py` dan `app/test2.py`.

## Alasan Teknis (Rationale) & Keputusan Desain
- Konfigurasi saat ini berpusat di source code (hardcoded). Dokumentasi ini bertindak sebagai mitigasi (*workaround*) sementara sembari sistem tersebut belum dipindahkan ke dalam konfigurasi *environment* (*.env*). Ini adalah keputusan pragmatis agar *developer* yang baru melakukan *clone* proyek langsung tahu di mana letak masalah jika RAG Agent tidak bisa menghubungi API LLM/Embeddings.
- Pemisahan informasi konfigurasi dalam seksi tersendiri memastikan *flow* membaca tidak terganggu ketika developer hanya ingin tahu cara *install* dan menjalankan secara bawaan.

## File yang Terdampak
- `[MODIFY]` `/README.md`: Menambahkan panduan merubah konfigurasi URL server.
- `[NEW]` `/docs/work/2026-05-09-readme-config.md`: Log pengerjaan saat ini.
