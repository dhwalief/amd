"""
engine.py — Async DAG Executor untuk Multi-Agent System
========================================================

Kerjaan Dev1 di Week 1 Phase 2.

Fungsi:
1. Parse DAG dari shared_memory
2. Execute agents sesuai dependency order
3. Handle errors & retries
4. Monitor progress

CATATAN:
- Gunakan asyncio untuk concurrent execution dimana possible
- Preserve execution order sesuai DAG
- Log semua aktivitas untuk debugging

Jalankan: python -m core.engine
"""

import asyncio
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from shared_memory import SharedMemory, AgentKey, DAG
from schemas import AgentStatus, AgentOutput

logger = logging.getLogger(__name__)


class DependencyEngine:
    """
    Main orchestrator untuk menjalankan semua agents sesuai DAG.
    
    Flow:
    1. Check which agents can run (dependencies satisfied)
    2. Run executable agents in parallel (await all)
    3. Move to next layer
    4. Repeat sampai semua selesai atau ada error
    """

    def __init__(self, memory: SharedMemory, max_retries: int = 2):
        """
        Args:
            memory: SharedMemory instance untuk menyimpan state
            max_retries: Berapa kali retry jika agent gagal
        """
        self.memory = memory
        self.max_retries = max_retries
        self.agent_registry: Dict[AgentKey, Callable] = {}
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging untuk engine."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def register_agent(self, agent_key: AgentKey, agent_func: Callable) -> None:
        """
        Register agent function ke registry.
        
        Args:
            agent_key: AgentKey dari agent
            agent_func: Async function yang mengeksekusi agent
                       Signature: async def agent_func(memory: SharedMemory) -> AgentOutput
        """
        if not asyncio.iscoroutinefunction(agent_func):
            raise ValueError(f"Agent function harus async: {agent_key}")
        self.agent_registry[agent_key] = agent_func
        logger.info(f"Registered agent: {agent_key}")

    async def execute_agent(
        self,
        agent_key: AgentKey,
        retry_count: int = 0
    ) -> AgentOutput:
        """
        Execute single agent dengan retry logic.
        
        Args:
            agent_key: AgentKey dari agent yang mau dijalankan
            retry_count: Current retry attempt (internal use)
        
        Returns:
            AgentOutput dari agent
        """
        if agent_key not in self.agent_registry:
            raise ValueError(f"Agent tidak terdaftar: {agent_key}")

        agent_func = self.agent_registry[agent_key]

        try:
            logger.info(f"▶️  Starting {agent_key.value}...")
            result = await agent_func(self.memory)
            logger.info(f"✅ Completed {agent_key.value}")
            return result

        except Exception as e:
            logger.error(f"❌ {agent_key.value} failed: {str(e)}")
            
            if retry_count < self.max_retries:
                logger.info(f"🔄 Retrying {agent_key.value} (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** retry_count)  # exponential backoff
                return await self.execute_agent(agent_key, retry_count + 1)
            else:
                # Return error output
                return AgentOutput(
                    agent_name=agent_key.value,
                    status=AgentStatus.FAILED,
                    error_message=f"Agent failed after {self.max_retries} retries: {str(e)}"
                )

    async def run_all(self) -> Dict[AgentKey, AgentOutput]:
        """
        Execute semua agents sesuai DAG.
        
        Returns:
            Dict mapping AgentKey -> AgentOutput untuk semua agents
        """
        results = {}
        completed_agents = set()

        logger.info("🚀 Starting DAG execution...")
        logger.info(f"Total agents: {len(DAG)}")

        while len(completed_agents) < len(DAG):
            # Find executable agents
            executable = []
            for agent_key, deps in DAG.items():
                if agent_key not in completed_agents:
                    # Check if all deps are completed
                    if all(dep in completed_agents for dep in deps):
                        executable.append(agent_key)

            if not executable:
                logger.warning("🚨 Deadlock detected! No executable agents but not all completed.")
                logger.warning(f"Completed: {completed_agents}")
                logger.warning(f"Remaining: {set(DAG.keys()) - completed_agents}")
                break

            # Execute all executable agents in parallel
            logger.info(f"📍 Layer: Executing {len(executable)} agents: {[a.value for a in executable]}")
            
            tasks = [self.execute_agent(agent_key) for agent_key in executable]
            layer_results = await asyncio.gather(*tasks)

            # Store results
            for agent_key, result in zip(executable, layer_results):
                results[agent_key] = result
                self.memory.set(agent_key, result)
                completed_agents.add(agent_key)
                logger.info(f"  └─ {agent_key.value}: {result.status.value}")

        logger.info("✨ DAG execution completed!")
        return results

    def get_summary(self, results: Dict[AgentKey, AgentOutput]) -> Dict[str, Any]:
        """
        Get summary dari execution results.
        
        Returns:
            Dict dengan success count, failure count, timing, etc.
        """
        total = len(results)
        succeeded = sum(1 for r in results.values() if r.status == AgentStatus.DONE)
        failed = sum(1 for r in results.values() if r.status == AgentStatus.FAILED)

        return {
            "total_agents": total,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": (succeeded / total * 100) if total > 0 else 0,
            "timestamp": datetime.utcnow().isoformat()
        }


async def main():
    """Example usage (untuk testing)."""
    print("⚙️  DependencyEngine loaded.")
    print("✅ Ready for agent registration & execution")


if __name__ == "__main__":
    asyncio.run(main())
