# 🗺️ מפת קריאות API בפרויקט

## סיכום: איפה משתמשים בכל מודל

```
┌─────────────────────────────────────────────────────────────┐
│                  CENTRAL ORCHESTRATOR                       │
│                    (הקורה של הסיסטם)                       │
└─────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
            PHASE A        PHASE B       (Optional)
         (תמיד רץ)      (אם צריך)
            │                │
       ┌────┴────┐       ┌────┴────┐
       ▼         ▼       ▼         ▼
    VALIDATE  ANSWER  POLISH    SYNTHESIS
      +                  +
   GEMINI*          GEMINI*
   (x2)             (1x)
```

**🎯 * = אתה יכול להחליף לClaude / ChatGPT / ClaudeOpus**

---

## 📍 קריאות API מפורטות

### 1️⃣ **VALIDATION_ENGINE** (Phase A - שלב 1)
📁 `src/peer_review_mcp/tools/validation_engine.py`

**שני REVIEWERS:**
1. **GeminiReviewer** ← **קריאה ל-API #1**
   - Mode: `validate`
   - Input: `question` + `context_summary`
   - Output: רשימת review points
   - **Client ברירת מחדל:** GeminiClient

2. **GeminiClarityReviewer** ← **קריאה ל-API #2**
   - Mode: `validate`
   - Input: `question` + `context_summary`
   - Output: רשימת review points על clarity
   - **Client ברירת מחדל:** GeminiClient

---

### 2️⃣ **SYNTHESIS_ENGINE** (Phase A - שלב 2)
📁 `src/peer_review_mcp/tools/synthesis_engine.py`

**AnswerSynthesisClient** ← **קריאה ל-API #3**
- Input: `question` + `context_summary` + `review_points`
- Output: התשובה המיוחדת
- **Client ברירת מחדל:** GeminiClient

```python
# central_orchestrator.py, line 123:
result = answer_tool(question, context_summary, review_points)
```

---

### 3️⃣ **POLISHING_ENGINE** (Phase B - אם צריך)
📁 `src/peer_review_mcp/tools/polishing_engine.py`

**GeminiReviewer** ← **קריאה ל-API #4**
- Mode: `polish`
- Input: `question` + `answer` + `context_summary`
- Output: רשימת הערות לשיפור
- **Client ברירת מחדל:** GeminiClient

```python
# central_orchestrator.py, line 80:
if should_polish:
    answer = self._run_phase_b(question, answer, context_summary, decision_log)
```

---

### 4️⃣ **POLISH SYNTHESIS** (Phase B - סיום)
📁 `src/peer_review_mcp/orchestrator/central_orchestrator.py`

**GeminiClient** ← **קריאה ל-API #5**
- Input: prompt עם התשובה + הערות הפולישינג
- Output: התשובה המשופרת
- **Client ברירת מחדל:** GeminiClient

```python
# central_orchestrator.py, line 159:
polished = self.polish_llm.generate(prompt).strip()
```

---

## 🎯 סך קריאות ל-API לכל request

```
מינימום: 3 קריאות (Phase A בלבד)
├─ API #1: Gemini Review (validation - issues)
├─ API #2: Gemini Review (validation - clarity)  
└─ API #3: Gemini Answer (synthesis)

מקסימום: 5 קריאות (Phase A + Phase B)
├─ API #1: Gemini Review (validation - issues)
├─ API #2: Gemini Review (validation - clarity)
├─ API #3: Gemini Answer (synthesis)
├─ API #4: Gemini Review (polish suggestions)
└─ API #5: Gemini Polish (final synthesis)
```

---

## ✅ Clients זמינים כרגע

1. **GeminiClient** - `from peer_review_mcp.LLM import GeminiClient`
2. **ClaudeClient** - `from peer_review_mcp.LLM import ClaudeClient`
3. **ChatGPTClient** - `from peer_review_mcp.LLM import ChatGPTClient`
4. **ClaudeOpusClient** - `from peer_review_mcp.LLM import ClaudeOpusClient`

כל אחד יש ממשק זהה: `client.generate(prompt: str) -> str`

---

## 🔄 איך להחליף מודל

### דוגמה 1: החלף ValidationEngine ל-Claude + ChatGPT

**File: `src/peer_review_mcp/tools/validation_engine.py`**

```python
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM import ClaudeClient, ChatGPTClient  # ← Import חדש
from peer_review_mcp.reviewers.gemini_clarity_reviewer import GeminiClarityReviewer

class ValidationEngine:
    def __init__(self):
        claude = ClaudeClient()
        gpt = ChatGPTClient()
        
        self.reviewers = [
            GeminiReviewer(claude),          # Issues detection with Claude
            GeminiReviewer(gpt),             # Clarity with ChatGPT
        ]
```

