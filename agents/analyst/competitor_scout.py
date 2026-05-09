import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import InquisitorOutput, CompetitorScoutOutput, AgentStatus
from core.factory import create_llm
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[CompetitorScoutOutput]:
    """
    Competitor Scout Agent
    Tugas: Menganalisis 3-5 kompetitor potensial di lokasi bisnis berdasarkan business context.
    """
    try:
        logger.info("Competitor Scout Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.COMPETITOR, AgentStatus.RUNNING)
        
        # 2. Ambil data dari Inquisitor
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        if not inquisitor_data:
            error_msg = "Data Inquisitor tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.COMPETITOR, error_msg)
            return None
            
        business_context = inquisitor_data.business_context
        
        # 3. Setup LLM
        llm = create_llm("scout_inquisitor_pool", temperature=0.3)
        
        # Gunakan structured output sesuai schema Pydantic
        llm_with_tools = llm.with_structured_output(CompetitorScoutOutput)
        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah Competitor Scout profesional.
Tugas Anda adalah menganalisis 3-5 kompetitor potensial di lokasi bisnis yang diminta.
Berikan analisis mendalam mencakup kompetitor (name, estimated_price_range, strength, weakness, threat_level), celah pasar (market gap), rata-rata harga pasar, dan peluang diferensiasi. Output harus dalam format JSON yang valid."""),
            ("user", """Mohon lakukan analisis kompetitor berdasarkan konteks bisnis berikut:
- Lokasi: {location}
- Ide Bisnis: {business_idea}
- Sektor: {preferred_sector}
- Budget: {budget}
- Target Income: {target_monthly_income}
""")
        ])
        
        chain = prompt | llm_with_tools
        
        logger.info("Competitor Scout Agent: Mengirim request ke LLM...")
        
        result: CompetitorScoutOutput = await chain.ainvoke({
            "location": business_context.location,
            "business_idea": business_context.business_idea or "Belum spesifik",
            "preferred_sector": business_context.preferred_sector or "Belum spesifik",
            "budget": business_context.budget,
            "target_monthly_income": business_context.target_monthly_income or "Tidak ditentukan"
        })
        
        # 5. Simpan Hasil ke Memory
        memory.set(AgentKey.COMPETITOR, result)
        logger.info("Competitor Scout Agent: Selesai mengeksekusi tugas dan berhasil menyimpan ke memory.")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.COMPETITOR, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada Competitor Scout Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.COMPETITOR, error_msg)
        return None
