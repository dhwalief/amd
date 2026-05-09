import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    InquisitorOutput,
    FinanceOutput,
    HROutput,
    AgentStatus
)
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[HROutput]:
    """
    HR Planner Agent
    Tugas: Merencanakan struktur SDM yang efisien sesuai skala bisnis dan budget CFO.
    """
    try:
        logger.info("HR Planner Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.HR_PLANNER, AgentStatus.RUNNING)
        
        # 2. Ambil data dari shared memory (Dependensi Utama)
        cfo_data = memory.get(AgentKey.CFO, FinanceOutput)
        if not cfo_data:
            error_msg = "Data CFO tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.HR_PLANNER, error_msg)
            return None

        # Mengambil konteks bisnis (Inquisitor) agar LLM tahu bisnis apa yang butuh SDM
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        business_idea = "Bisnis Umum"
        location = "Tidak ditentukan"
        if inquisitor_data and inquisitor_data.business_context:
            business_idea = inquisitor_data.business_context.business_idea or "Belum spesifik"
            location = inquisitor_data.business_context.location
        
        # Ekstrak data untuk prompt
        budget_bulanan_total = cfo_data.total_monthly_cost
        
        # 3. Setup LLM
        config = AGENT_CONFIG.get("worker_pool", {})
        base_url = config.get("base_url")
        model_name = config.get("model")
        
        if not base_url or not model_name:
            error_msg = "Konfigurasi worker_pool tidak lengkap di config.py"
            logger.error(error_msg)
            memory.set_failed(AgentKey.HR_PLANNER, error_msg)
            return None
            
        llm = ChatOpenAI(
            base_url=base_url,
            model=model_name,
            temperature=0.4,  # Diminta temperature 0.4 untuk HR planner yang kreatif namun stabil
            api_key="empty",
        )
        
        llm_with_tools = llm.with_structured_output(HROutput)
        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah pakar HR Planner profesional.
Tugas Anda adalah merekomendasikan struktur SDM (Sumber Daya Manusia) yang efisien sesuai skala bisnis dan batasan biaya operasional.
Anda harus merekomendasikan:
1. `roles` (list of object, dengan keys "role" sebagai string, "count" sebagai integer, dan "salary" sebagai float dalam mata uang Rupiah).
2. `total_monthly_salary` (float: total semua peran (count * salary)).
3. `hiring_priority` (list of string: peran mana yang paling penting direkrut lebih dulu).

Berikan output murni dalam format JSON yang valid sesuai skema yang diminta."""),
            ("user", """Mohon rumuskan rencana SDM (HR Planner) untuk bisnis berikut:
- Ide Bisnis: {business_idea}
- Lokasi: {location}
- Total Keseluruhan Biaya Bulanan (Proyeksi Maksimal CFO): Rp {budget_bulanan_total:,.2f}

Buatlah daftar posisi/peran yang paling krusial saja untuk memulai bisnis tersebut secara efisien agar pengeluaran total untuk gaji bulanan tetap proporsional dengan proyeksi total biaya bulanan yang telah ditetapkan.
""")
        ])
        
        chain = prompt | llm_with_tools
        
        logger.info("HR Planner Agent: Mengirim request ke LLM...")
        
        result: HROutput = await chain.ainvoke({
            "business_idea": business_idea,
            "location": location,
            "budget_bulanan_total": budget_bulanan_total
        })
        
        # Validasi ulang perhitungan total_monthly_salary agar akurat mutlak (LLM bisa meleset dalam perhitungan aritmatika)
        calculated_total = sum(role.get("count", 0) * role.get("salary", 0.0) for role in result.roles)
        result.total_monthly_salary = float(calculated_total)
        
        # 5. Simpan Hasil ke Memory
        memory.set(AgentKey.HR_PLANNER, result)
        logger.info("HR Planner Agent: Selesai mengeksekusi tugas dan berhasil menyimpan ke memory.")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.HR_PLANNER, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada HR Planner Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.HR_PLANNER, error_msg)
        return None
