"""
dashboard.py — Chat-First Co-Pilot Dashboard
============================================
Alur: Form (Layar 1) → Chat Co-Pilot (Layar 2)
"""

import asyncio
import logging
import sys
import os
import threading
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Final version with PDF support
import streamlit as st
from core.shared_memory import MockSharedMemory, AgentKey
from core.schemas import BusinessContext, InquisitorOutput, AgentStatus, AgentOutput, FinanceOutput

logger = logging.getLogger(__name__)


# ─── Background runner ────────────────────────────────────────────────────────
def run_ai_in_background(memory):
    from agents.executive.orchestrator import setup_and_run
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_and_run(memory))
        loop.close()
    except Exception as e:
        logger.error(f"Error in AI background thread: {e}")


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Business Co-Pilot — Go to America",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Session State ────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "memory": MockSharedMemory(session_id="streamlit_demo"),
        "execution_started": False,
        "chat_history": [],
        "current_context": None,
        "last_agent_snapshot": {},
        "review_injected": set(),
        "language": "id",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─── UI Translations ──────────────────────────────────────────────────────────
_T = {
    "id": {
        "app_title":        "🤖 Business Co-Pilot",
        "app_subtitle":     "AI-Powered Business Planning — Berbasis riset pasar real-time",
        "lang_label":       "🌐 Bahasa",
        "lang_options":     ["Bahasa Indonesia", "English"],
        "field_location":   "📍 Lokasi Bisnis *",
        "field_budget":     "💰 Estimasi Modal (IDR) *",
        "field_sector":     "🏢 Sektor Bisnis",
        "field_skills":     "🛠️ Keahlian Anda",
        "field_idea":       "💡 Ide Bisnis (opsional)",
        "field_assets":     "🏠 Aset yang Dimiliki (opsional)",
        "field_income":     "📊 Target Pendapatan/Bulan (IDR)",
        "submit_btn":       "🚀 Mulai Analisis",
        "err_location":     "📍 Lokasi bisnis wajib diisi.",
        "chat_title":       "### 💬 Business Co-Pilot",
        "chat_caption":     "Tanya apa saja atau beri perintah: *'Ubah budget jadi 20 juta'*, *'Jelaskan risiko terbesar'*, dll.",
        "chat_placeholder": "Tanya atau beri perintah kepada Co-Pilot...",
        "reset_btn":        "🔁 Reset & Mulai Ulang",
        "sidebar_title":    "### 🤖 Business Co-Pilot",
        "agents_done":      "{done}/{total} agen selesai",
        "pick_btn":         "✅ Pilih & Lanjutkan",
        "approve_btn":      "✅ Lanjutkan ke Keputusan CEO",
        "reasoning_label":  "🧠 Lihat alur pemikiran CEO",
        "next_steps_label": "**Klik untuk tindak lanjut:**",
        "welcome_msg": (
            "👋 **Halo! Saya Business Co-Pilot Anda.**\n\n"
            "Saya sudah menerima informasi bisnis Anda:\n"
            "- 📍 **Lokasi:** {location}\n"
            "- 💰 **Modal:** Rp {budget:,.0f}\n"
            "- 🏢 **Sektor:** {sector}\n\n"
            "Tim analis AI saya sedang bekerja — mengumpulkan riset pasar, menganalisis kompetitor, "
            "dan menyusun proyeksi keuangan. Saya akan update Anda secara real-time. "
            "Anda bisa bertanya apa saja kapan pun! 💬"
        ),
        "proposal_intro":   "🎯 **Tim analis sudah menyusun beberapa opsi strategi bisnis berdasarkan riset pasar.**\n\nSilakan pilih satu konsep yang paling sesuai — ini akan menjadi fondasi perencanaan operasional berikutnya.",
        "proposal_radio":   "Pilih konsep bisnis:",
        "proposal_locked":  "🚀 Pilihan **{title}** dikunci! Tim operasional sedang menyusun rencana detail...",
        "user_picked":      "✅ Saya memilih: **{title}**",
        "user_approved":    "✅ Lanjutkan ke evaluasi CEO.",
        "approve_ceo_btn":  "✅ Lanjutkan ke Keputusan CEO",
        "approve_continue_msg": "Lanjutkan ke evaluasi CEO.",
        "select_continue_btn": "✅ Pilih & Lanjutkan",
        "selected_label":   "Saya memilih",
        "operation_started_msg": "Pilihan **{title}** dikunci! Tim operasional sedang menyusun rencana detail...",
        "concept_label":    "Konsep",
        "target_label":     "Target Market",
        "capital_est_label": "Estimasi Modal",
        "pros_label":       "Keunggulan",
        "cons_label":       "Kelemahan",
        "agents_running":   "⏳ {n} agen berjalan",
        "agents_failed":    "⚠️ {n} agen gagal",
        "reset_confirm":    "🔁 Reset & Mulai Ulang",
        "currency":         "IDR",
        "currency_symbol":  "Rp",
        "budget_default":   50_000_000,
        "budget_step":      1_000_000,
        "income_default":   5_000_000,
        "income_step":      500_000,
        "exchange_rate":    1.0,
    },
    "en": {
        "app_title":        "🤖 Business Co-Pilot",
        "app_subtitle":     "AI-Powered Business Planning — Powered by real-time market research",
        "lang_label":       "🌐 Language",
        "lang_options":     ["Bahasa Indonesia", "English"],
        "field_location":   "📍 Business Location *",
        "field_budget":     "💰 Estimated Capital (USD) *",
        "field_sector":     "🏢 Business Sector",
        "field_skills":     "🛠️ Your Skills",
        "field_idea":       "💡 Business Idea (optional)",
        "field_assets":     "🏠 Existing Assets (optional)",
        "field_income":     "📊 Target Monthly Income (USD)",
        "submit_btn":       "🚀 Start Analysis",
        "err_location":     "📍 Business location is required.",
        "chat_title":       "### 💬 Business Co-Pilot",
        "chat_caption":     "Ask anything or give a command: *'Change budget to $5,000'*, *'Explain the biggest risk'*, etc.",
        "chat_placeholder": "Ask or give a command to the Co-Pilot...",
        "reset_btn":        "🔁 Reset & Start Over",
        "sidebar_title":    "### 🤖 Business Co-Pilot",
        "agents_done":      "{done}/{total} agents done",
        "pick_btn":         "✅ Select & Continue",
        "approve_btn":      "✅ Proceed to CEO Decision",
        "reasoning_label":  "🧠 View CEO's reasoning",
        "next_steps_label": "**Click to take action:**",
        "welcome_msg": (
            "👋 **Hello! I'm your Business Co-Pilot.**\n\n"
            "I have received your business information:\n"
            "- 📍 **Location:** {location}\n"
            "- 💰 **Capital:** ${budget:,.0f} USD (~Rp {budget_idr:,.0f})\n"
            "- 🏢 **Sector:** {sector}\n\n"
            "My AI analyst team is working now — gathering market research, analyzing competitors, "
            "and building financial projections. I will update you in real-time. "
            "Feel free to ask anything! 💬"
        ),
        "proposal_intro":   "🎯 **My analyst team has prepared several business strategy options based on market research.**\n\nPlease choose one concept — this will be the foundation for all operational planning ahead.",
        "proposal_radio":   "Choose a business concept:",
        "proposal_locked":  "🚀 **{title}** locked in! The operations team is building the detailed plan...",
        "user_picked":      "✅ I chose: **{title}**",
        "user_approved":    "✅ Proceed to CEO evaluation.",
        "approve_ceo_btn":  "✅ Proceed to CEO Decision",
        "approve_continue_msg": "Proceed to CEO evaluation.",
        "select_continue_btn": "✅ Select & Continue",
        "selected_label":   "I selected",
        "operation_started_msg": "**{title}** locked in! The operations team is building the detailed plan...",
        "concept_label":    "Concept",
        "target_label":     "Target Market",
        "capital_est_label": "Estimated Capital",
        "pros_label":       "Strengths",
        "cons_label":       "Weaknesses",
        "agents_running":   "⏳ {n} agents running",
        "agents_failed":    "⚠️ {n} agents failed",
        "reset_confirm":    "🔁 Reset & Start Over",
        "currency":         "USD",
        "currency_symbol":  "$",
        "budget_default":   3_000,
        "budget_step":      100,
        "income_default":   300,
        "income_step":      50,
        "exchange_rate":    16_000.0,
    },
}

