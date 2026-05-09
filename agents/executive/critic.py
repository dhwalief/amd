import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    GeoAnalystOutput,
    CompetitorScoutOutput,
    MarketOutput,
    PricingOutput,
    FinanceOutput,
    LegalOutput,
    OpsOutput,
    HROutput,
    SupplyPlanOutput,
    SOPOutput,
    CriticOutput,
    AgentStatus
)
from core.factory import create_llm
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[CriticOutput]:
    """
    Critic Agent (Executive Layer)
    Tugas: Menganalisis output seluruh agent sebelumnya, mencari inkonsistensi, asumsi yang tidak realistis, dan celah.
    """
    try:
        logger.info("Critic Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.CRITIC, AgentStatus.RUNNING)
        
        # 2. Ambil seluruh output dari memori dan gabungkan jadi satu konteks
        def extract_agent_data(key: AgentKey, schema) -> str:
            data = memory.get(key, schema)
            if not data:
                return f"[{key.value.upper()}]: TIDAK ADA DATA\n"
            return f"--- [{key.value.upper()}] ---\n{data.model_dump_json(indent=2)}\n"

        context_string = ""
        context_string += extract_agent_data(AgentKey.GEO_ANALYST, GeoAnalystOutput)
        context_string += extract_agent_data(AgentKey.COMPETITOR, CompetitorScoutOutput)
        context_string += extract_agent_data(AgentKey.GROWTH_HACKER, MarketOutput)
        context_string += extract_agent_data(AgentKey.PRICING, PricingOutput)
        context_string += extract_agent_data(AgentKey.CFO, FinanceOutput)
        context_string += extract_agent_data(AgentKey.LEGAL, LegalOutput)
        context_string += extract_agent_data(AgentKey.PRODUCT_ARCHITECT, OpsOutput)
        context_string += extract_agent_data(AgentKey.HR_PLANNER, HROutput)
        context_string += extract_agent_data(AgentKey.SUPPLY_PLANNER, SupplyPlanOutput)
        context_string += extract_agent_data(AgentKey.SOP_DESIGNER, SOPOutput)

        # 3. Setup LLM
        llm = create_llm("critic", temperature=0.2)
        
        llm_with_tools = llm.with_structured_output(CriticOutput)
        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah Executive Critic profesional (Gap Finder).
Tugas Anda adalah meninjau laporan/output dari seluruh agent spesialis di bawah Anda untuk sebuah rencana bisnis.
Carilah hal-hal berikut secara kritis:
1. Angka yang tidak konsisten antar agent (misal: HR Planner menyusun gaji total yang melebihi alokasi CFO, atau kapasitas Product Architect vs HPP Supply Planner).
2. Asumsi yang tidak realistis (misal: pricing terlalu tinggi dibandingkan data kompetitor, atau estimasi trafik tidak masuk akal).
3. Celah operasional/bisnis yang belum tercakup.

Keluarkan dalam format JSON terstruktur di mana array `issues_found` berisi severity ("critical", "warning", "info"), agent_source, description, dan suggestion yang detail."""),
            ("user", """Mohon lakukan tinjauan kritis dan holistik terhadap keseluruhan output agent berikut:

{context_string}

Berdasarkan data di atas, identifikasi isu-isunya, nilai tingkat risiko secara keseluruhan (`overall_risk_level`: "high", "medium", atau "low"), putuskan apakah revisi diperlukan (`revision_required`), dan berikan `summary` komprehensif.
""")
        ])
        
        chain = prompt | llm_with_tools
        
        logger.info("Critic Agent: Mengirim request konteks raksasa ke LLM (Qwen3-32B)...")
        
        result: CriticOutput = await chain.ainvoke({
            "context_string": context_string
        })
        
        # Kalkulasi otomatis critical_count agar akurat
        critical_count = sum(1 for issue in result.issues_found if str(issue.severity).lower() == "critical")
        result.critical_count = critical_count
        
        # 5. Simpan Hasil ke Memory
        memory.set(AgentKey.CRITIC, result)
        logger.info(f"Critic Agent: Selesai mengeksekusi tugas. Ditemukan {critical_count} critical issues.")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.CRITIC, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada Critic Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.CRITIC, error_msg)
        return None
