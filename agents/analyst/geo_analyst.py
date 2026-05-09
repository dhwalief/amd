import logging
import json
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import ValidationError

from config.config import AGENT_CONFIG
from core.schemas import GeoAnalystOutput, InquisitorOutput, AgentStatus
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> GeoAnalystOutput:
    """
    Menjalankan Geo Analyst agent untuk menganalisis lokasi berdasarkan konteks bisnis dari Inquisitor.
    """
    logger.info("Memulai eksekusi Geo Analyst agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.GEO_ANALYST, AgentStatus.RUNNING)
    
    try:
        # 2. Ambil data Inquisitor dari memory
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        
        if not inquisitor_data or inquisitor_data.status != AgentStatus.DONE:
            error_msg = "Data Inquisitor tidak ditemukan atau belum selesai."
            logger.error(error_msg)
            output = GeoAnalystOutput(
                status=AgentStatus.FAILED, 
                error_message=error_msg,
                location_score=0.0,
                demand_level="low",
                foot_traffic_estimate="",
                nearby_anchor=[],
                risk_factors=[],
                recommendation=""
            )
            memory.set_failed(AgentKey.GEO_ANALYST, error_msg)
            return output
            
        context = inquisitor_data.business_context
        
        # Konfigurasi LLM
        config = AGENT_CONFIG["analyst_pool"]
        
        # Inisialisasi LLM via Langchain
        llm = ChatOpenAI(
            base_url=config["base_url"],
            model=config["model"],
            temperature=0.4,
            timeout=120,
            max_retries=2,
            api_key="empty"  # vLLM API server usually accepts dummy keys
        )
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Geo Analyst, analis spasial dan demografi untuk sistem perencanaan bisnis 'Go to America'.
            
Konteks Bisnis:
- Lokasi Target: {location}
- Ide Bisnis / Sektor: {business_idea} / {preferred_sector}
- Budget: Rp {budget:,.2f}

Tugas Anda adalah mengekstrak analisis geografi dan demografi untuk lokasi tersebut dan mengembalikannya HANYA dalam format JSON yang valid.
Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "location_score": 0.0,
    "demand_level": "high",
    "foot_traffic_estimate": "...",
    "nearby_anchor": ["..."],
    "risk_factors": ["..."],
    "recommendation": "..."
}}

Panduan pengisian nilai JSON:
- location_score: angka float antara 0.0 hingga 1.0 (misal: 0.85)
- demand_level: harus salah satu dari: "high", "medium", atau "low"
- foot_traffic_estimate: kalimat singkat mengestimasi kepadatan lalu lalang manusia di lokasi tersebut
- nearby_anchor: array of string berisi daya tarik sekitar (misal: ["Kampus", "Perkantoran", "Stasiun"])
- risk_factors: array of string berisi potensi risiko lokasi (misal: ["Rawan macet", "Banyak kompetitor sejenis"])
- recommendation: kalimat singkat rekomendasi kelayakan lokasi
"""
        )
        
        business_idea_text = context.business_idea if context.business_idea else "Belum spesifik"
        preferred_sector_text = context.preferred_sector if context.preferred_sector else "Belum spesifik"
        
        logger.info(f"Mengirim prompt ke LLM untuk menganalisis lokasi: {context.location}...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "location": context.location,
            "business_idea": business_idea_text,
            "preferred_sector": preferred_sector_text,
            "budget": context.budget
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
        output = GeoAnalystOutput(**json_data)
        memory.set(AgentKey.GEO_ANALYST, output)
        
        logger.info("Eksekusi Geo Analyst agent selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        output = GeoAnalystOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            location_score=0.0,
            demand_level="low",
            foot_traffic_estimate="",
            nearby_anchor=[],
            risk_factors=[],
            recommendation=""
        )
        memory.set_failed(AgentKey.GEO_ANALYST, error_msg)
        return output
        
    except json.JSONDecodeError as e:
        error_msg = f"Gagal parsing respons JSON dari LLM: {str(e)}"
        logger.error(error_msg)
        
        output = GeoAnalystOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            location_score=0.0,
            demand_level="low",
            foot_traffic_estimate="",
            nearby_anchor=[],
            risk_factors=[],
            recommendation=""
        )
        memory.set_failed(AgentKey.GEO_ANALYST, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        output = GeoAnalystOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            location_score=0.0,
            demand_level="low",
            foot_traffic_estimate="",
            nearby_anchor=[],
            risk_factors=[],
            recommendation=""
        )
        memory.set_failed(AgentKey.GEO_ANALYST, error_msg)
        return output
