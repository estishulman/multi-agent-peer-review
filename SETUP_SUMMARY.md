ל# ✅ סיכום - LLM Clients Setup

## 🎯 מה שעשינו

יצרנו ממשק אחיד לקריאה לכל מודל (Claude, ChatGPT, Gemini) עם אותו API.

---

## 📦 קבצים שיצרנו

### 1. LLM Clients
```
src/peer_review_mcp/LLM/
├── gemini_client.py          ✅ (קיים)
├── claude_client.py           ✨ חדש
├── chatgpt_client.py          ✨ חדש
├── claude_opus_client.py      ✨ חדש
└── __init__.py                ✨ עדכן
```

### 2. Guides and Examples
```
📄 LLM_CLIENTS_GUIDE.md           - איך להשתמש בכל client
📄 EXAMPLES_MODEL_SWITCHING.md    - דוגמאות של החלפות
📄 API_CALLS_MAP.md               - מפה של כל קריאות API
```

### 3. Config
```
src/peer_review_mcp/
├── config.py                 ✨ עדכן עם API keys חדשים
└── pyproject.toml            ✨ עדכן עם dependencies
```

---

## 🔑 API Keys שצריך להוסיף

```bash
# בקובץ .env או כ-environment variables

GEMINI_API_KEY="your-gemini-key"
ANTHROPIC_API_KEY="your-claude-key"
OPENAI_API_KEY="your-chatgpt-key"
```

---

## 🚀 איך להשתמש כרגע

### דוגמה 1: השתמש בClaude
```python
from peer_review_mcp.LLM import ClaudeClient

client = ClaudeClient()
response = client.generate("Your prompt here")
```

### דוגמה 2: השתמש בChatGPT
```python
from peer_review_mcp.LLM import ChatGPTClient

client = ChatGPTClient()
response = client.generate("Your prompt here")
```

### דוגמה 3: דלול מודלים בreviewers
```python
from peer_review_mcp.LLM import ClaudeClient, ChatGPTClient
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer

claude = ClaudeClient()
gpt = ChatGPTClient()

# היום כל זה משתמש בGemini
# אתה יכול להחליף בקלות:
reviewer1 = GeminiReviewer(claude)  # עכשיו משתמש בClaude
reviewer2 = GeminiReviewer(gpt)     # עכשיו משתמש בChatGPT
```

---

## 📋 קומבינציות שאפשר

### Cost-Effective (מומלץ)
```python
ValidationEngine:     Gemini x2       (זול)
SynthesisEngine:      Gemini          (זול)
PolishingEngine:      Claude          (טוב יותר)
FinalSynthesis:       Gemini          (זול)
```

### Quality-First
```python
ValidationEngine:     Claude + ChatGPT + Gemini   (הכי טוב)
SynthesisEngine:      Claude                      (מוביל טוב)
PolishingEngine:      Claude                      (עריכה טובה)
FinalSynthesis:       Claude                      (פולישינג טוב)
```

### Balanced (אני מפלס את זה)
```python
ValidationEngine:     Gemini + Claude           (זול + טוב)
SynthesisEngine:      Claude                    (מוביל טוב)
PolishingEngine:      Gemini                    (מהיר)
FinalSynthesis:       ChatGPT                   (פולישינג)
```

---

## 📚 קבצים שכדאי לקרוא

1. **`LLM_CLIENTS_GUIDE.md`** - איך לא להשתמש בכל client
2. **`EXAMPLES_MODEL_SWITCHING.md`** - קוד קונקרטי לשינוי
3. **`API_CALLS_MAP.md`** - איפה משתמשים ב-API כרגע

---

## ✅ שלב הבא

בחר קומבינציה של מודלים ואז:

1. פתח את הקובץ בעדכון
2. עקוב אחרי דוגמה מ-`EXAMPLES_MODEL_SWITCHING.md`
3. שנה את ה-import ואת initialization
4. תריץ: `python -c "from peer_review_mcp.tools.validation_engine import ValidationEngine; print('✓')"`
5. תריץ tests: `pytest src/tests/ -v`

---

## 🆘 בעיות נפוצות

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic
```

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "API Key not found"
```bash
# בדוק שה-keys מוגדרים
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

### Client לא עובד?
```python
# בדוק שהclient מאותחל
from peer_review_mcp.LLM import ClaudeClient
client = ClaudeClient()
print(f"Model: {client.model}")
print(f"Timeout: {client.timeout}s")
```

---

## 🎓 תזכורת: Clients כולם זהים

כל client יש:
```python
# Create (Singleton)
client = SomeClient()

# Generate
response = client.generate("prompt")

# That's it!
```

---

## 📞 צור קשר

אם יש בעיות:
1. בדוק את `API_CALLS_MAP.md`
2. קרא את `LLM_CLIENTS_GUIDE.md`
3. עקוב אחרי `EXAMPLES_MODEL_SWITCHING.md`

