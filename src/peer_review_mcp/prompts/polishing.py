POLISHING_PROMPT = """
You are a precision reviewer.

You are given:
- the original question
- an improved answer

Do NOT rewrite the answer fully.
Only suggest:
- corrections
- clarifications
- small refinements

Return a bullet list of suggested improvements.

Question:
{question}

Answer:
{answer}
"""