---

### דוגמה 2: Multi-Model System (מומלץ)

```python
from peer_review_mcp.LLM import GeminiClient, ClaudeClient, ChatGPTClient
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer

class ValidationEngine:
    def __init__(self):
        gemini = GeminiClient()
        claude = ClaudeClient()
        gpt = ChatGPTClient()
        
        # כל reviewer עם model שונה
        self.reviewers = [
            GeminiReviewer(gemini),   # זול ומהיר
            GeminiReviewer(claude),   # יותר nuanced
            GeminiReviewer(gpt),      # טוב בlogic
        ]
```

---

### דוגמה 3: החלף Polishing ל-Claude

**File: `src/peer_review_mcp/tools/polishing_engine.py`**

```python
from peer_review_mcp.LLM import GeminiClient, ClaudeClient
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer

class PolishingEngine:
    def __init__(self):
        claude = ClaudeClient()
        
        self.reviewers: list[BaseReviewer] = [
            GeminiReviewer(claude),  # כתיבה טובה יותר
        ]
```

---

### דוגמה 4: חליפי מודל ב-CentralOrchestrator

**File: `src/peer_review_mcp/orchestrator/central_orchestrator.py`**

```python
from peer_review_mcp.LLM import GeminiClient, ChatGPTClient

class CentralOrchestrator:
    def __init__(self):
        # Polish synthesis with ChatGPT
        self.polish_llm = ChatGPTClient()
```

---

### דוגמה 5: SynthesisEngine עם Claude

**File: `src/peer_review_mcp/tools/synthesis_engine.py`**

```python
from peer_review_mcp.LLM import GeminiClient, ClaudeClient
from peer_review_mcp.LLM.synthesis_client import AnswerSynthesisClient

class SynthesisEngine:
    def __init__(self):
        claude = ClaudeClient()  # ← חדש
        self.synthesizer = AnswerSynthesisClient(claude)
```

---

## 📊 עלויות משוערות

| Model | Cost per API call | Speed | Quality |
|-------|------------------|-------|---------|
| Gemini | $0.00001-0.0001 | ⚡⚡⚡ מהיר | ⭐⭐⭐ טוב |
| Claude | $0.003-0.015 | ⚡⚡ בינוני | ⭐⭐⭐⭐ מעולה |
| ChatGPT | $0.0005-0.002 | ⚡⚡ בינוני | ⭐⭐⭐⭐ מעולה |
| Claude Opus | $0.015-0.075 | ⚡ איטי | ⭐⭐⭐⭐⭐ הטוב ביותר |

---

## 🎓 המלצות

### Cost-Effective (מומלץ לרוב)
```
ValidationEngine:     Gemini x2       (זול, מהיר)
SynthesisEngine:      Gemini          (זול, מהיר)
PolishingEngine:      Claude          (טוב יותר)
FinalSynthesis:       Gemini          (זול)
```
**עלות משוערת:** $0.0001-0.001 per request

### Quality-First
```
ValidationEngine:     Claude + ChatGPT + Gemini
SynthesisEngine:      Claude
PolishingEngine:      Claude
FinalSynthesis:       Claude Opus
```
**עלות משוערת:** $0.03-0.1 per request

### Balanced
```
ValidationEngine:     Gemini + Claude
SynthesisEngine:      Claude
PolishingEngine:      Gemini
FinalSynthesis:       ChatGPT
```
**עלות משוערת:** $0.005-0.02 per request

---

## 🚀 קיצור דרך - להחליף הכל לClaude

בקובץ אחד: `src/peer_review_mcp/tools/validation_engine.py`

```python
# שנה מ:
from peer_review_mcp.LLM.gemini_client import GeminiClient

# לְ:
from peer_review_mcp.LLM import ClaudeClient as GeminiClient

# זהו! כל משהו שמשתמש בGeminiClient עכשיו משתמש בClaude
```

---

## ✅ Checklist - כדי להחליף מודלים

- [ ] בחר קומבינציה (Cost-Effective / Quality-First / Balanced)
- [ ] וודא שיש API keys: `echo $ANTHROPIC_API_KEY`, `echo $OPENAI_API_KEY`
- [ ] קרא את `EXAMPLES_MODEL_SWITCHING.md` לדוגמאות מלאות
- [ ] תשנה קובץ בכל פעם ותבדוק imports
- [ ] תריץ tests: `pytest src/tests/ -v`
- [ ] תתחיל עם server: `python -m peer_review_mcp.server`

