# Business Co-Pilot — Konsep & Desain Sistem
## Perancangan Bisnis Berbasis AI Multi-Agent yang Kolaboratif

> Sistem ini bukan generator rencana bisnis sekali jalan. Ini adalah **partner berpikir** — user dan AI beriterasi bersama hingga tercapai rancangan bisnis yang realistis, kontekstual, dan benar-benar milik user.

---

## 1. Visi Produk

### 1.1 Masalah yang Diselesaikan

Kebanyakan orang yang ingin memulai bisnis menghadapi dua hambatan utama:

- **Informasi terlalu generik** — panduan bisnis di internet tidak mempertimbangkan modal spesifik mereka, lokasi mereka, atau kondisi pasar lokal mereka.
- **Tidak ada ruang untuk berdialog** — tool generator bisnis yang ada hanya menghasilkan output satu arah, tanpa memberi user kesempatan untuk mengoreksi asumsi yang salah.

### 1.2 Solusi

Business Co-Pilot membangun rencana bisnis **dari bawah ke atas**, dimulai dari kondisi nyata user — modal, lokasi, keahlian, preferensi — lalu mengumpulkan data pasar lokal secara real-time, menganalisisnya, dan mempresentasikan proposal yang bisa didiskusikan, dimodifikasi, atau ditolak oleh user sebelum rencana lengkap dibuat.

### 1.3 Prinsip Desain

| Prinsip | Implementasi |
|---------|-------------|
| **Kontekstual** | Semua analisis berbasis lokasi dan kondisi spesifik user, bukan data nasional generik |
| **Iteratif** | User bisa approve, modifikasi, atau tolak proposal di setiap tahap |
| **Transparan** | Setiap rekomendasi disertai alasan, sumber data, dan confidence level |
| **Realistis** | Output mencakup risiko, asumsi yang dipakai, dan skenario what-if |
| **Milik User** | Rencana akhir mencerminkan keputusan user, bukan keputusan AI |

---

## 2. Alur Sistem (7 Fase)

```
FASE 1        FASE 2         FASE 3        FASE 4
Discovery  →  Research    →  Proposal   →  User Review
(Inquisitor)  (Analyst Layer) (Orchestrator) ↕ iterasi

                                            ↓ setelah setuju

FASE 5        FASE 6         FASE 7
Deep       →  Validation  →  Final Review
Planning      (Executive)    & Approval
(Worker)                     ↕ iterasi
                             ↓ setelah setuju

                          [DOKUMEN FINAL]
```

---

### FASE 1 — Discovery

**Agent:** Inquisitor (Qwen2.5-7B)

User mengisi form awal, lalu Inquisitor menggali lebih dalam via tanya-jawab adaptif. Pertanyaan berikutnya ditentukan berdasarkan jawaban sebelumnya — bukan daftar pertanyaan kaku.

**Input form awal:**
```
Modal yang tersedia     : Rp ___________
Lokasi usaha            : ___________  (kota / kecamatan / kelurahan)
Wilayah target pasar    : ___________  (radius dari lokasi, atau nama area)
Keahlian / pengalaman   : ___________
Preferensi jenis bisnis : ___________ (opsional — bisa dikosongkan)
Jumlah anggota tim      : ___________
```

**Contoh tanya-jawab adaptif Inquisitor:**
```
Inquisitor: "Modal Anda Rp 30 juta. Apakah sudah termasuk biaya sewa tempat,
             atau itu modal terpisah?"
User: "Belum termasuk sewa, sewa sekitar 1,5 juta per bulan."

Inquisitor: "Apakah lokasi usaha sudah tersedia atau masih dalam pencarian?"
User: "Sudah ada, di depan perumahan."

Inquisitor: "Apakah ada kendaraan yang bisa dipakai untuk keperluan operasional?"
User: "Ada motor."
```

**Output:** `business_context.json` — profil user yang kaya dan personal, digunakan semua agent berikutnya.

---

### FASE 2 — Research & Analysis

**Agent:** Analyst Layer (paralel)

Semua agent analyst bekerja secara bersamaan menggunakan data dari `business_context.json`. Setiap agent melakukan web search real-time berdasarkan lokasi spesifik user.

| Agent | Tugas | Output |
|-------|-------|--------|
| **Geo Analyst** | Pemetaan demografi, daya beli, traffic area target | `geo_report` |
| **Competitor Scout** | Jumlah pesaing, kekuatan, kelemahan, gap pasar di radius X km | `competitor_report` |
| **Growth Hacker** | Peluang yang belum digarap, tren lokal, potensi diferensiasi | `growth_report` |
| **Pricing Strategist** | Range harga kompetitif, willingness-to-pay segmen target | `pricing_report` |
| **CFO** | Proyeksi modal, BEP, cashflow 12 bulan per opsi bisnis | `financial_model` |

