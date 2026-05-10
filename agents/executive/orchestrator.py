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

        # Baca preferensi bahasa
        lang = memory.get_language()
        is_en = lang == "en"
        lang_name = "English" if is_en else "Bahasa Indonesia"

        # PENTING: Gunakan string biasa + inject lang_name via concatenation
        template_body = (
            f"You are the Chief Executive Officer (CEO) and Orchestrator of a business planning multi-agent system.\n"
            f"OUTPUT LANGUAGE: You MUST respond entirely in {lang_name}.\n\n"
            "Your task is to read the reports from the evaluation team (Critic and Risk Manager), then provide a final decision on whether this business plan is viable to execute.\n\n"
            "IMPORTANT CONTEXT: All data you read are RESEARCH-BASED PROJECTIONS and PLANS — "
            "estimated figures derived from web search results (market prices, HR rates, equipment costs, competitor data) "
            "collected by analyst agents. This is NOT an actual financial report. "
            'You are evaluating a **plan** before the business exists, use language like: "plan", "projection", "research-based estimate".\n\n'
            "# Critic Report\n"
            "Projection Risk Level: {critic_risk_level}\n"
            "Revision Required: {critic_revision}\n"
            "Critical Issues Count: {critic_critical_count}\n"
            "Critic Summary: {critic_summary}\n\n"
            "# Risk Manager Report\n"
            "Plan Viability: {risk_viability}\n"
            "Worst Case Scenario: {risk_worst_case}\n"
            "Best Case Scenario: {risk_best_case}\n\n"
            "Provide final review in JSON format.\n"
            "Output Schema:\n"
            "{{\n"
            '    "approved": bool,\n'
            f'    "final_recommendation": "string (brief, concise recommendation in {lang_name})",\n'
            f'    "executive_summary": "string (summary of plan evaluation in {lang_name}, use projection/plan/estimate language)",\n'
            f'    "next_steps": ["business action step 1 in {lang_name}", "business action step 2", ...],\n'
            f'    "reasoning": "2-3 paragraphs of your narrative thought process in {lang_name}"\n'
            "}}\n\n"
            "IMPORTANT for next_steps:\n"
            "- Content must be BUSINESS ACTION STEPS that the owner/future owner can take.\n"
            '- DO NOT write technical system steps like "fix parsing error" or "debug agent".\n'
            '- CORRECT Example: "Negotiate raw material prices with suppliers to lower COGS below selling price".\n'
            '- INCORRECT Example: "Fix CFO agent JSON parsing error".\n\n'
            "OUTPUT ONLY JSON without any other formatting."
        )

        prompt = PromptTemplate(
            template=template_body,
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

        from core.llm_utils import invoke_with_retry, safe_parse_json
        content = await invoke_with_retry(llm, formatted_prompt, max_retries=3, agent_name="orchestrator")
        if not content:
            raise json.JSONDecodeError("LLM returned empty after retries", "", 0)

        parsed_data = safe_parse_json(content, agent_name="orchestrator")
        if parsed_data is None:
            raise json.JSONDecodeError("safe_parse_json failed", content, 0)

        
        result = OrchestratorReview(
            agent_name="orchestrator",
            status=AgentStatus.DONE,
            approved=parsed_data.get("approved", False),
            final_recommendation=parsed_data.get("final_recommendation", ""),
            executive_summary=parsed_data.get("executive_summary", ""),
            next_steps=parsed_data.get("next_steps", []),
            reasoning=parsed_data.get("reasoning", None)
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

    # Register Orchestrator (dirinya sendiri)
    engine.register_agent(AgentKey.ORCHESTRATOR, run)

    # Register Proposal Generator
    try:
        from agents.executive.proposal_generator import run as proposal_generator_run
        engine.register_agent(AgentKey.PROPOSAL_GENERATOR, proposal_generator_run)
    except ImportError as e:
        logger.error(f"Gagal mengimpor proposal_generator: {e}")



    # 4. Jalankan engine.run_all()
    logger.info("Mengeksekusi semua agent via DependencyEngine...")
    results = await engine.run_all()
    summary = engine.get_summary(results)
    
    logger.info(f"Summary Engine Run: {json.dumps(summary, indent=2)}")
    
    # Cek apakah sistem sedang menunggu intervensi (Paused di Virtual Node)
    ready_agents = memory.get_ready_agents()
    virtual_nodes = [k for k in ready_agents if k not in engine.registry]
    
    if virtual_nodes:
        logger.info(f"Engine Paused. Menunggu input user untuk node: {[v.value for v in virtual_nodes]}")
        return
    else:
        logger.info("Semua tahapan DAG selesai dieksekusi tanpa hambatan atau jeda lebih lanjut.")
        
        if memory.is_done(AgentKey.ORCHESTRATOR):
            final_review = memory.get(AgentKey.ORCHESTRATOR, OrchestratorReview)
            logger.info(f"HASIL AKHIR ORCHESTRATOR: Approved={final_review.approved} | {final_review.executive_summary}")




if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Menggunakan MockSharedMemory karena script dijalankan langsung
    from core.shared_memory import MockSharedMemory as SharedMemory
    
    mem = SharedMemory()
    asyncio.run(setup_and_run(mem))