def t(key: str) -> str:
    """Shortcut untuk mengambil terjemahan UI berdasarkan bahasa saat ini."""
    lang = st.session_state.get("language", "id")
    return _T.get(lang, _T["id"]).get(key, key)


# ─── Constants ────────────────────────────────────────────────────────────────
_AGENT_LABELS = {
    AgentKey.GEO_ANALYST:       "🗺️ Geo Analyst",
    AgentKey.COMPETITOR:        "🔍 Competitor Scout",
    AgentKey.GROWTH_HACKER:     "📈 Growth Hacker",
    AgentKey.PRICING:           "💰 Pricing Strategist",
    AgentKey.CFO:               "📊 CFO",
    AgentKey.LEGAL:             "⚖️ Legal",
    AgentKey.PRODUCT_ARCHITECT: "🏗️ Product Architect",
    AgentKey.HR_PLANNER:        "👥 HR Planner",
    AgentKey.SUPPLY_PLANNER:    "📦 Supply Planner",
    AgentKey.SOP_DESIGNER:      "📋 SOP Designer",
    AgentKey.CRITIC:            "🔍 Executive Critic",
    AgentKey.RISK_MANAGER:      "⚖️ Risk Manager",
    AgentKey.ORCHESTRATOR:      "🎯 Orchestrator (CEO)",
}

