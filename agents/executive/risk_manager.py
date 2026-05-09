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
        
        llm_with_tools = llm.with_structured_output(RiskManagerOutput)
        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah Chief Risk Officer (Risk Manager) profesional.
Tugas Anda adalah meninjau laporan hasil audit (dari Executive Critic) dan merumuskan manajemen risiko untuk bisnis ini.
Anda diwajibkan untuk:
1. Menyusun minimal 5 skenario risiko bisnis (`risk_scenarios`) yang realistis berdasarkan isu-isu dari Critic. Tiap skenario harus punya name, probability ("high", "medium", "low"), impact ("high", "medium", "low"), dan mitigasi.
2. Menggambarkan skenario terburuk (`worst_case_summary`) dan terbaik (`best_case_summary`).
3. Menilai kelayakan keseluruhan (`overall_viability` menjadi "viable", "risky", atau "not-viable").
4. Memberikan daftar rekomendasi mitigasi tingkat tinggi (`recommendations`).

Berikan output murni dalam format JSON yang mematuhi skema yang ditetapkan."""),
            ("user", """Mohon lakukan analisis risiko berdasarkan laporan temuan kritis berikut ini:

Laporan Critic:
{critic_issues_str}

Berdasarkan temuan di atas, buatlah minimal 5 skenario risiko (probability & impact), jabarkan kondisi worst-case dan best-case, lalu berikan keputusan `overall_viability` dan rekomendasi yang bisa ditindaklanjuti.
""")
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
