# Reference Implementations

LangGraph + LangChain reference implementations for the 28 agent design patterns.

## What's here

Each pattern gets up to two implementation folders:

| Folder | Framework | What it shows |
|--------|-----------|---------------|
| `langgraph/` | LangGraph `StateGraph` | The pattern as a visible graph with explicit nodes, edges, and conditional routing |
| `langchain/` | LangChain | The pattern as LCEL pipes or middleware, whichever best fits the pattern — less code, less visibility |

Both share the same hook factories ([`shared.py`](action/d-guardrail-sandwich/shared.py)) and model configuration ([`model_config.py`](model_config.py)).

### Implemented

| Pattern | Path | LangGraph | LangChain | Status |
|---------|------|:---------:|:---------:|--------|
| Guardrail Sandwich | `action/d-guardrail-sandwich/` | notebook + html + md | notebook + html + md | Done |
| Prompt Chaining | `action/c-prompt-chaining/` | notebook + html + md | notebook + html + md | Done |
| Generator-Critic | `reflection/a-generator-critic/` | notebook + html + md | notebook + html + md | Done |

### Roadmap

| Wave | Patterns | Status |
|------|----------|--------|
| 1 | ~~Prompt Chaining~~ ✓ · Context Triage, Semantic Compaction, Chain of Thought, ~~Generator-Critic~~ ✓ | In progress |
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

## How to draft a new reference implementation

Each RI follows the same recipe (extracted from the Guardrail Sandwich PR):

### 1. Create `shared.py` (shared factories)

A small Python file at `<pattern-folder>/shared.py` that:
- Defines framework-agnostic helper factories (enums, config-dict builders) — gates, hooks, schemas, whatever this pattern needs
- Is imported by **both** the LangGraph and LangChain notebooks
- Keeps the two notebooks in sync without code duplication

Name it `shared.py` after its *role* (the file both notebooks share), not its *contents* — contents vary by pattern (Prompt Chaining shares gate factories; Guardrail Sandwich shares hook factories + a hook runner), but the role is always the same.

### 2. Write the LangGraph notebook (`langgraph/tutorial.ipynb`)

Structure (cell order):

| Section | Cell type | Content |
|---------|-----------|---------|
| Title + quote | markdown | Pattern name, one-line thesis, pointer to langchain version |
| What this pattern does | markdown | 3-sentence explanation + comparison table (LangGraph vs LangChain) |
| Setup | markdown + code | Imports from `shared.py`, `model_config.py`, `nbtools.py`, langgraph |
| State | markdown + code | `TypedDict` state definition, minimal fields |
| Helper utilities | code | ToolNode wrappers, decoders, renderers |
| Core nodes | markdown + code | One section per graph node (explain → implement) |
| Build the graph | code | `StateGraph` assembly, `add_conditional_edges` |
| Mock tools | code | Deterministic fakes for the demo |
| Assemble demo | code | Instantiate factories + graph, display graph PNG |
| Mock runs (3–4) | markdown + code pairs | One run per scenario (happy path, pre-block, post-block, error) |
| Real backend | markdown + code | `get_model()` + free-text → structured args → same graph |
| What to remember | markdown | 5 bullet recap |
| Further reading | markdown | Links to langchain version, pattern README, REFERENCE_IMPL.md, official docs |

### 3. Write the LangChain notebook (`langchain/tutorial.ipynb`)

Same conceptual flow but uses the most natural LangChain surface for the pattern:
LCEL pipes for chain-shaped flows, middleware for agent-runtime hooks. Highlights
the **less code, less visibility** trade-off.

### 4. Export artifacts

From each notebook directory:
```bash
uv run jupyter nbconvert --to html tutorial.ipynb
uv run jupyter nbconvert --to markdown tutorial.ipynb
```

### 5. Update this file

- Move the pattern from "Planned" to "Done" in the roadmap table
- Add a row to the **Implemented** table with path + status

### Key conventions

