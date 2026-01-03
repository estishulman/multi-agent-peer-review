# LLM Clients - שימוש מובילים

כל ה-Clients יש להם אותו ממשק - זה עוזר להחלפת מודלים בקלות.

## 🔧 All Clients

כל client יש לו:
- **Singleton pattern** - רק אינסטנס אחד
- **`generate(prompt: str) -> str`** - שלח prompt, קבל תשובה
- **Error handling** - logging אוטומטי

---

## 📌 שימוש בכל Client

### Gemini (Google)
```python
from peer_review_mcp.LLM import GeminiClient

client = GeminiClient()
response = client.generate("Your prompt here")
```

**Requirements:**
- `GEMINI_API_KEY` בסביבה

---

### Claude (Anthropic)
```python
from peer_review_mcp.LLM import ClaudeClient

client = ClaudeClient()
response = client.generate("Your prompt here")
```

**Requirements:**
- `ANTHROPIC_API_KEY` בסביבה
- pip install anthropic

---

### Claude Opus (Anthropic - Premium)
```python
from peer_review_mcp.LLM import ClaudeOpusClient

client = ClaudeOpusClient()
response = client.generate("Your prompt here")
```

**Requirements:**
- `ANTHROPIC_API_KEY` בסביבה
- pip install anthropic

---

### ChatGPT (OpenAI)
```python
from peer_review_mcp.LLM import ChatGPTClient

client = ChatGPTClient()
response = client.generate("Your prompt here")
```

**Requirements:**
- `OPENAI_API_KEY` בסביבה
- pip install openai

---

## 🔄 שימוש בreviewer עם models שונים

### דוגמה 1: החלף ValidationEngine ל-Claude
```python
from peer_review_mcp.LLM import ClaudeClient
from peer_review_mcp.reviewers import GeminiReviewer

# בקובץ validation_engine.py
client = ClaudeClient()
self.reviewers = [
    GeminiReviewer(client),  # עכשיו משתמש בClaude בתוך GeminiReviewer
]
```

> **הערה:** GeminiReviewer למעשה יכול לקבל כל client עם ממשק `generate()`

### דוגמה 2: Multi-Model Validation
```python
from peer_review_mcp.LLM import GeminiClient, ClaudeClient, ChatGPTClient

# בקובץ validation_engine.py
gemini = GeminiClient()
claude = ClaudeClient()
gpt = ChatGPTClient()

self.reviewers = [
    GeminiReviewer(gemini),      # Issues detection
    ClaudeReviewer(claude),      # Clarity check
    ChatGPTReviewer(gpt),        # Additional perspective
]
```

---

## 🎯 איפה אנחנו משתמשים בCients

| קובץ | שימוש | Client ברירת מחדל |
|------|------|-----------------|
| `validation_engine.py` | בדוק שאלה | Gemini x2 |
| `synthesis_engine.py` | כתוב תשובה | Gemini |
| `polishing_engine.py` | כתוב הערות | Gemini |
| `central_orchestrator.py` | סיום polish | Gemini |

---

## 📋 דוגמה מלאה - החלף validation לClaude

**File: `src/peer_review_mcp/tools/validation_engine.py`**

```python
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM import ClaudeClient  # ← חדש
from peer_review_mcp.reviewers.gemini_clarity_reviewer import GeminiClarityReviewer

class ValidationEngine:
    def __init__(self):
        gemini = GeminiClient()
        claude = ClaudeClient()  # ← חדש
        
        self.reviewers = [
            GeminiReviewer(claude),          # ← עכשיו משתמש בClaude
            GeminiClarityReviewer(gemini),   # ← עדיין Gemini
        ]
```

---

## 🚀 דוגמה מלאה - Multi-Model System

```python
# src/peer_review_mcp/tools/validation_engine.py
from peer_review_mcp.LLM import GeminiClient, ClaudeClient, ChatGPTClient
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer

class ValidationEngine:
    def __init__(self):
        gemini = GeminiClient()
        claude = ClaudeClient()
        gpt = ChatGPTClient()
        
        self.reviewers = [
            GeminiReviewer(gemini),   # Gemini - זול ומהיר
            GeminiReviewer(claude),   # Claude - טוב לnuance
            GeminiReviewer(gpt),      # GPT - logic טוב
        ]
```

---

## ✅ Checklist - להפעיל את הכל

### 1. Install dependencies
```bash
pip install -e .
```

### 2. Set environment variables
```bash
export GEMINI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
```

### 3. Test each client
```python
from peer_review_mcp.LLM import GeminiClient, ClaudeClient, ChatGPTClient

# Test Gemini
g = GeminiClient()
print(g.generate("Say hi"))

# Test Claude
c = ClaudeClient()
print(c.generate("Say hi"))

# Test ChatGPT
gpt = ChatGPTClient()
print(gpt.generate("Say hi"))
```

---

## 🔍 Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic
```

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "API Key not found"
תבדוק:
```bash
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

### Timeout issues
כל client יש `timeout=30` seconds כברירת מחדל. תוכל להשנות:
```python
client = ClaudeClient(timeout=60)  # 60 seconds
```