**Confidence Level** — setiap output agent menyertakan:
```json
{
  "confidence": "sedang",
  "catatan": "Data traffic area berdasarkan estimasi demografi, bukan sensor fisik",
  "sumber": ["google.com/maps", "bps.go.id/makassar", "tokopedia.com/..."],
  "diakses_pada": "2025-05-09"
}
```

---

### FASE 3 — Proposal

**Agent:** Orchestrator (Qwen2.5-72B)

Orchestrator merangkum semua output analyst menjadi **2–3 opsi bisnis** yang dipersonalisasi. Setiap opsi disajikan dalam format ringkas dan mudah dipahami.

**Format proposal:**

```
┌─────────────────────────────────────────────────────────────┐
│  OPSI A: Warung Makan Rumahan                               │
│                                                             │
│  Modal awal   : Rp 18.500.000                              │
│  Modal kerja  : Rp 5.000.000 / bulan                       │
│  Estimasi BEP : 14 bulan                                    │
│  Risiko       : ⭐⭐ (rendah)                               │
│                                                             │
│  Kenapa cocok untuk Anda:                                   │
│  • Area perumahan dengan 1.200 KK dalam radius 500m        │
│  • Hanya 2 warung makan sejenis, keduanya tutup siang       │
│  • Modal Anda mencukupi tanpa perlu pinjaman               │
│  • Cocok dengan keahlian memasak yang Anda miliki           │
│                                                             │
│  [✅ Pilih Opsi Ini]  [✏️ Modifikasi]  [❌ Tidak Cocok]    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  OPSI B: Laundry Kiloan                                     │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  OPSI C: Toko Sembako Mini                                  │
│  ...                                                        │
└─────────────────────────────────────────────────────────────┘
```

---

### FASE 4 — User Review (Iterasi Pertama) ⭐

**Titik kolaborasi utama pertama.**

User dapat memberikan respons dalam empat mode:

```
✅  SETUJU         → lanjut ke Fase 5 dengan opsi yang dipilih
✏️  MODIFIKASI     → user memberikan perubahan spesifik
❌  TOLAK SEMUA    → user memberikan arahan baru
💬  SARAN BEBAS    → user mengusulkan ide di luar opsi yang ada
```

**Contoh skenario modifikasi:**
```
User: "Saya tertarik Opsi A tapi saya tidak bisa masak sendiri,
       butuh 1 karyawan. Apakah masih feasible?"

Sistem: CFO re-run dengan asumsi 1 karyawan UMR Makassar
        → BEP bergeser dari 14 bulan ke 19 bulan
        → Modal kerja naik Rp 2.500.000 / bulan
        → Masih feasible dengan modal yang ada
```

**Contoh skenario tolak + arahan baru:**
```
User: "Saya lebih tertarik bisnis online, tidak mau yang ada toko fisik."

Sistem: Geo Analyst + Growth Hacker + Competitor Scout re-run
        → fokus ke peluang bisnis online di wilayah Makassar
        → proposal baru: reseller produk lokal, jasa desain, dropship
```

**Preferensi tersimpan di Redis session** — setiap keputusan dan penolakan user diingat dan mempengaruhi semua output berikutnya. Sistem tidak akan menawarkan opsi yang sudah ditolak user.

---

### FASE 5 — Deep Planning

**Agent:** Worker Layer

Setelah user setuju dengan arah bisnis, Worker Layer menyusun rencana operasional lengkap.

| Agent | Output |
|-------|--------|
| **Legal & Compliance** | Izin yang dibutuhkan (NIB, PIRT, dll), prosedur pendaftaran, estimasi biaya dan waktu per yurisdiksi |
| **Product Architect** | Daftar produk/layanan, spesifikasi, paket harga, packaging |
| **HR Planner** | Struktur tim, deskripsi peran, estimasi gaji, jadwal kerja |
| **Supply Planner** | Daftar supplier lokal, stok awal, reorder point, estimasi biaya |
| **SOP Designer** | Prosedur operasi harian, checklist pembukaan/penutupan, standar layanan |

---

### FASE 6 — Validation

**Agent:** Executive Layer

| Agent | Tugas |
|-------|-------|
| **Critic** | Deteksi inkonsistensi antar output (misal: anggaran SDM vs proyeksi cashflow CFO tidak sinkron) |
| **Risk Manager** | Identifikasi risiko utama, skenario terburuk, dan strategi mitigasi |
| **Orchestrator** | Final review, rangkuman eksekutif, flag item yang perlu perhatian khusus |

