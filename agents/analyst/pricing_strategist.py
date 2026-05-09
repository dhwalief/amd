import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    InquisitorOutput, 
    GeoAnalystOutput, 
    CompetitorScoutOutput, 
    PricingOutput, 
    AgentStatus
)
from core.factory import create_llm
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[PricingOutput]:
    """
    Pricing Strategist Agent
    Tugas: Menentukan strategi harga berdasarkan kondisi lokasi dan kompetitor.
    """
    try:
        logger.info("Pricing Strategist Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.PRICING, AgentStatus.RUNNING)
        
        # 2. Ambil data dari shared memory (Dependensi Utama)
        geo_data = memory.get(AgentKey.GEO_ANALYST, GeoAnalystOutput)
        if not geo_data:
            error_msg = "Data Geo Analyst tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.PRICING, error_msg)
            return None
            
        competitor_data = memory.get(AgentKey.COMPETITOR, CompetitorScoutOutput)
        if not competitor_data:
            error_msg = "Data Competitor Scout tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.PRICING, error_msg)
            return None

        # Mengambil konteks bisnis (Inquisitor) agar LLM tahu produk apa yang diberi harga
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        business_idea = "Bisnis"
        budget = 0.0
        if inquisitor_data and inquisitor_data.business_context:
            business_idea = inquisitor_data.business_context.business_idea or business_idea
            budget = inquisitor_data.business_context.budget
        
        # Ekstrak data untuk prompt
        avg_competitor_price = competitor_data.average_market_price
        competitors_list = [
            f"- {c.name}: {c.estimated_price_range} (Strength: {c.strength}, Weakness: {c.weakness})" 
            for c in competitor_data.competitors
        ]
        competitors_str = "\n".join(competitors_list) if competitors_list else "Tidak ada kompetitor dominan."
        
        location_score = geo_data.location_score
        demand_level = geo_data.demand_level
        foot_traffic = geo_data.foot_traffic_estimate
        nearby_anchor = ", ".join(geo_data.nearby_anchor) if geo_data.nearby_anchor else "Tidak ada"
        risk_factors = ", ".join(geo_data.risk_factors) if geo_data.risk_factors else "Tidak ada"
        
        # 3. Setup LLM
        llm = create_llm("analyst_pool", temperature=0.1)
        
        llm_with_tools = llm.with_structured_output(PricingOutput)
        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah Pricing Strategist profesional.
Tugas Anda adalah merumuskan strategi penentuan harga jual untuk produk/layanan berdasarkan analisis lokasi dan harga kompetitor.
Anda harus merekomendasikan: recommended_price (float), price_range_min (float), price_range_max (float), pricing_strategy ("penetration", "skimming", atau "value-based"), margin_percentage (float), dan justification (penjelasan).
Berikan output dalam format JSON yang sesuai skema."""),
            ("user", """Mohon rumuskan strategi harga untuk produk/layanan berikut:
Ide Bisnis: {business_idea}
Budget Tersedia: Rp {budget:,.2f}

1. DATA KOMPETITOR:
Harga Rata-rata Pasar: Rp {avg_competitor_price:,.2f}
Detail Kompetitor:
{competitors_str}

2. KONDISI LOKASI (Menentukan Daya Beli Target Segmen):
Skor Lokasi: {location_score} / 1.0
Tingkat Permintaan: {demand_level}
Estimasi Keramaian: {foot_traffic}
Anchor/Daya Tarik Sekitar: {nearby_anchor}
Faktor Risiko: {risk_factors}

Tentukan strategi harga yang optimal dengan mempertimbangkan daya beli target segmen di lokasi tersebut dan harga rata-rata kompetitor.
""")
        ])
        
        chain = prompt | llm_with_tools
        
        logger.info("Pricing Strategist Agent: Mengirim request ke LLM...")
        
        result: PricingOutput = await chain.ainvoke({
            "business_idea": business_idea,
            "budget": budget,
            "avg_competitor_price": avg_competitor_price,
            "competitors_str": competitors_str,
            "location_score": location_score,
            "demand_level": demand_level,
            "foot_traffic": foot_traffic,
            "nearby_anchor": nearby_anchor,
            "risk_factors": risk_factors
        })
        
        # 5. Simpan Hasil ke Memory
        memory.set(AgentKey.PRICING, result)
        logger.info("Pricing Strategist Agent: Selesai mengeksekusi tugas dan berhasil menyimpan ke memory.")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.PRICING, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada Pricing Strategist Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.PRICING, error_msg)
        return None
