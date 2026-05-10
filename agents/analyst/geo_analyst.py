import logging
import json
from core.factory import create_llm
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

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
        
        # Baca preferensi bahasa
        lang = memory.get_language()
        is_en = lang == "en"
        lang_name = "English" if is_en else "Bahasa Indonesia"
        
        # Inisialisasi LLM via Factory
        llm = create_llm("analyst_pool", temperature=0.4, timeout=120)
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            f"""You are a Geo Analyst, spatial and demographic analyst for the 'Business Co-Pilot' system.
OUTPUT LANGUAGE: You MUST respond entirely in {lang_name}.

Business Context:
- Target Location: {{location}}
- Business Idea / Sector: {{business_idea}} / {{preferred_sector}}
- Budget: Rp {{budget:,.2f}}

Your task is to extract geography and demographic analysis for the location and return it ONLY in valid JSON format.
JSON Schema:
{{
    "location_score": 0.0,
    "demand_level": "high",
    "foot_traffic_estimate": "description in {lang_name}",
    "nearby_anchor": ["place 1", "place 2"],
    "risk_factors": ["risk 1", "risk 2"],
    "recommendation": "summary paragraph in {lang_name}"
}}

Instructions for JSON values:
- Use {lang_name} for all text content.
- location_score: float between 0.0 and 1.0.
- demand_level: "high", "medium", or "low".
- foot_traffic_estimate: brief sentence estimating foot traffic density.
- nearby_anchor: array of strings containing surrounding points of interest.
- risk_factors: array of strings containing potential location risks.
- recommendation: brief sentence on location viability.
"""
        )
        
        business_idea_text = context.business_idea if context.business_idea else ("Not specified" if is_en else "Belum spesifik")
        preferred_sector_text = context.preferred_sector if context.preferred_sector else ("Not specified" if is_en else "Belum spesifik")
        
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
