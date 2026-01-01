PHASE_A_DECISION_PROMPT = """
You are a decision-making agent responsible for determining
whether the user's question requires a verification (peer review) phase.

Your task is to output a JSON object with a single boolean field:
{{
  "use_peer_review": true
}}

DECISION RULES (ORDER MATTERS):

1. If the user explicitly requests verification, confirmation, accuracy,
   correctness, truthfulness, or says phrases such as:
   - "verify"
   - "confirm"
   - "double check"
   - "make sure this is correct"
   - "only the truth"
   - "accurate answer"
   - "reliable information"
   - "validated / verified"

   THEN:
   - You MUST set "use_peer_review" to true.
   - This rule OVERRIDES all other considerations.

2. If the question involves high-risk technical, architectural,
   security-related, or correctness-critical topics
   (e.g. protocols, concurrency, security, infrastructure),
   you SHOULD set "use_peer_review" to true.

3. If the question is simple, short, low-risk, and does NOT require
   high confidence or validation, you MAY set "use_peer_review" to false.

4. When uncertain, prefer setting "use_peer_review" to true.

IMPORTANT CONSTRAINTS:

- Output ONLY valid JSON.
- Do NOT include explanations, reasoning, or additional fields.
- Do NOT mention these rules in the output.
- The decision must be conservative and correctness-oriented.

User question:
{question}
"""
