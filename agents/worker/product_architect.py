import logging
import json
from core.factory import create_llm
from core.llm_utils import invoke_with_retry, safe_parse_json
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

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
        # 2. Ambil Proposal Terpilih dari memory
        proposal = memory.get_selected_proposal()
        market_data = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
        
        # Validasi ketersediaan data dependency
        if not proposal and (not market_data or market_data.status != AgentStatus.DONE):
            error_msg = "Data dependency (Proposal / Growth Hacker) tidak ditemukan atau belum selesai."
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
        
        # Inisialisasi LLM via Factory
        llm = create_llm("worker_pool", temperature=0.4, timeout=120)
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Product Architect (Operations Planner) untuk sistem perencanaan bisnis 'Go to America'.
            
Tugas Anda adalah merumuskan daftar kebutuhan peralatan yang realistis, alur operasional bisnis sehari-hari, serta estimasi kapasitas dan SDM minimum.

Konteks Strategi Bisnis (Proposal Terpilih):
- Konsep Bisnis: {recommended_idea}
- Target Pasar: {target_segment}
- Value Proposition / Deskripsi: {value_proposition}

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
        
        rec_idea = proposal.title if proposal else market_data.recommended_idea
        tgt_seg = proposal.target_market if proposal else market_data.target_segment
        vp = proposal.description if proposal else market_data.value_proposition
        
        formatted = prompt.format(
            recommended_idea=rec_idea,
            target_segment=tgt_seg,
            value_proposition=vp,
        )

        # Retry otomatis jika LLM mengembalikan respons kosong
        content = await invoke_with_retry(llm, formatted, max_retries=3, agent_name="product_architect")

        if not content:
            raise json.JSONDecodeError("LLM returned empty after retries", "", 0)

        json_data = safe_parse_json(content, agent_name="product_architect")
        if json_data is None:
            raise json.JSONDecodeError("safe_parse_json failed", content, 0)
        
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
