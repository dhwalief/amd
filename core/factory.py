from langchain_openai import ChatOpenAI
from config.config import AGENT_CONFIG

def create_llm(agent_key: str, temperature: float = 0.7, timeout: int = 120, **kwargs):
    """
    Fungsi untuk membuat instance ChatOpenAI berdasarkan config.py
    """
    if agent_key not in AGENT_CONFIG:
        raise ValueError(f"Agen '{agent_key}' tidak ditemukan di konfigurasi.")

    config = AGENT_CONFIG[agent_key]

    return ChatOpenAI(
        base_url=config["base_url"],
        api_key="EMPTY",  # vLLM lokal tidak butuh API Key
        model=config["model"],
        temperature=temperature,
        timeout=kwargs.get('request_timeout', timeout),
        max_retries=2
    )