_AGENT_MESSAGES = {
    "id": {
        AgentKey.GEO_ANALYST:       "\U0001f5fa\ufe0f **Riset lokasi selesai.** Potensi pasar dan demografis sudah dianalisis.",
        AgentKey.COMPETITOR:        "\U0001f50d **Pemetaan kompetitor selesai.** Data pesaing utama sudah ditemukan.",
        AgentKey.GROWTH_HACKER:     "\U0001f4c8 **Analisis peluang pertumbuhan pasar selesai.**",
        AgentKey.PRICING:           "\U0001f4b0 **Strategi harga sudah dirumuskan** berdasarkan data kompetitor dan margin.",
        AgentKey.CFO:               "\U0001f4ca **Proyeksi keuangan selesai.** Modal awal, BEP, dan proyeksi laba sudah dihitung.",
        AgentKey.LEGAL:             "\u2696\ufe0f **Analisis kepatuhan hukum selesai.** Perizinan yang diperlukan sudah dipetakan.",
        AgentKey.PRODUCT_ARCHITECT: "\U0001f3d7\ufe0f **Desain produk & peralatan selesai.**",
        AgentKey.HR_PLANNER:        "\U0001f465 **Perencanaan SDM selesai.** Kebutuhan staf dan estimasi gaji sudah dihitung.",
        AgentKey.SUPPLY_PLANNER:    "\U0001f4e6 **Rencana supply chain selesai.** HPP dan kebutuhan bahan baku sudah diperhitungkan.",
        AgentKey.SOP_DESIGNER:      "\U0001f4cb **SOP selesai dirancang.**",
        AgentKey.CRITIC:            "\U0001f50d **Evaluasi kritis rencana selesai.** Inkonsistensi dan celah sudah diidentifikasi.",
        AgentKey.RISK_MANAGER:      "\u2696\ufe0f **Analisis risiko selesai.** Skenario dan mitigasi sudah dipetakan.",
        AgentKey.ORCHESTRATOR:      "\U0001f3af **Evaluasi CEO selesai.** Keputusan dan rekomendasi siap disampaikan.",
    },
    "en": {
        AgentKey.GEO_ANALYST:       "\U0001f5fa\ufe0f **Location research complete.** Market potential and demographics analyzed.",
        AgentKey.COMPETITOR:        "\U0001f50d **Competitor mapping complete.** Key competitor data gathered.",
        AgentKey.GROWTH_HACKER:     "\U0001f4c8 **Market growth analysis complete.**",
        AgentKey.PRICING:           "\U0001f4b0 **Pricing strategy formulated** based on competitor data and margins.",
        AgentKey.CFO:               "\U0001f4ca **Financial projections complete.** Capital, BEP, and profit projections calculated.",
        AgentKey.LEGAL:             "\u2696\ufe0f **Legal compliance analysis complete.** Required licenses mapped.",
        AgentKey.PRODUCT_ARCHITECT: "\U0001f3d7\ufe0f **Product design & equipment planning complete.**",
        AgentKey.HR_PLANNER:        "\U0001f465 **HR planning complete.** Staff needs and salary estimates calculated.",
        AgentKey.SUPPLY_PLANNER:    "\U0001f4e6 **Supply chain plan complete.** COGS and raw material needs calculated.",
        AgentKey.SOP_DESIGNER:      "\U0001f4cb **Standard Operating Procedures (SOP) designed.**",
        AgentKey.CRITIC:            "\U0001f50d **Critical evaluation complete.** Inconsistencies and gaps identified.",
        AgentKey.RISK_MANAGER:      "\u2696\ufe0f **Risk analysis complete.** Scenarios and mitigation strategies mapped.",
        AgentKey.ORCHESTRATOR:      "\U0001f3af **CEO evaluation complete.** Decision and recommendations ready.",
    },
}

def get_agent_message(key: AgentKey) -> str:
    lang = st.session_state.get("language", "id")
    return _AGENT_MESSAGES.get(lang, _AGENT_MESSAGES["id"]).get(key, f"\u2705 **{key.value}** done.")



# ─── Co-Pilot helpers ─────────────────────────────────────────────────────────
def trigger_agent_rerun(rerun_key: str, memory):
    from core.dag import RERUN_MAP
    _specific = {
        "hr":    [AgentKey.HR_PLANNER, AgentKey.SOP_DESIGNER],
        "legal": [AgentKey.LEGAL],
        "sop":   [AgentKey.SOP_DESIGNER],
    }
    agents = _specific.get(rerun_key) or RERUN_MAP.get(rerun_key, [])
    if agents:
        memory.invalidate_agents(agents)
    from streamlit.runtime.scriptrunner import add_script_run_ctx
    t = threading.Thread(target=run_ai_in_background, args=(memory,))
    add_script_run_ctx(t)
    t.start()


