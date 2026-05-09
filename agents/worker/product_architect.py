import logging
import json
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
# pyrefly: ignore [missing-import]
from langchain.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from config.config import AGENT_CONFIG
from core.schemas import OpsOutput, MarketOutput, AgentStatus, EquipmentItem
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> OpsOutput:
    """
    Menjalankan Product Architect agent untuk merumuskan daftar peralatan, alur operasional,
    dan kebutuhan kapasitas/SDM minimum berdasarkan strategi pasar.
    """
    logger.info("Memulai eksekusi Product Architect agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.PRODUCT_ARCHITECT, AgentStatus.RUNNING)
    
    try:
        # 2. Ambil data Growth Hacker dari memory
        market_data = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
        
        # Validasi ketersediaan data dependency
        if not market_data or market_data.status != AgentStatus.DONE:
            error_msg = "Data dependency (Growth Hacker) tidak ditemukan atau belum selesai."
            logger.error(error_msg)
            output = OpsOutput(
                status=AgentStatus.FAILED, 
                error_message=error_msg,
                equipment_list=[],
                total_equipment_cost=0.0,
                operational_flow=[],
                daily_capacity=0,
                minimum_staff=0
            )
            memory.set_failed(AgentKey.PRODUCT_ARCHITECT, error_msg)
            return output
        
        # Konfigurasi LLM
        config = AGENT_CONFIG["worker_pool"]
        
        # Inisialisasi LLM via Langchain
        llm = ChatOpenAI(
            base_url=config["base_url"],
            model=config["model"],
            temperature=0.4,
            timeout=120,
            max_retries=2,
            api_key="empty"
        )
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Product Architect (Operations Planner) untuk sistem perencanaan bisnis 'Go to America'.
            
Tugas Anda adalah merumuskan daftar kebutuhan peralatan yang realistis, alur operasional bisnis sehari-hari, serta estimasi kapasitas dan SDM minimum.

Konteks Strategi Bisnis (Dari Growth Hacker):
- Ide Bisnis: {recommended_idea}
- Target Pasar: {target_segment}
- Value Proposition: {value_proposition}

Tugas Anda adalah merumuskan rencana operasional dan mengembalikannya HANYA dalam format JSON yang valid.
Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "equipment_list": [
        {{"name": "...", "quantity": 1, "estimated_cost": 0.0, "priority": "must-have"}}
    ],
    "total_equipment_cost": 0.0,
    "operational_flow": ["Langkah 1...", "Langkah 2..."],
    "daily_capacity": 0,
    "minimum_staff": 0
}}

Panduan pengisian nilai JSON:
- equipment_list: array object berisi alat-alat yang dibutuhkan. 'priority' harus salah satu dari: "must-have" atau "nice-to-have".
- total_equipment_cost: total jumlah (float) biaya dari seluruh equipment.
- operational_flow: array of string berisi urutan langkah operasional sehari-hari secara kronologis (dari persiapan hingga tutup).
- daily_capacity: estimasi kapasitas produksi/layanan maksimal per hari (integer).
- minimum_staff: estimasi jumlah staff minimal per hari (integer).
"""
        )
        
        logger.info("Mengirim prompt ke LLM untuk merumuskan operasi & peralatan...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "recommended_idea": market_data.recommended_idea,
            "target_segment": market_data.target_segment,
            "value_proposition": market_data.value_proposition
        })
        
        # 4. Parsing JSON dari output LLM
        logger.info("Memparsing respons JSON dari LLM...")
        
        content = response.content.strip()
        # Membersihkan backticks jika LLM mereturn markdown JSON
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        json_data = json.loads(content)
        
        # 5. Validasi Pydantic, Buat Output dan Simpan ke Memory
        output = OpsOutput(**json_data)
        memory.set(AgentKey.PRODUCT_ARCHITECT, output)
        
        logger.info("Eksekusi Product Architect agent selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        output = OpsOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            equipment_list=[],
            total_equipment_cost=0.0,
            operational_flow=[],
            daily_capacity=0,
            minimum_staff=0
        )
        memory.set_failed(AgentKey.PRODUCT_ARCHITECT, error_msg)
        return output
        
    except json.JSONDecodeError as e:
        error_msg = f"Gagal parsing respons JSON dari LLM: {str(e)}"
        logger.error(error_msg)
        
        output = OpsOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            equipment_list=[],
            total_equipment_cost=0.0,
            operational_flow=[],
            daily_capacity=0,
            minimum_staff=0
        )
        memory.set_failed(AgentKey.PRODUCT_ARCHITECT, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        output = OpsOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            equipment_list=[],
            total_equipment_cost=0.0,
            operational_flow=[],
            daily_capacity=0,
            minimum_staff=0
        )
        memory.set_failed(AgentKey.PRODUCT_ARCHITECT, error_msg)
        return output
