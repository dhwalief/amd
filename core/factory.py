"""
factory.py — LLM Connector Factory
==================================

Dibuat untuk mempermudah dan menyederhanakan inisialisasi ChatOpenAI
bagi seluruh agent. Factory ini membaca AGENT_CONFIG dan secara otomatis
menggunakan "EMPTY" API key yang dibutuhkan oleh local vLLM.

CARA PAKAI:
    from core.factory import create_llm
    
    # Buat instance LLM untuk analyst pool dengan temperature tertentu
    llm = create_llm("analyst_pool", temperature=0.4)
    
    # Langsung pakai dengan langchain
    chain = prompt | llm
"""

import logging
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI

from config.config import AGENT_CONFIG

logger = logging.getLogger(__name__)

def create_llm(agent_key: str, temperature: float = 0.7, timeout: int = 120) -> ChatOpenAI:
    """
    Membuat dan mengembalikan instance ChatOpenAI berdasarkan key di AGENT_CONFIG.
    
    Args:
        agent_key (str): Key yang sesuai dengan entri di config.py (misal: "analyst_pool", "cfo", "orchestrator").
        temperature (float, optional): Tingkat kreativitas/keacakan model. Default 0.7.
        timeout (int, optional): Batas waktu request dalam detik. Default 120.
        
    Returns:
        ChatOpenAI: Instance model langchain yang siap dipakai dengan invoke() atau LCEL.
        
    Raises:
        ValueError: Jika agent_key tidak ditemukan di dalam AGENT_CONFIG.
    """
    
    if agent_key not in AGENT_CONFIG:
        error_msg = f"agent_key '{agent_key}' tidak ditemukan di AGENT_CONFIG. Pastikan key tersebut terdaftar di config/config.py."
        logger.error(error_msg)
        raise ValueError(error_msg)
        
    config = AGENT_CONFIG[agent_key]
    
    logger.debug(f"Menginisialisasi LLM untuk '{agent_key}' -> model: {config.get('model')} | base_url: {config.get('base_url')}")
    
    return ChatOpenAI(
        base_url=config["base_url"],
        model=config["model"],
        temperature=temperature,
        timeout=timeout,
        max_retries=2,
        api_key="EMPTY"  # vLLM lokal tidak butuh API key asli
    )