def handle_chat_command(msg: str, memory):
    import re
    msg_lower = msg.lower()

    if any(kw in msg_lower for kw in ["ubah budget", "ganti budget", "ubah anggaran", "budget jadi", "anggaran jadi"]):
        numbers = re.findall(r'[\d.,]+', msg)
        if numbers:
            raw = numbers[0].replace(",", "").replace(".", "")
            nb = float(raw)
            if "juta" in msg_lower: nb *= 1_000_000
            elif "ribu" in msg_lower: nb *= 1_000
            inq = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
            if inq and inq.business_context:
                inq.business_context.budget = nb
                memory.set(AgentKey.INQUISITOR, inq)
                if st.session_state.current_context:
                    st.session_state.current_context.budget = nb
            trigger_agent_rerun("budget", memory)
            return f"✅ Budget diperbarui ke **Rp {nb:,.0f}**. Menghitung ulang proyeksi keuangan..."
        return "❓ Sertakan jumlah. Contoh: *'Ubah budget jadi 20 juta'*"

    if any(kw in msg_lower for kw in ["ubah lokasi", "ganti lokasi", "pindah ke", "lokasi baru", "lokasi jadi"]):
        match = re.search(r'(?:ubah lokasi|ganti lokasi|pindah ke|lokasi baru|lokasi jadi)\s+(?:ke\s+)?(.+)', msg_lower)
        if match:
            loc = match.group(1).strip().title()
            inq = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
            if inq and inq.business_context:
                inq.business_context.location = loc
                memory.set(AgentKey.INQUISITOR, inq)
                if st.session_state.current_context:
                    st.session_state.current_context.location = loc
            trigger_agent_rerun("location", memory)
            return f"✅ Lokasi diperbarui ke **{loc}**. Me-riset ulang pasar..."
        return "❓ Sertakan lokasi. Contoh: *'Ubah lokasi ke Surabaya'*"

    if any(kw in msg_lower for kw in ["hitung ulang keuangan", "revisi cfo", "update keuangan"]):
        trigger_agent_rerun("budget", memory)
        return "✅ Menghitung ulang proyeksi keuangan..."
    if any(kw in msg_lower for kw in ["revisi legal", "update legal"]):
        trigger_agent_rerun("legal", memory)
        return "✅ Meninjau ulang aspek legal..."
    if any(kw in msg_lower for kw in ["revisi sop", "update sop", "perbaiki sop"]):
        trigger_agent_rerun("sop", memory)
        return "✅ Merancang ulang SOP..."
    if any(kw in msg_lower for kw in ["revisi sdm", "update hr"]):
        trigger_agent_rerun("hr", memory)
        return "✅ Merencanakan ulang SDM..."

    # Perintah 'lanjut' — lanjutkan dari diskusi Critic ke USER_REVIEW_2
    if any(kw in msg_lower for kw in ["lanjut", "lanjutkan", "proceed", "continue", "ok lanjut", "oke lanjut"]):
        ready = memory.get_ready_agents()
        if AgentKey.USER_REVIEW_2 in ready and "review_2_done" not in st.session_state.review_injected:
            from core.schemas import UserFeedbackOutput
            memory.set(AgentKey.USER_REVIEW_2, UserFeedbackOutput(approved=True, agent_name="user"))
            st.session_state.review_injected.add("review_2_done")
            from streamlit.runtime.scriptrunner import add_script_run_ctx
            _t = threading.Thread(target=run_ai_in_background, args=(memory,))
            add_script_run_ctx(_t)
            _t.start()
            return "✅ Baik! Melanjutkan ke analisis risiko dan keputusan CEO..."
        elif memory.is_done(AgentKey.ORCHESTRATOR):
            return "ℹ️ Analisis sudah selesai. Anda bisa bertanya atau memberi perintah lebih lanjut."
        else:
            return "⏳ Sistem masih memproses. Sebentar lagi Co-Pilot akan siap melanjutkan."

    return None


def ask_copilot_llm(question: str, memory) -> str:
    from core.factory import create_llm
    from core.schemas import OrchestratorReview, CriticOutput, RiskManagerOutput
    ctx = []
    orc = memory.get(AgentKey.ORCHESTRATOR, OrchestratorReview)
    if orc:
        ctx.append(f"Ringkasan: {orc.executive_summary}\nRekomendasi: {orc.final_recommendation}")
    crit = memory.get(AgentKey.CRITIC, CriticOutput)
    if crit:
        ctx.append(f"Risk Level: {crit.overall_risk_level} | Isu Kritis: {crit.critical_count} | {crit.summary}")
    risk = memory.get(AgentKey.RISK_MANAGER, RiskManagerOutput)
    if risk:
        ctx.append(f"Viabilitas: {risk.overall_viability} | Best: {risk.best_case_summary} | Worst: {risk.worst_case_summary}")
    cfo = memory.get(AgentKey.CFO, FinanceOutput)
    if cfo:
        ctx.append(f"Proyeksi Modal: Rp {cfo.recommended_capital:,.0f} | BEP: {cfo.bep_months:.1f} bulan")
    context_str = "\n".join(ctx) if ctx else "Belum ada data laporan tersedia."
    prompt = (
        "Anda adalah Business Co-Pilot AI yang membantu perencanaan bisnis berbasis riset pasar. "
        "Jawab dalam Bahasa Indonesia yang jelas dan profesional.\n\n"
        f"Konteks Laporan:\n{context_str}\n\nPertanyaan: {question}"
    )
    try:
        llm = create_llm("orchestrator", temperature=0.5)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(llm.ainvoke(prompt))
        loop.close()
        return response.content.strip()
    except Exception as e:
        return f"❌ Gagal menghubungi Co-Pilot: {e}"


