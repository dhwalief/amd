import json
import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import ValidationError
from langchain_core.prompts import PromptTemplate

from core.factory import create_llm
from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    AgentStatus, 
    ProposalOption, 
    ProposalGeneratorOutput,
    InquisitorOutput,
    GeoAnalystOutput,
    CompetitorScoutOutput,
    MarketOutput,
    PricingOutput
)

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory, **kwargs) -> ProposalGeneratorOutput:
    """
    Agen Proposal Generator (Fase 3).
    Membaca data riset dari lapis Analyst dan Inquisitor, lalu menyintesisnya
    menjadi 2-3 opsi strategi bisnis untuk dipilih pengguna.
    """
    logger.info("Mulai eksekusi Proposal Generator...")
    try:
        # 1. Pastikan semua dependensi sudah selesai (meskipun DependencyEngine sudah menjaminnya)
        # Tapi tidak ada salahnya dicek.
        
        # 2. Tarik semua data dari Shared Memory
        inq_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        geo_data = memory.get(AgentKey.GEO_ANALYST, GeoAnalystOutput)
        comp_data = memory.get(AgentKey.COMPETITOR, CompetitorScoutOutput)
        growth_data = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
        pricing_data = memory.get(AgentKey.PRICING, PricingOutput)

        if not all([inq_data, geo_data, comp_data, growth_data, pricing_data]):
            return ProposalGeneratorOutput(
                agent_name="proposal_generator",
                status=AgentStatus.FAILED,
                options=[],
                error_message="Data dari Analyst Layer belum lengkap."
            )

        # 3. Siapkan bahasa dan mata uang
        lang = inq_data.business_context.preferred_language or "id"
        is_en = lang == "en"
        currency_symbol = "$" if is_en else "Rp"
        exchange_rate = 16000.0 if is_en else 1.0
        
        # 4. Siapkan LLM (Orchestrator class)
        llm = create_llm("orchestrator", temperature=0.5)
        
        # 5. Siapkan Prompt
        prompt = PromptTemplate(
            template='''You are the Chief Strategy Officer of the Business Co-Pilot system.
Your task is to formulate 2 to 3 DIFFERENT BUSINESS PROPOSAL OPTIONS based on the following research data.

# LANGUAGE INSTRUCTION
- You MUST respond in {language_name}.
- All text fields (title, description, target_market, pros, cons) must be in {language_name}.

# BUSINESS CONTEXT
Location: {location}
Initial Capital: {currency_symbol} {budget:,.0f}
Skills: {skills}
Assets: {assets}
User Idea: {ide}

# RESEARCH DATA
1. Location (Geo Analyst): {geo_recommendation}
2. Competition (Competitor Scout): {comp_count} main competitors. Avg market price: {currency_symbol} {avg_price:,.0f}. Gap: {market_gap}
3. Growth & Marketing (Growth Hacker): Recommendation: {growth_idea}. GTM Strategy: {gtm}. Channels: {channels}
4. Pricing (Pricing Strategist): Recommended Price: {currency_symbol} {pricing_rec:,.0f}. Margin: {margin}%. Strategy: {pricing_strategy}

# INSTRUCTIONS
Create 2 or 3 sensible and distinct business options (e.g., Option 1: Premium/Quality, Option 2: Mass-market/Low-cost, Option 3: Organic/Lean-startup).
Options must be realistic according to the initial capital.

OUTPUT ONLY in JSON format with the following schema:
{{
    "options": [
        {{
            "id": "opt_1",
            "title": "Option Title",
            "description": "Concept description...",
            "target_market": "Target market segment...",
            "pros": ["Advantage 1", "Advantage 2"],
            "cons": ["Disadvantage 1", "Disadvantage 2"],
            "estimated_startup_cost_range": "{currency_symbol} 1,000 - {currency_symbol} 2,000"
        }}
    ]
}}
Ensure the output is valid JSON. Use the selected language ({language_name}) for all content.
''',
            input_variables=[
                "language_name", "location", "budget", "skills", "assets", "ide",
                "geo_recommendation", "comp_count", "avg_price", "market_gap",
                "growth_idea", "gtm", "channels", "pricing_rec", "margin", "pricing_strategy",
                "currency_symbol"
            ]
        )

        formatted_prompt = prompt.format(
            language_name="English" if is_en else "Bahasa Indonesia",
            location=inq_data.business_context.location,
            budget=inq_data.business_context.budget / exchange_rate,
            skills=", ".join(inq_data.business_context.skills),
            assets=", ".join(inq_data.business_context.existing_assets),
            ide=inq_data.business_context.business_idea or ("No specific idea" if is_en else "Belum ada ide pasti"),
            geo_recommendation=geo_data.recommendation,
            comp_count=len(comp_data.competitors),
            avg_price=comp_data.average_market_price / exchange_rate,
            market_gap=", ".join(comp_data.market_gap),
            growth_idea=growth_data.recommended_idea,
            gtm=growth_data.go_to_market_strategy,
            channels=", ".join(growth_data.marketing_channels),
            pricing_rec=pricing_data.recommended_price / exchange_rate,
            margin=pricing_data.margin_percentage,
            pricing_strategy=pricing_data.pricing_strategy,
            currency_symbol=currency_symbol
        )

        # 5. Invoke LLM
        response = await llm.ainvoke(formatted_prompt)
        content = response.content.strip()
        
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        parsed_data = json.loads(content)
        
        # 6. Parse dan validasi ke Pydantic Schema
        options = []
        for opt in parsed_data.get("options", []):
            options.append(ProposalOption(**opt))
            
        result = ProposalGeneratorOutput(
            agent_name="proposal_generator",
            status=AgentStatus.DONE,
            options=options
        )
        
        # 7. Simpan ke Memory
        memory.set(AgentKey.PROPOSAL_GENERATOR, result)
        logger.info(f"Proposal Generator selesai. Menghasilkan {len(options)} opsi.")
        return result

    except ValidationError as e:
        logger.error(f"Validation error saat parsing Proposal: {e}")
        return ProposalGeneratorOutput(
            agent_name="proposal_generator",
            status=AgentStatus.FAILED,
            options=[],
            error_message=f"Validation error: {e}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Error parse JSON Proposal: {e}\nContent: {content}")
        return ProposalGeneratorOutput(
            agent_name="proposal_generator",
            status=AgentStatus.FAILED,
            options=[],
            error_message=f"JSON Parse error: {e}"
        )
    except Exception as e:
        logger.error(f"System error di Proposal Generator: {e}")
        return ProposalGeneratorOutput(
            agent_name="proposal_generator",
            status=AgentStatus.FAILED,
            options=[],
            error_message=f"System error: {e}"
        )
