# 🚀 QUICK START - Developer Guide

**Read this first!** (5 min)

---

## 📌 You Have 2 Roles

### 👤 Developer 1 — Backend & Agent Logic ⚡
**Your mission:** Core infrastructure, agent execution, state management

**Week 1 Tasks:**
1. `core/test_shared_memory.py` — Run tests (Mon-Tue)
2. `core/schemas.py` — Add Layer 4 + Utility schemas (Wed)
3. `core/engine.py` — Complete DAG executor (Thu-Fri)

**First command to run:**
```bash
cd d:\AMERIKA\amd\core
pytest test_shared_memory.py -v
```

**Expected result:** 4 tests PASSED ✅

---

### 👤 Developer 2 — Frontend & Data 🎨
**Your mission:** UI/UX, data processing, RAG pipeline

**Week 1 Tasks:**
1. `data/` folder — Add legal docs & KB files (Mon-Tue)
2. `core/rag.py` — Test retrieve function (Wed)
3. `app/components.py` — Test Streamlit components (Thu)

**First command to run:**
```bash
cd d:\AMERIKA\amd
streamlit run app/components.py
```

**Expected result:** Component test page loads ✅

---

## 📋 Dependency Between You

```
Dev2 creates data/ → Dev1 reads data in RAG
Dev1 builds engine → Dev2 displays status in UI
Both work independently most of the time
Sync on Tue/Thu at 11 AM
```

---

## 🎯 Week 1 Success Criteria

**Dev1 Done When:**
- ✅ All unit tests pass
- ✅ Schemas complete
- ✅ Engine ready to register agents

**Dev2 Done When:**
- ✅ data/ folder has 20+ files
- ✅ RAG retrieve() works
- ✅ Streamlit dashboard loads

**Both Done When:**
- ✅ Can run: `streamlit run app/dashboard.py`
- ✅ Form submits → Memory updates ✅
- ✅ Mock integration works

---

## 🔑 Key Commands

```bash
# Dev1: Test backend
cd core && pytest test_shared_memory.py -v

# Dev1: Run engine
python -m core.engine

# Dev2: Test components
streamlit run app/components.py

# Dev2: Run dashboard
streamlit run app/dashboard.py

# Everyone: Check structure
tree /F d:\AMERIKA\amd
```

---

## 📖 Must-Read Files (in order)

1. `.agent/rules.md` — 2 min
2. `.agent/plan/agent-structure-plan.md` — 10 min
3. `WEEK1_CHECKLIST.md` — 5 min
4. This file — Done ✅

---

## 🆘 If You Get Stuck

**Import error?**
- Check relative path vs absolute path
- Use: `from core.shared_memory import ...` (absolute)
- Don't use: `from shared_memory import ...` (relative)

**Test fails?**
- Read error message carefully
- Check all dependencies installed: `poetry install`
- Run from correct directory

**Not sure what to do?**
- Check WEEK1_CHECKLIST.md for your role
- Ask on daily standup (10 min)
- Call pair programming session (Tue/Thu 11 AM)

---

## 📞 Team Sync

- **Daily:** 10-min standup (share progress)
- **Tuesday 11 AM:** Pair programming (30 min)
- **Thursday 11 AM:** Pair programming (30 min)
- **Friday 3 PM:** Week review (30 min)

---

## ✨ Good Luck!

You have everything you need.
Read the checklist.
Follow the tasks.
Ask questions.

**Week 1 goal:** Solid foundation ✅
**Week 2-3 goal:** Implement agents 🤖
**Week 4 goal:** Polish & test 🎉

**Let's build something amazing!** 🚀

---

**Next:** Open `WEEK1_CHECKLIST.md` in your editor → start with your first task
