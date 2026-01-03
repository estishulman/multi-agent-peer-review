ה# 🔀 דוגמאות - החלפת מודלים

זה קובץ עם דוגמאות קונקרטיות איך להחליף מודלים בחלקים שונים של המערכת.

---

## דוגמה 1: ValidationEngine - Claude + ChatGPT

**קובץ: `src/peer_review_mcp/tools/validation_engine.py`**

```python
import logging
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM import ClaudeClient, ChatGPTClient  # ← Import חדש
from peer_review_mcp.models.review_result import ReviewMode
from peer_review_mcp.models.review_point import ReviewPoint

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Validation engine with Claude + ChatGPT reviewers.
    """

    def __init__(self):
        claude = ClaudeClient()
        gpt = ChatGPTClient()

        self.reviewers = [
            GeminiReviewer(claude),     # Issues detection
            GeminiReviewer(gpt),        # Clarity check
        ]
        logger.info("ValidationEngine initialized with %d reviewers", len(self.reviewers))

    def validate(self, question: str, context_summary: str = None) -> dict:
        review_points: list[ReviewPoint] = []

        for reviewer in self.reviewers:
            try:
                result = reviewer.review(
                    question=question,
                    answer=context_summary,
                    mode="validate",
                )
                for item in result.items:
                    if isinstance(item, dict):
                        review_point = ReviewPoint(
                            text=item.get("text", str(item)),
                            risk_type=item.get("risk_type"),
                            severity=item.get("severity"),
                            confidence=item.get("confidence", 0.8),
                        )
                    else:
                        review_point = ReviewPoint(
                            text=item.strip() if isinstance(item, str) else str(item),
                            risk_type=None,
                            severity=None,
                            confidence=0.8,
                        )
                    review_points.append(review_point)
            except Exception as e:
                logger.exception("Reviewer %s failed during validation: %s",
                                type(reviewer).__name__, e)
                continue

        logger.info("Validation complete: %d review points found", len(review_points))
        return {
            "items": review_points,
            "count": len(review_points),
        }
```

---

## דוגמה 2: SynthesisEngine - Claude

**קובץ: `src/peer_review_mcp/tools/synthesis_engine.py`**

```python
from typing import Optional
from peer_review_mcp.LLM import ClaudeClient  # ← חדש
from peer_review_mcp.LLM.synthesis_client import AnswerSynthesisClient

class SynthesisEngine:
    def __init__(self):
        claude = ClaudeClient()  # ← השתמש בClaude בדל Gemini
        self.synthesizer = AnswerSynthesisClient(claude)

    def answer(
        self,
        question: str,
        context_summary: Optional[str] = None,
        review_points: list[str] = None,
    ) -> dict:
        if review_points is None:
            review_points = []

        final_answer = self.synthesizer.synthesize(
            question=question,
            context_summary=context_summary,
            review_points=review_points,
        )

        return {
            "answer": final_answer,
            "review_count": len(review_points),
        }
```

---

## דוגמה 3: PolishingEngine - Claude

**קובץ: `src/peer_review_mcp/tools/polishing_engine.py`**

```python
import logging
from peer_review_mcp.LLM import ClaudeClient  # ← חדש
from peer_review_mcp.models.polish_comment import PolishComment
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.reviewers.base import BaseReviewer

logger = logging.getLogger(__name__)


class PolishingEngine:
    """
    Phase B - Polishing with Claude.
    """

    def __init__(self):
        claude = ClaudeClient()  # ← השתמש בClaude
        self.reviewers: list[BaseReviewer] = [
            GeminiReviewer(claude),
        ]
        logger.info("PolishingEngine initialized with %d reviewers", len(self.reviewers))

    def review_for_polish(self, *, question: str, answer: str, context_summary: str = None) -> list[PolishComment]:
        """
        Review answer for polish suggestions using Claude.
        """
        comments: list[PolishComment] = []
        logger.debug("Starting polish review for question: %s", question[:100])

        for reviewer in self.reviewers:
            try:
                result = reviewer.review(
                    question=question,
                    answer=answer,
                    mode="polish",
                )
                for item in result.items:
                    text = item.strip() if isinstance(item, str) else str(item)
                    if text:
                        comments.append(PolishComment(text=text))
                logger.debug("Reviewer %s returned %d polish comments",
                           type(reviewer).__name__, len([c for c in result.items if c.strip()]))
            except Exception as e:
                logger.exception("Reviewer %s failed during polish: %s",
                                type(reviewer).__name__, e)
                continue

        return comments
```

---

## דוגמה 4: CentralOrchestrator - ChatGPT לפולישינג

**קובץ: `src/peer_review_mcp/orchestrator/central_orchestrator.py`**

