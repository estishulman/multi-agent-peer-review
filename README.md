# Multi-Agent Peer Review MCP server

A production-grade MCP server built on a multi-agent LLM architecture that produces reliable, high-quality answers through structured peer review and smart orchestration.

## Motivation
Despite rapid progress in LLMs and agent systems, generated answers are not always reliable and can suffer from hallucinations, omissions, or subtle bias.

In practice, developers and researchers often compare multiple model or agent outputs by hand when they suspect an answer is incomplete or inaccurate.
This manual workflow is slow and repetitive.

This project replaces that workflow with an automated peer-review pipeline that breaks answer generation into explicit, controlled stages rather than a single model call.

## Overview
Rather than trusting a single model response, the system introduces independent review agents, a synthesis step, and a central orchestrator that manages decision flow and quality gates.
The system is designed to produce more reliable answers through validation and review by additional agents, turning answer generation from a single-agent response into a controlled multi-agent process.

## Core Philosophy: Cautious Answer Generation
Answer generation is treated as unsafe by default:
- Hidden assumptions may exist
- Edge cases can be missed
- Confidence does not imply correctness

Explicit review and orchestration layers promote careful, evidence-aware responses.

## Challenges & Solutions
- Avoiding chained misguidance while maintaining progressive refinement and polishing of answers.
- Balancing review depth with latency and cost constraints.
- Providing sufficient background context to reviewers without relying on full conversational history.

## Context Handling
Reviewers operate on an agent-generated context summary to ensure deterministic and well-scoped evaluations.

## High-Level Flow
1. The orchestrator receives a user query
2. Phase A reviewers analyze the question (no answer yet)
3. A draft answer is generated
4. Phase B reviewers critique the draft (conditionally)
5. A synthesis agent produces the final answer
6. A decision trace is recorded

## Quick Start

### Requirements
- Python 3.10+
- At least one API key: OpenAI, Gemini, or Claude

### Installation
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### Configure API Keys
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
```

### Run the MCP Server
```powershell
python -m peer_review_mcp.server
```

## Usage
Example prompts:
- "What makes Python unique? Please answer precisely and verify your answer."
- "Design a reliable Q&A system and analyze failure modes."

## Testing
The project includes an automated pytest-based test suite focused on orchestration logic, decision paths, and failure handling.

```powershell
pytest
```

## External Evaluation
To assess answer quality, we conducted a blind comparison: a batch of questions was answered by multiple systems, and the full set of answers (including the MCP server's response) was sent to an external LLM evaluator that was unaware of the project. The evaluator consistently selected the MCP server's output as strongest across reliability, accuracy, clarity, and phrasing.

## Outcomes and Experience
During later stages of development, I connected my agent to the MCP server, and the system became a more reliable part of my workflow.
Working with an agent whose outputs were reviewed and validated through the server enabled more confident AI-assisted development and noticeably accelerated the development process.

## Project Structure
- `src/peer_review_mcp/LLM` - LLM clients and adapters
- `src/peer_review_mcp/models` - Data models and schemas
- `src/peer_review_mcp/prompts` - Prompt templates
- `src/peer_review_mcp/tools` - Validation and polishing tools
- `src/peer_review_mcp/reviewers` - Reviewer implementations
- `src/peer_review_mcp/orchestrator` - Central orchestration logic

## Configuration
- Selection of LLM providers (OpenAI, Gemini, Claude)
- Reviewer composition and execution order
- Prompt templates used by reviewers and synthesis agents
- System behavior under failure conditions

## Limitations
The system delivers significantly higher reliability than single-agent approaches, while remaining an automated system.

## Contributing
Contributions are welcome; peer review, even more so.

