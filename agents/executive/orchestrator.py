import asyncio
import json
import logging
from typing import Optional

# pyrefly: ignore [missing-import]
from pydantic import ValidationError
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate

from core.factory import create_llm
from core.shared_memory import SharedMemory, AgentKey
from core.schemas import AgentStatus, CriticOutput, RiskManagerOutput, OrchestratorReview
from core.engine import DependencyEngine

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory, **kwargs) -> OrchestratorReview:
    """
    Bagian 1: Final Review (LLM).
    Membaca output dari Critic dan Risk Manager, lalu melakukan evaluasi akhir dengan Qwen2.5-72B.
    """
    logger.info("Mulai eksekusi Orchestrator...")
    try:
        # Cek apakah Critic dan Risk Manager sudah selesai
        if not (memory.is_done(AgentKey.CRITIC) and memory.is_done(AgentKey.RISK_MANAGER)):
            return OrchestratorReview(
                agent_name="orchestrator",
                status=AgentStatus.LOCKED,
                approved=False,
                final_recommendation="",
                executive_summary="",
                next_steps=[],
                error_message="Dependencies (Critic, Risk Manager) belum terpenuhi."
            )

        # Baca data dari memory
        critic_data = memory.get(AgentKey.CRITIC, CriticOutput)
        risk_data = memory.get(AgentKey.RISK_MANAGER, RiskManagerOutput)

        if not critic_data or not risk_data:
            return OrchestratorReview(
                agent_name="orchestrator",
                status=AgentStatus.FAILED,
                approved=False,
                final_recommendation="",
                executive_summary="",
                next_steps=[],
                error_message="Gagal mendapatkan data dari Critic atau Risk Manager."
            )

        llm = create_llm("orchestrator", temperature=0.3)
        
        prompt = PromptTemplate(
            template='''Anda adalah Chief Executive Officer (CEO) sekaligus Orchestrator dari multi-agent system perencanaan bisnis.
Tugas Anda adalah membaca laporan dari tim evaluasi (Critic dan Risk Manager), lalu memberikan keputusan akhir apakah rencana bisnis ini layak dijalankan (approved) atau tidak.

# Laporan Critic
Risk Level Keseluruhan: {critic_risk_level}
Apakah butuh revisi: {critic_revision}
Jumlah Isu Kritikal: {critic_critical_count}
Ringkasan Critic: {critic_summary}

# Laporan Risk Manager
Viability Keseluruhan: {risk_viability}
Worst Case Scenario: {risk_worst_case}
Best Case Scenario: {risk_best_case}

Berikan review akhir dalam format JSON.
Schema output:
{{
    "approved": bool,
    "final_recommendation": "string",
    "executive_summary": "string",
    "next_steps": ["langkah 1", "langkah 2"]
}}

Keluarkan HANYA JSON tanpa format lain (jangan gunakan blok markdown atau backtick jika tidak perlu, tapi pastikan valid JSON).
''',
            input_variables=[
                "critic_risk_level", "critic_revision", "critic_critical_count", "critic_summary",
                "risk_viability", "risk_worst_case", "risk_best_case"
            ]
        )

        formatted_prompt = prompt.format(
            critic_risk_level=critic_data.overall_risk_level,
            critic_revision=str(critic_data.revision_required),
            critic_critical_count=critic_data.critical_count,
            critic_summary=critic_data.summary,
            risk_viability=risk_data.overall_viability,
            risk_worst_case=risk_data.worst_case_summary,
            risk_best_case=risk_data.best_case_summary
        )

        response = await llm.ainvoke(formatted_prompt)
        content = response.content.strip()
        
        # Bersihkan format JSON jika LLM membungkus dengan markdown block
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        parsed_data = json.loads(content)
        
        result = OrchestratorReview(
            agent_name="orchestrator",
            status=AgentStatus.DONE,
            approved=parsed_data.get("approved", False),
            final_recommendation=parsed_data.get("final_recommendation", ""),
            executive_summary=parsed_data.get("executive_summary", ""),
            next_steps=parsed_data.get("next_steps", [])
        )
        
        # Simpan ke shared memory
        memory.set(AgentKey.ORCHESTRATOR, result)
        logger.info("Orchestrator selesai dieksekusi.")
        return result

    except ValidationError as e:
        logger.error(f"Validation error saat parsing output LLM: {e}")
        return OrchestratorReview(
            agent_name="orchestrator",
            status=AgentStatus.FAILED,
            approved=False,
            final_recommendation="",
            executive_summary="",
            next_steps=[],
            error_message=f"Validation error: {e}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Error parse JSON dari LLM: {e}")
        return OrchestratorReview(
            agent_name="orchestrator",
            status=AgentStatus.FAILED,
            approved=False,
            final_recommendation="",
            executive_summary="",
            next_steps=[],
            error_message=f"JSON Parse error: {e}"
        )
    except Exception as e:
        logger.error(f"Error di Orchestrator: {e}")
        return OrchestratorReview(
            agent_name="orchestrator",
            status=AgentStatus.FAILED,
            approved=False,
            final_recommendation="",
            executive_summary="",
            next_steps=[],
            error_message=f"System error: {e}"
        )


