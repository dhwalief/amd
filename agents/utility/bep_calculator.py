import logging
from core.shared_memory import SharedMemory, AgentKey
from core.schemas import AgentStatus, AgentOutput, FinanceOutput, PricingOutput

logger = logging.getLogger(__name__)

def calculate_bep_units(fixed_cost: float, price_per_unit: float, variable_cost_per_unit: float) -> float:
    """
    Menghitung Break-Even Point (BEP) dalam satuan unit.
    
    Formula: BEP Units = fixed_cost / (price_per_unit - variable_cost_per_unit)
    
    Args:
        fixed_cost (float): Total biaya tetap per bulan (total_monthly_cost).
        price_per_unit (float): Harga jual per unit (recommended_price).
        variable_cost_per_unit (float): Biaya variabel per unit.
        
    Returns:
        float: Jumlah unit yang harus terjual untuk BEP.
        
    Raises:
        ValueError: Jika price_per_unit <= variable_cost_per_unit
        
    Contoh Kalkulasi:
        >>> calculate_bep_units(10000000, 50000, 30000)
        500.0
    """
    if price_per_unit <= variable_cost_per_unit:
        raise ValueError("Harga jual per unit harus lebih besar dari biaya variabel per unit (margin positif).")
    
    return fixed_cost / (price_per_unit - variable_cost_per_unit)


def calculate_bep_revenue(bep_units: float, price_per_unit: float) -> float:
    """
    Menghitung Break-Even Point (BEP) dalam nilai mata uang (Revenue).
    
    Formula: BEP Revenue = bep_units * price_per_unit
    
    Args:
        bep_units (float): Jumlah unit BEP.
        price_per_unit (float): Harga jual per unit.
        
    Returns:
        float: Nilai pendapatan (revenue) untuk mencapai BEP.
        
    Contoh Kalkulasi:
        >>> calculate_bep_revenue(500.0, 50000)
        25000000.0
    """
    return bep_units * price_per_unit


def calculate_bep_months(total_startup_cost: float, monthly_net_profit: float) -> float:
    """
    Menghitung berapa bulan yang dibutuhkan untuk balik modal (Payback Period).
    
    Formula: BEP Months = total_startup_cost / monthly_net_profit
    
    Args:
        total_startup_cost (float): Total biaya modal awal.
        monthly_net_profit (float): Proyeksi laba bersih per bulan.
        
    Returns:
        float: Jumlah bulan untuk mencapai BEP modal.
        
    Raises:
        ValueError: Jika monthly_net_profit <= 0
        
    Contoh Kalkulasi:
        >>> calculate_bep_months(50000000, 10000000)
        5.0
    """
    if monthly_net_profit <= 0:
        raise ValueError("Proyeksi laba bersih per bulan harus lebih besar dari nol untuk bisa balik modal.")
        
    return total_startup_cost / monthly_net_profit


async def run(memory: SharedMemory) -> AgentOutput:
    """
    Utility agent untuk menghitung Break-Even Point (BEP).
    Murni menggunakan kalkulasi Python tanpa melibatkan pemanggilan LLM.
    """
    agent_name = "bep_calculator"
    logger.info(f"Mulai kalkulasi BEP di {agent_name}...")
    
    try:
        # Pastikan dependencies sudah selesai di shared memory
        if not memory.deps_satisfied([AgentKey.CFO, AgentKey.PRICING]):
            return AgentOutput(
                agent_name=agent_name,
                status=AgentStatus.LOCKED,
                error_message="Dependencies (CFO, Pricing) belum terpenuhi."
            )
            
        # 1. Baca FinanceOutput dan PricingOutput dari memory
        finance_data = memory.get(AgentKey.CFO, FinanceOutput)
        pricing_data = memory.get(AgentKey.PRICING, PricingOutput)
        
        if not finance_data or not pricing_data:
            return AgentOutput(
                agent_name=agent_name,
                status=AgentStatus.FAILED,
                error_message="Gagal mendapatkan data FinanceOutput atau PricingOutput."
            )
            
        # 2. Ambil data yang dibutuhkan dari object memory
        price_per_unit = pricing_data.recommended_price
        fixed_cost = finance_data.total_monthly_cost
        total_startup_cost = finance_data.total_startup_cost
        
        # Asumsi profit per bulan menggunakan proyeksi bulan ke-6
        monthly_net_profit = finance_data.projected_net_profit_month6
        
        # Hitung variable_cost_per_unit dari margin
        # Contoh: Jika margin 30% (bisa format 30.0 atau 0.3), kita pakai selisihnya
        margin = pricing_data.margin_percentage
        if margin > 1:
            margin = margin / 100.0  # Konversi ke persentase decimal (e.g., 30.0 -> 0.3)
            
        variable_cost_per_unit = price_per_unit * (1 - margin)
        
        logger.info(f"[BEP Input] Price/unit: {price_per_unit}, Variable Cost/unit: {variable_cost_per_unit}")
        logger.info(f"[BEP Input] Fixed Cost: {fixed_cost}, Startup Cost: {total_startup_cost}, Profit: {monthly_net_profit}")
        
        # 3. Jalankan ketiga kalkulasi
        bep_units = calculate_bep_units(fixed_cost, price_per_unit, variable_cost_per_unit)
        bep_revenue = calculate_bep_revenue(bep_units, price_per_unit)
        bep_months = calculate_bep_months(total_startup_cost, monthly_net_profit)
        
        # 4. Print hasil kalkulasi ke log
        logger.info("=== HASIL KALKULASI BEP ===")
        logger.info(f"BEP Units   : {bep_units:,.2f} unit per bulan")
        logger.info(f"BEP Revenue : Rp {bep_revenue:,.2f} per bulan")
        logger.info(f"BEP Months  : {bep_months:,.2f} bulan (Payback Period)")
        logger.info("===========================")
        
        # 5. Return AgentOutput biasa dengan status DONE
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.DONE
        )
        
    except ValueError as ve:
        logger.error(f"Validasi/Kalkulasi gagal: {ve}")
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error_message=f"Kalkulasi error: {str(ve)}"
        )
    except Exception as e:
        logger.error(f"Error sistem di bep_calculator: {e}")
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error_message=f"System error: {str(e)}"
        )