**Contoh output Risk Manager:**
```
RISIKO UTAMA:

🔴 Tinggi   : Kenaikan harga bahan baku
             Probabilitas: 70% dalam 6 bulan
             Dampak: BEP mundur 2-3 bulan
             Mitigasi: Kontrak harga dengan supplier, buffer stock 2 minggu

🟡 Sedang   : Pesaing baru masuk di area yang sama
             Probabilitas: 40% dalam 12 bulan
             Dampak: Revenue turun 15-20%
             Mitigasi: Bangun loyalitas pelanggan sejak bulan pertama

🟢 Rendah   : Karyawan keluar di bulan pertama
             Probabilitas: 25%
             Dampak: Operasional terganggu 1-2 minggu
             Mitigasi: SOP lengkap agar onboarding cepat
```

---

### FASE 7 — Final Review & Approval (Iterasi Kedua) ⭐

**Titik kolaborasi utama kedua.**

User melihat rencana bisnis lengkap dan dapat:

```
✅  APPROVE SEMUA   → generate dokumen final
✏️  REVISI BAGIAN   → "Anggaran SDM terlalu besar, kurangi 1 karyawan"
❓  WHAT-IF         → "Bagaimana kalau modal saya 50% lebih kecil?"
                      "Kalau ada pesaing baru buka di sebelah bulan depan?"
```

Loop revisi berlanjut sampai user puas → dokumen final di-generate.

---

## 3. Fitur Khusus

### 3.1 Konteks Lokal Real-Time

Geo Analyst dan Competitor Scout menggunakan **web search real-time** dengan query yang dibangun dari data spesifik user:

```python
# Contoh query yang dibangun otomatis
f"warung makan {kelurahan} {kecamatan} Makassar"
f"laundry kiloan {kecamatan} Makassar harga"
f"daya beli masyarakat {kecamatan} Makassar 2025"
```

Bukan data generik nasional — data yang relevan untuk kelurahan spesifik user.

### 3.2 Memori Preferensi User

Semua keputusan dan penolakan user tersimpan di Redis session dan aktif mempengaruhi output selanjutnya:

```
user_prefs = {
  "tolak": ["bisnis dengan toko fisik", "bisnis F&B"],
  "preferensi": ["online", "modal kecil", "bisa dijalankan sendiri"],
  "prioritas": "ROI cepat lebih penting dari skala besar"
}
```

### 3.3 Confidence Score & Transparansi

Setiap angka dalam rencana bisnis disertai asumsi yang dipakai:

```
Estimasi pelanggan harian: 45 orang
└── Asumsi: 3% dari 1.500 penduduk dalam radius 300m
└── Confidence: sedang
└── Catatan: angka ini perlu divalidasi dengan observasi langsung 2-3 hari
```

### 3.4 Skenario What-If

User bisa mengajukan pertanyaan skenario kapan saja:

```
"Bagaimana kalau modal saya 30% lebih kecil?"
"Kalau saya buka 2 cabang di tahun kedua?"
"Kalau harga bahan baku naik 20%?"
```

CFO dan Financial Model re-run dengan parameter baru, tanpa mengulang seluruh pipeline.

### 3.5 Partial Re-Run

Ketika user memodifikasi proposal, hanya agent yang terdampak yang re-run — bukan seluruh pipeline dari awal. Orchestrator menentukan agen mana yang perlu dipanggil ulang berdasarkan jenis perubahan.

```
User mengubah: "tambah 1 karyawan"
Agent yang re-run: CFO, HR Planner, Risk Manager
Agent yang tidak re-run: Geo Analyst, Competitor Scout, Growth Hacker,
                          Pricing Strategist, Legal, Product Architect,
                          Supply Planner, SOP Designer
```

---

## 4. Output Akhir

Dokumen final yang di-generate setelah user approve mencakup:

```
RENCANA BISNIS — [Nama Bisnis User]
Dibuat: [tanggal] | Lokasi: [lokasi] | Modal: [modal]

1. Ringkasan Eksekutif
2. Analisis Pasar & Lokasi
   - Profil demografi area target
   - Peta persaingan
   - Peluang yang diidentifikasi
3. Model Bisnis
   - Produk / layanan
   - Strategi harga
   - Target segmen
4. Proyeksi Keuangan
   - Modal awal & rincian penggunaan
   - Proyeksi cashflow 12 bulan
   - Break-even analysis
   - Skenario optimis / moderat / pesimis
5. Rencana Operasional
   - Struktur tim & SDM
   - SOP harian
   - Rantai pasok & supplier
6. Aspek Legal & Perizinan
   - Izin yang dibutuhkan
   - Prosedur & estimasi waktu
7. Manajemen Risiko
   - Risiko utama & mitigasi
   - Skenario terburuk & rencana darurat
8. Rencana Aksi 90 Hari Pertama
   - Timeline setup
   - Milestone per minggu
   - KPI yang perlu dipantau

[Format: Markdown + PDF]
[Semua asumsi & sumber data tercantum di lampiran]
```

