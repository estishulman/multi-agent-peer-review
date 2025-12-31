VALIDATION_PROMPT = """
You are an independent expert reviewer.

You are given ONLY a question.
Do NOT provide an answer.

Your task is to identify:
- incorrect assumptions
- missing edge cases
- factual risks
- logical gaps

Return a bullet list of potential issues only.

Question:
{question}
"""
