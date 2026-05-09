root/
│
├── .env                        # Endpoint vLLM (MI300X) & API Keys
├── requirements.txt            # Streamlit, Pydantic, Loguru, asyncio
├── run.sh                      # Script sekali klik untuk start
│
├── app/                        # FRONTEND (Streamlit)
│   ├── main.py                 # UI Utama & Dashboard Juri
│   ├── components.py           # Visualisasi DAG (Graphviz/Pillows)
│   └── styles.css              # Custom styling agar tidak "terlalu streamlit"
│
├── core/                       # BACKEND ENGINE
│   ├── engine.py               # Orchestrator & Dependency Runner (Async)
│   ├── state.py                # Local Singleton State (Pengganti Redis)
│   ├── schemas.py              # Pydantic models (Kontrak output agent)
│   └── factory.py              # LLM Connector (OpenAI SDK to vLLM)
│
├── agents/                     # LOGIC AGENT (Tetap seperti buatanmu)
│   ├── executive/              # Orchestrator, Critic, Risk Manager
│   ├── analyst/                # Geo, Competitor, Growth, CFO
│   ├── worker/                 # Inquisitor, Legal, Product, HR, SOP
│   └── utility/                # Pure Python (BEP, Cashflow, Supply)
│
├── data/                       # KNOWLEDGE BASE
│   ├── legal_docs/             # RAG sederhana (PDF/Text)
│   └── templates/              # Template Markdown untuk Report
│
└── output/                     # PERSISTENCE
    └── reports/                # Markdown hasil generate per sesi