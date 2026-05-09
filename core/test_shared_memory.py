"""
test_shared_memory.py — Unit Tests untuk SharedMemory
=====================================================

CATATAN:
- Gunakan MockSharedMemory untuk testing (tidak perlu Redis running)
- Nanti untuk production, ganti dengan real Redis

Jalankan: pytest test_shared_memory.py -v
"""

import pytest
from datetime import datetime
from core.schemas import AgentOutput, AgentStatus, BusinessContext, InquisitorOutput
from core.shared_memory import AgentKey, MockSharedMemory, DAG


class TestMockSharedMemory:
    """Test suite untuk MockSharedMemory implementation."""

    @pytest.fixture
    def memory(self):
        """Setup mock shared memory untuk setiap test."""
        return MockSharedMemory()

    def test_set_and_get_basic(self, memory):
        """Test: set & get output dari agent."""
        output = InquisitorOutput(
            business_context=BusinessContext(
                location="Jakarta, Indonesia",
                budget=50_000_000,
                skills=["cooking", "management"],
                existing_assets=["motor"],
            )
        )
        
        # Set output
        memory.set(AgentKey.INQUISITOR, output)
        
        # Get output
        retrieved = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        assert retrieved.agent_name == "inquisitor"
        assert retrieved.business_context.location == "Jakarta, Indonesia"

    def test_is_done(self, memory):
        """Test: check if agent is done."""
        assert not memory.is_done(AgentKey.GEO_ANALYST)
        
        output = InquisitorOutput(
            business_context=BusinessContext(
                location="Jakarta",
                budget=50_000_000,
                skills=["cooking"],
                existing_assets=[],
            )
        )
        memory.set(AgentKey.INQUISITOR, output)
        
        assert memory.is_done(AgentKey.INQUISITOR)

    def test_deps_satisfied(self, memory):
        """Test: check if all dependencies are satisfied."""
        # Inquisitor has no deps, harus bisa langsung execute
        assert memory.deps_satisfied([])
        
        # GEO_ANALYST depends on INQUISITOR
        assert not memory.deps_satisfied(DAG[AgentKey.GEO_ANALYST])
        
        # Set INQUISITOR as done
        output = InquisitorOutput(
            business_context=BusinessContext(
                location="Jakarta",
                budget=50_000_000,
                skills=["cooking"],
                existing_assets=[],
            )
        )
        memory.set(AgentKey.INQUISITOR, output)
        
        # Now GEO_ANALYST deps should be satisfied
        assert memory.deps_satisfied(DAG[AgentKey.GEO_ANALYST])

    def test_list_executable_agents(self, memory):
        """Test: list agents yang bisa dijalankan sekarang."""
        # Only INQUISITOR pada awalnya
        executable = memory.get_executable_agents(DAG)
        assert AgentKey.INQUISITOR in executable
        assert AgentKey.GEO_ANALYST not in executable
        
        # Setelah INQUISITOR selesai, GEO_ANALYST & COMPETITOR bisa jalan
        output = InquisitorOutput(
            business_context=BusinessContext(
                location="Jakarta",
                budget=50_000_000,
                skills=["cooking"],
                existing_assets=[],
            )
        )
        memory.set(AgentKey.INQUISITOR, output)
        
        executable = memory.get_executable_agents(DAG)
        assert AgentKey.GEO_ANALYST in executable
        assert AgentKey.COMPETITOR in executable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
