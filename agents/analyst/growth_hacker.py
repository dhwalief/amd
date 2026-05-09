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
        
        # Ekstrak data untuk context prompt
        competitors_str = json.dumps([c.model_dump() for c in comp_data.competitors], indent=2)
        market_gap_str = ", ".join(comp_data.market_gap) if comp_data.market_gap else "Belum teridentifikasi"
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Growth Hacker dan Marketing Planner visioner untuk sistem perencanaan bisnis 'Go to America'.
            
Tugas Anda adalah memformulasikan ide bisnis yang kreatif dan strategi pemasaran yang kuat, dengan memanfaatkan celah pasar (market gap) dari kompetitor dan potensi lokasi yang ada.

Konteks Lokasi (Dari Geo Analyst):
- Skor Lokasi: {location_score} / 1.0
- Tingkat Permintaan: {demand_level}
- Keramaian (Foot Traffic): {foot_traffic}
- Daya Tarik Sekitar (Anchor): {nearby_anchor}
- Risiko Lokasi: {risk_factors}
- Rekomendasi Lokasi: {location_rec}

Konteks Kompetitor & Pasar (Dari Competitor Scout):
- Daftar Kompetitor Utama:
{competitors}
- Celah Pasar (Market Gap): {market_gap}
- Peluang Diferensiasi: {differentiation}

Tugas Anda adalah merumuskan strategi dan mengembalikannya HANYA dalam format JSON yang valid.
Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "business_ideas": ["ide 1", "ide 2", "ide 3"],
    "recommended_idea": "...",
    "target_segment": "...",
    "value_proposition": "...",
    "marketing_channels": ["channel 1", "channel 2"],
    "go_to_market_strategy": "..."
}}

Panduan pengisian nilai JSON:
- business_ideas: array of string berisi 3 hingga 5 ide bisnis yang kreatif dan relevan.
- recommended_idea: 1 ide bisnis terbaik dan paling spesifik dari daftar di atas.
- target_segment: penjelasan demografi/psikografi segmen pasar yang dituju.
- value_proposition: nilai jual unik (Unique Value Proposition) yang membedakan dari kompetitor.
- marketing_channels: array of string berisi saluran pemasaran yang paling efektif untuk target.
- go_to_market_strategy: paragraf singkat mengenai langkah konkret pertama meluncurkan bisnis ini.
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
