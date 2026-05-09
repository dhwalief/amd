import logging
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import ValidationError

from config.config import AGENT_CONFIG
from core.schemas import InquisitorOutput, BusinessContext, AgentStatus
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory, user_input: str = "") -> InquisitorOutput:
    """
    Menjalankan Inquisitor agent untuk menggali informasi awal bisnis dari user.
    """
    logger.info("Memulai eksekusi Inquisitor agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.INQUISITOR, AgentStatus.RUNNING)
    
    try:
        # Konfigurasi LLM
        config = AGENT_CONFIG["scout_inquisitor_pool"]
        
        # Inisialisasi LLM via Langchain
        llm = ChatOpenAI(
            base_url=config["base_url"],
            model=config["model"],
            temperature=0.5,
            timeout=120,
            max_retries=2,
            api_key="empty"  # vLLM API server usually accepts dummy keys
        )
        
        # 2. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Inquisitor, seorang analis bisnis awal yang bertugas menggali informasi penting dari pengguna untuk merencanakan strategi bisnis 'Go to America'.
            
Tugas Anda adalah mengekstrak informasi bisnis dari input pengguna dan mengembalikannya HANYA dalam format JSON yang valid.
Informasi yang perlu diekstrak:
1. Lokasi bisnis (location)
2. Budget dalam Rupiah (budget)
3. Skill yang dimiliki (skills)
4. Aset yang ada (existing_assets)
5. Ide bisnis (business_idea, jika ada)
6. Sektor yang diminati (preferred_sector, jika ada)
7. Target pendapatan per bulan (target_monthly_income, jika ada)

Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "location": "...",
    "budget": 0.0,
    "skills": ["..."],
    "existing_assets": ["..."],
    "business_idea": "...",
    "preferred_sector": "...",
    "target_monthly_income": 0.0
}}

Jika ada nilai yang tidak disebutkan oleh pengguna, berikan null (untuk text/number) atau list kosong [] (untuk list array).

Input Pengguna:
{user_input}
"""
        )
        
        # Jika user_input kosong (misal saat dijalankan dari CLI testing), gunakan dummy input
        if not user_input:
            user_input = "Lokasi di Jakarta Selatan, budget 50 juta, skill saya masak dan marketing. Aset ada motor dan alat masak. Sektor F&B."
            logger.info("user_input kosong, menggunakan data dummy untuk testing.")
            
        logger.info("Mengirim prompt ke LLM...")
        
        chain = prompt | llm
        response = await chain.ainvoke({"user_input": user_input})
        
        # 3. Parsing JSON dari output LLM
        logger.info("Memparsing respons JSON dari LLM...")
        
        content = response.content.strip()
        # Membersihkan backticks jika LLM mereturn markdown JSON
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        json_data = json.loads(content)
        
        # 4. Validasi dengan Pydantic
        business_context = BusinessContext(**json_data)
        
        # 5. Buat Output dan Simpan ke Memory
        output = InquisitorOutput(business_context=business_context)
        memory.set(AgentKey.INQUISITOR, output)
        
        logger.info("Eksekusi Inquisitor agent selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        # Fallback empty context agar Pydantic InquisitorOutput tidak error saat diinisialisasi
        empty_context = BusinessContext(location="", budget=0, skills=[], existing_assets=[])
        output = InquisitorOutput(status=AgentStatus.FAILED, error_message=error_msg, business_context=empty_context)
        memory.set_failed(AgentKey.INQUISITOR, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        empty_context = BusinessContext(location="", budget=0, skills=[], existing_assets=[])
        output = InquisitorOutput(status=AgentStatus.FAILED, error_message=error_msg, business_context=empty_context)
        memory.set_failed(AgentKey.INQUISITOR, error_msg)
        return output
