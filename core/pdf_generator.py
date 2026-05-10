"""core/pdf_generator.py — Business Plan PDF Generator"""
import logging
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

def find_available_fonts():
    """Finds common sans-serif font paths across different Operating Systems."""
    import os
    candidates = [
        # Windows
        {"name": "Arial", "path": r"C:\Windows\Fonts\arial.ttf", "bold": r"C:\Windows\Fonts\arialbd.ttf", "italic": r"C:\Windows\Fonts\ariali.ttf"},
        # Linux (Common on Ubuntu/Debian/Streamlit Cloud)
        {"name": "DejaVuSans", "path": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "italic": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"},
        {"name": "LiberationSans", "path": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "italic": "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"},
    ]
    for c in candidates:
        if os.path.exists(c["path"]):
            return c
    return None

def generate_business_plan_pdf(memory) -> bytes:
    from fpdf import FPDF, XPos, YPos
    import os
    from core.shared_memory import AgentKey
    from core.schemas import (
        InquisitorOutput, OrchestratorReview, CriticOutput, RiskManagerOutput,
        FinanceOutput, MarketOutput, OpsOutput, SupplyPlanOutput, HROutput, LegalOutput,
    )

    inq    = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
    orc    = memory.get(AgentKey.ORCHESTRATOR, OrchestratorReview)
    critic = memory.get(AgentKey.CRITIC, CriticOutput)
    risk   = memory.get(AgentKey.RISK_MANAGER, RiskManagerOutput)
    cfo    = memory.get(AgentKey.CFO, FinanceOutput)
    growth = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
    ops    = memory.get(AgentKey.PRODUCT_ARCHITECT, OpsOutput)
    supply = memory.get(AgentKey.SUPPLY_PLANNER, SupplyPlanOutput)
    hr     = memory.get(AgentKey.HR_PLANNER, HROutput)
    legal  = memory.get(AgentKey.LEGAL, LegalOutput)

    ctx      = inq.business_context if inq else None
    biz_name = (ctx.business_idea or "Rencana Bisnis") if ctx else "Rencana Bisnis"
    location = ctx.location if ctx else "-"
    sector   = str(ctx.preferred_sector or "-") if ctx else "-"
    budget   = ctx.budget if ctx else 0
    lang     = getattr(ctx, "preferred_language", "id") if ctx else "id"
    is_en    = lang == "en"
    date_str = datetime.now().strftime("%d %B %Y")

    # ── Font Setup (Cross-Platform) ──────────────────────────────────────────
    font_info = find_available_fonts()
    use_unicode = font_info is not None
    font_family = font_info["name"] if use_unicode else "Helvetica"

    class PDF(FPDF):
        def header(self):
            self._set_font("B", 9)
            self.set_text_color(120, 120, 120)
            title_text = f"{'BUSINESS PLAN' if is_en else 'RENCANA BISNIS'} - {self._s(biz_name)}"
            self.cell(0, 8, self._s(title_text), align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(200, 200, 200)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(2)

        def footer(self):
            self.set_y(-14)
            self._set_font("I", 8)
            self.set_text_color(150, 150, 150)
            footer_text = f"Business Co-Pilot AI | {date_str} | Page {self.page_no()}"
            self.cell(0, 8, self._s(footer_text), align="C")

        def _set_font(self, style="", size=10):
            self.set_font(font_family, style, size)

        def _s(self, text: str) -> str:
            """Safe string — converts unicode characters to ascii equivalents for standard fonts."""
            if not text: return ""
            t = str(text)
            # Pre-clean common problematic characters
            replacements = {
                "\u2014": "-", "\u2013": "-",  # em-dash, en-dash
                "\u2018": "'", "\u2019": "'",  # curly single quotes
                "\u201c": '"', "\u201d": '"',  # curly double quotes
                "\u2022": "*",                 # bullet
                "\u2713": "v", "\u2705": "v",  # checkmarks
                "\u26a0": "!", "\u274c": "x",  # warning, cross
                "\u2026": "...",               # ellipsis
            }
            for old, new in replacements.items():
                t = t.replace(old, new)
            
            if use_unicode:
                return t
                
            # If not using unicode font, strip everything above ASCII
            return "".join(c if ord(c) < 128 else "" for c in t)

    pdf = PDF()
    if use_unicode:
        pdf.add_font(font_family, "", font_info["path"])
        if os.path.exists(font_info.get("bold", "")):
            pdf.add_font(font_family, "B", font_info["bold"])
        if os.path.exists(font_info.get("italic", "")):
            pdf.add_font(font_family, "I", font_info["italic"])

    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Helpers ──────────────────────────────────────────────────────────────
    BLUE  = (30, 90, 180)
    GREEN = (50, 130, 90)
    RED   = (180, 60, 40)
    GRAY  = (90, 90, 90)

    def section(title):
        pdf._set_font("B", 13)
        pdf.set_text_color(*BLUE)
        pdf.ln(4)
        pdf.cell(0, 8, pdf._s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(*BLUE)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_text_color(30, 30, 30)
        pdf.ln(3)

    def sub(title):
        pdf._set_font("B", 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 6, pdf._s(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)

    def body(text, indent=0):
        if not text: return
        pdf._set_font("", 9)
        pdf.set_x(pdf.l_margin + indent)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - indent, 5, pdf._s(str(text)))
        pdf.ln(1)

    def bullets(items, indent=4):
        pdf._set_font("", 9)
        for item in (items or []):
            pdf.set_x(pdf.l_margin + indent)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - indent, 5,
                           f"*  {pdf._s(str(item))}")
        pdf.ln(1)

    def kv(key, val, bold_val=False):
        pdf._set_font("B", 9)
        pdf.set_text_color(*GRAY)
        pdf.cell(60, 5, pdf._s(f"{key}:"), new_x=XPos.RIGHT, new_y=YPos.SAME)
        pdf._set_font("B" if bold_val else "", 9)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 5, pdf._s(str(val)), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def badge(text, color, text_color=(255, 255, 255)):
        pdf.set_fill_color(*color)
        pdf.set_text_color(*text_color)
        pdf._set_font("B", 11)
        pdf.cell(0, 9, f"  {pdf._s(text)}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 30, 30)
        pdf.ln(2)

    # ════════════════════════════════════════════════════════════════════════
    # COVER
    # ════════════════════════════════════════════════════════════════════════
    pdf.set_y(45)
    pdf._set_font("B", 26)
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 14, "BUSINESS PLAN" if is_en else "RENCANA BISNIS", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf._set_font("B", 16)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 10, pdf._s(biz_name), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf._set_font("", 11)
    pdf.set_text_color(*GRAY)
    loc_lbl = "Location" if is_en else "Lokasi"
    pdf.cell(0, 6, f"{loc_lbl}: {pdf._s(location)}  |  Sector: {pdf._s(sector)}",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Capital: Rp {budget:,.0f}", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Date: {date_str}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    pdf._set_font("I", 9)
    pdf.cell(0, 6, "Generated by Business Co-Pilot AI | Multi-Agent Research System",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if orc:
        pdf.ln(8)
        if orc.approved:
            badge("  STATUS: VIABLE / LAYAK DIEKSEKUSI", GREEN)
        else:
            badge("  STATUS: NEEDS REFINEMENT / PERLU PENYEMPURNAAN", RED)

    # ════════════════════════════════════════════════════════════════════════
    # 1. EXECUTIVE SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    pdf.add_page()
    section("1. Executive Summary" if is_en else "1. Ringkasan Eksekutif")
    if orc:
        body(orc.executive_summary)
        pdf.ln(2)
        sub("Final Recommendation:" if is_en else "Rekomendasi Final:")
        body(orc.final_recommendation, indent=4)
        if orc.next_steps:
            pdf.ln(2)
            sub("Next Steps:" if is_en else "Langkah Selanjutnya:")
            bullets(orc.next_steps, indent=4)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 2. BUSINESS PROFILE
    # ════════════════════════════════════════════════════════════════════════
    section("2. Business Profile" if is_en else "2. Profil Bisnis")
    if ctx:
        kv("Business Idea" if is_en else "Ide Bisnis", ctx.business_idea or "-")
        kv("Location" if is_en else "Lokasi", ctx.location)
        kv("Sector" if is_en else "Sektor", ctx.preferred_sector or "-")
        kv("Initial Capital" if is_en else "Modal Awal", f"Rp {ctx.budget:,.0f}", bold_val=True)
        if ctx.target_monthly_income:
            kv("Target Monthly Income" if is_en else "Target Pendapatan/Bln",
               f"Rp {ctx.target_monthly_income:,.0f}")
        if ctx.skills:
            kv("Owner Skills" if is_en else "Keahlian Pemilik", ", ".join(ctx.skills))

    # ════════════════════════════════════════════════════════════════════════
    # 3. MARKET ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    section("3. Market Analysis" if is_en else "3. Analisis Pasar")
    if growth:
        body(getattr(growth, "market_summary", None) or getattr(growth, "recommended_idea", "-"))
        kv("Target Segment", getattr(growth, "target_segment", "-"))
        kv("Value Proposition", getattr(growth, "value_proposition", "-"))
        strats = getattr(growth, "growth_strategies", None)
        if strats:
            sub("Growth Strategies:" if is_en else "Strategi Pertumbuhan:")
            bullets(strats)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 4. FINANCIAL PROJECTIONS
    # ════════════════════════════════════════════════════════════════════════
    section("4. Financial Projections" if is_en else "4. Proyeksi Keuangan")
    if cfo:
        kv("Recommended Capital" if is_en else "Modal yang Disarankan",
           f"Rp {cfo.recommended_capital:,.0f}", bold_val=True)
        kv("Total Monthly Cost" if is_en else "Total Biaya Bulanan",
           f"Rp {cfo.total_monthly_cost:,.0f}")
        kv("Projected Monthly Revenue" if is_en else "Proyeksi Pendapatan/Bln",
           f"Rp {cfo.projected_monthly_revenue:,.0f}")
        kv("Net Profit (Month 6)" if is_en else "Laba Bersih (Bln 6)",
           f"Rp {cfo.projected_net_profit_month6:,.0f}")
        kv("Break Even Point", f"{cfo.bep_months:.1f} months" if is_en else f"{cfo.bep_months:.1f} bulan",
           bold_val=True)
        kv("Financial Risk" if is_en else "Risiko Keuangan", cfo.risk_level.upper())

        if cfo.startup_cost:
            pdf.ln(2)
            sub("Startup Cost Breakdown:" if is_en else "Rincian Biaya Awal:")
            for item in cfo.startup_cost:
                label  = item.get("item", item.get("name", "-"))
                amount = float(item.get("amount", item.get("cost", 0)))
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.cell(90, 5, f"*  {pdf._s(str(label))}", new_x=XPos.RIGHT, new_y=YPos.SAME)
                pdf.cell(0, 5, f"Rp {amount:,.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if cfo.monthly_cost:
            pdf.ln(2)
            sub("Monthly Operating Cost:" if is_en else "Biaya Operasional Bulanan:")
            for item in cfo.monthly_cost:
                label  = item.get("item", item.get("name", "-"))
                amount = float(item.get("amount", item.get("cost", 0)))
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.cell(90, 5, f"*  {pdf._s(str(label))}", new_x=XPos.RIGHT, new_y=YPos.SAME)
                pdf.cell(0, 5, f"Rp {amount:,.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 5. OPERATIONS PLAN
    # ════════════════════════════════════════════════════════════════════════
    section("5. Operations Plan" if is_en else "5. Rencana Operasional")
    if ops:
        kv("Daily Capacity" if is_en else "Kapasitas Harian", f"{ops.daily_capacity} units/day" if is_en else f"{ops.daily_capacity} unit/hari")
        kv("Minimum Staff" if is_en else "Staf Minimum", f"{ops.minimum_staff} people" if is_en else f"{ops.minimum_staff} orang")
        kv("Total Equipment Cost" if is_en else "Total Biaya Peralatan", f"Rp {ops.total_equipment_cost:,.0f}")

        if ops.equipment_list:
            pdf.ln(2)
            sub("Equipment List:" if is_en else "Daftar Peralatan:")
            for eq in ops.equipment_list:
                name = eq.name if hasattr(eq, "name") else eq.get("name", "-")
                qty  = eq.quantity if hasattr(eq, "quantity") else eq.get("quantity", 1)
                cost = float(eq.estimated_cost if hasattr(eq, "estimated_cost") else eq.get("estimated_cost", 0))
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.cell(85, 5, f"*  {pdf._s(str(name))} (x{qty})", new_x=XPos.RIGHT, new_y=YPos.SAME)
                pdf.cell(0, 5, f"Rp {cost:,.0f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if ops.operational_flow:
            pdf.ln(2)
            sub("Operational Flow:" if is_en else "Alur Operasional:")
            for j, step in enumerate(ops.operational_flow, 1):
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 4, 5,
                               f"{j}. {pdf._s(str(step))}")
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 6. SUPPLY CHAIN & COGS
    # ════════════════════════════════════════════════════════════════════════
    section("6. Supply Chain & COGS" if is_en else "6. Supply Chain & HPP")
    if supply:
        kv("COGS per Unit" if is_en else "HPP per Unit", f"Rp {supply.hpp_per_unit:,.2f}", bold_val=True)
        kv("Daily COGS" if is_en else "COGS Harian", f"Rp {supply.daily_cogs:,.0f}")
        kv("Monthly COGS" if is_en else "COGS Bulanan", f"Rp {supply.monthly_cogs:,.0f}")
        if supply.supplier_recommendations:
            sub("Supplier Recommendations:" if is_en else "Rekomendasi Supplier:")
            bullets(supply.supplier_recommendations)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 7. HR PLAN
    # ════════════════════════════════════════════════════════════════════════
    section("7. HR Plan" if is_en else "7. Perencanaan SDM")
    if hr:
        kv("Total Monthly Salary" if is_en else "Total Gaji Bulanan",
           f"Rp {hr.total_monthly_salary:,.0f}")
        if hr.roles:
            sub("Staff Roles:" if is_en else "Posisi Staf:")
            for role in hr.roles:
                rname  = role.get("role", role.get("position", "-"))
                count  = role.get("count", role.get("quantity", 1))
                salary = float(role.get("salary", role.get("monthly_salary", 0)))
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.cell(85, 5, f"*  {pdf._s(str(rname))} (x{count})", new_x=XPos.RIGHT, new_y=YPos.SAME)
                pdf.cell(0, 5, f"Rp {salary:,.0f}/mo", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if hr.hiring_priority:
            sub("Hiring Priority:" if is_en else "Prioritas Rekrutmen:")
            bullets(hr.hiring_priority)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 8. LEGAL & COMPLIANCE
    # ════════════════════════════════════════════════════════════════════════
    section("8. Legal & Compliance" if is_en else "8. Hukum & Perizinan")
    if legal:
        if legal.required_licenses:
            sub("Required Licenses:" if is_en else "Perizinan yang Diperlukan:")
            bullets(legal.required_licenses)
        if legal.jurisdiction:
            kv("Jurisdiction" if is_en else "Yurisdiksi", legal.jurisdiction)
        if legal.compliance_notes:
            sub("Compliance Notes:" if is_en else "Catatan Kepatuhan:")
            body(legal.compliance_notes, indent=4)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 9. RISK ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    section("9. Risk Analysis" if is_en else "9. Analisis Risiko")
    if risk:
        kv("Overall Viability" if is_en else "Viabilitas", risk.overall_viability, bold_val=True)
        sub("Best Case Scenario:" if is_en else "Skenario Terbaik:")
        body(risk.best_case_summary, indent=4)
        sub("Worst Case Scenario:" if is_en else "Skenario Terburuk:")
        body(risk.worst_case_summary, indent=4)
        if hasattr(risk, "mitigation_strategies") and risk.mitigation_strategies:
            sub("Mitigation Strategies:" if is_en else "Strategi Mitigasi:")
            bullets(risk.mitigation_strategies)
    else:
        body("Data not available." if is_en else "Data tidak tersedia.")

    # ════════════════════════════════════════════════════════════════════════
    # 10. EVALUATION & FINAL DECISION
    # ════════════════════════════════════════════════════════════════════════
    section("10. Evaluation & Final Decision" if is_en else "10. Evaluasi & Keputusan Akhir")
    if critic:
        kv("Risk Level (Critic)", critic.overall_risk_level.upper())
        kv("Critical Issues" if is_en else "Isu Kritis", str(critic.critical_count))
        kv("Revision Required" if is_en else "Perlu Revisi", ("Yes" if critic.revision_required else "No") if is_en else ("Ya" if critic.revision_required else "Tidak"))

        if critic.issues_found:
            pdf.ln(2)
            sub("Findings:" if is_en else "Temuan:")
            for iss in critic.issues_found:
                sev = str(iss.severity).upper()
                pdf._set_font("B", 9)
                pdf.set_x(pdf.l_margin + 4)
                pdf.cell(0, 5, f"[{sev}] {pdf._s(iss.agent_source.upper())}:",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf._set_font("", 9)
                pdf.set_x(pdf.l_margin + 8)
                pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 8, 5,
                               pdf._s(iss.description))
                pdf.ln(1)

    if orc:
        pdf.ln(3)
        color = GREEN if orc.approved else RED
        label = ("FINAL DECISION: VIABLE" if orc.approved else "FINAL DECISION: NEEDS REFINEMENT") if is_en else ("KEPUTUSAN AKHIR: LAYAK" if orc.approved else "KEPUTUSAN AKHIR: PERLU PENYEMPURNAAN")
        badge(label, color)

        reasoning = getattr(orc, "reasoning", None)
        if reasoning:
            sub("CEO Reasoning:" if is_en else "Alur Pemikiran CEO:")
            body(reasoning, indent=4)

    return bytes(pdf.output())
