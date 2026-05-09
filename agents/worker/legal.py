import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    InquisitorOutput,
    FinanceOutput,
    PricingOutput,
    LegalOutput,
    AgentStatus
)
from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

# Coba import RAG pipeline (graceful fallback jika belum dibuat)
try:
    from core.rag import get_rag_pipeline
    RAG_MODULE_AVAILABLE = True
except ImportError:
    RAG_MODULE_AVAILABLE = False
    logger.warning("Modul core.rag tidak ditemukan. Berjalan tanpa RAG (graceful fallback).")

async def run(memory: SharedMemory) -> Optional[LegalOutput]:
    """
    Legal & Compliance Agent
    Tugas: Menentukan perizinan dan compliance notes menggunakan LLM dan RAG (opsional).
    """
    try:
        logger.info("Legal Agent: Memulai eksekusi...")
        
        # 1. Update status
        memory.set_status(AgentKey.LEGAL, AgentStatus.RUNNING)
        
        # 2. Ambil data dari shared memory
        cfo_data = memory.get(AgentKey.CFO, FinanceOutput)
        pricing_data = memory.get(AgentKey.PRICING, PricingOutput)
        
        if not cfo_data:
            error_msg = "Data CFO tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.LEGAL, error_msg)
            return None
            
        if not pricing_data:
            error_msg = "Data Pricing Strategist tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.LEGAL, error_msg)
            return None
            
        # Ambil konteks bisnis dari Inquisitor
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        business_type = "Bisnis Umum"
        location = "Indonesia"
        if inquisitor_data and inquisitor_data.business_context:
            business_type = inquisitor_data.business_context.business_idea or inquisitor_data.business_context.preferred_sector or business_type
            location = inquisitor_data.business_context.location

        # 3. Eksekusi RAG Pipeline
        rag_context = ""
        rag_available = False
        if RAG_MODULE_AVAILABLE:
            try:
                rag = get_rag_pipeline()
                if rag:
                    docs = rag.retrieve(f"perizinan usaha {business_type} di {location}", k=3)
                    # Support multiple return types from RAG retriever (Langchain docs objects or strings)
                    docs_content = [getattr(doc, 'page_content', str(doc)) for doc in docs]
                    rag_context = "\n\n".join(docs_content)
                    rag_available = len(docs_content) > 0
                    logger.info(f"RAG berhasil mengambil {len(docs_content)} dokumen relevan.")
            except Exception as e:
                logger.warning(f"Gagal menjalankan RAG Pipeline: {e}. Melanjutkan tanpa RAG.")
                
        # 4. Setup LLM
        config = AGENT_CONFIG.get("analyst_pool", {})
        base_url = config.get("base_url")
        model_name = config.get("model")
        
        if not base_url or not model_name:
            error_msg = "Konfigurasi analyst_pool tidak lengkap di config.py"
            logger.error(error_msg)
            memory.set_failed(AgentKey.LEGAL, error_msg)
            return None
            
        llm = ChatOpenAI(
            base_url=base_url,
            model=model_name,
            temperature=0.1,
            api_key="empty",
        )
        
        llm_with_tools = llm.with_structured_output(LegalOutput)
        
        # 5. Setup Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Anda adalah pakar Hukum dan Kepatuhan (Legal & Compliance) profesional.
Tugas Anda adalah merumuskan dokumen perizinan yang dibutuhkan, yurisdiksi, catatan kepatuhan (compliance notes), dan sumber hukum yang relevan untuk sebuah bisnis.
Apabila terdapat 'Dokumen Referensi Hukum (RAG)', prioritaskan informasi dari dokumen tersebut.
Jika tidak ada, gunakan pengetahuan Anda dengan cermat. Berikan penilaian `confidence_level` ("high", "medium", atau "low").
Output harus berupa JSON yang valid dan mematuhi skema yang diminta."""),
            ("user", """Mohon rumuskan analisis hukum untuk bisnis berikut:
- Tipe Bisnis: {business_type}
- Lokasi (Yurisdiksi): {location}
- Rekomendasi Modal Awal: Rp {capital:,.2f}
- Strategi Harga: {pricing_strategy}

Dokumen Referensi Hukum (RAG):
{rag_context}

Tentukan izin spesifik apa saja yang wajib dimiliki, yurisdiksi yang berlaku, catatan kepatuhan (termasuk aspek perpajakan atau regulasi), dan daftar sumber / referensi.
""")
        ])
        
        chain = prompt | llm_with_tools
        
        logger.info("Legal Agent: Mengirim request ke LLM...")
        
        result: LegalOutput = await chain.ainvoke({
            "business_type": business_type,
            "location": location,
            "capital": cfo_data.recommended_capital,
            "pricing_strategy": pricing_data.pricing_strategy,
            "rag_context": rag_context if rag_available else "Tidak ada dokumen referensi spesifik yang dikirimkan. Gunakan general knowledge Anda."
        })
        
        # Override field rag_available sesuai dengan state sesungguhnya
        result.rag_available = rag_available
        
        # 6. Simpan Hasil ke Memory
        memory.set(AgentKey.LEGAL, result)
        logger.info("Legal Agent: Selesai mengeksekusi tugas dan berhasil menyimpan ke memory.")
        
        return result
        
    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.LEGAL, error_msg)
        return None
    except Exception as e:
        error_msg = f"Terjadi kesalahan pada Legal Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.LEGAL, error_msg)
        return None
