import logging
from typing import Optional

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    InquisitorOutput,
    FinanceOutput,
    OpsOutput,
    SupplyPlanOutput,
    AgentStatus
)

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> Optional[SupplyPlanOutput]:
    """
    Supply Planner Agent (Utility Layer)
    Tugas: Murni kalkulasi Python deterministik untuk perencanaan supply dan HPP (tanpa LLM).
    """
    try:
        logger.info("Supply Planner Agent: Memulai eksekusi (Python Mode)...")
        
        # 1. Update status
        memory.set_status(AgentKey.SUPPLY_PLANNER, AgentStatus.RUNNING)
        
        # 2. Ambil data dari shared memory (Dependensi Utama)
        cfo_data = memory.get(AgentKey.CFO, FinanceOutput)
        if not cfo_data:
            error_msg = "Data CFO tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.SUPPLY_PLANNER, error_msg)
            return None
            
        ops_data = memory.get(AgentKey.PRODUCT_ARCHITECT, OpsOutput)
        if not ops_data:
            error_msg = "Data Product Architect (OpsOutput) tidak ditemukan di shared memory."
            logger.error(error_msg)
            memory.set_failed(AgentKey.SUPPLY_PLANNER, error_msg)
            return None

        # Ambil konteks dari Inquisitor untuk diferensiasi raw materials generik
        inquisitor_data = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
        
        # 3. Ekstrak Parameter Kalkulasi
        daily_capacity = float(ops_data.daily_capacity)
        if daily_capacity <= 0:
            daily_capacity = 1.0  # Fallback prevent division by zero
            
        business_idea = "Bisnis"
        sector = ""
        if inquisitor_data and inquisitor_data.business_context:
            business_idea = inquisitor_data.business_context.business_idea or business_idea
            sector = str(inquisitor_data.business_context.preferred_sector).lower()
        
        # 4. Generate Raw Materials secara deterministik berdasarkan sektor (tanpa LLM)
        raw_materials = []
        if "f&b" in sector or "makanan" in sector or "minuman" in sector or "kuliner" in sector:
            raw_materials = [
                {"item": "Bahan Pokok (Daging/Sayur/Tepung/Biji Kopi)", "unit": "kg", "qty_per_day": daily_capacity * 0.25, "price_per_unit": 45000.0},
                {"item": "Bahan Pelengkap (Bumbu/Susu/Sirup)", "unit": "kemasan", "qty_per_day": daily_capacity * 0.1, "price_per_unit": 35000.0},
                {"item": "Packaging (Box/Gelas/Kantong)", "unit": "pcs", "qty_per_day": daily_capacity, "price_per_unit": 1200.0}
            ]
        elif "jasa" in sector or "service" in sector:
            raw_materials = [
                {"item": "Consumables (Alat/Bahan Habis Pakai)", "unit": "set", "qty_per_day": daily_capacity, "price_per_unit": 5000.0},
                {"item": "ATK & Kelengkapan Administrasi", "unit": "pcs", "qty_per_day": daily_capacity * 0.5, "price_per_unit": 1500.0}
            ]
        else:
            raw_materials = [
                {"item": f"Material Utama {business_idea}", "unit": "unit", "qty_per_day": daily_capacity, "price_per_unit": 15000.0},
                {"item": "Packaging Standar", "unit": "pcs", "qty_per_day": daily_capacity, "price_per_unit": 2000.0}
            ]
            
        # 5. Kalkulasi Wajib
        daily_cogs = sum(float(item["qty_per_day"]) * float(item["price_per_unit"]) for item in raw_materials)
        monthly_cogs = daily_cogs * 26
        hpp_per_unit = daily_cogs / daily_capacity
        
        # 6. Supplier Rekomendasi Generik
        supplier_recommendations = [
            "Distributor Grosir Lokal / Pasar Induk terdekat",
            "Marketplace B2B (Mbizmarket, Ralali) untuk pengadaan kuantitas besar",
            "Supplier Spesialis (via Tokopedia/Shopee B2B) untuk Packaging & ATK",
            "Pabrik Produsen Langsung (apabila volume pemesanan memenuhi MOQ)"
        ]
        
        # 7. Bentuk Output Object
        result = SupplyPlanOutput(
            raw_materials=raw_materials,
            daily_cogs=float(daily_cogs),
            monthly_cogs=float(monthly_cogs),
            hpp_per_unit=float(hpp_per_unit),
            supplier_recommendations=supplier_recommendations
        )
        
        # 8. Simpan Hasil ke Memory
        memory.set(AgentKey.SUPPLY_PLANNER, result)
        logger.info(f"Supply Planner Agent: Selesai mengeksekusi tugas. HPP: Rp {hpp_per_unit:,.2f}")
        
        return result
        
    except Exception as e:
        error_msg = f"Terjadi kesalahan kalkulasi pada Supply Planner Agent: {e}"
        logger.error(error_msg)
        memory.set_failed(AgentKey.SUPPLY_PLANNER, error_msg)
        return None
