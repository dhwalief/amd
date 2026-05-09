import asyncio
import logging

# 1. Import semua agent dari afiqa
print("[TEST 0] Menguji proses import...")
try:
    from agents.worker.inquisitor import run as inquisitor_run
    from agents.analyst.geo_analyst import run as geo_analyst_run
    from agents.analyst.growth_hacker import run as growth_hacker_run
    from agents.analyst.cfo import run as cfo_run
    from agents.worker.product_architect import run as product_architect_run
    from agents.worker.sop_designer import run as sop_designer_run
    print("[PASS] Import semua agent afiqa berhasil.")
except Exception as e:
    print(f"[FAIL] Import gagal: {e}")

# Import core dependencies
from core.factory import create_llm
from core.shared_memory import MockSharedMemory as SharedMemory, AgentKey

# Nonaktifkan logging berlebih dari Langchain/HTTP jika tidak dibutuhkan
logging.getLogger("httpx").setLevel(logging.WARNING)

async def run_tests():
    print("\n--- MULAI TESTING ---\n")
    
    # 2. Test koneksi LLM via factory
    print("[TEST 1] Koneksi LLM via Factory")
    try:
        # Mengambil konfigurasi dari scout_inquisitor_pool
        llm = create_llm("scout_inquisitor_pool", temperature=0.5)
        print("-> Mengirim pesan 'Halo, kamu siapa?' ke model...")
        response = await llm.ainvoke("Halo, kamu siapa? Jawab dengan satu kalimat singkat saja.")
        print(f"-> Hasil LLM: {response.content.strip()}")
        print("[PASS] Test koneksi LLM via factory berhasil.\n")
    except Exception as e:
        print(f"[FAIL] Test koneksi LLM gagal: {e}\n")

    # 3. Test Inquisitor end-to-end
    print("[TEST 2] Inquisitor Agent End-to-End")
    try:
        memory = SharedMemory()
        user_input = "Saya mau buka usaha kopi di Makassar, budget 30 juta, skill barista."
        print(f"-> Simulasi input user: '{user_input}'")
        
        # Eksekusi inquisitor
        result = await inquisitor_run(memory, user_input=user_input)
        
        # Validasi hasil
        print(f"-> Status Output: {result.status.name}")
        if result.status.name == "DONE" and result.business_context:
            ctx = result.business_context
            print(f"-> Location: {ctx.location}")
            print(f"-> Budget: Rp {ctx.budget:,.2f}")
            print(f"-> Skills: {', '.join(ctx.skills) if ctx.skills else 'Tidak ada'}")
            print("[PASS] Test eksekusi Inquisitor E2E berhasil.\n")
        else:
            print(f"[FAIL] Inquisitor tidak berstatus DONE atau context kosong. Error: {result.error_message}\n")
            
    except Exception as e:
        print(f"[FAIL] Test Inquisitor gagal dengan exception: {e}\n")
        
    print("--- SELESAI TESTING ---")

if __name__ == "__main__":
    asyncio.run(run_tests())