- Both notebooks add `shared.py`, `model_config.py`, and `nbtools.py` to `sys.path` by **searching upward for each file by name** (`next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / marker).exists())`) — not by counting `../..`, which breaks if the folder depth changes
- Name the per-pattern shared-factory file `shared.py` (after its role), not after its contents (`gates.py`/`hooks.py`) — the contents differ per pattern, the role doesn't
- Root-level shared helpers live in `nbtools.py` (display/util plumbing, e.g. `show_graph`) and `model_config.py` (model loading) — the counterpart to each pattern's `shared.py`. Only put genuinely cross-cutting, framework-agnostic helpers there; pattern logic stays in `shared.py` or the notebook
- Default model: `ernie:ernie-5.1` via AI Studio (OpenAI-compatible)
- Mock runs first (no API key needed), real LLM section last
- `print_trace()` or equivalent — short, readable audit output
- Graph visualization via the shared `show_graph()` from root `nbtools.py` (`from nbtools import show_graph`) — it tries `draw_mermaid_png()` and falls back to ASCII (`draw_ascii()`, needs `grandalf`) when the remote Mermaid API is unreachable. Don't re-implement it per notebook; pass an `alt=` label.
- **Avoid Mermaid reserved words as node/step ids** (`style`, `end`, `graph`, `subgraph`, `class`, …). A node literally named `style` makes `draw_mermaid_png()` return HTTP 400 — rename it (e.g. `restyle`)
- For deterministic mock runs (no API key), use **`FakeListChatModel`** from `langchain_core.language_models.fake_chat_models` — it returns a fixed list of replies **in call order and cycles** when exhausted, so a multi-step pipeline's call sequence lines up with the list and retries keep working. Do **not** use `GenericFakeChatModel` (its `messages` iterator *exhausts* and raises `StopIteration` on re-invocation, breaking any retry demo) or `FakeChatModel` (constant `"fake response"`, can't satisfy gates). The `fake` module's `FakeListLLM`/`FakeStreamingListLLM` are old-style string LLMs, not chat models — wrong type for a `ChatPromptTemplate | model` pipe.
- Keep framework-agnostic mock helpers framework-agnostic: the LangGraph `llm_call` is a bare `Callable`, so its fakes are plain Python functions (no langchain dependency) — don't reach for `FakeListChatModel` there.
- Use `from __future__ import annotations` + type hints everywhere
- Enums are `(str, Enum)` for JSON serialization
- Dataclasses (e.g. a `StepSpec`): only fields the logic reads — drop set-but-unused fields (e.g. a `description` nobody renders), and prefer a required field over a verbose `field(default_factory=...)` default that's never exercised
- Hook/gate crashes → fail-closed (BLOCK/reject), never silently pass
- No trailing `print("X ready")` cell-end noise; keep only prints that show real results (traces, smoke tests, accumulated state)

### Keep the two impls aligned

A reader should be able to flip between the LangGraph and LangChain notebooks
and recognize the same pattern. Align everything that isn't *forced* to differ
by the framework:

- **Same vocabulary for the same concept.** If one side calls a parameter
  `prompt_template` / `max_retries`, the other side uses the same names — not
  `template` / `retries`. Same for the core abstraction (e.g. a "step", a
  "gate"), the gate-runner function, and the trace fields.
- **Same demo, same data, same gates.** Both run the identical scenario
  (e.g. the 2-step `rewrite → factcheck` pipeline) on the identical input,
  with gates built from the **same `shared.py` factories** — so outputs line up
  side by side.
- **Same safety semantics.** Fail-closed, bounded-retry, and any anchored
  checks (e.g. `starts_with_gate` for a one-word verdict, not a substring
  match) must behave identically on both sides. Fix a bug in one → fix it in
  the other in the same pass.
- **Let only the framework mechanism differ**, and name that difference
  explicitly in the comparison table (StateGraph nodes/edges + manual retry
  loop vs. LCEL `prompt | model | parser | gate` + `.with_retry()`). The
  *shape* differs; the *concepts and names* should not.
- **No dead imports / unused factories.** When a fix changes which gate a
  notebook uses, drop the now-unused import from **both** notebooks.

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
| **Run cells yourself** | Above; `.env` only for `RUN_REAL_LLM=1` cells | Mock outputs by default, live LLM outputs when opted in |

## Running cells

- **Deterministic cells** (mock data) run without any API key
- **"Real LLM" cells** default to `ernie:ernie-5.1` via AI Studio. Set `MODEL_PROVIDER` + `MODEL_NAME` in `.env` to switch. Any OpenAI-compatible endpoint works via `OPENAI_BASE_URL`.
- To re-run the full notebook: **Kernel → Restart & Run All**

## Running tests

```bash
# Re-execute notebooks. Live-backend cells are opt-in with RUN_REAL_LLM=1.
uv run pytest --nbmake --nbmake-timeout=120 \
  action/*/langgraph/tutorial.ipynb action/*/langchain/tutorial.ipynb \
  reflection/*/langgraph/tutorial.ipynb reflection/*/langchain/tutorial.ipynb

# Run pure-Python test suites
uv run pytest --import-mode=importlib -v
```

## Project structure

```
.env.example          # LLM provider config — copy to .env
model_config.py       # Shared model loader (register_model_provider + load_chat_model)
nbtools.py            # Shared notebook helpers (show_graph: PNG with ASCII fallback)
REFERENCE_IMPL.md     # This file

action/d-guardrail-sandwich/
  shared.py           # Shared hook factories + runner (amount_threshold, blocklist, output_schema, run_single_hook)
  langgraph/
    tutorial.ipynb    # LangGraph StateGraph implementation
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
  langchain/
    tutorial.ipynb    # LangChain middleware implementation
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export

action/c-prompt-chaining/
  shared.py           # Shared gate factories (length_gate, keys_gate, starts_with_gate, json_gate, regex_gate, any_gate, all_gate)
  langgraph/
    tutorial.ipynb    # LangGraph StateGraph: one node per step + early-exit routing
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
  langchain/
    tutorial.ipynb    # LangChain LCEL: prompt | model | parser | gate, with .with_retry()
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export

reflection/a-generator-critic/
  shared.py           # Shared critique parser, policy, mock data, reviser, trace printer
  langgraph/
    tutorial.ipynb    # LangGraph StateGraph: generate -> critique -> gate -> optional revise
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
  langchain/
    tutorial.ipynb    # LangChain LCEL: generator pipe + critic pipe + deterministic policy gate
    tutorial.html     # Pre-rendered HTML
    tutorial.md       # Markdown export
```