---

## 5. Arsitektur Sistem

### 5.1 Kesesuaian dengan Arsitektur Multi-Agent yang Ada

Konsep Business Co-Pilot **80% cocok langsung** dengan arsitektur yang sudah dirancang. Berikut pemetaannya:

| Komponen Arsitektur | Peran dalam Business Co-Pilot | Status |
|--------------------|------------------------------|--------|
| Inquisitor | Fase 1 — Discovery & tanya-jawab adaptif | ✅ Langsung pakai |
| Analyst Layer | Fase 2 — Research paralel real-time | ✅ Langsung pakai |
| Orchestrator | Fase 3 — Generate proposal 2-3 opsi | ✅ Langsung pakai |
| Worker Layer | Fase 5 — Deep planning operasional | ✅ Langsung pakai |
| Critic + Risk Manager | Fase 6 — Validation & risk assessment | ✅ Langsung pakai |
| Redis shared memory | State antar fase + memori preferensi user | ✅ Perlu tambah key baru |
| WebSocket | Live update progress ke frontend | ✅ Langsung pakai |
| DAG + Dependency Engine | Orkestrasi agent sesuai urutan fase | 🔄 Perlu tambah conditional re-run |
| output/sessions/ | Dokumen final permanen | ✅ Langsung pakai |

### 5.2 Yang Perlu Ditambah ke Arsitektur

#### Redis — Tambahan Key untuk Business Co-Pilot

```
# Key yang sudah ada
session:{id}:status
session:{id}:agent:{name}
session:{id}:meta

# Key baru untuk Business Co-Pilot
session:{id}:phase              → fase saat ini (discovery/analysis/proposal/review1/planning/validation/review2/final)
session:{id}:user_prefs         → preferensi & penolakan user yang terakumulasi
session:{id}:feedback:{n}       → feedback user per iterasi (n = nomor iterasi)
session:{id}:approved_option    → opsi yang dipilih user di Fase 4
session:{id}:rerun_log          → log agent mana yang di-rerun dan kenapa
session:{id}:whatif:{n}         → hasil kalkulasi skenario what-if
```

#### DAG — Tambahan Conditional Re-Run

```python
# dag.py — tambahan untuk partial re-run
RERUN_MAP = {
    # Jika user mengubah ini → agent ini yang perlu re-run
    "tambah_karyawan":       ["cfo", "hr_planner", "risk_manager"],
    "ubah_modal":            ["cfo", "risk_manager", "supply_planner"],
    "ubah_jenis_bisnis":     ["geo_analyst", "competitor_scout", "growth_hacker",
                              "pricing_strategist", "cfo"],
    "ubah_lokasi":           ["geo_analyst", "competitor_scout", "growth_hacker",
                              "pricing_strategist"],
    "ubah_produk":           ["product_architect", "pricing_strategist",
                              "supply_planner", "cfo"],
}
```

#### Frontend — Halaman Baru

```
frontend/src/pages/
  ├── InputForm.jsx          ← sudah ada (Fase 1 — form awal)
  ├── Discovery.jsx          ← BARU (Fase 1 — tanya-jawab adaptif Inquisitor)
  ├── Progress.jsx           ← sudah ada (Fase 2 — live progress analyst)
  ├── ProposalReview.jsx     ← BARU (Fase 4 — tampilkan 2-3 opsi, user pilih/modif/tolak)
  ├── PlanningProgress.jsx   ← sudah ada versi dasarnya (Fase 5-6)
  ├── FinalReview.jsx        ← BARU (Fase 7 — review rencana lengkap, approve/revisi)
  └── Report.jsx             ← sudah ada (output final + download PDF)

frontend/src/components/
  ├── DagVisualization.jsx   ← sudah ada
  ├── AgentCard.jsx          ← sudah ada
  ├── OutputSection.jsx      ← sudah ada
  ├── ProposalCard.jsx       ← BARU (card per opsi bisnis di Fase 4)
  ├── FeedbackInput.jsx      ← BARU (input modifikasi / saran bebas user)
  ├── WhatIfPanel.jsx        ← BARU (panel skenario what-if)
  └── ConfidenceTag.jsx      ← BARU (badge confidence level per data point)
```

