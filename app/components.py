"""
components.py — Reusable UI Components untuk Streamlit
======================================================

Kerjaan Dev2 di Week 1 Phase 1.

Fungsi:
1. DAG visualization (dependency graph)
2. Status indicator cards
3. Agent result display
4. Progress tracking

Dipakai oleh: app/dashboard.py, app/reports.py
"""

import logging
import streamlit as st
from typing import Dict, List, Optional

from shared_memory import AgentKey, DAG
from schemas import AgentStatus, AgentOutput

logger = logging.getLogger(__name__)


def display_dag_status(status_dict: Dict[str, str]) -> None:
    """
    Display DAG dengan status setiap agent menggunakan Streamlit columns.
    
    Args:
        status_dict: Dict mapping agent_key -> status (dari memory.snapshot())
    
    Contoh status_dict:
        {
            "inquisitor": "done",
            "geo_analyst": "running",
            "competitor_scout": "done",
            ...
        }
    """
    st.subheader("📊 Agent Execution Status")
    
    # Color mapping
    color_map = {
        "done": "🟢",
        "running": "🟡",
        "pending": "⚪",
        "failed": "🔴",
        "locked": "🔵",
    }
    
    # Display di 3 columns (Layer Executive, Analyst, Worker)
    col1, col2, col3 = st.columns(3)
    
    # Executive Layer
    with col1:
        st.write("**Executive Layer**")
        for agent_key in [AgentKey.ORCHESTRATOR, AgentKey.CRITIC, AgentKey.RISK_MANAGER]:
            status = status_dict.get(agent_key.value, "pending")
            emoji = color_map.get(status, "❓")
            st.write(f"{emoji} {agent_key.value}: {status}")
    
    # Analyst Layer
    with col2:
        st.write("**Analyst Layer**")
        analyst_agents = [
            AgentKey.GEO_ANALYST, AgentKey.COMPETITOR, AgentKey.GROWTH_HACKER,
            AgentKey.CFO, AgentKey.PRICING
        ]
        for agent_key in analyst_agents:
            status = status_dict.get(agent_key.value, "pending")
            emoji = color_map.get(status, "❓")
            st.write(f"{emoji} {agent_key.value}: {status}")
    
    # Worker Layer
    with col3:
        st.write("**Worker Layer**")
        worker_agents = [
            AgentKey.INQUISITOR, AgentKey.LEGAL, AgentKey.PRODUCT_ARCHITECT,
            AgentKey.HR_PLANNER, AgentKey.SUPPLY_PLANNER, AgentKey.SOP_DESIGNER
        ]
        for agent_key in worker_agents:
            status = status_dict.get(agent_key.value, "pending")
            emoji = color_map.get(status, "❓")
            st.write(f"{emoji} {agent_key.value}: {status}")


def display_agent_output(
    agent_name: str,
    output: Optional[AgentOutput],
    expanded: bool = False
) -> None:
    """
    Display single agent output dalam expandable container.
    
    Args:
        agent_name: Nama agent untuk display
        output: AgentOutput object (atau None jika belum selesai)
        expanded: Apakah default-nya expanded atau collapsed
    """
    if not output:
        st.info(f"⏳ {agent_name}: Belum dijalankan")
        return
    
    # Status color
    if output.status == AgentStatus.DONE:
        status_emoji = "✅"
        status_color = "green"
    elif output.status == AgentStatus.FAILED:
        status_emoji = "❌"
        status_color = "red"
    else:
        status_emoji = "🔄"
        status_color = "orange"
    
    with st.expander(
        f"{status_emoji} {agent_name} — {output.status.value}",
        expanded=expanded
    ):
        st.json(output.model_dump())


def display_progress_bar(
    completed: int,
    total: int,
    label: str = "Progress"
) -> None:
    """
    Display progress bar dengan percentage.
    
    Args:
        completed: Jumlah agents yang selesai
        total: Total jumlah agents
        label: Label untuk progress
    """
    progress = completed / total if total > 0 else 0
    st.progress(progress, text=f"{label}: {completed}/{total} ({progress*100:.0f}%)")


def display_error_alert(agent_name: str, error_msg: str) -> None:
    """
    Display error alert untuk agent yang gagal.
    
    Args:
        agent_name: Nama agent
        error_msg: Error message
    """
    st.error(f"❌ {agent_name} failed:\n\n{error_msg}")


def display_dependency_info(agent_key: AgentKey) -> None:
    """
    Display dependency requirements untuk specific agent.
    
    Args:
        agent_key: AgentKey
    """
    deps = DAG.get(agent_key, [])
    if not deps:
        st.caption("ℹ️ No dependencies — dapat dijalankan kapan saja")
    else:
        deps_str = ", ".join([dep.value for dep in deps])
        st.caption(f"ℹ️ Requires: {deps_str}")


if __name__ == "__main__":
    # Simple test
    st.set_page_config(page_title="Components Test", layout="wide")
    st.title("🧪 Component Test Page")
    
    # Test DAG status display
    test_status = {
        "inquisitor": "done",
        "geo_analyst": "running",
        "competitor_scout": "done",
        "growth_hacker": "pending",
        "pricing_strategist": "pending",
        "cfo": "pending",
        "legal_compliance": "pending",
        "product_architect": "pending",
        "hr_planner": "pending",
        "supply_planner": "pending",
        "sop_designer": "pending",
        "critic": "pending",
        "risk_manager": "pending",
        "orchestrator": "pending",
    }
    
    display_dag_status(test_status)
    
    st.divider()
    display_progress_bar(2, 14, "Example Progress")
