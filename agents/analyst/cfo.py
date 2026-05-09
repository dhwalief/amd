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
        
        # Validasi ketersediaan data dependency
        missing_deps = []
        if not market_data or market_data.status != AgentStatus.DONE:
            missing_deps.append("Growth Hacker")
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
        llm = create_llm("cfo", temperature=0.6, timeout=120)
        
        # 3. Buat System Prompt
        prompt = PromptTemplate.from_template(
            """Anda adalah Chief Financial Officer (CFO) untuk sistem perencanaan bisnis 'Go to America'.
            
Tugas Anda adalah merumuskan proyeksi keuangan yang realistis, Break Even Point (BEP), dan kebutuhan modal awal berdasarkan strategi pasar dan penetapan harga.

Konteks Bisnis (Dari Growth Hacker):
- Ide Bisnis Terpilih: {recommended_idea}
- Segmen Target: {target_segment}
- Go-to-Market Strategy: {go_to_market}

Konteks Harga (Dari Pricing Strategist):
- Harga Jual Rekomendasi: Rp {recommended_price:,.2f}
- Strategi Harga: {pricing_strategy}
- Target Margin: {margin_percentage}%

Tugas Anda adalah merumuskan rencana keuangan dan mengembalikannya HANYA dalam format JSON yang valid.
Format JSON harus persis seperti ini tanpa tambahan teks apapun di luar JSON:
{{
    "startup_cost": [
        {{"name": "...", "amount": 0.0, "category": "equipment", "is_recurring": false}}
    ],
    "monthly_cost": [
        {{"name": "...", "amount": 0.0, "category": "operational", "is_recurring": true}}
    ],
    "total_startup_cost": 0.0,
    "total_monthly_cost": 0.0,
    "recommended_capital": 0.0,
    "bep_units": 0.0,
    "bep_revenue": 0.0,
    "bep_months": 0.0,
    "projected_monthly_revenue": 0.0,
    "projected_net_profit_month6": 0.0,
    "risk_level": "medium"
}}

Panduan pengisian nilai JSON:
- startup_cost: array object (name, amount, category, is_recurring). category harus salah satu dari: "equipment", "operational", "marketing". is_recurring umumnya false untuk startup cost.
- monthly_cost: array object (name, amount, category, is_recurring). category harus salah satu dari: "equipment", "operational", "marketing". is_recurring umumnya true untuk biaya bulanan.
- total_startup_cost: total jumlah (float) dari seluruh startup_cost.
- total_monthly_cost: total jumlah (float) dari seluruh monthly_cost.
- recommended_capital: total_startup_cost ditambah buffer 25% untuk cadangan kas.
- bep_units: estimasi jumlah unit terjual yang dibutuhkan untuk mencapai BEP.
- bep_revenue: total pendapatan dalam Rupiah untuk mencapai BEP.
- bep_months: estimasi waktu (dalam bulan) untuk mencapai BEP.
- projected_monthly_revenue: estimasi pendapatan kotor per bulan (Rupiah).
- projected_net_profit_month6: estimasi laba bersih di bulan ke-6 beroperasi (Rupiah).
- risk_level: tingkat risiko finansial, harus salah satu dari: "high", "medium", atau "low".
"""
        )
        
        logger.info("Mengirim prompt ke LLM untuk merumuskan proyeksi keuangan...")
        
        chain = prompt | llm
        response = await chain.ainvoke({
            "recommended_idea": market_data.recommended_idea,
            "target_segment": market_data.target_segment,
            "go_to_market": market_data.go_to_market_strategy,
            "recommended_price": pricing_data.recommended_price,
            "pricing_strategy": pricing_data.pricing_strategy,
            "margin_percentage": pricing_data.margin_percentage
        })
        
        # 4. Parsing JSON dari output LLM
        logger.info("Memparsing respons JSON dari LLM...")
        
        content = response.content.strip()
        # Membersihkan backticks jika LLM mereturn markdown JSON
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        json_data = json.loads(content)
        
        # 5. Validasi Pydantic, Buat Output dan Simpan ke Memory
        output = FinanceOutput(**json_data)
        memory.set(AgentKey.CFO, output)
        
        logger.info("Eksekusi CFO agent selesai dengan sukses.")
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
