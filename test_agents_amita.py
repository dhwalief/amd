import asyncio
from core.factory import create_llm

print("=== 1. Testing Imports ===")

try:
    import agents.analyst.competitor_scout
    print("PASS: Import agents.analyst.competitor_scout")
except Exception as e:
    print(f"FAIL: Import agents.analyst.competitor_scout ({e})")

try:
    import agents.analyst.pricing_strategist
    print("PASS: Import agents.analyst.pricing_strategist")
except Exception as e:
    print(f"FAIL: Import agents.analyst.pricing_strategist ({e})")

try:
    import agents.worker.legal
    print("PASS: Import agents.worker.legal")
except Exception as e:
    print(f"FAIL: Import agents.worker.legal ({e})")

try:
    import agents.worker.hr_planner
    print("PASS: Import agents.worker.hr_planner")
except Exception as e:
    print(f"FAIL: Import agents.worker.hr_planner ({e})")

try:
    import agents.utility.supply_planner
    print("PASS: Import agents.utility.supply_planner")
except Exception as e:
    print(f"FAIL: Import agents.utility.supply_planner ({e})")

try:
    import agents.executive.critic
    print("PASS: Import agents.executive.critic")
except Exception as e:
    print(f"FAIL: Import agents.executive.critic ({e})")

try:
    import agents.executive.risk_manager
    print("PASS: Import agents.executive.risk_manager")
except Exception as e:
    print(f"FAIL: Import agents.executive.risk_manager ({e})")


async def test_llm_connection():
    print("\n=== 2. Testing LLM Connection ===")
    try:
        llm = create_llm("critic", temperature=0.2)
        response = llm.invoke("Halo, kamu siapa?")
        print("PASS: LLM Connection")
        # Handle Windows stdout encoding issue for emojis/unicode
        try:
            print(f"Hasil: {response.content}")
        except UnicodeEncodeError:
            print(f"Hasil: {response.content.encode('ascii', 'ignore').decode('ascii')}")
    except Exception as e:
        print(f"FAIL: LLM Connection ({e})")

async def main():
    await test_llm_connection()

if __name__ == "__main__":
    # 4. Jalankan dengan asyncio.run() untuk bagian async
    asyncio.run(main())
