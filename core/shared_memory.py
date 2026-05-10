# Contoh

"""
shared_memory.py — Shared Memory Interface
==========================================
Dibuat oleh: Dev 1 (Ketua)
Dipakai oleh: SEMUA developer dan semua agent

ATURAN:
- Semua agent WAJIB pakai class ini untuk baca dan tulis data
- DILARANG pakai dict biasa, file JSON, atau variable global
- Satu key per agent — lihat KEY_MAP di bawah

CARA PAKAI:
    from shared_memory import SharedMemory, AgentKey
    memory = SharedMemory()

    # Tulis output
    memory.set(AgentKey.MARKET, market_output)

    # Baca output
    data = memory.get(AgentKey.MARKET, MarketOutput)

    # Cek apakah agent sudah selesai
    if memory.is_done(AgentKey.MARKET):
        ...

    # Cek apakah semua dependency terpenuhi
    if memory.deps_satisfied([AgentKey.GEO_ANALYST, AgentKey.COMPETITOR]):
        ...
"""

import json
import logging
from enum import Enum
from typing import Optional, Type, TypeVar
from datetime import datetime

# pyrefly: ignore [missing-import]
import redis
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from core.schemas import AgentStatus, AgentOutput

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=AgentOutput)


# ─────────────────────────────────────────────
# KEY MAP — satu key per agent, jangan karang sendiri
# ─────────────────────────────────────────────

class AgentKey(str, Enum):
    """
    Kunci resmi untuk setiap agent di shared memory.
    Semua developer wajib pakai enum ini — jangan hardcode string.
    
    SALAH  : memory.get("market")
    BENAR  : memory.get(AgentKey.MARKET, MarketOutput)
    """
    INQUISITOR        = "inquisitor"
    GEO_ANALYST       = "geo_analyst"
    COMPETITOR        = "competitor_scout"
    GROWTH_HACKER     = "growth_hacker"
    PRICING           = "pricing_strategist"
    USER_VALIDATION   = "user_validation"
    CFO               = "cfo"
    LEGAL             = "legal_compliance"
    PRODUCT_ARCHITECT = "product_architect"
    HR_PLANNER        = "hr_planner"
    SUPPLY_PLANNER    = "supply_planner"
    SOP_DESIGNER      = "sop_designer"
    CRITIC            = "critic"
    RISK_MANAGER      = "risk_manager"
    ORCHESTRATOR      = "orchestrator"


# ─────────────────────────────────────────────
# DEPENDENCY GRAPH — Python code, bukan LLM
# ─────────────────────────────────────────────

DAG: dict[AgentKey, list[AgentKey]] = {
    AgentKey.INQUISITOR:        [],
    AgentKey.GEO_ANALYST:       [AgentKey.INQUISITOR],
    AgentKey.COMPETITOR:        [AgentKey.INQUISITOR],
    AgentKey.GROWTH_HACKER:     [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR],
    AgentKey.PRICING:           [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR],
    AgentKey.USER_VALIDATION:   [AgentKey.GROWTH_HACKER, AgentKey.PRICING],
    AgentKey.CFO:               [AgentKey.USER_VALIDATION],
    AgentKey.LEGAL:             [AgentKey.CFO, AgentKey.USER_VALIDATION],
    AgentKey.PRODUCT_ARCHITECT: [AgentKey.USER_VALIDATION],
    AgentKey.HR_PLANNER:        [AgentKey.CFO],
    AgentKey.SUPPLY_PLANNER:    [AgentKey.CFO],
    AgentKey.SOP_DESIGNER:      [AgentKey.PRODUCT_ARCHITECT,
                                  AgentKey.HR_PLANNER,
                                  AgentKey.SUPPLY_PLANNER],
    AgentKey.CRITIC:            [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR,
                                  AgentKey.GROWTH_HACKER, AgentKey.PRICING,
                                  AgentKey.USER_VALIDATION,
                                  AgentKey.CFO, AgentKey.LEGAL,
                                  AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER,
                                  AgentKey.SUPPLY_PLANNER, AgentKey.SOP_DESIGNER],
    AgentKey.RISK_MANAGER:      [AgentKey.CRITIC],
    AgentKey.ORCHESTRATOR:      [AgentKey.CRITIC, AgentKey.RISK_MANAGER],
}


