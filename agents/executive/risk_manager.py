import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    CriticOutput,
    RiskManagerOutput,
    AgentStatus
)
from core.factory import create_llm
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[RiskManagerOutput]:
    """
    Risk Manager Agent (Executive Layer)
    Tugas: Menganalisis isu-isu dari Critic dan merumuskan skenario risiko mitigasi.
    """
    try:
        logger.info("Risk Manager Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.RISK_MANAGER, AgentStatus.RUNNING)
        
        # 2. Ambil data dari shared memory (Dependensi Utama)
        critic_data = memory.get(AgentKey.CRITIC, CriticOutput)
        if not critic_data:
            error_msg = "Data Critic tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.RISK_MANAGER, error_msg)
            return None

        critic_issues_str = critic_data.model_dump_json(indent=2)
        
        # 3. Setup LLM
        llm = create_llm("risk_manager", temperature=0.1)

        # Baca preferensi bahasa
        lang = memory.get_language()
        is_en = lang == "en"
        lang_name = "English" if is_en else "Bahasa Indonesia"
        
        llm_with_tools = llm.with_structured_output(RiskManagerOutput)

        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a professional Chief Risk Officer (Risk Manager).
OUTPUT LANGUAGE: You MUST respond entirely in {lang_name}.

Your task is to review the findings from the Executive Critic and formulate risk management for this **business plan**.

IMPORTANT CONTEXT: All data you receive are RESEARCH-BASED PROJECTIONS and PLANS — estimated figures come from web search results (market prices, HR rates, competitor data, etc.) collected in real-time by analyst agents. This is NOT an actual financial report. You are assessing the risk of a plan that has not yet been realized, so use language like "projection", "plan", "estimate based on research".

You are required to:
1. Develop at least 5 realistic business risk scenarios (`risk_scenarios`) based on the issues from the Critic. Each scenario must have a `scenario_name`, `probability` ("high", "medium", "low"), `impact` ("high", "medium", "low"), and `mitigation`.
2. Describe the worst-case scenario (`worst_case_summary`) and best-case scenario (`best_case_summary`) from a projection perspective.
3. Assess the overall viability of the plan (`overall_viability`: "viable", "risky", or "not-viable").
4. Provide a list of actionable mitigation recommendations (`recommendations`).
5. Write `reasoning`: 2-3 paragraphs of your narrative thought process in {lang_name}.

Provide pure output in JSON format adhering to the established schema."""),
            ("user", f"""Please perform a risk analysis based on the following finding report.
            
REMEMBER: You must respond in {lang_name}.

Critic Report:
{critic_issues_str}

Remember: this is a planning projection, not an actual financial report.""")
        ])

        
        chain = prompt | llm_with_tools
        
        logger.info("Risk Manager Agent: Mengirim request ke LLM (R1-Distill-Llama-70B)...")
        
        result: RiskManagerOutput = await chain.ainvoke({
            "critic_issues_str": critic_issues_str
        })
        
        # 5. Simpan Hasil ke Memory
        memory.set(AgentKey.RISK_MANAGER, result)
        logger.info(f"Risk Manager Agent: Selesai mengeksekusi tugas. Status Viability: {result.overall_viability}")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.RISK_MANAGER, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada Risk Manager Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.RISK_MANAGER, error_msg)
        return None
