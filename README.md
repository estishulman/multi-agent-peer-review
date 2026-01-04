Multi-Agent Peer Review System
A production-style multi-agent LLM architecture for generating reliable, high-quality answers through structured peer review and orchestration.

Motivation
While modern LLMs and agent-based systems are powerful, their answers are not always reliable and can hallucinate.

In practice, developers and researchers often find themselves manually comparing answers across multiple models or agents when they suspect that a response may be incomplete, biased, or incorrect.
This manual comparison process is time-consuming, repetitive, and difficult to scale.

This project aims to replace that frustrating manual workflow with an automated, structured peer-review pipeline.

Overview
This project implements a multi-agent system that treats answer generation as a deliberative, multi-stage process, rather than a single LLM invocation.

Instead of trusting one model response, the system introduces independent review agents, a synthesis agent, and a central orchestrator that manages decision flow and quality gates.

Key Features
- Multi-agent orchestration with validation and polishing phases  → Reduces hallucinations and single-model bias
- Quality gates with conditional Phase B polishing based on heuristics
- Decision-trace logging for observability and debugging
- Modular reviewers and tools for easy extension
- Simple MCP tool interface: one call, one answer

Core Philosophy: Cautious Answer Generation
The system is built on the assumption that agent-generated answers should be treated with caution by default.

Rather than trusting a single response, the architecture assumes that:

- Answers may contain hidden assumptions
- Important edge cases may be missed
- Confidence does not necessarily imply correctness

By introducing explicit review and orchestration layers, the system promotes careful, evidence-aware answer generation.

Challenges & Solutions
- Preventing misleading chains while still improving answers: Phase A produces question-level review points only; an answer is generated after those checks. Phase B reviews the draft for weaknesses, and a final answer is generated from those findings.
- Keeping the pipeline efficient: not every question is routed to the peer-review server, and even within the server Phase B runs only when Phase A signals the need for deeper review.
- Preserving context without full chat history: the agent supplies a concise context summary to reviewers.

Proven in Practice
During later development stages, this tool became a core part of the workflow, consistently delivering reliable answers and eliminating manual cross-model comparison.

Internal Testing
In internal testing, the tool consistently produced more accurate and reliable answers than single-agent runs.

Contributing
Pull requests are welcome. Please open an issue to discuss larger changes before you start.

## Testing & Coverage

The project includes an automated test suite using pytest.
Tests focus on core orchestration logic, decision paths, and fallback behavior to ensure reliable agent execution.


## Quick Start

Requirements
- Python 3.10+
- At least one API key: GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY

### Step 1: Clone & Install
```powershell
# Clone the repository
cd D:\path\to\multi-agent-peer-review
# Create virtual environment
python -m venv .venv
# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# Install the project
pip install -e .
```

### Step 2: Configure API Keys
Create a `.env` file in the project root:
```env
# Required: At least one API key
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Step 3: Run the MCP Server
```powershell
python -m peer_review_mcp.server
```

### Step 4: Connect From an Agent (Example)
Add a server entry to your MCP client configuration:
```json
{
  "mcp_servers": {
    "peer-review": {
      "command": "python",
      "args": ["-m", "peer_review_mcp.server"]
    }
  }
}
```

### Step 5: OpenAI Codex CLI
Choose either Step 4 or Step 5 depending on your MCP client.
```powershell
codex mcp add peer-review -- `
  D:\path\to\multi-agent-peer-review\.venv\Scripts\python.exe `
  -u D:\path\to\multi-agent-peer-review\src\peer_review_mcp\server.py

codex
```

Usage
Example prompts:
- "What makes Python unique? Please answer precisely and verify your answer."
- "Design a reliable Q&A system for medical information. Compare three architectures, detail failure modes and edge cases, and specify when human review is mandatory."

Testing
```powershell
pytest
```

Project Structure
- src/peer_review_mcp/LLM: LLM clients and adapters
- src/peer_review_mcp/models: Data models and schema types
- src/peer_review_mcp/prompts: Prompt templates used by reviewers
- src/peer_review_mcp/tools: Validation and polishing tools
- src/peer_review_mcp/reviewers: Reviewer implementations
- src/peer_review_mcp/orchestrator: Central decision flow

Logging
The project uses Python's built-in `logging` module.
Logs go to stdout/stderr by default; file logging is not configured out of the box.