def inject_agent_status_messages():
    current = st.session_state.memory.snapshot()
    last = st.session_state.last_agent_snapshot
    ordered = [
        AgentKey.GEO_ANALYST, AgentKey.COMPETITOR, AgentKey.GROWTH_HACKER,
        AgentKey.PRICING, AgentKey.CFO, AgentKey.LEGAL,
        AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER, AgentKey.SUPPLY_PLANNER,
        AgentKey.SOP_DESIGNER, AgentKey.CRITIC, AgentKey.RISK_MANAGER, AgentKey.ORCHESTRATOR,
    ]
    injected = False
    for key in ordered:
        if current.get(key.value) == AgentStatus.DONE.value and last.get(key.value) != AgentStatus.DONE.value:
            # Critic: tampilkan isu-isu secara detail, ajak user diskusi
            if key == AgentKey.CRITIC and "critic_issues_injected" not in st.session_state.review_injected:
                from core.schemas import CriticOutput
                crit = st.session_state.memory.get(AgentKey.CRITIC, CriticOutput)
                if crit:
                    _inject_critic_issues(crit)
                    st.session_state.review_injected.add("critic_issues_injected")
                    injected = True
            else:
                msg = get_agent_message(key)
                st.session_state.chat_history.append({"role": "assistant", "type": "status", "content": msg})
                injected = True
    st.session_state.last_agent_snapshot = dict(current)
    return injected


def _inject_critic_issues(crit):
    """Paparkan setiap isu Critic ke chat secara terstruktur dan ajak user berdiskusi."""
    _sev_emoji  = {"critical": "\u274c", "warning": "\u26a0\ufe0f", "info": "\u2139\ufe0f"}
    _sev_label  = {"critical": "Kritis", "warning": "Perlu Perhatian", "info": "Informasi"}

    # Pembuka
    intro = (
        f"\U0001f50d **Tim evaluasi saya (Executive Critic) telah menyelesaikan analisis rencana bisnis Anda.**\n\n"
        f"Ditemukan **{crit.critical_count} isu kritis** dari total {len(crit.issues_found)} temuan. "
        f"Risk level keseluruhan: **{crit.overall_risk_level.upper()}**.\n\n"
        f"{crit.summary}"
    )
    st.session_state.chat_history.append({"role": "assistant", "type": "status", "content": intro})

    # Setiap isu sebagai pesan terpisah
    for i, issue in enumerate(crit.issues_found, 1):
        sev = str(issue.severity).lower()
        emoji = _sev_emoji.get(sev, "\u2139\ufe0f")
        label = _sev_label.get(sev, sev.title())
        issue_msg = (
            f"{emoji} **[{label}] Isu #{i} \u2014 {issue.agent_source.upper()}**\n\n"
            f"{issue.description}\n\n"
            f"\U0001f4a1 **Saran:** {issue.suggestion}"
        )
        st.session_state.chat_history.append({"role": "assistant", "type": "critic_issue", "content": issue_msg})

    # Penutup: arahkan ke kolom chat di bawah
    closing = (
        "\U0001f4ac **Ada pertanyaan atau ingin menyesuaikan sesuatu?**\n\n"
        "Gunakan **kolom chat di bawah halaman ini** untuk:\n"
        "- Menanyakan detail isu tertentu, misal: *\"Jelaskan isu #2 lebih detail\"*\n"
        "- Mengubah parameter, misal: *'Ubah budget jadi 30 juta'* atau *'Ubah lokasi ke Bandung'*\n"
        "- Melanjutkan ke keputusan akhir: ketik **`lanjut`**"
    )
    st.session_state.chat_history.append({"role": "assistant", "type": "critic_closing", "content": closing})



