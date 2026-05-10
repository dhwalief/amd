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

        # 3. Siapkan LLM (Orchestrator class)
        llm = create_llm("orchestrator", temperature=0.5)
        
        # 4. Siapkan Prompt
        prompt = PromptTemplate(
            template='''Anda adalah Chief Strategy Officer dari sistem Business Co-Pilot.
Tugas Anda adalah merumuskan 2 hingga 3 OPSI PROPOSAL BISNIS yang berbeda berdasarkan data riset lapangan berikut.

# KONTEKS BISNIS
Lokasi: {location}
Modal Awal Tersedia: Rp {budget:,.0f}
Keahlian: {skills}
Aset Tersedia: {assets}
Ide Awal User: {ide}

# DATA RISET
1. Lokasi (Geo Analyst): {geo_recommendation} (Potensi: {geo_score})
2. Kompetisi (Competitor Scout): Ada {comp_count} kompetitor utama. Rata-rata harga pasar: Rp {avg_price:,.0f}. Gap: {market_gap}
3. Growth & Marketing (Growth Hacker): Rekomendasi Utama: {growth_idea}. Strategi GTM: {gtm}. Channel: {channels}
4. Pricing (Pricing Strategist): Harga Rekomendasi: Rp {pricing_rec:,.0f}. Margin: {margin}%. Strategi: {pricing_strategy}

# INSTRUKSI
Buat 2 atau 3 opsi bisnis yang masuk akal dan berbeda satu sama lain (misalnya: Opsi 1 fokus premium/kualitas, Opsi 2 fokus mass-market/murah, Opsi 3 fokus organik/lean-startup).
Opsi harus realistis dengan modal awal yang tersedia.

Keluarkan HANYA dalam format JSON dengan skema berikut:
{{
    "options": [
        {{
            "id": "opt_1",
            "title": "Nama Opsi 1",
            "description": "Deskripsi konsep...",
            "target_market": "Target pasar...",
            "pros": ["Kelebihan 1", "Kelebihan 2"],
            "cons": ["Kekurangan 1", "Kekurangan 2"],
            "estimated_startup_cost_range": "Rp 20 Juta - Rp 30 Juta"
        }}
    ]
}}
Pastikan output adalah valid JSON. Jangan gunakan block markdown (```json) jika tidak perlu, pastikan bisa langsung di-parse.
''',
            input_variables=[
                "location", "budget", "skills", "assets", "ide",
                "geo_recommendation", "geo_score", "comp_count", "avg_price", "market_gap",
                "growth_idea", "gtm", "channels", "pricing_rec", "margin", "pricing_strategy"
            ]
        )

        formatted_prompt = prompt.format(
            location=inq_data.business_context.location,
            budget=inq_data.business_context.budget,
            skills=", ".join(inq_data.business_context.skills),
            assets=", ".join(inq_data.business_context.existing_assets),
            ide=inq_data.business_context.business_idea or "Belum ada ide pasti",
            geo_recommendation=geo_data.recommendation,
            geo_score=geo_data.location_score,
            comp_count=len(comp_data.competitors),
            avg_price=comp_data.average_market_price,
            market_gap=", ".join(comp_data.market_gap),
            growth_idea=growth_data.recommended_idea,
            gtm=growth_data.go_to_market_strategy,
            channels=", ".join(growth_data.marketing_channels),
            pricing_rec=pricing_data.recommended_price,
            margin=pricing_data.margin_percentage,
            pricing_strategy=pricing_data.pricing_strategy
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
