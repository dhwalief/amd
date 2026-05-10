from core.schemas import AgentKey

# ─────────────────────────────────────────────
# DEPENDENCY GRAPH — Business Co-Pilot (v5)
# ─────────────────────────────────────────────
# Menyertakan Virtual Node (USER_REVIEW) untuk menjeda pipeline (DAG Pausing).

DAG: dict[AgentKey, list[AgentKey]] = {
    AgentKey.INQUISITOR:         [],
    AgentKey.GEO_ANALYST:        [AgentKey.INQUISITOR],
    AgentKey.COMPETITOR:         [AgentKey.INQUISITOR],
    AgentKey.GROWTH_HACKER:      [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR],
    AgentKey.PRICING:            [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR],
    
    # Proposal disiapkan sebelum CFO agar CFO memiliki baseline opsi, atau
    # Orchestrator membuat proposal setelah Analyst Layer (Geo, dkk) selesai.
    AgentKey.PROPOSAL_GENERATOR: [AgentKey.GROWTH_HACKER, AgentKey.PRICING],
    
    # Jeda untuk Review Pertama
    AgentKey.USER_REVIEW_1:      [AgentKey.PROPOSAL_GENERATOR],
    
    # Worker Layer + CFO berjalan SETELAH Proposal disetujui
    AgentKey.CFO:                [AgentKey.USER_REVIEW_1],
    AgentKey.LEGAL:              [AgentKey.CFO],
    AgentKey.PRODUCT_ARCHITECT:  [AgentKey.USER_REVIEW_1],
    AgentKey.HR_PLANNER:         [AgentKey.CFO],
    AgentKey.SUPPLY_PLANNER:     [AgentKey.CFO],
    AgentKey.SOP_DESIGNER:       [AgentKey.PRODUCT_ARCHITECT,
                                  AgentKey.HR_PLANNER,
                                  AgentKey.SUPPLY_PLANNER],
                                  
    # Validation
    AgentKey.CRITIC:             [AgentKey.LEGAL, AgentKey.SOP_DESIGNER],
    AgentKey.RISK_MANAGER:       [AgentKey.CRITIC],
    AgentKey.ORCHESTRATOR:       [AgentKey.CRITIC, AgentKey.RISK_MANAGER],
    
    # Jeda untuk Final Review
    AgentKey.USER_REVIEW_2:      [AgentKey.ORCHESTRATOR],
}

# ─────────────────────────────────────────────
# PARTIAL RE-RUN MAP
# ─────────────────────────────────────────────
# Digunakan untuk menghapus status DONE dari agen terdampak jika ada perubahan feedback user.

RERUN_MAP: dict[str, list[AgentKey]] = {
    "tambah_karyawan":       [AgentKey.CFO, AgentKey.HR_PLANNER, AgentKey.RISK_MANAGER, AgentKey.CRITIC, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2],
    "ubah_modal":            [AgentKey.CFO, AgentKey.RISK_MANAGER, AgentKey.SUPPLY_PLANNER, AgentKey.HR_PLANNER, AgentKey.CRITIC, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2],
    "ubah_jenis_bisnis":     [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR, AgentKey.GROWTH_HACKER, AgentKey.PRICING, AgentKey.PROPOSAL_GENERATOR, AgentKey.USER_REVIEW_1, AgentKey.CFO, AgentKey.LEGAL, AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER, AgentKey.SUPPLY_PLANNER, AgentKey.SOP_DESIGNER, AgentKey.CRITIC, AgentKey.RISK_MANAGER, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2],
    "ubah_lokasi":           [AgentKey.GEO_ANALYST, AgentKey.COMPETITOR, AgentKey.GROWTH_HACKER, AgentKey.PRICING, AgentKey.PROPOSAL_GENERATOR, AgentKey.USER_REVIEW_1, AgentKey.CFO, AgentKey.LEGAL, AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER, AgentKey.SUPPLY_PLANNER, AgentKey.SOP_DESIGNER, AgentKey.CRITIC, AgentKey.RISK_MANAGER, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2],
    "ubah_produk":           [AgentKey.PRODUCT_ARCHITECT, AgentKey.PRICING, AgentKey.SUPPLY_PLANNER, AgentKey.CFO, AgentKey.SOP_DESIGNER, AgentKey.CRITIC, AgentKey.RISK_MANAGER, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2],
    # fallback jika perubahan terlalu umum
    "all_downstream":        [AgentKey.CFO, AgentKey.LEGAL, AgentKey.PRODUCT_ARCHITECT, AgentKey.HR_PLANNER, AgentKey.SUPPLY_PLANNER, AgentKey.SOP_DESIGNER, AgentKey.CRITIC, AgentKey.RISK_MANAGER, AgentKey.ORCHESTRATOR, AgentKey.USER_REVIEW_2]
}
