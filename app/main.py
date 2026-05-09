# File: main.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config.config import AGENT_CONFIG

# 1. Fungsi Pencipta LLM (Factory Pattern)
def create_llm(agent_key: str, temperature: float = 0.7, request_timeout: int = 120):
    """
    Fungsi untuk membuat instance ChatOpenAI berdasarkan config.py
    """
    if agent_key not in AGENT_CONFIG:
        raise ValueError(f"Agen '{agent_key}' tidak ditemukan di konfigurasi.")

    config = AGENT_CONFIG[agent_key]

    return ChatOpenAI(
        base_url=config["base_url"],
        api_key="EMPTY",  # vLLM lokal tidak butuh API Key
        model=config["model"],
        temperature=temperature,
        timeout=request_timeout,
        max_retries=2
    )

# 2. Inisialisasi Model
# Executive Layer
orchestrator_llm = create_llm("orchestrator", temperature=0.3)
critic_llm       = create_llm("critic",        temperature=0.2)
risk_manager_llm = create_llm("risk_manager",  temperature=0.1)

# Analyst Layer
geo_analyst_llm      = create_llm("analyst_pool", temperature=0.4)
competitor_scout_llm = create_llm("scout_inquisitor_pool", temperature=0.3)
growth_hacker_llm    = create_llm("analyst_pool", temperature=0.7)
pricing_llm          = create_llm("analyst_pool", temperature=0.1)  # Qwen2.5-14B
cfo_llm              = create_llm("cfo",           temperature=0.6)

# Worker Layer
inquisitor_llm       = create_llm("scout_inquisitor_pool", temperature=0.5)
legal_llm            = create_llm("analyst_pool",          temperature=0.1)
product_arch_llm     = create_llm("worker_pool",           temperature=0.4)
hr_planner_llm       = create_llm("worker_pool",           temperature=0.4)
sop_designer_llm     = create_llm("worker_pool",           temperature=0.1)

# 3. Contoh Penggunaan Multiplexing
# Identitas agent dibedakan lewat system prompt, bukan endpoint
geo_prompt = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah analis geografi yang ahli membaca data spasial dan demografi."),
    ("user", "{input}")
])

growth_prompt = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah Growth Hacker yang kreatif dan agresif."),
    ("user", "{input}")
])

pricing_prompt = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah ahli strategi penetapan harga yang memahami pasar Indonesia."),
    ("user", "{input}")
])

legal_prompt = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah konsultan hukum bisnis multi-yurisdiksi. Selalu sertakan sumber dan tanggal regulasi."),
    ("user", "{input}")
])

# Menyatukan Prompt dan LLM
geo_agent    = geo_prompt    | geo_analyst_llm
growth_agent = growth_prompt | growth_hacker_llm
pricing_agent = pricing_prompt | pricing_llm
legal_agent  = legal_prompt  | legal_llm

if __name__ == "__main__":
    print("Menguji koneksi ke Geo Analyst...")
    response = geo_agent.invoke({"input": "Apa keuntungan bisnis minimarket di pesisir pantai Makassar?"})
    print(response.content)