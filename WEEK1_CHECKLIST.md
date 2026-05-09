# ✅ STARTING CHECKLIST - Week 1

## Status Awal
- ✅ core/shared_memory.py — Complete (dengan MockSharedMemory)
- ✅ core/engine.py — Skeleton siap
- ✅ core/rag.py — Skeleton siap  
- ✅ core/test_shared_memory.py — Test template siap
- ✅ app/components.py — UI components siap
- ✅ app/dashboard.py — Streamlit dashboard siap
- ✅ data/ folder structure — Created
- ✅ output/reports/ — Created

---

## DEVELOPER 1 — Backend & Agent Logic

### Week 1: Foundation (Days 1-5)

#### Task 1: Complete SharedMemory Implementation ✅
- [x] File sudah ada: `core/shared_memory.py`
- [ ] **Test MockSharedMemory** 
  ```bash
  cd core
  pytest test_shared_memory.py -v
  ```
  Expected output: 4 test cases PASSED
  
- [ ] **Fix any import errors**
  - Check: `from schemas import AgentStatus, AgentOutput`
  - Check: `from shared_memory import DAG`

- [ ] **Create mock test data** di test file:
  - Test BusinessContext creation
  - Test dependency checking

**Timeline:** Monday - Tuesday
**Acceptance Criteria:**
- All tests pass
- `MockSharedMemory` methods work: `set()`, `get()`, `is_done()`, `deps_satisfied()`

---

#### Task 2: Complete core/schemas.py ✅
Current status: ~50% lengkap (Layer 1-3 ada, Layer 4 belum)

- [ ] **Baca existing schemas** di `core/schemas.py`
  - Lines 1-80: AgentStatus enum & AgentOutput base class ✓
  - Lines 80-150: Layer 1 (Inquisitor) ✓
  - Lines 150-200: Layer 2 (Analyst) ✓
  - Lines 200-250: Layer 3 (Finance/CFO) ✓

- [ ] **Add Layer 4 schemas** (Worker Layer outputs):
  ```python
  class LegalComplianceOutput(AgentOutput):
      agent_name: str = "legal_compliance"
      legal_requirements: list[str]  # e.g., "Register NIB", "Get SIUP"
      risk_factors: list[str]
      documentation_needed: list[str]
      recommended_jurisdictions: list[str]
      ...

  class ProductArchitectOutput(AgentOutput):
      agent_name: str = "product_architect"
      product_specs: dict
      ...

  class HRPlannerOutput(AgentOutput):
      ...

  class SOPDesignerOutput(AgentOutput):
      ...
  ```

- [ ] **Add Utility layer schemas**:
  ```python
  class BEPCalculationOutput(AgentOutput):
      agent_name: str = "bep_calculator"
      bep_units: int
      bep_revenue: float
      ...

  class CashflowOutput(AgentOutput):
      agent_name: str = "cashflow_simulator"
      monthly_projection: list[dict]  # 12 months
      ...
  ```

- [ ] **Add top-level BusinessPlan schema** yang aggregate semua:
  ```python
  class BusinessPlan(BaseModel):
      business_context: BusinessContext
      geo_analysis: GeoAnalystOutput
      competitor_analysis: CompetitorScoutOutput
      ... (all other outputs)
      created_at: str
  ```

**Timeline:** Wednesday
**Acceptance Criteria:**
- Semua schemas defined
- Import di test file berhasil
- No Pydantic validation errors

---

#### Task 3: Build core/engine.py ✅
File sudah ada dengan skeleton.

- [ ] **Complete DependencyEngine class**:
  - [x] `__init__()` ✓
  - [x] `register_agent()` ✓
  - [x] `execute_agent()` ✓
  - [x] `run_all()` (main DAG executor) ✓
  - [x] `get_summary()` ✓

- [ ] **Test dengan mock agents**:
  ```python
  async def mock_inquisitor(memory):
      # Return dummy output
      return InquisitorOutput(...)
  
  engine = DependencyEngine(memory)
  engine.register_agent(AgentKey.INQUISITOR, mock_inquisitor)
  results = await engine.run_all()
  ```

- [ ] **Verify DAG execution order**:
  - Inquisitor runs first (no deps)
  - Then Geo & Competitor parallel (both depend on Inquisitor)
  - Then Growth & Pricing parallel (depend on Geo & Competitor)
  - etc.

**Timeline:** Thursday-Friday
**Acceptance Criteria:**
- No syntax errors
- Mock agent test runs successfully
- Correct execution order

---

### Week 2: Agent Implementation (Days 6-12)

#### Task 4: Implement Analyst Agents

**Priority 1: Geo Analyst (Qwen2.5-14B)**
- Create `agents/analyst/geo_analyst.py`
- Load business context dari shared memory
- Call LLM with geographic analysis prompt
- Return GeoAnalystOutput

**Priority 2: Competitor Scout (Qwen2.5-7B)**
- Create `agents/analyst/competitor_scout.py`
- Integrate DuckDuckGo web search
- Parse competitor info
- Return CompetitorScoutOutput

**Priority 3: Growth Hacker (Qwen2.5-14B)**
- Create `agents/analyst/growth_hacker.py`
- Marketing strategy generation
- Return MarketOutput

**Priority 4: CFO (DeepSeek R1 Distill Qwen-14B)**
- Create `agents/analyst/cfo.py`
- Financial analysis & projections
- Return FinanceOutput

---

#### Task 5: Implement Utility Functions