### 5.3 Full System Flow

```
User buka aplikasi
       │
       ▼
[InputForm.jsx] ─────────────────────────────────────────────
       │ POST /session/start + input awal
       ▼
[Discovery.jsx] ──── WebSocket ──── Inquisitor (Qwen2.5-7B)
       │ tanya-jawab adaptif
       │ user jawab → Inquisitor generate pertanyaan berikut
       │ sampai context cukup → DONE
       ▼
[Progress.jsx] ───── WebSocket ──── Analyst Layer (paralel)
       │ Geo, Competitor, Growth, Pricing, CFO
       │ web search real-time per agent
       │ selesai → Orchestrator generate proposal
       ▼
[ProposalReview.jsx] ─────────────────────────────────────────
       │ tampilkan 2-3 ProposalCard
       │ user: ✅ setuju / ✏️ modif / ❌ tolak / 💬 saran
       │
       ├── ✅ setuju ──────────────────────────────────────────
       │                                                        │
       ├── ✏️ modif → FeedbackInput → partial re-run           │
       │          → proposal diperbarui → kembali ke review    │
       │                                                        │
       └── ❌ tolak / 💬 saran → agent re-run sesuai RERUN_MAP │
                              → proposal baru                   │
                                                               ↓
[PlanningProgress.jsx] ── WebSocket ── Worker Layer (paralel)
       │ Legal, Product Architect, HR, Supply, SOP
       │ selesai → Critic + Risk Manager → Orchestrator review
       ▼
[FinalReview.jsx] ────────────────────────────────────────────
       │ tampilkan rencana lengkap
       │ user: ✅ approve / ✏️ revisi bagian / ❓ what-if
       │
       ├── ✅ approve → output_formatter → output/sessions/
       │                                                    │
       ├── ✏️ revisi → FeedbackInput → partial re-run      │
       │           → rencana diperbarui → kembali ke review │
       │                                                    │
       └── ❓ what-if → WhatIfPanel → CFO re-run           │
                     → hasil ditampilkan → tetap di review  │
                                                           ↓
[Report.jsx] ─────────────────────────────────────────────────
       │ tampilkan rencana bisnis final
       │ download PDF / Markdown
       ▼
    [SELESAI]
```

---

## 6. Stack Teknologi

| Layer | Teknologi | Alasan |
|-------|-----------|--------|
| **Frontend** | React + Vite + TailwindCSS | Ringan, cepat, komponen reusable |
| **Backend API** | FastAPI (Python) | Async native, WebSocket support, mudah integrasi dengan langchain |
| **Agent Framework** | LangChain | Sudah dipakai di konfigurasi awal |
| **State Sementara** | Redis | Pub/sub untuk WebSocket, fast read/write antar agent |
| **State Permanen** | File sistem (`output/sessions/`) | Sederhana, tidak perlu database untuk MVP |
| **LLM Inference** | vLLM (ROCm) | Sudah berjalan di infrastruktur |
| **Web Search** | Tavily API / SerpAPI | Real-time search untuk agent analyst |
| **PDF Generator** | WeasyPrint / Pandoc | Convert markdown output ke PDF |

---

## 7. Rencana Pengembangan

### MVP (Minimum Viable Product)

Fokus pada alur utama tanpa fitur tambahan:

- [ ] Fase 1 — Discovery (form + Inquisitor)
- [ ] Fase 2 — Research (Analyst Layer paralel dengan web search)
- [ ] Fase 3 — Proposal (2 opsi saja dulu)
- [ ] Fase 4 — User Review (approve / tolak saja, belum modifikasi detail)
- [ ] Fase 5 — Deep Planning (Worker Layer)
- [ ] Fase 7 — Output final (Markdown dulu, PDF menyusul)

### V1 (Setelah MVP Stabil)

- [ ] Modifikasi detail di Fase 4 (partial re-run)
- [ ] Fase 6 — Critic + Risk Manager
- [ ] Skenario what-if
- [ ] Confidence score di setiap output
- [ ] Output PDF

### V2 (Pengembangan Lanjut)

- [ ] Riwayat session (user bisa buka rencana lama)
- [ ] Komparasi antar sesi (bandingkan 2 rencana berbeda)
- [ ] Export ke format lain (Excel untuk cashflow, dll)
- [ ] Mode kolaborasi (2 user mengerjakan 1 rencana bersama)

---

*Dokumen ini mendeskripsikan konsep dan desain sistem Business Co-Pilot berbasis arsitektur multi-agent. Arsitektur teknis lengkap (model, GPU, container, dependency graph) tersedia di dokumen terpisah: arsitektur-multiagent-v5-final.md*