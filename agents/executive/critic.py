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
        lang_instruction = "Respond in English." if lang == "en" else "Jawab dalam Bahasa Indonesia."

        llm_with_tools = llm.with_structured_output(CriticOutput)

        
        # 4. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Anda adalah Executive Critic profesional (Gap Finder) untuk sistem **perencanaan bisnis**.
{lang_instruction}

KONTEKS PENTING: Semua data yang Anda terima adalah PROYEKSI DAN RENCANA berbasis riset — angka-angka estimasi dihasilkan dari hasil pencarian web (harga pasar, tarif SDM, biaya peralatan, dan data kompetitor yang dikumpulkan secara real-time). Ini bukan laporan keuangan aktual, bukan data historis perusahaan, dan bukan laporan audit. Semua angka adalah ESTIMASI BERBASIS DATA PASAR untuk membantu user merencanakan bisnis sebelum benar-benar berdiri.

ATURAN KRITIS:
- ABAIKAN SEPENUHNYA data yang menunjukkan error teknis sistem (seperti "error parsing JSON", "agent gagal", "data tidak tersedia", dll). Itu adalah error sistem teknis yang bukan tanggung jawab user/bisnis.
- HANYA laporkan isu yang relevan dengan PERENCANAAN BISNIS: inkonsistensi antar angka proyeksi, asumsi pasar yang tidak realistis, celah strategi, dll.
- Jika data dari suatu agen tidak tersedia karena error teknis, CATAT sebagai keterbatasan data, bukan sebagai isu kritis bisnis.

Tugas Anda adalah meninjau konsistensi dan kewajaran estimasi dari seluruh agen spesialis:
1. Angka yang tidak konsisten antar agen (misal: total gaji HR melebihi alokasi proyeksi CFO, atau HPP Supply Planner lebih tinggi dari harga jual Pricing).
2. Asumsi yang tidak realistis dibandingkan konteks pasar riil yang ada.
3. Celah operasional/bisnis dalam rencana yang belum tercakup.

Gunakan bahasa "rencana", "proyeksi", "estimasi", "berdasarkan riset pasar" — BUKAN "laporan keuangan" atau "data historis".
Keluarkan dalam format JSON. Array `issues_found` berisi severity ("critical", "warning", "info"), agent_source, description, dan suggestion yang detail.
Tambahkan field `reasoning` berisi 2-3 paragraf alur berpikir Anda secara naratif sebelum menyimpulkan."""),
            ("user", """Mohon lakukan tinjauan kritis terhadap keseluruhan **proyeksi rencana bisnis** dari agen-agen berikut:

{context_string}

Ingat:
- Ini adalah proyeksi perencanaan berbasis riset pasar, bukan laporan keuangan aktual.
- ABAIKAN error teknis sistem (parsing, agent gagal, dll) — itu bukan isu bisnis.
- Fokus HANYA pada inkonsistensi antar angka proyeksi dan kewajaran asumsi bisnis.
- Identifikasi isu, nilai `overall_risk_level` ("high"/"medium"/"low"), putuskan `revision_required`, dan tulis `summary` + `reasoning` naratif.
""")
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