Create `agents/utility/calculators.py`:
- `calculate_bep()` — Break-even analysis (pure Python, no LLM)
- `simulate_cashflow()` — 12-month projection
- `plan_supply_chain()` — Supply chain logic

---

### Week 3-4: Testing & Integration

- [ ] End-to-end test dengan mock data
- [ ] Performance testing
- [ ] Error handling & retries

---

## DEVELOPER 2 — Frontend & Data

### Week 1: Foundation (Days 1-5)

#### Task 1: Setup Data Structure ✅
- [x] Create `data/legal_docs/indonesia/` folder ✓
- [x] Create `data/legal_docs/usa/` folder ✓
- [x] Create `data/rag_kb/` folder ✓
- [x] Create `data/templates/` folder ✓
- [x] Create `output/reports/` folder ✓

- [ ] **Add sample legal documents**:
  - `data/legal_docs/indonesia/cv.txt` — Business entity registration
  - `data/legal_docs/indonesia/siup.txt` — Business permit requirements
  - `data/legal_docs/usa/llc.txt` — LLC formation
  - etc.

- [ ] **Add knowledge base files**:
  - `data/rag_kb/business_glossary.txt` — Terms & definitions
  - `data/rag_kb/market_research.txt` — Market data
  - `data/rag_kb/compliance.txt` — Regulatory info

**Timeline:** Monday-Tuesday
**Acceptance Criteria:**
- Semua folders exist
- 5+ knowledge base documents created

---

#### Task 2: Setup RAG Pipeline ✅
File sudah ada: `core/rag.py`

- [ ] **Test RAG pipeline**:
  ```python
  from core.rag import get_rag_pipeline
  
  rag = get_rag_pipeline()
  docs = rag.retrieve("legal requirements untuk minimarket", k=3)
  print(docs)
  ```

- [ ] **Uncomment embeddings saat ready**:
  - Pilih embedding model: `text-embedding-3-small` (OpenAI) atau open-source alternative
  - Test FAISS index building
  - Save & load dari disk

**Timeline:** Wednesday
**Acceptance Criteria:**
- `retrieve()` function returns results
- Index builds without errors

---

#### Task 3: Build Streamlit Components ✅
File sudah ada: `app/components.py`

- [ ] **Test components.py**:
  ```bash
  streamlit run app/components.py
  ```
  Expected: Component test page shows DAG status visualization

- [ ] **Fix any missing imports**:
  - Check: from core.shared_memory
  - Check: from core.schemas

**Timeline:** Thursday
**Acceptance Criteria:**
- No import errors
- Components render correctly

---

### Week 2: Frontend (Days 6-12)

#### Task 4: Build Streamlit Dashboard ✅
File sudah ada: `app/dashboard.py`

- [ ] **Test dashboard**:
  ```bash
  streamlit run app/dashboard.py
  ```
  Expected: Form input visible, submit button works

- [ ] **Complete TODO sections** di dashboard.py:
  - [ ] Import fix untuk AgentOutput display
  - [ ] Implement display_agent_output() untuk setiap agent
  - [ ] Connect dengan engine execution

- [ ] **Test form submission**:
  - Fill form → click Submit → verify memory state updated

**Timeline:** Monday-Wednesday
**Acceptance Criteria:**
- Dashboard loads without errors
- Form submission works
- Status display updates

---

#### Task 5: Web Search Integration

Create `core/web_search.py`:
- Wrapper untuk DuckDuckGo
- Query formatting per agent type
- Result parsing & caching

---

#### Task 6: Report Generation

Create `app/reports.py`:
- Markdown report generation
- PDF export (using `weasyprint` atau similar)
- Template rendering

---

### Week 3-4: Polish & Testing

- [ ] Add legal document templates
- [ ] Create sample test data
- [ ] UI polish & accessibility
- [ ] End-to-end demo

---

## 🎯 DAILY STANDUP FORMAT (5 min)

```
Dev1:
- Yesterday: Completed X
- Today: Working on Y  
- Blocker: Z (if any)

Dev2:
- Yesterday: Completed X
- Today: Working on Y
- Blocker: Z (if any)
```

---

## 📞 PAIR PROGRAMMING SESSIONS

- **Tuesday 11 AM** (30 min): Architecture review
- **Thursday 11 AM** (30 min): Integration checkpoint
- **Friday 3 PM** (30 min): Week review & plan next week

---

## 🚀 QUICK RUN COMMANDS

```bash
# Setup
poetry install
poetry shell

# Dev1: Test shared memory
cd core
pytest test_shared_memory.py -v

# Dev1: Run engine test
python -m core.engine

# Dev2: Test components
streamlit run app/components.py

# Dev2: Run dashboard
streamlit run app/dashboard.py

# Full integration (saat ready)
poetry run python app/main.py
```

---

## ⚠️ COMMON PITFALLS

1. **Import errors** — Always use absolute imports from project root
2. **Async mistakes** — All agent functions MUST be async
3. **Schema changes** — Coordinate dengan partner sebelum ubah schema
4. **Mock vs Real** — Use MockSharedMemory saat development
5. **JSON serialization** — Pastikan AgentOutput bisa `.model_dump_json()`

---

## 📚 REFERENCE

- Read first: `.agent/plan/agent-structure-plan.md`
- Then read: `.agent/plan/project-structure.md`
- Development rules: `.agent/rules.md`

---

Good luck! 🚀

Hubungi ketua kalau ada yang tidak jelas!
