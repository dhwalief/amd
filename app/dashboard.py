"""
dashboard.py — Main Streamlit Dashboard
========================================

Kerjaan Dev2 di Week 2 Phase 2.

Flow:
1. User input business context via form
2. Submit untuk start DAG execution
3. Real-time status monitoring
4. Display hasil per agent
5. Export report

Jalankan: streamlit run app/dashboard.py
"""

import asyncio
import logging
import sys
import os
import threading
from datetime import datetime

# Tambahkan root directory ke PYTHONPATH agar bisa mengimpor 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from core.shared_memory import MockSharedMemory, AgentKey
from core.schemas import BusinessContext, InquisitorOutput, AgentStatus, AgentOutput
from app.components import display_dag_status, display_progress_bar, display_agent_output

logger = logging.getLogger(__name__)

def run_ai_in_background(memory):
    from agents.executive.orchestrator import setup_and_run
    import asyncio
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_and_run(memory))
        loop.close()
    except Exception as e:
        logger.error(f"Error in AI background thread: {e}")

# Streamlit page config
st.set_page_config(
    page_title="Go to America - Multi-Agent System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "memory" not in st.session_state:
    st.session_state.memory = MockSharedMemory(session_id="streamlit_demo")
    logger.info("Initialized session memory")

if "execution_started" not in st.session_state:
    st.session_state.execution_started = False

if "execution_results" not in st.session_state:
    st.session_state.execution_results = {}


# ────────────────────────────────────
# SIDEBAR — User Input Form
# ────────────────────────────────────

with st.sidebar:
    st.title("📝 Business Context")
    st.write("Fill in your business details below")
    
    # Input form
    location = st.text_input(
        "📍 Business Location",
        placeholder="e.g., Jakarta, Indonesia",
        value="Jakarta, Indonesia"
    )
    
    budget = st.number_input(
        "💰 Total Budget (IDR)",
        min_value=1_000_000,
        value=50_000_000,
        step=1_000_000,
    )
    
    skills = st.text_input(
        "🎯 Skills (comma-separated)",
        placeholder="e.g., cooking, management, design",
        value="cooking, management"
    )
    
    assets = st.text_input(
        "🏠 Existing Assets (comma-separated)",
        placeholder="e.g., motor, laptop, shop",
        value="motor, laptop"
    )
    
    business_idea = st.text_area(
        "💡 Business Idea (optional)",
        placeholder="Describe your idea if you have one...",
        height=100
    )
    
    sector = st.selectbox(
        "🏢 Preferred Sector",
        ["F&B", "Retail", "Services", "Technology", "Healthcare", "Other"]
    )
    
    target_income = st.number_input(
        "📊 Target Monthly Income (IDR)",
        min_value=0,
        value=5_000_000,
        step=500_000,
    )
    
    st.divider()
    
    # Submit button
    if st.button("🚀 Start Analysis", use_container_width=True, type="primary"):
        # Prepare business context
        context = BusinessContext(
            location=location,
            budget=budget,
            skills=[s.strip() for s in skills.split(",") if s.strip()],
            existing_assets=[a.strip() for a in assets.split(",") if a.strip()],
            business_idea=business_idea if business_idea else None,
            preferred_sector=sector if sector != "Other" else None,
            target_monthly_income=target_income if target_income > 0 else None,
        )
        
        # Store in memory
        output = InquisitorOutput(business_context=context)
        st.session_state.memory.set(AgentKey.INQUISITOR, output)
        st.session_state.execution_started = True
        
        # Start AI in background thread
        from streamlit.runtime.scriptrunner import add_script_run_ctx
        thread = threading.Thread(target=run_ai_in_background, args=(st.session_state.memory,))
        add_script_run_ctx(thread)
        thread.start()
        
        st.success("✅ Context stored! Starting agent execution...")


# ────────────────────────────────────
# MAIN AREA — Status & Results
# ────────────────────────────────────

st.title("🤖 Go to America - Multi-Agent System")
st.write("**AI-Powered Business Planning for Indonesia → Global Expansion**")

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Status", "📋 Results", "📄 Report"])

with tab1:
    st.subheader("Live Execution Status")
    
    if not st.session_state.execution_started:
        st.info("👉 Fill in the form on the left and click 'Start Analysis' to begin")
    else:
        # Get current status
        status_snapshot = st.session_state.memory.snapshot()
        
        # Calculate progress
        total_agents = len(status_snapshot)
        completed = sum(
            1 for status in status_snapshot.values()
            if status == AgentStatus.DONE.value
        )
        failed = sum(
            1 for status in status_snapshot.values()
            if status == AgentStatus.FAILED.value
        )
        
        # Display progress
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completed", completed, f"{total_agents}")
        with col2:
            st.metric("Failed", failed, "0")
        with col3:
            progress = (completed / total_agents * 100) if total_agents > 0 else 0
            st.metric("Progress", f"{progress:.0f}%", "")
        
        st.divider()
        
        # Display DAG status
        display_dag_status(status_snapshot)
        
        # Display progress bar
        st.divider()
        display_progress_bar(completed, total_agents, "Overall Progress")
        
        # Auto-refresh note
        st.caption("💡 Tip: Page auto-refreshes every 2 seconds during execution")


with tab2:
    st.subheader("Agent Results")
    
    if not st.session_state.execution_started:
        st.info("No execution started yet")
    else:
        # Display results untuk setiap agent
        status_snapshot = st.session_state.memory.snapshot()
        
        # Group by layer
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Executive Layer**")
            for agent_key in [AgentKey.ORCHESTRATOR, AgentKey.CRITIC, AgentKey.RISK_MANAGER]:
                if status_snapshot.get(agent_key.value) == "done":
                    st.success(f"✅ {agent_key.value}")
                    with st.expander(f"Lihat Hasil {agent_key.value}"):
                        output = st.session_state.memory.get(agent_key, AgentOutput)
                        display_agent_output(agent_key.value, output)
        
        with col2:
            st.write("**Analyst Layer**")
            for agent_key in [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR, AgentKey.GROWTH_HACKER, AgentKey.CFO, AgentKey.PRICING]:
                if status_snapshot.get(agent_key.value) == "done":
                    st.success(f"✅ {agent_key.value}")
                    with st.expander(f"Lihat Hasil {agent_key.value}"):
                        output = st.session_state.memory.get(agent_key, AgentOutput)
                        display_agent_output(agent_key.value, output)
        
        with col3:
            st.write("**Worker Layer**")
            for agent_key in [AgentKey.INQUISITOR, AgentKey.LEGAL, AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER, AgentKey.SOP_DESIGNER]:
                if status_snapshot.get(agent_key.value) == "done":
                    st.success(f"✅ {agent_key.value}")
                    with st.expander(f"Lihat Hasil {agent_key.value}"):
                        output = st.session_state.memory.get(agent_key, AgentOutput)
                        display_agent_output(agent_key.value, output)


with tab3:
    st.subheader("Business Plan Report")
    
    if not st.session_state.execution_started:
        st.info("Complete execution to generate report")
    else:
        st.write("Report akan generate otomatis setelah semua agents selesai")
        
        # TODO: Export buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export as Markdown"):
                st.write("📥 Export feature coming soon...")
        
        with col2:
            if st.button("📥 Export as PDF"):
                st.write("📥 PDF export coming soon...")


# ────────────────────────────────────
# FOOTER
# ────────────────────────────────────

st.divider()
st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💼 Go to America Multi-Agent System v0.1")

# Auto-refresh setiap 2 detik saat execution berjalan
if st.session_state.execution_started:
    import time
    time.sleep(2)
    st.rerun()