async def setup_and_run(memory: SharedMemory):
    """
    Bagian 2: Register dan Jalankan Semua Agent.
    """
    logger.info("Memulai setup seluruh agent...")
    engine = DependencyEngine(memory)

    # 1. Import semua agent dari agents/worker/, agents/analyst/, agents/executive/, agents/utility/
    
    try:
        from agents.worker.inquisitor import run as inquisitor_run
        engine.register_agent(AgentKey.INQUISITOR, inquisitor_run)
    except ImportError: pass

    try:
        from agents.worker.product_architect import run as product_architect_run
        engine.register_agent(AgentKey.PRODUCT_ARCHITECT, product_architect_run)
    except ImportError: pass

    try:
        from agents.worker.sop_designer import run as sop_designer_run
        engine.register_agent(AgentKey.SOP_DESIGNER, sop_designer_run)
    except ImportError: pass

    try:
        from agents.worker.legal import run as legal_run
        engine.register_agent(AgentKey.LEGAL, legal_run)
    except ImportError: pass

    try:
        from agents.worker.hr_planner import run as hr_planner_run
        engine.register_agent(AgentKey.HR_PLANNER, hr_planner_run)
    except ImportError: pass

    # --- Analyst Agents ---
    try:
        from agents.analyst.cfo import run as cfo_run
        engine.register_agent(AgentKey.CFO, cfo_run)
    except ImportError: pass

    try:
        from agents.analyst.geo_analyst import run as geo_analyst_run
        engine.register_agent(AgentKey.GEO_ANALYST, geo_analyst_run)
    except ImportError: pass

    try:
        from agents.analyst.growth_hacker import run as growth_hacker_run
        engine.register_agent(AgentKey.GROWTH_HACKER, growth_hacker_run)
    except ImportError: pass

    try:
        from agents.analyst.competitor_scout import run as competitor_scout_run
        engine.register_agent(AgentKey.COMPETITOR, competitor_scout_run)
    except ImportError: pass

    try:
        from agents.analyst.pricing_strategist import run as pricing_strategist_run
        engine.register_agent(AgentKey.PRICING, pricing_strategist_run)
    except ImportError: pass

    # --- Executive Agents ---
    # Critic & Risk Manager akan otomatis terdaftar jika sudah diimplementasikan
    try:
        from agents.executive.critic import run as critic_run
        engine.register_agent(AgentKey.CRITIC, critic_run)
    except ImportError: pass

    try:
        from agents.executive.risk_manager import run as risk_manager_run
        engine.register_agent(AgentKey.RISK_MANAGER, risk_manager_run)
    except ImportError: pass

    try:
        from agents.utility.supply_planner import run as supply_planner_run
        engine.register_agent(AgentKey.SUPPLY_PLANNER, supply_planner_run)
    except ImportError: pass

    try:
        from agents.utility.schema_validator import run as schema_validator_run
        engine.register_agent(AgentKey.SCHEMA_VALIDATOR, schema_validator_run) # asumsikan key tersedia
    except Exception: pass

    try:
        from agents.utility.output_formatter import run as output_formatter_run
        engine.register_agent(AgentKey.OUTPUT_FORMATTER, output_formatter_run)
    except Exception: pass

    # 4. Jalankan engine.run_all()
    logger.info("Mengeksekusi semua agent via DependencyEngine...")
    results = await engine.run_all()
    summary = engine.get_summary(results)
    
    logger.info(f"Summary Engine Run: {json.dumps(summary, indent=2)}")
    
    # 5. Setelah semua selesai, jalankan run(memory) untuk final review
    logger.info("Menjalankan Orchestrator untuk Final Review...")
    final_review = await run(memory)
    
    # 6. Print summary hasil eksekusi
    print("\n" + "="*40)
    print("      HASIL AKHIR ORCHESTRATOR      ")
    print("="*40)
    print(f"Status              : {final_review.status.value}")
    if final_review.status == AgentStatus.DONE:
        print(f"Approved            : {final_review.approved}")
        print(f"Executive Summary   : {final_review.executive_summary}")
        print(f"Final Recommendation: {final_review.final_recommendation}")
        print("\nNext Steps:")
        for step in final_review.next_steps:
            print(f"- {step}")
    else:
        print(f"Error Message       : {final_review.error_message}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Menggunakan MockSharedMemory karena script dijalankan langsung
    from core.shared_memory import MockSharedMemory as SharedMemory
    
    mem = SharedMemory()
    asyncio.run(setup_and_run(mem))
