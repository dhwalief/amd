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
        
        # Baca preferensi bahasa
        lang = memory.get_language()
        is_en = lang == "en"
        lang_name = "English" if is_en else "Bahasa Indonesia"
        
        llm_with_tools = llm.with_structured_output(CriticOutput)

        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional Executive Critic (Gap Finder) for a business planning system.
OUTPUT LANGUAGE: You MUST respond entirely in {lang_name}.

IMPORTANT CONTEXT: All data provided are RESEARCH-BASED PROJECTIONS and PLANS. Estimated figures are derived from web search results (market prices, HR rates, equipment costs, etc.) collected in real-time. This is NOT an actual financial report or historical company data. You are evaluating a plan before it exists, so use terminology like "projections", "plans", "market-based estimates".

CRITICAL RULES:
- COMPLETELY IGNORE technical system errors (e.g., "JSON parsing error", "agent failed", "data not available"). These are technical issues, not business planning issues.
- ONLY report issues relevant to BUSINESS PLANNING: inconsistencies between projection numbers, unrealistic market assumptions, strategic gaps, etc.
- If data from an agent is missing due to technical error, note it as a data limitation, not a critical business issue.

Your task is to review the consistency and reasonableness of estimates from all specialized agents:
1. Inconsistent numbers between agents (e.g., total HR salaries exceed CFO's projected allocation, or Supply Planner's COGS is higher than Pricing's selling price).
2. Unrealistic assumptions compared to real market contexts.
3. Operational or business gaps in the plan that haven't been covered.

Use terms like "plan", "projection", "estimate", "based on market research" — NOT "financial statements" or "historical data".
Output MUST be in JSON format. The `issues_found` array should contain severity ("critical", "warning", "info"), agent_source, description, and suggestion.
Include a `reasoning` field with 2-3 paragraphs of your narrative thought process in {lang_name} before concluding."""),
            ("user", f"""Please perform a critical review of the following **business plan projections** from the analyst team.
            
REMEMBER: You must respond in {lang_name}.

{context_string}

Focus ONLY on projection inconsistencies and business assumption reasonableness.""")
        ])

        chain = prompt | llm_with_tools
        
        logger.info("Critic Agent: Mengirim request konteks ke LLM (Qwen3-32B)...")
        
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
