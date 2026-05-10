import asyncio
import logging
from typing import Callable

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import AgentStatus, AgentOutput

logger = logging.getLogger(__name__)

class DependencyEngine:
    """
    Engine untuk mengelola dan menjalankan semua agen secara asinkron
    berdasarkan urutan dependensi (DAG) yang telah disiapkan di SharedMemory.
    """
    def __init__(self, memory: SharedMemory):
        self.memory = memory
        self.registry: dict[AgentKey, Callable] = {}
        
    def register_agent(self, key: AgentKey, run_func: Callable):
        """Mendaftarkan fungsi agen ke dalam eksekutor."""
        self.registry[key] = run_func
        
    async def run_all(self) -> dict[AgentKey, AgentOutput]:
        """
        Mengeksekusi semua agen yang terdaftar dengan mengecek ketersediaan dependensi
        menggunakan logika asyncio. Agen akan diblokir dari antrean jika dependensinya
        masih belum selesai.
        """
        results = {}
        tasks = {}
        
        while True:
            # Dapatkan semua agen yang ready dari SharedMemory
            ready_agents = self.memory.get_ready_agents()
            
            # Start agen yang baru ready dan belum berjalan
            for key in ready_agents:
                if key in self.registry and key not in tasks:
                    self.memory.set_status(key, AgentStatus.RUNNING)
                    run_func = self.registry[key]
                    logger.info(f"Dispatching agent: {key.value}")
                    # Eksekusi fungsi run agent
                    tasks[key] = asyncio.create_task(run_func(self.memory))
            
            if not tasks:
                # Jika tidak ada tasks yang berjalan, cek status antrean
                ready_agents = self.memory.get_ready_agents()
                virtual_nodes = [k for k in ready_agents if k not in self.registry]
                
                unexecuted = set(self.registry.keys()) - set(results.keys())
                
                if virtual_nodes:
                    logger.info(f"Engine paused at virtual nodes: {[v.value for v in virtual_nodes]}. Menunggu eksekusi manual / intervensi user.")
                    break
                elif unexecuted:
                    logger.warning(f"Engine selesai tetapi ada agen yang stuck (tidak terpenuhi dependensinya): {unexecuted}")
                    break
                else:
                    logger.info("Engine selesai: semua task tereksekusi.")
                    break
                
            # Tunggu setidaknya satu task selesai
            done, pending = await asyncio.wait(
                tasks.values(), 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Proses task yang selesai
            for t in done:
                # Cari key dari task
                key = next(k for k, v in tasks.items() if v == t)
                try:
                    result = t.result()
                    if isinstance(result, AgentOutput):
                        # memory.set sudah memanggil output.status = DONE secara internal
                        self.memory.set(key, result)
                    else:
                        logger.error(f"Agent {key.value} did not return AgentOutput.")
                        self.memory.set_failed(key, "Invalid return type")
                    results[key] = result
                except Exception as e:
                    logger.error(f"Agent {key.value} failed: {e}")
                    self.memory.set_failed(key, str(e))
                
                # Hapus dari dict task yang aktif
                del tasks[key]
                
        return results

    def get_summary(self, results: dict) -> dict:
        """Mengembalikan rekap performa / hasil eksekusi run_all."""
        summary = {
            "total_executed": len(results),
            "success": sum(1 for r in results.values() if getattr(r, 'status', None) == AgentStatus.DONE),
            "failed": sum(1 for r in results.values() if getattr(r, 'status', None) == AgentStatus.FAILED),
        }
        return summary
