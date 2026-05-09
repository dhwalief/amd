# Contoh

"""
schemas.py — Kontrak Data Antar Agent
======================================
Dibuat oleh: Dev 1 (Ketua)
Dipakai oleh: SEMUA developer dan semua agent

ATURAN:
- Jangan ubah field yang sudah ada tanpa diskusi tim
- Tambah field baru boleh, tapi harus optional (punya default value)
- Semua agent wajib return Pydantic model ini, bukan dict biasa
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────
# STATUS ENUM — dipakai semua agent
# ─────────────────────────────────────────────

class AgentStatus(str, Enum):
    PENDING  = "pending"   # belum mulai, dependency belum terpenuhi
    RUNNING  = "running"   # sedang dijalankan
    DONE     = "done"      # selesai, output tersedia
    FAILED   = "failed"    # error, perlu retry atau abort
    LOCKED   = "locked"    # dependency belum selesai, tidak bisa jalan


# ─────────────────────────────────────────────
# BASE — semua output agent inherit dari sini
# ─────────────────────────────────────────────

class AgentOutput(BaseModel):
    agent_name: str
    status: AgentStatus = AgentStatus.DONE
    completed_at: Optional[str] = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    error_message: Optional[str] = None  # diisi kalau status FAILED


# ─────────────────────────────────────────────
# LAYER 1 — DISCOVERY
# ─────────────────────────────────────────────

class BusinessContext(BaseModel):
    """Output Inquisitor — konteks awal bisnis dari user."""
    location: str                        # "Makassar, Sulawesi Selatan"
    budget: float                        # dalam Rupiah, e.g. 20_000_000
    skills: list[str]                    # ["masak", "barista", "desain"]
    existing_assets: list[str]           # ["motor", "laptop", "gerobak"]
    business_idea: Optional[str] = None  # kalau user sudah punya ide
    preferred_sector: Optional[str] = None  # "F&B", "jasa", "retail", dll
    target_monthly_income: Optional[float] = None  # target pendapatan bersih/bulan


class InquisitorOutput(AgentOutput):
    agent_name: str = "inquisitor"
    business_context: BusinessContext


# ─────────────────────────────────────────────
# LAYER 2 — ANALYST
# ─────────────────────────────────────────────

class Competitor(BaseModel):
    name: str
    estimated_price_range: str           # "15.000 - 30.000"
    strength: str                        # "harga murah, lokasi strategis"
    weakness: str                        # "kualitas tidak konsisten"
    threat_level: str                    # "high" | "medium" | "low"


class GeoAnalystOutput(AgentOutput):
    agent_name: str = "geo_analyst"
    location_score: float                # 0.0 - 1.0, potensi lokasi
    demand_level: str                    # "high" | "medium" | "low"
    foot_traffic_estimate: str           # "tinggi saat jam makan siang"
    nearby_anchor: list[str]             # ["kampus UNHAS", "kos-kosan"]
    risk_factors: list[str]              # ["banjir saat hujan", "parkir sempit"]
    recommendation: str                  # ringkasan rekomendasi lokasi


class CompetitorScoutOutput(AgentOutput):
    agent_name: str = "competitor_scout"
    competitors: list[Competitor]
    market_gap: list[str]                # peluang yang belum diisi kompetitor
    average_market_price: float          # rata-rata harga pasar (Rupiah)
    differentiation_opportunity: str     # rekomendasi diferensiasi


class MarketOutput(AgentOutput):
    """Output Growth Hacker / Marketing Planner."""
    agent_name: str = "growth_hacker"
    business_ideas: list[str]            # 3-5 ide bisnis yang direkomendasikan
    recommended_idea: str                # ide bisnis terpilih
    target_segment: str                  # "mahasiswa usia 18-24"
    value_proposition: str               # UVP — apa yang bikin beda
    marketing_channels: list[str]        # ["Instagram", "TikTok", "brosur"]
    go_to_market_strategy: str           # strategi masuk pasar


class PricingOutput(AgentOutput):
    agent_name: str = "pricing_strategist"
    recommended_price: float             # harga jual per unit (Rupiah)
    price_range_min: float
    price_range_max: float
    pricing_strategy: str                # "penetration" | "skimming" | "value-based"
    margin_percentage: float             # target margin (%)
    justification: str                   # alasan pricing


# ─────────────────────────────────────────────
# LAYER 3 — FINANCE
# ─────────────────────────────────────────────

class CostItem(BaseModel):
    name: str                            # "kompor gas", "sewa tempat"
    amount: float                        # Rupiah
    category: str                        # "equipment" | "operational" | "marketing"
    is_recurring: bool = False           # True = biaya bulanan


class FinanceOutput(AgentOutput):
    agent_name: str = "cfo"
    startup_cost: list[CostItem]         # semua biaya awal
    monthly_cost: list[CostItem]         # biaya operasional per bulan
    total_startup_cost: float            # total modal awal (Rupiah)
    total_monthly_cost: float            # total biaya bulanan
    recommended_capital: float           # total_startup + buffer 25%
    bep_units: float                     # berapa unit terjual untuk BEP
    bep_revenue: float                   # berapa pendapatan untuk BEP (Rupiah)
    bep_months: float                    # berapa bulan untuk balik modal
    projected_monthly_revenue: float     # proyeksi pendapatan bulan pertama
    projected_net_profit_month6: float   # proyeksi laba bersih bulan ke-6
    risk_level: str                      # "high" | "medium" | "low"


# ─────────────────────────────────────────────
# LAYER 4 — OPERATIONS / WORKER
# ─────────────────────────────────────────────

class EquipmentItem(BaseModel):
    name: str
    quantity: int
    estimated_cost: float                # Rupiah per unit
    priority: str                        # "must-have" | "nice-to-have"


class OpsOutput(AgentOutput):
    agent_name: str = "product_architect"
    equipment_list: list[EquipmentItem]
    total_equipment_cost: float
    operational_flow: list[str]          # urutan proses, e.g. ["beli bahan", "masak", "kemas", "jual"]
    daily_capacity: int                  # berapa unit bisa diproduksi per hari
    minimum_staff: int                   # jumlah SDM minimum


class HROutput(AgentOutput):
    agent_name: str = "hr_planner"
    roles: list[dict]                    # [{"role": "kasir", "count": 1, "salary": 2_000_000}]
    total_monthly_salary: float
    hiring_priority: list[str]           # urutan rekrut


class SOPOutput(AgentOutput):
    agent_name: str = "sop_designer"
    sop_sections: list[dict]             # [{"title": "Pembukaan Toko", "steps": [...]}]
    quality_standards: list[str]
    daily_checklist: list[str]


class LegalOutput(AgentOutput):
    agent_name: str = "legal_compliance"
    required_licenses: list[dict]        # [{"name": "NIB", "authority": "OSS", "url": "..."}]
    jurisdiction: str
    compliance_notes: list[str]
    sources: list[str]                   # URL sumber hukum
    rag_available: bool = False          # apakah RAG tersedia untuk yurisdiksi ini
    confidence_level: str = "medium"     # "high" | "medium" | "low"


# ─────────────────────────────────────────────
# LAYER 5 — EXECUTIVE REVIEW
# ─────────────────────────────────────────────

class Issue(BaseModel):
    severity: str                        # "critical" | "warning" | "info"
    agent_source: str                    # agent mana yang jadi sumber masalah
    description: str                     # deskripsi masalah
    suggestion: str                      # saran perbaikan


class CriticOutput(AgentOutput):
    agent_name: str = "critic"
    issues_found: list[Issue]
    overall_risk_level: str              # "high" | "medium" | "low"
    revision_required: bool
    critical_count: int                  # jumlah issue severity=critical
    summary: str                         # ringkasan hasil review


class RiskScenario(BaseModel):
    scenario_name: str                   # "bahan baku naik 30%"
    probability: str                     # "high" | "medium" | "low"
    impact: str                          # "high" | "medium" | "low"
    mitigation: str                      # langkah mitigasi


class RiskManagerOutput(AgentOutput):
    agent_name: str = "risk_manager"
    risk_scenarios: list[RiskScenario]
    worst_case_summary: str
    best_case_summary: str
    overall_viability: str               # "viable" | "risky" | "not-viable"
    recommendations: list[str]


class OrchestratorReview(AgentOutput):
    agent_name: str = "orchestrator"
    approved: bool
    final_recommendation: str
    executive_summary: str
    next_steps: list[str]


# ─────────────────────────────────────────────
# UTILITY — Supply Planner (Python function output)
# ─────────────────────────────────────────────

class SupplyPlanOutput(AgentOutput):
    """
    Dihasilkan oleh Python function, bukan LLM.
    Tetap pakai schema supaya konsisten dengan agent lain.
    """
    agent_name: str = "supply_planner"
    raw_materials: list[dict]            # [{"item": "kopi", "unit": "kg", "qty_per_day": 2, "price_per_unit": 80_000}]
    daily_cogs: float                    # Cost of Goods Sold per hari
    monthly_cogs: float
    hpp_per_unit: float                  # Harga Pokok Produksi per unit
    supplier_recommendations: list[str]
