import logging
from core.shared_memory import SharedMemory, AgentKey, DAG
from core.schemas import AgentStatus, AgentOutput

logger = logging.getLogger(__name__)

def check_agent_ready(memory: SharedMemory, agent_key: AgentKey) -> bool:
    """
    Mengecek apakah semua dependency untuk agent tersebut sudah berstatus DONE di memory.
    
    Fungsi ini membaca DAG dari shared_memory dan mengecek status output masing-masing agent dependency.
    
    Args:
        memory (SharedMemory): Instance memory tempat data/state tersimpan.
        agent_key (AgentKey): Key dari agent yang akan dicek.
        
    Returns:
        bool: True jika tidak ada dependency atau semua dependency berstatus DONE. False jika belum siap.
        
    Contoh:
        >>> check_agent_ready(memory, AgentKey.GEO_ANALYST)
        True
    """
    dependencies = DAG.get(agent_key, [])
    
    if not dependencies:
        return True
        
    for dep in dependencies:
        # Cek apakah output dari tiap dependency ada di memory dan berstatus DONE
        output = memory.get(dep, AgentOutput)
        if not output or output.status != AgentStatus.DONE:
            return False
            
    return True


def get_blocked_agents(memory: SharedMemory) -> list[AgentKey]:
    """
    Mendapatkan daftar agent yang belum bisa dieksekusi karena ada dependency 
    (prasyarat) yang belum selesai (belum DONE).
    
    Args:
        memory (SharedMemory): Instance memory.
        
    Returns:
        list[AgentKey]: Daftar agent yang berstatus PENDING/LOCKED dan belum siap jalan.
    """
    blocked_agents = []
    
    for agent_key in DAG.keys():
        output = memory.get(agent_key, AgentOutput)
        
        # Agent yang belum masuk memory atau masih berstatus PENDING/LOCKED
        if not output or output.status in [AgentStatus.PENDING, AgentStatus.LOCKED]:
            if not check_agent_ready(memory, agent_key):
                blocked_agents.append(agent_key)
                
    return blocked_agents


def get_ready_agents(memory: SharedMemory) -> list[AgentKey]:
    """
    Mendapatkan daftar agent yang semua dependency-nya sudah berstatus DONE
    dan agent tersebut siap untuk dieksekusi (belum pernah dijalankan).
    
    Args:
        memory (SharedMemory): Instance memory.
        
    Returns:
        list[AgentKey]: Daftar agent yang sudah bebas hambatan dan bisa dieksekusi.
    """
    ready_agents = []
    
    for agent_key in DAG.keys():
        output = memory.get(agent_key, AgentOutput)
        
        # Jika belum dieksekusi sama sekali atau masih PENDING/LOCKED
        if not output or output.status in [AgentStatus.PENDING, AgentStatus.LOCKED]:
            if check_agent_ready(memory, agent_key):
                ready_agents.append(agent_key)
                
    return ready_agents


def get_execution_summary(memory: SharedMemory) -> dict:
    """
    Mengambil ringkasan dari status eksekusi semua agent yang ada di dalam DAG.
    
    Args:
        memory (SharedMemory): Instance memory.
        
    Returns:
        dict: Dictionary statistik status agent yang memuat "total", "done", "running", dll.
    """
    summary = {
        "total": len(DAG),
        "done": 0,
        "running": 0,
        "pending": 0,
        "failed": 0,
        "locked": 0,
        "ready_to_run": [key.value for key in get_ready_agents(memory)]
    }
    
    for agent_key in DAG.keys():
        output = memory.get(agent_key, AgentOutput)
        
        if not output:
            # Belum ada record di memory, bisa pending (siap) atau locked (menunggu)
            if check_agent_ready(memory, agent_key):
                summary["pending"] += 1
            else:
                summary["locked"] += 1
        else:
            status = output.status
            if status == AgentStatus.DONE:
                summary["done"] += 1
            elif status == AgentStatus.RUNNING:
                summary["running"] += 1
            elif status == AgentStatus.FAILED:
                summary["failed"] += 1
            elif status == AgentStatus.PENDING:
                summary["pending"] += 1
            elif status == AgentStatus.LOCKED:
                summary["locked"] += 1
                
    return summary


def print_dependency_tree(agent_key: AgentKey) -> None:
    """
    Mencetak dependency tree dari suatu agent ke console (stdout).
    
    Args:
        agent_key (AgentKey): Agent yang ingin diprint dependency-nya.
    """
    dependencies = DAG.get(agent_key, [])
    dep_names = [dep.value for dep in dependencies]
    
    if not dep_names:
        print(f"{agent_key.value} -> [Tidak ada dependency]")
    else:
        print(f"{agent_key.value} -> [{', '.join(dep_names)}]")
