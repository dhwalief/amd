# Pembagian Kerja Eksekusi (Branch: afiqa)

Karena kalian sudah siap *ngoding*, berikut adalah peta jalan (roadmap) file-file Python yang harus kalian buat di dalam folder `agents/`. Kita akan menggunakan pola **Mock-First** seperti instruksi ketua.

## 🧑‍💻 DEV 2 (Layer Hulu: Riset & Operasional)
Dev 2 bertanggung jawab mengubah input ide bisnis mentah menjadi rencana pasar dan alat operasional.

### 1. `agents/market_agent.py`
File ini menampung agen-agen riset pasar. Kalian harus membuat fungsi yang me-return Pydantic model dari `core.schemas`.
**Fungsi yang harus dibuat:**
- `run_geo_analyst(context: BusinessContext) -> GeoAnalystOutput`
- `run_competitor_scout(context: BusinessContext) -> CompetitorScoutOutput`
- `run_growth_hacker(geo: GeoAnalystOutput, comp: CompetitorScoutOutput) -> MarketOutput`
- `run_pricing_strategist(geo: GeoAnalystOutput, comp: CompetitorScoutOutput) -> PricingOutput`

### 2. `agents/ops_agent.py`
File ini menampung agen yang mengurus operasional, legal, dan SDM.
**Fungsi yang harus dibuat:**
- `run_product_architect(market: MarketOutput) -> OpsOutput`
- `run_hr_planner(cfo_mock_data) -> HROutput`
- `run_legal_compliance(cfo_mock_data, pricing_mock_data) -> LegalOutput`
- `run_sop_designer(ops_data, hr_data) -> SOPOutput`

---

## 🧑‍💻 DEV 3 (Layer Hilir: Keuangan & Validasi)
Dev 3 bertanggung jawab atas uang, risiko, kritik, dan hasil akhir (PDF/Markdown).

### 1. `agents/finance_agent.py`
File ini mengatur uang dan *supply chain*.
**Fungsi yang harus dibuat:**
- `run_supply_planner(cfo_mock_data) -> SupplyPlanOutput` *(Catatan: ini pure Python function tanpa LLM)*
- `run_cfo(market: MarketOutput, pricing: PricingOutput) -> FinanceOutput`

### 2. `agents/critic_agent.py`
File ini adalah para pengawas/juri yang mengkritik output agen lain.
**Fungsi yang harus dibuat:**
- `run_critic(semua_data_sebelumnya) -> CriticOutput`
- `run_risk_manager(critic: CriticOutput) -> RiskManagerOutput`
- `run_orchestrator_review(critic: CriticOutput, risk: RiskManagerOutput) -> OrchestratorReview`

### 3. `agents/output_formatter.py`
**Fungsi yang harus dibuat:**
- `generate_markdown_report(semua_output) -> str` (Menggabungkan semua data pydantic menjadi dokumen laporan yang rapi untuk ditampilkan di `app/main.py`).

---

## Contoh Kode Mocking untuk Memulai
Saat kalian membuat file-file di atas, jangan panggil vLLM dulu. Buat fungsi palsu (Mock) agar aplikasinya bisa di-*run* dari awal sampai akhir tanpa error.

**Contoh isi `agents/market_agent.py` (oleh Dev 2):**
```python
from core.schemas import GeoAnalystOutput, AgentStatus

def run_geo_analyst_mock() -> GeoAnalystOutput:
    return GeoAnalystOutput(
        agent_name="geo_analyst",
        status=AgentStatus.DONE,
        location_score=0.85,
        demand_level="high",
        foot_traffic_estimate="Ramai di malam hari",
        nearby_anchor=["Universitas", "Mall"],
        risk_factors=["Kurang lahan parkir"],
        recommendation="Sangat cocok untuk kedai kopi take-away"
    )
```