# ─────────────────────────────────────────────
# SHARED MEMORY CLASS
# ─────────────────────────────────────────────

class SharedMemory:
    """
    Interface terpusat untuk semua agent.
    Backed by Redis — satu instance Redis untuk seluruh sistem.
    
    Untuk development / testing tanpa Redis, pakai MockSharedMemory di bawah.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        session_id: Optional[str] = None,
    ):
        """
        Args:
            host: Redis host. Di Docker Compose pakai "shared-memory".
            port: Redis port. Default 6379.
            session_id: ID unik per user session. Kalau None, pakai "default".
                        Penting supaya dua user tidak saling overwrite state.
        """
        self.redis = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )
        self.session_id = session_id or "default"
        self._verify_connection()

    def _verify_connection(self):
        try:
            self.redis.ping()
            logger.info(f"SharedMemory connected — session: {self.session_id}")
        except redis.ConnectionError:
            raise RuntimeError(
                "Tidak bisa konek ke Redis. "
                "Pastikan container 'shared-memory' sudah jalan.\n"
                "Jalankan: docker compose up shared-memory -d"
            )

    def _key(self, agent_key: AgentKey) -> str:
        """Internal: buat full Redis key dengan session prefix."""
        return f"{self.session_id}:{agent_key.value}"

    def _status_key(self, agent_key: AgentKey) -> str:
        return f"{self.session_id}:{agent_key.value}:status"

    # ── TULIS ──────────────────────────────────

    def set(self, key: AgentKey, output: AgentOutput) -> None:
        """
        Simpan output agent ke shared memory.
        Otomatis set status = DONE dan catat timestamp.
        
        Contoh:
            memory.set(AgentKey.MARKET, market_output)
        """
        output.status = AgentStatus.DONE
        output.completed_at = datetime.utcnow().isoformat()

        self.redis.set(self._key(key), output.model_dump_json())
        self.redis.set(self._status_key(key), AgentStatus.DONE.value)

        logger.info(f"[{self.session_id}] {key.value} → DONE")

    def set_status(self, key: AgentKey, status: AgentStatus) -> None:
        """
        Update status agent tanpa menulis output.
        Dipakai Orchestrator untuk tandai agent sebagai RUNNING atau LOCKED.
        
        Contoh:
            memory.set_status(AgentKey.MARKET, AgentStatus.RUNNING)
        """
        self.redis.set(self._status_key(key), status.value)
        logger.info(f"[{self.session_id}] {key.value} → {status.value}")

    def set_failed(self, key: AgentKey, error: str) -> None:
        """
        Tandai agent sebagai FAILED dengan pesan error.
        
        Contoh:
            memory.set_failed(AgentKey.CFO, "LLM timeout setelah 60 detik")
        """
        self.redis.set(self._status_key(key), AgentStatus.FAILED.value)
        self.redis.set(f"{self._key(key)}:error", error)
        logger.error(f"[{self.session_id}] {key.value} → FAILED: {error}")

    # ── BACA ──────────────────────────────────

    def get(self, key: AgentKey, model: Type[T]) -> Optional[T]:
        """
        Baca output agent dari shared memory.
        Return None kalau agent belum selesai atau belum pernah jalan.
        
        Contoh:
            market = memory.get(AgentKey.MARKET, MarketOutput)
            if market:
                ideas = market.business_ideas
        """
        raw = self.redis.get(self._key(key))
        if not raw:
            return None
        try:
            return model.model_validate_json(raw)
        except Exception as e:
            logger.error(f"Gagal parse output {key.value}: {e}")
            return None

    def get_status(self, key: AgentKey) -> AgentStatus:
        """
        Baca status agent saat ini.
        Return PENDING kalau agent belum pernah diset.
        """
        raw = self.redis.get(self._status_key(key))
        if not raw:
            return AgentStatus.PENDING
        try:
            return AgentStatus(raw)
        except ValueError:
            return AgentStatus.PENDING

    def get_error(self, key: AgentKey) -> Optional[str]:
        """Baca pesan error agent yang FAILED."""
        return self.redis.get(f"{self._key(key)}:error")

    # ── CEK STATUS ────────────────────────────

    def is_done(self, key: AgentKey) -> bool:
        """Apakah agent sudah selesai dengan sukses?"""
        return self.get_status(key) == AgentStatus.DONE

    def is_failed(self, key: AgentKey) -> bool:
        """Apakah agent gagal?"""
        return self.get_status(key) == AgentStatus.FAILED

    def deps_satisfied(self, key: AgentKey) -> bool:
        """
        Cek apakah semua dependency agent ini sudah DONE.
        Dipakai Orchestrator sebelum dispatch agent.
        
        Contoh:
            if memory.deps_satisfied(AgentKey.CFO):
                dispatch(cfo_agent)
        """
        deps = DAG.get(key, [])
        return all(self.is_done(dep) for dep in deps)

    def get_ready_agents(self) -> list[AgentKey]:
        """
        Kembalikan semua agent yang siap dijalankan:
        - dependency-nya sudah DONE
        - statusnya masih PENDING atau LOCKED
        
        Dipakai Orchestrator untuk tahu agent mana yang bisa di-dispatch sekarang.
        """
        ready = []
        for agent_key, deps in DAG.items():
            status = self.get_status(agent_key)
            if status in (AgentStatus.PENDING, AgentStatus.LOCKED):
                if all(self.is_done(dep) for dep in deps):
                    ready.append(agent_key)
        return ready

    # ── UTILITAS ──────────────────────────────

    def snapshot(self) -> dict:
        """
        Kembalikan snapshot status semua agent.
        Berguna untuk debug dan display progress ke user.
        
        Contoh output:
            {
                "inquisitor": "done",
                "geo_analyst": "running",
                "competitor_scout": "pending",
                ...
            }
        """
        return {
            key.value: self.get_status(key).value
            for key in AgentKey
        }

    def reset(self) -> None:
        """
        Hapus semua data session ini dari Redis.
        Dipakai untuk mulai session baru atau reset saat testing.
        
        ⚠️ Hati-hati — ini hapus semua output agent untuk session ini.
        """
        pattern = f"{self.session_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
        logger.info(f"Session {self.session_id} direset.")


# ─────────────────────────────────────────────
# MOCK — untuk development tanpa Redis
# ─────────────────────────────────────────────

class MockSharedMemory(SharedMemory):
    """
    Versi in-memory tanpa Redis.
    Dipakai saat development lokal sebelum Docker siap.

    CARA PAKAI — ganti import di agent kalian:
        # Kalau Redis belum siap:
        from shared_memory import MockSharedMemory as SharedMemory

        # Kalau Redis sudah siap (production / demo):
        from shared_memory import SharedMemory
    """

    def __init__(self, session_id: Optional[str] = None):
        # Sengaja tidak panggil super().__init__() — tidak butuh Redis
        self.session_id = session_id or "mock"
        self._store: dict[str, str] = {}
        logger.warning("MockSharedMemory aktif — data tidak persisten, tidak pakai Redis")

    def _verify_connection(self):
        pass  # tidak ada koneksi yang perlu diverifikasi

    def set(self, key: AgentKey, output: AgentOutput) -> None:
        output.status = AgentStatus.DONE
        output.completed_at = datetime.utcnow().isoformat()
        self._store[self._key(key)] = output.model_dump_json()
        self._store[self._status_key(key)] = AgentStatus.DONE.value
        logger.info(f"[MOCK][{self.session_id}] {key.value} → DONE")

    def set_status(self, key: AgentKey, status: AgentStatus) -> None:
        self._store[self._status_key(key)] = status.value

    def set_failed(self, key: AgentKey, error: str) -> None:
        self._store[self._status_key(key)] = AgentStatus.FAILED.value
        self._store[f"{self._key(key)}:error"] = error

    def get(self, key: AgentKey, model: Type[T]) -> Optional[T]:
        raw = self._store.get(self._key(key))
        if not raw:
            return None
        return model.model_validate_json(raw)

    def get_status(self, key: AgentKey) -> AgentStatus:
        raw = self._store.get(self._status_key(key))
        if not raw:
            return AgentStatus.PENDING
        return AgentStatus(raw)

    def get_error(self, key: AgentKey) -> Optional[str]:
        return self._store.get(f"{self._key(key)}:error")

    def reset(self) -> None:
        self._store.clear()
        logger.info(f"MockSharedMemory session {self.session_id} direset.")
