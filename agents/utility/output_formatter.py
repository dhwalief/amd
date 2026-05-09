import os
import logging
from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    AgentStatus,
    AgentOutput,
    InquisitorOutput,
    GeoAnalystOutput,
    CompetitorScoutOutput,
    MarketOutput,
    PricingOutput,
    FinanceOutput,
    LegalOutput,
    OpsOutput,
    HROutput,
    SOPOutput,
    CriticOutput,
    RiskManagerOutput
)

logger = logging.getLogger(__name__)

def format_business_report(memory: SharedMemory) -> str:
    """
    Membaca semua output agent dari SharedMemory dan merendernya 
    menjadi satu kesatuan laporan bisnis berformat Markdown.
    
    Args:
        memory (SharedMemory): Instance memori yang memuat seluruh output agent.
        
    Returns:
        str: Hasil laporan berformat Markdown.
    """
    lines = []
    lines.append("# Laporan Strategi Bisnis — Go to America")
    lines.append("")
    
    # --- 1. Profil Bisnis (Inquisitor) ---
    lines.append("## 1. Profil Bisnis (dari Inquisitor)")
    inq = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
    if inq and inq.status == AgentStatus.DONE:
        ctx = inq.business_context
        lines.append(f"- **Lokasi:** {ctx.location}")
        lines.append(f"- **Budget:** Rp {ctx.budget:,.0f}")
        lines.append(f"- **Keahlian (Skills):** {', '.join(ctx.skills) if ctx.skills else 'Tidak ada'}")
        lines.append(f"- **Aset Dimiliki:** {', '.join(ctx.existing_assets) if ctx.existing_assets else 'Tidak ada'}")
        if ctx.business_idea:
            lines.append(f"- **Ide Bisnis Spesifik:** {ctx.business_idea}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 2. Analisis Lokasi (Geo Analyst) ---
    lines.append("## 2. Analisis Lokasi (dari Geo Analyst)")
    geo = memory.get(AgentKey.GEO_ANALYST, GeoAnalystOutput)
    if geo and geo.status == AgentStatus.DONE:
        lines.append(f"- **Location Score:** {geo.location_score * 100:.1f}%")
        lines.append(f"- **Demand Level:** {geo.demand_level}")
        lines.append(f"- **Foot Traffic Estimate:** {geo.foot_traffic_estimate}")
        lines.append(f"- **Rekomendasi Utama:** {geo.recommendation}")
        lines.append("\n**Nearby Anchors:**")
        for anchor in geo.nearby_anchor:
            lines.append(f"  - {anchor}")
        lines.append("\n**Risk Factors (Lokasi):**")
        for risk in geo.risk_factors:
            lines.append(f"  - {risk}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 3. Analisis Kompetitor (Competitor Scout) ---
    lines.append("## 3. Analisis Kompetitor (dari Competitor Scout)")
    comp = memory.get(AgentKey.COMPETITOR, CompetitorScoutOutput)
    if comp and comp.status == AgentStatus.DONE:
        lines.append(f"- **Rata-rata Harga Pasar:** Rp {comp.average_market_price:,.0f}")
        lines.append(f"- **Diferensiasi (Opportunity):** {comp.differentiation_opportunity}")
        lines.append("\n**Daftar Kompetitor:**")
        for c in comp.competitors:
            lines.append(f"  - **{c.name}** ({c.threat_level.upper()} threat)")
            lines.append(f"    - Harga: {c.estimated_price_range}")
            lines.append(f"    - Kekuatan: {c.strength}")
            lines.append(f"    - Kelemahan: {c.weakness}")
        lines.append("\n**Market Gap:**")
        for gap in comp.market_gap:
            lines.append(f"  - {gap}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 4. Strategi Marketing (Growth Hacker) ---
    lines.append("## 4. Strategi Marketing (dari Growth Hacker)")
    mkt = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
    if mkt and mkt.status == AgentStatus.DONE:
        lines.append(f"- **Ide Bisnis Terpilih:** {mkt.recommended_idea}")
        lines.append(f"- **Target Segment:** {mkt.target_segment}")
        lines.append(f"- **Value Proposition (UVP):** {mkt.value_proposition}")
        lines.append(f"- **Go-to-Market Strategy:** {mkt.go_to_market_strategy}")
        lines.append("\n**Marketing Channels:**")
        for ch in mkt.marketing_channels:
            lines.append(f"  - {ch}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 5. Strategi Harga (Pricing Strategist) ---
    lines.append("## 5. Strategi Harga (dari Pricing Strategist)")
    prc = memory.get(AgentKey.PRICING, PricingOutput)
    if prc and prc.status == AgentStatus.DONE:
        lines.append(f"- **Strategi:** {prc.pricing_strategy}")
        lines.append(f"- **Rekomendasi Harga:** Rp {prc.recommended_price:,.0f} / unit")
        lines.append(f"- **Rentang Harga (Min-Max):** Rp {prc.price_range_min:,.0f} - Rp {prc.price_range_max:,.0f}")
        lines.append(f"- **Target Margin:** {prc.margin_percentage:.1f}%")
        lines.append(f"- **Justifikasi:** {prc.justification}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 6. Proyeksi Keuangan (CFO) ---
    lines.append("## 6. Proyeksi Keuangan (dari CFO)")
    cfo = memory.get(AgentKey.CFO, FinanceOutput)
    if cfo and cfo.status == AgentStatus.DONE:
        lines.append(f"- **Total Modal Awal (Startup Cost):** Rp {cfo.total_startup_cost:,.0f}")
        lines.append(f"- **Total Biaya Bulanan (Monthly Cost):** Rp {cfo.total_monthly_cost:,.0f}")
        lines.append(f"- **Rekomendasi Modal (Buffer):** Rp {cfo.recommended_capital:,.0f}")
        lines.append(f"- **Break-Even Point (BEP):** {cfo.bep_units:,.0f} unit terjual ({cfo.bep_months:,.1f} bulan)")
        lines.append(f"- **Proyeksi Revenue / Bulan:** Rp {cfo.projected_monthly_revenue:,.0f}")
        lines.append(f"- **Proyeksi Profit / Bulan (Bulan ke-6):** Rp {cfo.projected_net_profit_month6:,.0f}")
        lines.append(f"- **Tingkat Risiko Finansial:** {cfo.risk_level.upper()}")
        
        lines.append("\n**Rincian Modal Awal:**")
        for c in cfo.startup_cost:
            lines.append(f"  - {c.name}: Rp {c.amount:,.0f} ({c.category})")
            
        lines.append("\n**Rincian Biaya Operasional Bulanan:**")
        for c in cfo.monthly_cost:
            lines.append(f"  - {c.name}: Rp {c.amount:,.0f} ({c.category})")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 7. Kepatuhan Hukum (Legal & Compliance) ---
    lines.append("## 7. Kepatuhan Hukum (dari Legal & Compliance)")
    leg = memory.get(AgentKey.LEGAL, LegalOutput)
    if leg and leg.status == AgentStatus.DONE:
        lines.append(f"- **Yurisdiksi:** {leg.jurisdiction}")
        lines.append(f"- **Tingkat Keyakinan (Confidence):** {leg.confidence_level}")
        lines.append("\n**Izin / Lisensi yang Diperlukan:**")
        for lic in leg.required_licenses:
            name = lic.get('name', 'Unknown')
            auth = lic.get('authority', '-')
            url = lic.get('url', '')
            lines.append(f"  - **{name}** (Otoritas: {auth}){f' - [Referensi]({url})' if url else ''}")
        lines.append("\n**Catatan Kepatuhan Tambahan:**")
        for note in leg.compliance_notes:
            lines.append(f"  - {note}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 8. Rencana Operasional (Product Architect) ---
    lines.append("## 8. Rencana Operasional (dari Product Architect)")
    ops = memory.get(AgentKey.PRODUCT_ARCHITECT, OpsOutput)
    if ops and ops.status == AgentStatus.DONE:
        lines.append(f"- **Kapasitas Produksi Harian:** {ops.daily_capacity} unit")
        lines.append(f"- **Kebutuhan Minimum Staf:** {ops.minimum_staff} orang")
        lines.append(f"- **Estimasi Total Biaya Alat:** Rp {ops.total_equipment_cost:,.0f}")
        lines.append("\n**Alur Operasional (Flow):**")
        for i, step in enumerate(ops.operational_flow, 1):
            lines.append(f"  {i}. {step}")
        lines.append("\n**Daftar Kebutuhan Peralatan:**")
        for eq in ops.equipment_list:
            lines.append(f"  - {eq.name} (Qty: {eq.quantity}) — Prioritas: {eq.priority} — Est/Unit: Rp {eq.estimated_cost:,.0f}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 9. Rencana SDM (HR Planner) ---
    lines.append("## 9. Rencana SDM (dari HR Planner)")
    hr = memory.get(AgentKey.HR_PLANNER, HROutput)
    if hr and hr.status == AgentStatus.DONE:
        lines.append(f"- **Estimasi Gaji Bulanan Total:** Rp {hr.total_monthly_salary:,.0f}")
        lines.append("\n**Daftar Posisi dan Peran:**")
        for role in hr.roles:
            r_name = role.get('role', 'Unknown')
            r_count = role.get('count', 1)
            r_sal = role.get('salary', 0)
            lines.append(f"  - {r_name} (x{r_count}): Rp {r_sal:,.0f} / bulan")
        lines.append("\n**Prioritas Rekrutmen:**")
        for i, p in enumerate(hr.hiring_priority, 1):
            lines.append(f"  {i}. {p}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 10. SOP Operasional (SOP Designer) ---
    lines.append("## 10. SOP Operasional (dari SOP Designer)")
    sop = memory.get(AgentKey.SOP_DESIGNER, SOPOutput)
    if sop and sop.status == AgentStatus.DONE:
        lines.append("**Standar Kualitas & Layanan:**")
        for q in sop.quality_standards:
            lines.append(f"- {q}")
        lines.append("\n**Checklist Harian (Daily Routine):**")
        for chk in sop.daily_checklist:
            lines.append(f"- [ ] {chk}")
        lines.append("\n**Dokumen SOP Lengkap:**")
        for sec in sop.sop_sections:
            title = sec.get('title', 'Unknown Section')
            lines.append(f"\n### {title}")
            for step in sec.get('steps', []):
                lines.append(f"- {step}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 11. Temuan Critic ---
    lines.append("## 11. Temuan Critic")
    crt = memory.get(AgentKey.CRITIC, CriticOutput)
    if crt and crt.status == AgentStatus.DONE:
        lines.append(f"- **Tingkat Risiko Keseluruhan:** {crt.overall_risk_level.upper()}")
        lines.append(f"- **Wajib Revisi:** {'Ya' if crt.revision_required else 'Tidak'}")
        lines.append(f"- **Ringkasan Evaluasi:** {crt.summary}")
        if crt.issues_found:
            lines.append("\n**Daftar Isu yang Ditemukan:**")
            for issue in crt.issues_found:
                lines.append(f"  - **[{issue.severity.upper()}]** dari agen `{issue.agent_source}`: {issue.description}")
                lines.append(f"    *Saran Perbaikan:* {issue.suggestion}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    # --- 12. Analisis Risiko (Risk Manager) ---
    lines.append("## 12. Analisis Risiko (dari Risk Manager)")
    rsk = memory.get(AgentKey.RISK_MANAGER, RiskManagerOutput)
    if rsk and rsk.status == AgentStatus.DONE:
        lines.append(f"- **Kelayakan Rencana (Viability):** {rsk.overall_viability.upper()}")
        lines.append(f"- **Ringkasan Skenario Terburuk:** {rsk.worst_case_summary}")
        lines.append(f"- **Ringkasan Skenario Terbaik:** {rsk.best_case_summary}")
        lines.append("\n**Skenario Risiko Spesifik:**")
        for sc in rsk.risk_scenarios:
            lines.append(f"  - **{sc.scenario_name}**")
            lines.append(f"    - Probabilitas: {sc.probability.upper()} | Dampak: {sc.impact.upper()}")
            lines.append(f"    - Mitigasi: {sc.mitigation}")
        lines.append("\n**Rekomendasi Manajerial Utama:**")
        for rec in rsk.recommendations:
            lines.append(f"  - {rec}")
    else:
        lines.append("Data belum tersedia")
    lines.append("")

    return "\n".join(lines)


def save_report(report: str, filename: str = "output/laporan_bisnis.md") -> str:
    """
    Menyimpan laporan string ke dalam file. Membuat direktori jika belum tersedia.
    
    Args:
        report (str): Konten markdown yang sudah diformat.
        filename (str): Lokasi penyimpanan file output.
        
    Returns:
        str: Absolute path di mana file tersebut berhasil disimpan.
    """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
        
    return os.path.abspath(filename)


async def run(memory: SharedMemory) -> AgentOutput:
    """
    Utility agent untuk mengumpulkan semua data output di shared memory, 
    kemudian memformatnya menjadi dokumen laporan Markdown (MD) tunggal yang rapi.
    """
    agent_name = "output_formatter"
    logger.info(f"Mulai menyusun laporan bisnis gabungan di {agent_name}...")
    
    try:
        # 1. Format string Markdown dari memory
        report_content = format_business_report(memory)
        
        # 2. Simpan string tersebut ke file
        output_file = "output/laporan_bisnis.md"
        filepath = save_report(report_content, output_file)
        
        # 3. Catat di logger
        logger.info("Laporan berhasil disusun dan dirender ke Markdown!")
        logger.info(f"Lokasi Laporan: {filepath}")
        
        # 4. Return Output Agent
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.DONE
        )
        
    except Exception as e:
        logger.error(f"Gagal menyusun atau menyimpan laporan di output_formatter: {e}")
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error_message=f"Formatter Error: {str(e)}"
        )
