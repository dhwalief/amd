import logging
import json
from core.factory import create_llm
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.schemas import MarketOutput, GeoAnalystOutput, CompetitorScoutOutput, AgentStatus
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> MarketOutput:
    """
    Menjalankan Growth Hacker / Marketing Planner agent untuk merumuskan ide bisnis kreatif
    dan strategi marketing berdasarkan analisis lokasi dan kompetitor.
    """
    logger.info("Memulai eksekusi Growth Hacker agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.GROWTH_HACKER, AgentStatus.RUNNING)
    
    try:
        # 2. Ambil data Geo Analyst dan Competitor Scout dari memory
        geo_data = memory.get(AgentKey.GEO_ANALYST, GeoAnalystOutput)
        comp_data = memory.get(AgentKey.COMPETITOR, CompetitorScoutOutput)
        
        # Validasi ketersediaan data dependency
        missing_deps = []
        if not geo_data or geo_data.status != AgentStatus.DONE:
            missing_deps.append("Geo Analyst")
        if not comp_data or comp_data.status != AgentStatus.DONE:
            missing_deps.append("Competitor Scout")
            
        if missing_deps:
            error_msg = f"Data dependency tidak ditemukan atau belum selesai: {', '.join(missing_deps)}."
            logger.error(error_msg)
            output = MarketOutput(
                status=AgentStatus.FAILED, 
                error_message=error_msg,
                business_ideas=[],
                recommended_idea="",
                target_segment="",
                value_proposition="",
                marketing_channels=[],
                go_to_market_strategy=""
            )
            memory.set_failed(AgentKey.GROWTH_HACKER, error_msg)
            return output
        
        # Inisialisasi LLM via Factory
        llm = create_llm("analyst_pool", temperature=0.7, timeout=120)
        
        # Baca preferensi bahasa
        lang = memory.get_language()
        is_en = lang == "en"
        lang_name = "English" if is_en else "Bahasa Indonesia"

        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            f"""You are a visionary Growth Hacker and Marketing Planner for the 'Business Co-Pilot' system.
OUTPUT LANGUAGE: You MUST respond entirely in {lang_name}.

Your task is to formulate creative business ideas and strong marketing strategies, utilizing market gaps from competitors and location potential.

Location Context (From Geo Analyst):
- Location Score: {{location_score}} / 1.0
- Demand Level: {{demand_level}}
- Foot Traffic: {{foot_traffic}}
- Nearby Anchors: {{nearby_anchor}}
- Location Risks: {{risk_factors}}
- Location Recommendation: {{location_rec}}

Competitor & Market Context (From Competitor Scout):
- Main Competitors:
{{competitors}}
- Market Gaps: {{market_gap}}
- Differentiation Opportunities: {{differentiation}}

Task: Formulate the strategy and return it ONLY in valid JSON format.
JSON Schema:
{{
    "business_ideas": ["creative idea 1", "idea 2", "idea 3"],
    "recommended_idea": "detailed best idea...",
    "target_segment": "demographic/psychographic target...",
    "value_proposition": "Unique Value Proposition...",
    "marketing_channels": ["channel 1", "channel 2"],
    "go_to_market_strategy": "short paragraph about the first concrete steps..."
}}

Instructions for JSON values:
- Use {lang_name} for ALL text values inside the JSON.
- business_ideas: array of strings containing 3 to 5 creative and relevant business ideas.
- recommended_idea: the 1 best and most specific business idea from the list.
- target_segment: description of the target market segment.
- value_proposition: what makes this business different from competitors.
- marketing_channels: array of effective marketing channels.
- go_to_market_strategy: brief paragraph about the launch steps.
"""
        )
        
        logger.info("Mengirim prompt ke LLM untuk merumuskan ide bisnis dan marketing...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "location_score": geo_data.location_score,
            "demand_level": geo_data.demand_level,
            "foot_traffic": geo_data.foot_traffic_estimate,
            "nearby_anchor": ", ".join(geo_data.nearby_anchor) if geo_data.nearby_anchor else "Tidak ada",
            "risk_factors": ", ".join(geo_data.risk_factors) if geo_data.risk_factors else "Minim",
            "location_rec": geo_data.recommendation,
            "competitors": competitors_str,
            "market_gap": market_gap_str,
            "differentiation": comp_data.differentiation_opportunity
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
        output = MarketOutput(**json_data)
        memory.set(AgentKey.GROWTH_HACKER, output)
        
        logger.info("Eksekusi Growth Hacker agent selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        output = MarketOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            business_ideas=[],
            recommended_idea="",
            target_segment="",
            value_proposition="",
            marketing_channels=[],
            go_to_market_strategy=""
        )
        memory.set_failed(AgentKey.GROWTH_HACKER, error_msg)
        return output
        
    except json.JSONDecodeError as e:
        error_msg = f"Gagal parsing respons JSON dari LLM: {str(e)}"
        logger.error(error_msg)
        
        output = MarketOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            business_ideas=[],
            recommended_idea="",
            target_segment="",
            value_proposition="",
            marketing_channels=[],
            go_to_market_strategy=""
        )
        memory.set_failed(AgentKey.GROWTH_HACKER, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        output = MarketOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            business_ideas=[],
            recommended_idea="",
            target_segment="",
            value_proposition="",
            marketing_channels=[],
            go_to_market_strategy=""
        )
        memory.set_failed(AgentKey.GROWTH_HACKER, error_msg)
        return output
