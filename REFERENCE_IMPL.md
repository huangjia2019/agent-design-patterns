# Reference Implementations

LangGraph + LangChain reference implementations for the 28 agent design patterns.

## What's here

Each pattern gets up to two implementation folders:

| Folder | Framework | What it shows |
|--------|-----------|---------------|
| `langgraph/` | LangGraph `StateGraph` | The pattern as a visible graph with explicit nodes, edges, and conditional routing |
| `langchain/` | LangChain v1 middleware | The pattern as middleware plugged into `create_agent` — less code, less visibility |

Both share the same hook factories ([`hooks.py`](action/d-guardrail-sandwich/hooks.py)) and model configuration ([`model_config.py`](model_config.py)).

### Implemented

| Pattern | Path | LangGraph | LangChain | Status |
|---------|------|:---------:|:---------:|--------|
| Guardrail Sandwich | `action/d-guardrail-sandwich/` | notebook + html + md | notebook + html + md | Done |

### Roadmap

| Wave | Patterns | Status |
|------|----------|--------|
| 1 | Context Triage, Semantic Compaction, Chain of Thought, Prompt Chaining, Generator-Critic | Planned |
| 2 | Progressive Discovery, Complexity Routing, Iterative Hypothesis, Self-Heal Loop | Planned |
| 3 | Multimodal Fusion, Parallel Exploration, Fan-out & Gather | Planned |
| 4 | Hierarchical Retention, Progress Tracking, Failure Journals, Experience Replay | Planned |
| 5 | Tool Dispatch, RAG | Planned |
| 6 | Hierarchical Delegation, Adversarial Review, Handoff Chain | Planned |
| 7 | Plan & Execute, Approval Gate, Blast Radius, Progressive Commitment | Planned |
| 8 | Observability Harness, Skill Package, Composition patterns | Planned |

### Coming soon

- **Agent Chat UI** — interactive frontend for testing patterns via chat interface
- **Agent Service Runtime** — `langgraph dev` / cloud deployment for serving pattern graphs as APIs

---

## Quick start

```bash
# 0. Install uv (if you don't have it)
# macOS / Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Or: brew install uv / pipx install uv

# 1. Sync project with all dependencies
uv sync --extra langgraph --extra dev

# 2. Set up your API key (needed only for the "Real LLM" cells)
cp .env.example .env
# Default: ernie provider + ernie-5.1 via AI Studio — just fill in OPENAI_API_KEY
# Set MODEL_PROVIDER + MODEL_NAME to switch providers. See .env.example.

# 3. Launch JupyterLab
uv run jupyter lab
```

## Three ways to use the notebooks

| Method | What you need | What you see |
|--------|--------------|-------------|
| **Read on GitHub** | Nothing | Rendered notebook with saved outputs |
| **Read pre-rendered HTML** | Nothing | Single-page walkthrough as HTML |
| **Read in JupyterLab** | `uv sync --extra langgraph --extra dev` then `uv run jupyter lab` | Same, but you can collapse/expand cells |
| **Run cells yourself** | Above + `.env` with API key | Your own LLM outputs, can tweak parameters |

## Running cells

- **Deterministic cells** (mock data) run without any API key
- **"Real LLM" cells** default to `ernie:ernie-5.1` via AI Studio. Set `MODEL_PROVIDER` + `MODEL_NAME` in `.env` to switch. Any OpenAI-compatible endpoint works via `OPENAI_BASE_URL`.
- To re-run the full notebook: **Kernel → Restart & Run All**

## Running tests

```bash
# Re-execute notebooks (needs .env for real-backend cells)
uv run pytest --nbmake --nbmake-timeout=120 'action/**/langgraph/tutorial.ipynb' 'action/**/langchain/tutorial.ipynb'

# Run pure-Python test suites
uv run pytest --import-mode=importlib -v
```

## Project structure

```
.env.example          # LLM provider config — copy to .env
model_config.py       # Shared model loader (register_model_provider + load_chat_model)
REFERENCE_IMPL.md     # This file

action/d-guardrail-sandwich/
  hooks.py            # Shared hook factories (amount_threshold, blocklist, output_schema)
  langgraph/
    tutorial.ipynb    # LangGraph StateGraph implementation
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
  langchain/
    tutorial.ipynb    # LangChain middleware implementation
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
```
