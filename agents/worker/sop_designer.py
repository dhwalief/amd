import logging
import json
from core.factory import create_llm
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.schemas import SOPOutput, OpsOutput, HROutput, SupplyPlanOutput, AgentStatus
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> SOPOutput:
    """
    Menjalankan SOP Designer agent untuk membuat Standar Operasional Prosedur (SOP) harian,
    standar kualitas, dan checklist harian berdasarkan operasional, SDM, dan bahan baku.
    """
    logger.info("Memulai eksekusi SOP Designer agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.SOP_DESIGNER, AgentStatus.RUNNING)
    
    try:
        # 2. Ambil data dari memory
        ops_data = memory.get(AgentKey.PRODUCT_ARCHITECT, OpsOutput)
        hr_data = memory.get(AgentKey.HR_PLANNER, HROutput)
        supply_data = memory.get(AgentKey.SUPPLY_PLANNER, SupplyPlanOutput)
        
        # Validasi ketersediaan data dependency
        missing_deps = []
        if not ops_data or ops_data.status != AgentStatus.DONE:
            missing_deps.append("Product Architect")
        if not hr_data or hr_data.status != AgentStatus.DONE:
            missing_deps.append("HR Planner")
        if not supply_data or supply_data.status != AgentStatus.DONE:
            missing_deps.append("Supply Planner")
            
        if missing_deps:
            error_msg = f"Data dependency tidak ditemukan atau belum selesai: {', '.join(missing_deps)}."
            logger.error(error_msg)
            output = SOPOutput(
                status=AgentStatus.FAILED, 
                error_message=error_msg,
                sop_sections=[],
                quality_standards=[],
                daily_checklist=[]
            )
            memory.set_failed(AgentKey.SOP_DESIGNER, error_msg)
            return output
        
        # Inisialisasi LLM via Factory
        llm = create_llm("worker_pool", temperature=0.1, timeout=120)
        
        # Ekstrak data untuk context prompt
        operational_flow_str = ", ".join(ops_data.operational_flow) if ops_data.operational_flow else "Tidak didefinisikan"
        roles_str = json.dumps(hr_data.roles, indent=2) if hr_data.roles else "Tidak ada"
        
        # Mengamankan raw_materials karena ini dictionary dari Supply Planner
        raw_materials_str = "Tidak ada"
        if supply_data.raw_materials:
            try:
                raw_materials_str = json.dumps([{"item": rm.get("item", ""), "unit": rm.get("unit", "")} for rm in supply_data.raw_materials], indent=2)
            except Exception:
                pass
        # Ambil Proposal Terpilih
        proposal = memory.get_selected_proposal()
        business_title = proposal.title if proposal else "Sistem Perencanaan Bisnis"
        business_concept = proposal.description if proposal else "Standar Umum"
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah SOP Designer (Perancang Standar Operasional Prosedur) profesional.
            
Tugas Anda adalah membuat SOP harian yang sangat terstruktur, standar kualitas, dan checklist tugas harian untuk bisnis berikut:
- Konsep Bisnis: {business_title}
- Detail: {business_concept}

Konteks Operasional (Dari Product Architect):
- Alur Operasional: {operational_flow}

Konteks SDM (Dari HR Planner):
- Peran Staf yang Ada:
{roles}

Konteks Bahan Baku (Dari Supply Planner):
- Bahan Baku Utama:
{raw_materials}

Tugas Anda adalah merumuskan dokumen SOP dan mengembalikannya HANYA dalam format JSON yang valid.
Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "sop_sections": [
        {{
            "title": "Pembukaan Toko",
            "steps": ["Buka pintu", "Nyalakan mesin", "Cek bahan baku"]
        }}
    ],
    "quality_standards": [
        "Semua pesanan harus disajikan dalam waktu maksimal 10 menit",
        "Kebersihan area kasir harus selalu dijaga"
    ],
    "daily_checklist": [
        "Cek stok bahan baku",
        "Buang sampah",
        "Hitung uang kasir"
    ]
}}

Panduan pengisian nilai JSON:
- sop_sections: array object berisi bagian-bagian SOP. Setiap object memiliki 'title' (string) dan 'steps' (array of string urutan langkah kerjanya secara mendetail).
- quality_standards: array of string berisi standar kualitas yang harus dijaga secara ketat oleh pegawai.
- daily_checklist: array of string berisi daftar tugas (to-do list) wajib setiap hari.
"""
        )
        
        logger.info("Mengirim prompt ke LLM untuk merumuskan SOP...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "business_title": business_title,
            "business_concept": business_concept,
            "operational_flow": operational_flow_str,
            "roles": roles_str,
            "raw_materials": raw_materials_str
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
        output = SOPOutput(**json_data)
        memory.set(AgentKey.SOP_DESIGNER, output)
        
        logger.info("Eksekusi SOP Designer agent selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        output = SOPOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            sop_sections=[],
            quality_standards=[],
            daily_checklist=[]
        )
        memory.set_failed(AgentKey.SOP_DESIGNER, error_msg)
        return output
        
    except json.JSONDecodeError as e:
        error_msg = f"Gagal parsing respons JSON dari LLM: {str(e)}"
        logger.error(error_msg)
        
        output = SOPOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            sop_sections=[],
            quality_standards=[],
            daily_checklist=[]
        )
        memory.set_failed(AgentKey.SOP_DESIGNER, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        output = SOPOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            sop_sections=[],
            quality_standards=[],
            daily_checklist=[]
        )
        memory.set_failed(AgentKey.SOP_DESIGNER, error_msg)
        return output