def inject_review_messages():
    memory = st.session_state.memory
    ready = memory.get_ready_agents()
    injected = False

    # Proposal Selection
    if AgentKey.USER_REVIEW_1 in ready and "review_1" not in st.session_state.review_injected:
        from core.schemas import ProposalGeneratorOutput
        pd = memory.get(AgentKey.PROPOSAL_GENERATOR, ProposalGeneratorOutput)
        if pd and pd.options:
            st.session_state.chat_history.append({
                "role": "assistant", "type": "proposal_review",
                "content": t("proposal_intro"),
                "options": [opt.model_dump() for opt in pd.options],
            })
            st.session_state.review_injected.add("review_1")
            injected = True

    # Final Review prompt
    if AgentKey.USER_REVIEW_2 in ready and "review_2" not in st.session_state.review_injected:
        from core.schemas import CriticOutput, RiskManagerOutput
        crit = memory.get(AgentKey.CRITIC, CriticOutput)
        risk = memory.get(AgentKey.RISK_MANAGER, RiskManagerOutput)
        rl = crit.overall_risk_level.upper() if crit else "N/A"
        vi = risk.overall_viability if risk else "N/A"
        _en_rv = st.session_state.language == "en"
        st.session_state.chat_history.append({
            "role": "assistant", "type": "final_review_prompt",
            "content": (
                f"📋 **{'All analysts have completed their work.' if _en_rv else 'Seluruh tim analis dan operasional sudah menyelesaikan tugasnya.'}**\n\n"
                + ("Evaluation summary based on market research:\n" if _en_rv else "Hasil evaluasi berdasarkan riset pasar:\n")
                + f"- Risk Level: **{rl}**\n"
                + f"- {'Plan Viability' if _en_rv else 'Viabilitas Rencana'}: **{vi}**\n\n"
                + ("Click the button below to proceed to the CEO's final decision." if _en_rv else "Klik tombol di bawah untuk melanjutkan ke keputusan akhir CEO.")
            ),
        })
        st.session_state.review_injected.add("review_2")
        injected = True

    # Orchestrator result
    if memory.is_done(AgentKey.ORCHESTRATOR) and "orc_result" not in st.session_state.review_injected:
        from core.schemas import OrchestratorReview
        final = memory.get(AgentKey.ORCHESTRATOR, OrchestratorReview)
        if final:
            _en_orc = st.session_state.language == "en"
            emoji = "🎉" if final.approved else "⚠️"
            verdict = ("**Business plan assessed as VIABLE!**" if final.approved else "**Business plan needs refinement.**") if _en_orc else ("**Rencana bisnis Anda dinilai LAYAK!**" if final.approved else "**Rencana bisnis perlu penyempurnaan.**")
            sum_lbl = "**📝 Summary:**" if _en_orc else "**📝 Ringkasan:**"
            rec_lbl = "**🏁 Recommendation:**" if _en_orc else "**🏁 Rekomendasi:**"
            steps_hdr = "\n\n**🚀 Next Steps:**\n" if _en_orc else "\n\n**🚀 Langkah Selanjutnya:**\n"
            steps = steps_hdr + "\n".join([f"- {s}" for s in final.next_steps]) if final.next_steps else ""
            st.session_state.chat_history.append({
                "role": "assistant", "type": "final_result",
                "content": (
                    f"{emoji} {verdict}\n\n"
                    f"{sum_lbl}\n{final.executive_summary}\n\n"
                    f"{rec_lbl}\n{final.final_recommendation}{steps}"
                ),
                "approved": final.approved,
                "next_steps": final.next_steps,
                "reasoning": getattr(final, "reasoning", None),
            })
            st.session_state.review_injected.add("orc_result")
            injected = True

    return injected

# ═══════════════════════════════════════════════════════════════════════════════
# LAYAR 1 — Business Context Form
# ═══════════════════════════════════════════════════════════════════════════════

if not st.session_state.execution_started:

    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown(f"## {t('app_title')}")
        st.caption(t("app_subtitle"))

        # Language selector — di luar form agar langsung reaktif
        lang_choice = st.radio(
            t("lang_label"), ["Bahasa Indonesia", "English"],
            horizontal=True,
            index=0 if st.session_state.language == "id" else 1,
        )
        new_lang = "id" if lang_choice == "Bahasa Indonesia" else "en"
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            st.rerun()

        st.divider()

        with st.form("business_context_form"):
            _cfg = _T[st.session_state.language]  # shortcut config bahasa saat ini
            location = st.text_input(t("field_location"), placeholder="Jakarta Selatan, Bali...")
            budget = st.number_input(
                t("field_budget"), min_value=0,
                value=_cfg["budget_default"], step=_cfg["budget_step"],
            )
            sector = st.selectbox(t("field_sector"), ["F&B", "Retail", "Services", "Technology", "Healthcare", "Other"])
            skills = st.text_input(t("field_skills"), placeholder="Masak / Cooking, Marketing...")
            business_idea = st.text_area(t("field_idea"), placeholder="...", height=100)
            assets = st.text_input(t("field_assets"), placeholder="Kendaraan / Vehicle...")
            target_income = st.number_input(
                t("field_income"), min_value=0,
                value=_cfg["income_default"], step=_cfg["income_step"],
            )
            submitted = st.form_submit_button(t("submit_btn"), use_container_width=True, type="primary")

        if submitted:
            if not location:
                st.error(t("err_location"))
            else:
                lang = st.session_state.language
                _cfg = _T[lang]
                exchange_rate = _cfg["exchange_rate"]  # 1.0 for IDR, 16000.0 for USD

                # Konversi ke IDR untuk diproses agen
                budget_idr = budget * exchange_rate
                income_idr = target_income * exchange_rate if target_income > 0 else None

                context = BusinessContext(
                    location=location, budget=budget_idr,
                    skills=[s.strip() for s in skills.split(",") if s.strip()],
                    existing_assets=[a.strip() for a in assets.split(",") if a.strip()],
                    business_idea=business_idea if business_idea else None,
                    preferred_sector=sector if sector != "Other" else None,
                    target_monthly_income=income_idr,
                    preferred_language=lang,
                )
                st.session_state.memory.set(AgentKey.INQUISITOR, InquisitorOutput(business_context=context))
                st.session_state.current_context = context
                st.session_state.execution_started = True

                # Pesan sambutan dengan format mata uang yang sesuai
                if lang == "en":
                    welcome = _cfg["welcome_msg"].format(
                        location=location, budget=budget, budget_idr=budget_idr, sector=sector
                    )
                else:
                    welcome = _cfg["welcome_msg"].format(
                        location=location, budget=budget_idr, sector=sector
                    )

                st.session_state.chat_history = [{"role": "assistant", "type": "welcome", "content": welcome}]
                st.session_state.last_agent_snapshot = {}
                st.session_state.review_injected = set()
                from streamlit.runtime.scriptrunner import add_script_run_ctx
                _t = threading.Thread(target=run_ai_in_background, args=(st.session_state.memory,))
                add_script_run_ctx(_t)
                _t.start()
                st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# LAYAR 2 — Chat Co-Pilot