```python
import time
from dataclasses import dataclass, field
from typing import Optional, List
import logging

from peer_review_mcp.tools.validate_tool import validate_tool
from peer_review_mcp.tools.answer_tool import answer_tool
from peer_review_mcp.tools.polishing_engine import PolishingEngine
from peer_review_mcp.models.review_point import ReviewPoint

from peer_review_mcp.LLM import ChatGPTClient  # ← חדש
from peer_review_mcp.prompts.polish_synthesis import POLISH_SYNTHESIS_PROMPT

logger = logging.getLogger(__name__)


class CentralOrchestrator:
    """
    Orchestrator with ChatGPT for final polish synthesis.
    """

    def __init__(self):
        logger.info("CentralOrchestrator initialized")
        self.polishing_engine = PolishingEngine()
        self.polish_llm = ChatGPTClient()  # ← השתמש בChatGPT לפולישינג

    # ... rest of the class remains the same ...
    
    def _run_phase_b(self, question: str, answer: str, context_summary: Optional[str], decision_log: list[str]) -> str:
        """Phase B: Polish answer based on review suggestions."""
        logger.debug("Running Phase B polishing")

        comments = self.polishing_engine.review_for_polish(
            question=question,
            answer=answer,
            context_summary=context_summary,
        )
        decision_log.append(f"polish_comments_count: {len(comments)}")
        logger.debug("Polish review complete: %d comments", len(comments))

        if not comments:
            return answer

        formatted = "\n".join(f"- {c.text}" for c in comments)

        prompt = POLISH_SYNTHESIS_PROMPT.format(
            question=question,
            answer=answer,
            comments=formatted,
            context=context_summary if context_summary else "(No previous context)",
        )

        polished = self.polish_llm.generate(prompt).strip()  # ← ChatGPT עונה
        return polished or answer
```

---

## דוגמה 5: Full Multi-Model System

**קובץ: `src/peer_review_mcp/tools/validation_engine.py`**

```python
import logging
from peer_review_mcp.reviewers.gemini_reviewer import GeminiReviewer
from peer_review_mcp.LLM import GeminiClient, ClaudeClient, ChatGPTClient
from peer_review_mcp.models.review_result import ReviewMode
from peer_review_mcp.models.review_point import ReviewPoint

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Multi-Model Validation Engine.
    - Gemini: עלות נמוכה
    - Claude: nuanced analysis
    - ChatGPT: logic-based analysis
    """

    def __init__(self):
        gemini = GeminiClient()
        claude = ClaudeClient()
        gpt = ChatGPTClient()

        self.reviewers = [
            GeminiReviewer(gemini),   # זול, מהיר
            GeminiReviewer(claude),   # nuanced
            GeminiReviewer(gpt),      # logic
        ]
        logger.info("ValidationEngine initialized with %d reviewers", len(self.reviewers))

    def validate(self, question: str, context_summary: str = None) -> dict:
        """
        Validate with multiple models for better coverage.
        """
        review_points: list[ReviewPoint] = []

        for idx, reviewer in enumerate(self.reviewers, 1):
            try:
                logger.debug("Running reviewer %d/%d", idx, len(self.reviewers))
                result = reviewer.review(
                    question=question,
                    answer=context_summary,
                    mode="validate",
                )
                for item in result.items:
                    if isinstance(item, dict):
                        review_point = ReviewPoint(
                            text=item.get("text", str(item)),
                            risk_type=item.get("risk_type"),
                            severity=item.get("severity"),
                            confidence=item.get("confidence", 0.8),
                        )
                    else:
                        review_point = ReviewPoint(
                            text=item.strip() if isinstance(item, str) else str(item),
                            risk_type=None,
                            severity=None,
                            confidence=0.8,
                        )
                    review_points.append(review_point)
            except Exception as e:
                logger.exception("Reviewer %s failed during validation: %s",
                                type(reviewer).__name__, e)
                continue

        logger.info("Validation complete: %d review points found from %d reviewers", 
                   len(review_points), len(self.reviewers))
        return {
            "items": review_points,
            "count": len(review_points),
        }
```

---

## 🎯 תרגול: בחר קומבינציה

### אופציה A: חוסך עלויות (Gemini everywhere)
```python
# כל מקום - Gemini
# זול ביותר
```

### אופציה B: טוב מאד (Claude everywhere)
```python
# כל מקום - Claude
# יקר יותר אבל יותר טוב
```

### אופציה C: Balanced (מומלץ)
```python
ValidationEngine: Gemini + Claude + ChatGPT (3 מודלים)
SynthesisEngine: Claude (מוביל טוב)
PolishingEngine: Claude (עריכה טובה)
FinalSynthesis: ChatGPT (פולישינג סופי)
```

### אופציה D: Premium (יקר)
```python
ValidationEngine: Claude Opus + ChatGPT (פרימיום)
SynthesisEngine: Claude Opus (הטוב ביותר)
PolishingEngine: Claude Opus (הטוב ביותר)
FinalSynthesis: Claude Opus (הטוב ביותר)
```

---

## ✅ Checklist - לפני שאתה משנה

- [ ] בדוק ש-API keys מוגדרים: `echo $ANTHROPIC_API_KEY`, `echo $OPENAI_API_KEY`
- [ ] יש לך הרשאה להשתמש ב-API keys האלה
- [ ] בדוק את העלויות של כל model
- [ ] תעשה backup של הקבצים לפני שאתה משנה
- [ ] תריץ את ה-tests אחרי שאתה משנה

---

## 🚀 תהליך שינוי

1. **בחר קומבינציה** - איזה מודלים להשתמש
2. **שנה קובץ אחד בכל פעם** - validation_engine.py → synthesis_engine.py → etc
3. **תבדוק שה-imports עובדים**:
   ```bash
   python -c "from peer_review_mcp.tools.validation_engine import ValidationEngine; print('✓')"
   ```
4. **תריץ את ה-tests**:
   ```bash
   pytest src/tests/ -v
   ```
5. **בדוק עם server**:
   ```bash
   python -m peer_review_mcp.server
   ```

