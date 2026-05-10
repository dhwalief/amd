import logging
import json
from core.factory import create_llm
# pyrefly: ignore [missing-import]
from langchain_core.prompts import PromptTemplate
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from core.schemas import FinanceOutput, MarketOutput, PricingOutput, AgentStatus, CostItem
from core.shared_memory import SharedMemory, AgentKey

logger = logging.getLogger(__name__)

async def run(memory: SharedMemory) -> FinanceOutput:
    """
    Menjalankan CFO agent (Chief Financial Officer) untuk membuat proyeksi keuangan, BEP, dan modal awal
    berdasarkan strategi pasar dan harga yang telah ditentukan.
    """
    logger.info("Memulai eksekusi CFO agent...")
    
    # 1. Update status
    memory.set_status(AgentKey.CFO, AgentStatus.RUNNING)
    
    try:
        # 2. Ambil data Growth Hacker dan Pricing Strategist dari memory
        market_data = memory.get(AgentKey.GROWTH_HACKER, MarketOutput)
        pricing_data = memory.get(AgentKey.PRICING, PricingOutput)
        
        from core.schemas import UserValidationOutput
        user_val = memory.get(AgentKey.USER_VALIDATION, UserValidationOutput)
        
        # Validasi ketersediaan data dependency
        missing_deps = []
        if not user_val or user_val.status != AgentStatus.DONE:
            missing_deps.append("User Validation")
        if not pricing_data or pricing_data.status != AgentStatus.DONE:
            missing_deps.append("Pricing Strategist")
            
        if missing_deps:
            error_msg = f"Data dependency tidak ditemukan atau belum selesai: {', '.join(missing_deps)}."
            logger.error(error_msg)
            output = FinanceOutput(
                status=AgentStatus.FAILED, 
                error_message=error_msg,
                startup_cost=[],
                monthly_cost=[],
                total_startup_cost=0.0,
                total_monthly_cost=0.0,
                recommended_capital=0.0,
                bep_units=0.0,
                bep_revenue=0.0,
                bep_months=0.0,
                projected_monthly_revenue=0.0,
                projected_net_profit_month6=0.0,
                risk_level="high"
            )
            memory.set_failed(AgentKey.CFO, error_msg)
            return output
        
        # Inisialisasi LLM via Factory
        llm = create_llm("cfo", temperature=0.3, timeout=120)
        
        # 3. Buat System Prompt (Hanya minta List Item)
        prompt = PromptTemplate.from_template(
            """Anda adalah Data Extractor Keuangan.
            
Tugas Anda adalah merumuskan DAFTAR kebutuhan modal awal dan biaya bulanan berdasarkan ide bisnis yang telah disetujui pengguna.
JANGAN MENGHITUNG TOTALNYA, sistem kami yang akan menghitungnya.

Ide Bisnis Tervalidasi: {selected_idea}
Harga Jual Rekomendasi: Rp {recommended_price:,.2f}
Target Margin: {margin_percentage}%

Keluarkan HANYA format JSON valid seperti ini:
{{
    "startup_cost": [
        {{"name": "...", "amount": 0.0, "category": "equipment", "is_recurring": false}}
    ],
    "monthly_cost": [
        {{"name": "...", "amount": 0.0, "category": "operational", "is_recurring": true}}
    ],
    "risk_level": "medium"
}}
"""
        )
        
        logger.info("Mengirim prompt ke LLM untuk ekstrak item biaya...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "selected_idea": user_val.selected_idea,
            "recommended_price": pricing_data.recommended_price,
            "margin_percentage": pricing_data.margin_percentage
        })
        
        # 4. Parsing JSON dari output LLM
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        json_data = json.loads(content)
        
        # 5. KALKULASI DETERMINISTIK PYTHON (Mencegah Halusinasi Math LLM)
        startup_costs = json_data.get("startup_cost", [])
        monthly_costs = json_data.get("monthly_cost", [])
        
        total_startup = sum(item.get("amount", 0) for item in startup_costs)
        total_monthly = sum(item.get("amount", 0) for item in monthly_costs)
        
        recommended_capital = total_startup * 1.25  # Buffer 25%
        
        # Hitung BEP (Break Even Point)
        price = pricing_data.recommended_price
        margin = pricing_data.margin_percentage / 100.0
        contribution_margin_per_unit = price * margin
        
        if contribution_margin_per_unit > 0:
            bep_units = total_monthly / contribution_margin_per_unit
        else:
            bep_units = 0
            
        bep_revenue = bep_units * price
        
        # Asumsi penjualan (2x dari BEP untuk estimasi profit)
        projected_monthly_revenue = bep_revenue * 2
        projected_net_profit = projected_monthly_revenue - total_monthly - (projected_monthly_revenue * (1 - margin))
        
        if projected_net_profit > 0:
            bep_months = total_startup / projected_net_profit
        else:
            bep_months = 999.0
        
        # Buat objek akhir
        output = FinanceOutput(
            startup_cost=startup_costs,
            monthly_cost=monthly_costs,
            total_startup_cost=total_startup,
            total_monthly_cost=total_monthly,
            recommended_capital=recommended_capital,
            bep_units=bep_units,
            bep_revenue=bep_revenue,
            bep_months=bep_months,
            projected_monthly_revenue=projected_monthly_revenue,
            projected_net_profit_month6=projected_net_profit,
            risk_level=json_data.get("risk_level", "medium")
        )
        
        memory.set(AgentKey.CFO, output)
        logger.info("Eksekusi CFO agent (Deterministic Math) selesai dengan sukses.")
        return output

    except ValidationError as e:
        error_msg = f"Validasi output JSON gagal: {str(e)}"
        logger.error(error_msg)
        
        output = FinanceOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            startup_cost=[],
            monthly_cost=[],
            total_startup_cost=0.0,
            total_monthly_cost=0.0,
            recommended_capital=0.0,
            bep_units=0.0,
            bep_revenue=0.0,
            bep_months=0.0,
            projected_monthly_revenue=0.0,
            projected_net_profit_month6=0.0,
            risk_level="high"
        )
        memory.set_failed(AgentKey.CFO, error_msg)
        return output
        
    except json.JSONDecodeError as e:
        error_msg = f"Gagal parsing respons JSON dari LLM: {str(e)}"
        logger.error(error_msg)
        
        output = FinanceOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            startup_cost=[],
            monthly_cost=[],
            total_startup_cost=0.0,
            total_monthly_cost=0.0,
            recommended_capital=0.0,
            bep_units=0.0,
            bep_revenue=0.0,
            bep_months=0.0,
            projected_monthly_revenue=0.0,
            projected_net_profit_month6=0.0,
            risk_level="high"
        )
        memory.set_failed(AgentKey.CFO, error_msg)
        return output
        
    except Exception as e:
        error_msg = f"Eksekusi gagal: {str(e)}"
        logger.error(error_msg)
        
        output = FinanceOutput(
            status=AgentStatus.FAILED, 
            error_message=error_msg,
            startup_cost=[],
            monthly_cost=[],
            total_startup_cost=0.0,
            total_monthly_cost=0.0,
            recommended_capital=0.0,
            bep_units=0.0,
            bep_revenue=0.0,
            bep_months=0.0,
            projected_monthly_revenue=0.0,
            projected_net_profit_month6=0.0,
            risk_level="high"
        )
        memory.set_failed(AgentKey.CFO, error_msg)
        return output