# ═══════════════════════════════════════════════════════════════════════════════

else:
    memory = st.session_state.memory

    inject_agent_status_messages()
    inject_review_messages()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(t("sidebar_title"))
        if st.session_state.current_context:
            ctx = st.session_state.current_context
            st.caption(f"📍 {ctx.location}")
            st.caption(f"💰 {t('currency_symbol')} {ctx.budget:,.0f}")
            st.caption(f"🏢 {ctx.preferred_sector or 'General'}")
        st.divider()

        snapshot = memory.snapshot()
        total = len(snapshot)
        done  = sum(1 for s in snapshot.values() if s == AgentStatus.DONE.value)
        failed = sum(1 for s in snapshot.values() if s == AgentStatus.FAILED.value)
        running = sum(1 for s in snapshot.values() if s == AgentStatus.RUNNING.value)
        st.progress(done / total if total > 0 else 0,
                    text=t("agents_done").format(done=done, total=total))
        if running: st.caption(t("agents_running").format(n=running))
        if failed:  st.caption(t("agents_failed").format(n=failed))
        st.divider()

        for key, label in _AGENT_LABELS.items():
            status = snapshot.get(key.value, "pending")
            if   status == AgentStatus.DONE.value:    st.markdown(f"✅ {label}")
            elif status == AgentStatus.RUNNING.value: st.markdown(f"⏳ {label}")
            elif status == AgentStatus.FAILED.value:  st.markdown(f"❌ {label}")
            else:                                      st.markdown(f"○ _{label}_")

        st.divider()
        if st.button(t("reset_confirm"), type="secondary", use_container_width=True):
            for k in ["memory", "execution_started", "chat_history", "current_context",
                      "last_agent_snapshot", "review_injected"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # ── Chat area ─────────────────────────────────────────────────────────────
    st.markdown(t("chat_title"))
    st.caption(t("chat_caption"))

    chat_container = st.container(height=540)
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            role     = msg["role"]
            msg_type = msg.get("type", "text")
            avatar   = "🤖" if role == "assistant" else "🧑"

            with st.chat_message(role, avatar=avatar):
                st.markdown(msg["content"])

                # Proposal selection
                if msg_type == "proposal_review" and "review_1_done" not in st.session_state.review_injected:
                    opts = msg.get("options", [])
                    if opts:
                        titles = [o["title"] for o in opts]
                        sel_title = st.radio(t("proposal_radio"), titles, key=f"radio_{i}")
                        sel = next((o for o in opts if o["title"] == sel_title), None)
                        if sel:
                            st.markdown(f"**{t('concept_label')}:** {sel.get('description','')}")
                            st.markdown(f"**{t('target_label')}:** {sel.get('target_market','')}")
                            st.markdown(f"**{t('capital_est_label')}:** {sel.get('estimated_startup_cost_range','')}")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.success(f"**{t('pros_label')}:**\n" + "\n".join([f"- {p}" for p in sel.get("pros", [])]))
                            with c2:
                                st.error(f"**{t('cons_label')}:**\n" + "\n".join([f"- {c}" for c in sel.get("cons", [])]))
                        if st.button(t("select_continue_btn"), key=f"pick_{i}", type="primary"):
                            from core.schemas import UserFeedbackOutput
                            memory.set(AgentKey.USER_REVIEW_1, UserFeedbackOutput(
                                approved=True, agent_name="user",
                                selected_option=sel["id"] if sel else None,
                            ))
                            st.session_state.review_injected.add("review_1_done")
                            st.session_state.chat_history.append({"role": "user", "content": f"✅ {t('selected_label')}: **{sel_title}**"})
                            st.session_state.chat_history.append({
                                "role": "assistant", "type": "status",
                                "content": f"🚀 {t('operation_started_msg').format(title=sel_title)}",
                            })
                            from streamlit.runtime.scriptrunner import add_script_run_ctx
                            t_thread = threading.Thread(target=run_ai_in_background, args=(memory,))
                            add_script_run_ctx(t_thread)
                            t_thread.start()
                            st.rerun()

                # Final review prompt
                if msg_type == "final_review_prompt" and "review_2_done" not in st.session_state.review_injected:
                    if st.button(t("approve_ceo_btn"), key=f"approve_{i}", type="primary"):
                        from core.schemas import UserFeedbackOutput
                        memory.set(AgentKey.USER_REVIEW_2, UserFeedbackOutput(approved=True, agent_name="user"))
                        st.session_state.review_injected.add("review_2_done")
                        st.session_state.chat_history.append({"role": "user", "content": f"✅ {t('approve_continue_msg')}"})
                        from streamlit.runtime.scriptrunner import add_script_run_ctx
                        t_thread = threading.Thread(target=run_ai_in_background, args=(memory,))
                        add_script_run_ctx(t_thread)
                        t_thread.start()
                        st.rerun()

                # Final result — keputusan CEO + PDF download
                if msg_type == "final_result":
                    reasoning = msg.get("reasoning")
                    if reasoning:
                        with st.expander(t("reasoning_label")):
                            st.info(reasoning)

                    next_steps = msg.get("next_steps", [])
                    is_en = st.session_state.language == "en"
                    if next_steps:
                        st.divider()
                        st.markdown(t("next_steps_label"))
                        _step_actions = [
                            {"kws": ["keuangan","cfo","hpp","harga","biaya","modal","financial","cost","budget","capital"], "key": "budget",  "lbl": "🔄 Recalculate" if is_en else "🔄 Hitung Ulang"},
                            {"kws": ["lokasi","kompetitor","pasar","wilayah","location","market","competitor"],          "key": "location", "lbl": "🗺 Re-research" if is_en else "🗺 Riset Ulang"},
                            {"kws": ["sdm","staf","rekrutmen","hr","karyawan","staff","human","resource"],               "key": "hr",       "lbl": "👥 Replan HR" if is_en else "👥 Replan SDM"},
                            {"kws": ["legal","perizinan","izin","hukum","license","compliance","permit"],                "key": "legal",    "lbl": "⚖ Re-research Legal" if is_en else "⚖ Riset Legal"},
                            {"kws": ["sop","prosedur","operasional","procedure","standard"],                             "key": "sop",      "lbl": "📋 Redo SOP" if is_en else "📋 Ulang SOP"},
                        ]
                        for j, step in enumerate(next_steps):
                            col_t, col_b = st.columns([4, 1])
                            with col_t:
                                st.markdown(f"- {step}")
                            with col_b:
                                for act in _step_actions:
                                    if any(kw in step.lower() for kw in act["kws"]):
                                        if st.button(act["lbl"], key=f"act_{i}_{j}"):
                                            trigger_agent_rerun(act["key"], memory)
                                            st.session_state.chat_history.append({
                                                "role": "assistant", "type": "status",
                                                "content": f"⚡ **{act['lbl']}** {'started' if is_en else 'dimulai'}...",
                                            })
                                            st.rerun()
                                        break

                    # ── PDF Download ──────────────────────────────────────────────────
                    st.divider()
                    st.caption(
                        "Download the complete business plan document from all agent analyses."
                        if is_en else
                        "Unduh dokumen rencana bisnis lengkap dari seluruh hasil analisis agen."
                    )
                    pdf_btn_label = "📥 Download Business Plan (PDF)" if is_en else "📥 Unduh Rencana Bisnis (PDF)"
                    if st.button(pdf_btn_label, key=f"pdf_btn_{i}", type="primary", use_container_width=True):
                        with st.spinner("Generating PDF..." if is_en else "Membuat dokumen PDF..."):
                            try:
                                from core.pdf_generator import generate_business_plan_pdf
                                pdf_bytes = generate_business_plan_pdf(memory)
                                ctx_loc = (
                                    st.session_state.current_context.location
                                    if st.session_state.current_context else "business"
                                )
                                filename = f"business_plan_{ctx_loc.replace(' ', '_').lower()}.pdf"
                                st.download_button(
                                    label="📄 Click to download PDF" if is_en else "📄 Klik untuk mengunduh PDF",
                                    data=pdf_bytes,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"pdf_dl_{i}",
                                    use_container_width=True,
                                )
                            except Exception as e:
                                st.error(f"PDF generation failed: {e}" if is_en else f"Gagal membuat PDF: {e}")

    # ── Chat input ────────────────────────────────────────────────────────────
    if user_input := st.chat_input(t("chat_placeholder")):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        spinner_txt = "Processing..." if st.session_state.language == "en" else "Co-Pilot sedang memproses..."
        with st.spinner(spinner_txt):
            reply = handle_chat_command(user_input, memory)
            if reply is None:
                reply = ask_copilot_llm(user_input, memory)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    # ── Auto-refresh setiap 2 detik ───────────────────────────────────────────
    import time
    time.sleep(2)
    st.rerun()

