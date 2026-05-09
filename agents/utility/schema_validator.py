import logging
import json
from pydantic import ValidationError

from core.shared_memory import SharedMemory, AgentKey
from core.schemas import (
    AgentStatus,
    AgentOutput,
    BusinessContext,
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

# Mapping AgentKey ke Schema Output masing-masing
SCHEMA_MAP = {
    AgentKey.INQUISITOR: InquisitorOutput,
    AgentKey.GEO_ANALYST: GeoAnalystOutput,
    AgentKey.COMPETITOR: CompetitorScoutOutput,
    AgentKey.GROWTH_HACKER: MarketOutput,
    AgentKey.PRICING: PricingOutput,
    AgentKey.CFO: FinanceOutput,
    AgentKey.LEGAL: LegalOutput,
    AgentKey.PRODUCT_ARCHITECT: OpsOutput,
    AgentKey.HR_PLANNER: HROutput,
    AgentKey.SOP_DESIGNER: SOPOutput,
    AgentKey.CRITIC: CriticOutput,
    AgentKey.RISK_MANAGER: RiskManagerOutput,
}

def validate_agent_output(agent_key: AgentKey, data: dict) -> tuple[bool, str]:
    """
    Validasi apakah tipe data dictionary (data mentah) mematuhi Pydantic schema 
    dari agen yang bersangkutan.
    
    Args:
        agent_key (AgentKey): Key dari agen.
        data (dict): Dictionary mentah yang akan divalidasi.
        
    Returns:
        tuple[bool, str]: (True, "valid") jika berhasil divalidasi. (False, pesan error) jika gagal.
    """
    schema_class = SCHEMA_MAP.get(agent_key)
    if not schema_class:
        # Jika Orchestrator atau agent lain yang tidak masuk di mapping dasar
        return True, "Tidak ada di schema mapping (dianggap bypass)"
        
    try:
        # Mencoba instantiate schema dengan data dict
        schema_class(**data)
        return True, "valid"
    except ValidationError as e:
        return False, f"Pydantic Validation Error:\n{str(e)}"
    except Exception as e:
        return False, f"Unknown error saat validasi schema: {e}"


def validate_all_outputs(memory: SharedMemory) -> dict[str, tuple[bool, str]]:
    """
    Melakukan validasi Pydantic untuk *semua* output agent yang sudah 
    memiliki status DONE di shared memory.
    
    Args:
        memory (SharedMemory): Instance memory (bisa Redis atau Mock).
        
    Returns:
        dict[str, tuple[bool, str]]: Mapping nama agent ke hasil validasinya.
    """
    results = {}
    
    for key in AgentKey:
        schema_class = SCHEMA_MAP.get(key)
        if not schema_class:
            continue
            
        # Hanya mengecek yang sudah selesai
        if memory.get_status(key) != AgentStatus.DONE:
            continue
            
        raw = None
        # Ekstrak data mentah JSON sesuai dengan tipe shared memory
        try:
            if hasattr(memory, "redis"):
                # Redis-based SharedMemory
                raw = memory.redis.get(memory._key(key))
            elif hasattr(memory, "_store"):
                # MockSharedMemory local dict
                # key di mock _store biasanya value string dari enum
                raw = memory._store.get(key.value)
                
            if not raw:
                # Kemungkinan fail fetching data
                results[key.value] = (False, "Status DONE tapi raw data kosong di memory.")
                continue
                
            # Konversi raw data ke dict
            if isinstance(raw, str):
                data = json.loads(raw)
            elif isinstance(raw, bytes):
                data = json.loads(raw.decode('utf-8'))
            elif hasattr(raw, "model_dump"): # Jika kebetulan Pydantic object
                data = raw.model_dump()
            elif isinstance(raw, dict):
                data = raw
            else:
                results[key.value] = (False, f"Tipe data raw tidak valid: {type(raw)}")
                continue
                
            # Validasi Pydantic Schema
            is_valid, msg = validate_agent_output(key, data)
            results[key.value] = (is_valid, msg)
            
        except json.JSONDecodeError as e:
            results[key.value] = (False, f"Bukan JSON yang valid: {e}")
        except Exception as e:
            results[key.value] = (False, f"Error ekstrasi memory: {e}")
            
    return results


def validate_business_context(data: dict) -> tuple[bool, str]:
    """
    Validasi khusus (business rules) untuk model BusinessContext, melampaui Pydantic type checking.
    
    Args:
        data (dict): Dictionary BusinessContext mentah.
        
    Returns:
        tuple[bool, str]: (True, "valid") jika semua bisnis rule terpenuhi, (False, pesan error) jika melanggar.
    """
    try:
        # Pastikan format dasarnya sudah benar via Pydantic
        ctx = BusinessContext(**data)
        
        # Validasi bisnis (Custom Rules)
        if ctx.budget <= 0:
            return False, "budget harus > 0 (modal tidak boleh nol atau minus)"
            
        if not ctx.location or not ctx.location.strip():
            return False, "location tidak boleh string kosong"
            
        if not ctx.skills or len(ctx.skills) == 0:
            return False, "skills tidak boleh kosong, harus ada minimal 1 keahlian"
            
        return True, "valid"
        
    except ValidationError as e:
        return False, f"Gagal parsing Pydantic saat mengecek BusinessContext: {str(e)}"
    except Exception as e:
        return False, f"Unknown error saat memvalidasi BusinessContext: {e}"


async def run(memory: SharedMemory) -> AgentOutput:
    """
    Utility agent untuk menyisir semua output yang ada di shared memory
    dan memverifikasi apakah struktur datanya taat terhadap Pydantic schemas yang ditetapkan.
    """
    agent_name = "schema_validator"
    logger.info(f"Mulai validasi semua output di {agent_name}...")
    
    try:
        # Jalankan validasi semua output di DAG yang berstatus DONE
        results = validate_all_outputs(memory)
        
        # Ekstra Validasi untuk Inquisitor (jika sudah DONE)
        if memory.get_status(AgentKey.INQUISITOR) == AgentStatus.DONE:
            inq_model = memory.get(AgentKey.INQUISITOR, InquisitorOutput)
            if inq_model and inq_model.business_context:
                is_valid_ctx, msg_ctx = validate_business_context(inq_model.business_context.model_dump())
                results["business_context_rules"] = (is_valid_ctx, msg_ctx)

        logger.info("\n=== HASIL VALIDASI SCHEMA ===")
        
        if not results:
            logger.info("ℹ️ Tidak ada output agent berstatus DONE untuk divalidasi.")
        
        for agent_val, (is_valid, msg) in results.items():
            if is_valid:
                logger.info(f"✅ {agent_val: <25}: Valid")
            else:
                # Sengaja dilog sebagai WARNING sesuai requirement, alih-alih error langsung putus
                logger.warning(f"❌ {agent_val: <25}: TIDAK VALID -> {msg}")
                
        logger.info("=============================\n")
        
        # Return AgentOutput standar
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.DONE
        )
        
    except Exception as e:
        logger.error(f"Error sistem di schema_validator: {e}")
        return AgentOutput(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error_message=f"System error: {e}"
        )
