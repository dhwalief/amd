import logging
from core.shared_memory import SharedMemory, AgentKey
from core.schemas import AgentStatus, AgentOutput, FinanceOutput, PricingOutput

logger = logging.getLogger(__name__)

def simulate_monthly_cashflow(
    startup_cost: float,
    monthly_revenue: float,
    monthly_cost: float,
    months: int = 12
) -> list[dict]:
    """
    Mensimulasikan arus kas bulanan bisnis dari bulan ke-1 hingga bulan ke-N.
    Bulan pertama menginisiasi cumulative profit dengan nilai minus dari startup cost.
    
    Args:
        startup_cost (float): Total biaya modal awal.
        monthly_revenue (float): Pendapatan (revenue) setiap bulannya.
        monthly_cost (float): Biaya (cost) tetap & variabel bulanan.
        months (int, optional): Jumlah bulan yang disimulasikan. Defaults to 12.
        
    Returns:
        list[dict]: Daftar riwayat cashflow setiap bulan.
        
    Contoh:
        >>> simulate_monthly_cashflow(10000000, 5000000, 3000000, 3)
        [
            {'month': 1, 'revenue': 5000000.0, 'cost': 3000000.0, 'net_profit': 2000000.0, 'cumulative_profit': -8000000.0, 'is_profitable': False},
            {'month': 2, 'revenue': 5000000.0, 'cost': 3000000.0, 'net_profit': 2000000.0, 'cumulative_profit': -6000000.0, 'is_profitable': False},
            {'month': 3, 'revenue': 5000000.0, 'cost': 3000000.0, 'net_profit': 2000000.0, 'cumulative_profit': -4000000.0, 'is_profitable': False}
        ]
    """
    cashflow = []
    cumulative_profit = -startup_cost
    
    for i in range(1, months + 1):
        net_profit = monthly_revenue - monthly_cost
        cumulative_profit += net_profit
        
        # Menentukan apakah sudah mencapai profitabilitas penuh (balik modal)
        is_profitable = cumulative_profit > 0
        
        cashflow.append({
            "month": i,
            "revenue": monthly_revenue,
            "cost": monthly_cost,
            "net_profit": net_profit,
            "cumulative_profit": cumulative_profit,
            "is_profitable": is_profitable
        })
        
    return cashflow


def find_breakeven_month(cashflow: list[dict]) -> int:
    """
    Mencari bulan pertama di mana is_profitable menjadi True (telah break-even/balik modal).
    
    Args:
        cashflow (list[dict]): Hasil simulasi cashflow dari simulate_monthly_cashflow().
        
    Returns:
        int: Angka bulan tercapainya BEP. Jika belum BEP, mengembalikan -1.
        
    Contoh:
        >>> data = [{'month': 1, 'is_profitable': False}, {'month': 2, 'is_profitable': True}]
        >>> find_breakeven_month(data)
        2
    """
    for entry in cashflow:
        if entry.get("is_profitable"):
            return entry["month"]
    return -1


def calculate_roi(cashflow: list[dict], startup_cost: float) -> float:
    """
    Menghitung persentase Return on Investment (ROI) untuk keseluruhan periode simulasi.
    
    Formula: ROI = (total_net_profit / startup_cost) * 100
    
    Args:
        cashflow (list[dict]): Hasil simulasi cashflow.
        startup_cost (float): Total biaya investasi (modal awal).
        
    Returns:
        float: Persentase ROI selama periode disimulasikan.
        
    Raises:
        ValueError: Jika startup_cost <= 0.
        
    Contoh:
        >>> cashflow = [{'net_profit': 2500000}, {'net_profit': 2500000}]
        >>> calculate_roi(cashflow, 20000000)
        25.0
    """
    if startup_cost <= 0:
        raise ValueError("Startup cost harus lebih dari 0 untuk menghitung ROI.")
        
    total_net_profit = sum(entry.get("net_profit", 0) for entry in cashflow)
    
    roi_percentage = (total_net_profit / startup_cost) * 100.0
    return roi_percentage


async def run(memory: SharedMemory) -> AgentOutput:
    """
    Utility agent untuk menyimulasikan arus kas berdasarkan output CFO dan Strategi Harga.
    """
    agent_name = "cashflow_simulator"
    logger.info(f"Mulai kalkulasi {agent_name}...")
    
    try:
        # Cek dependencies di memory
        if not memory.deps_satisfied([AgentKey.CFO, AgentKey.PRICING]):
            return AgentOutput(
                agent_name=agent_name,
                status=AgentStatus.LOCKED,
                error_message="Dependencies (CFO, Pricing) belum terpenuhi."
            )
            
        # Baca output Finance & Pricing
        finance_data = memory.get(AgentKey.CFO, FinanceOutput)
        pricing_data = memory.get(AgentKey.PRICING, PricingOutput)
        
        if not finance_data or not pricing_data:
            return AgentOutput(
                agent_name=agent_name,
                status=AgentStatus.FAILED,
                error_message="Gagal mendapatkan data FinanceOutput atau PricingOutput dari memory."
            )
            
        # Ekstrak parameter yang dibutuhkan untuk simulasi
        startup_cost = finance_data.total_startup_cost
        monthly_revenue = finance_data.projected_monthly_revenue
        monthly_cost = finance_data.total_monthly_cost
        
        # 1. Jalankan simulasi 12 bulan
        cashflow_12_months = simulate_monthly_cashflow(
            startup_cost=startup_cost,
            monthly_revenue=monthly_revenue,
            monthly_cost=monthly_cost,
            months=12
        )
        
        # 2. Cetak tabel cashflow per bulan
        logger.info("\n=== SIMULASI CASHFLOW (12 BULAN) ===")
        header = f"{'Bulan':^7} | {'Revenue':^15} | {'Cost':^15} | {'Net Profit':^15} | {'Cumulative':^15}"
        logger.info(header)
        logger.info("-" * len(header))
        
        for data in cashflow_12_months:
            month = data["month"]
            rev = f"Rp {data['revenue']:,.0f}"
            cost = f"Rp {data['cost']:,.0f}"
            prof = f"Rp {data['net_profit']:,.0f}"
            cum = f"Rp {data['cumulative_profit']:,.0f}"
            
            row_str = f"{month:^7} | {rev:>15} | {cost:>15} | {prof:>15} | {cum:>15}"
            logger.info(row_str)
            
        logger.info("====================================\n")
        
        # 3. Catat bulan BEP & ROI
        bep_month = find_breakeven_month(cashflow_12_months)
        roi = calculate_roi(cashflow_12_months, startup_cost)
        
        if bep_month != -1:
            logger.info(f"-> BEP Tercapai pada : Bulan ke-{bep_month}")
        else:
            logger.info("-> BEP Tercapai pada : Belum tercapai dalam periode simulasi (12 bulan)")
            
        logger.info(f"-> Proyeksi ROI (12m) : {roi:.2f} %")
        
        # Return AgentOutput dengan status DONE
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
        logger.error(f"Error sistem di cashflow_simulator: {e}")
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error_message=f"System error: {str(e)}"
        )
