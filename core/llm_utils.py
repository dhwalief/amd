"""
core/llm_utils.py — Shared LLM Utility Functions
===================================================
Menyediakan fungsi-fungsi bersama untuk:
- Parsing JSON dari output LLM (dengan retry + strip thinking tags)
- Menangani respons kosong / malformed
"""

import json
import re
import logging
import asyncio
from typing import Any, Optional

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str) -> str:
    """
    Bersihkan dan ekstrak JSON murni dari respons LLM.
    Menangani:
    - Thinking tags: <think>...</think> dari Qwen3
    - Markdown code blocks: ```json ... ``` atau ``` ... ```
    - Teks ekstra sebelum/sesudah JSON
    """
    if not content:
        return ""

    # 1. Hapus thinking tags (Qwen3 / o1-style)
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    content = content.strip()

    # 2. Hapus markdown code blocks
    if content.startswith("```json"):
        content = content[7:]
        end = content.rfind("```")
        if end != -1:
            content = content[:end]
    elif content.startswith("```"):
        content = content[3:]
        end = content.rfind("```")
        if end != -1:
            content = content[:end]

    content = content.strip()

    # 3. Kalau masih ada teks ekstra sebelum JSON, cari { atau [
    if content and content[0] not in ("{", "["):
        # Cari JSON object atau array pertama
        match = re.search(r"(\{|\[)", content)
        if match:
            content = content[match.start():]

    return content


async def invoke_with_retry(
    llm,
    prompt: str,
    max_retries: int = 3,
    delay_seconds: float = 2.0,
    agent_name: str = "unknown",
) -> Optional[str]:
    """
    Panggil LLM dengan retry otomatis jika respons kosong atau gagal.
    Return string konten LLM yang sudah dibersihkan, atau None jika semua retry gagal.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = await llm.ainvoke(prompt)
            raw = response.content if hasattr(response, "content") else str(response)
            content = extract_json_from_response(raw)
            if content:
                return content
            logger.warning(
                f"[{agent_name}] Attempt {attempt}/{max_retries}: LLM returned empty content. Retrying..."
            )
        except Exception as e:
            logger.warning(f"[{agent_name}] Attempt {attempt}/{max_retries}: LLM error: {e}")

        if attempt < max_retries:
            await asyncio.sleep(delay_seconds)

    logger.error(f"[{agent_name}] All {max_retries} attempts failed. Returning None.")
    return None


def safe_parse_json(content: str, agent_name: str = "unknown") -> Optional[dict]:
    """
    Parse JSON string dengan error handling yang ramah.
    Return dict/list atau None jika gagal.
    """
    if not content:
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"[{agent_name}] JSON parse error: {e} | Content preview: {content[:200]!r}")
        return None
