import os
from dotenv import load_dotenv

load_dotenv()

NODE_DHIWA  = os.getenv("NODE_DHIWA")   # orchestrator-72b
NODE_AMITHA = os.getenv("NODE_AMITHA")  # DeepSeek-R1-Distill-Llama-70B
NODE_AFIQA  = os.getenv("NODE_AFIQA")  # qwen3-32b, r1-distill-14b
NODE_AHMAD  = os.getenv("NODE_AHMAD")  # qwen2.5-14b, 7b, 3b

AGENT_CONFIG = {

    # --- MESIN DHIWA ---
    "orchestrator": {
        "base_url": f"http://{NODE_DHIWA}:8000/v1",
        "model": "Qwen/Qwen2.5-72B-Instruct"
    },

    # --- MESIN AMITHA ---
    "risk_manager": {
        "base_url": f"http://{NODE_AMITHA}:8000/v1",
        "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
    },

    # --- MESIN AFIQA ---
    "critic": {
        "base_url": f"http://{NODE_AFIQA}:8000/v1",
        "model": "Qwen/Qwen3-32B"
    },
    "cfo": {
        "base_url": f"http://{NODE_AFIQA}:8002/v1",
        "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
    },

    # --- MESIN AHMAD ---
    # Geo Analyst, Growth Hacker, Legal & Compliance, Pricing Strategist
    "analyst_pool": {
        "base_url": f"http://{NODE_AHMAD}:8000/v1",
        "model": "Qwen/Qwen2.5-14B-Instruct"
    },
    # Inquisitor, Competitor Scout
    "scout_inquisitor_pool": {
        "base_url": f"http://{NODE_AHMAD}:8001/v1",
        "model": "Qwen/Qwen2.5-7B-Instruct"
    },
    # Product Architect, HR Planner, SOP Designer
    "worker_pool": {
        "base_url": f"http://{NODE_AHMAD}:8002/v1",
        "model": "Qwen/Qwen2.5-3B-Instruct"
    },
}