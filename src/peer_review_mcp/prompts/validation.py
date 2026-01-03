VALIDATION_PROMPT = """
You are an independent expert reviewer.

You are given:
- A question
- Optional context about what has been discussed before

Your task is to identify potential issues with the question, considering the context:
- incorrect assumptions (especially related to context)
- missing edge cases
- factual risks
- logical gaps
- redundancy or repetition of what was already discussed
- security concerns
- API/tooling misuse

For each issue, classify it by:
- risk_type: one of [assumptions, api_tooling, edge_cases, concurrency, security, other]
- severity: one of [low, medium, high]
- confidence: 0.0-1.0, how confident you are this is an actual issue

Return a JSON array with this structure:
[
  {{
    "text": "description of the issue",
    "risk_type": "assumptions|api_tooling|edge_cases|concurrency|security|other",
    "severity": "low|medium|high",
    "confidence": 0.85
  }},
  ...
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- Be specific and actionable in your descriptions
- Consider if the question relates to context already discussed
- Assign high severity only to critical issues
- Be honest about confidence levels

Context (if provided):
{answer}

Question:
{question}
"""
