# Agent Design Patterns

> **A 7×6 framework for agent architecture. 28 patterns, each placed at a coordinate, each with runnable code and a verified engineering slice from real production codebases.**

*The model spends. The harness budgets. This repo is the vocabulary you can put in your project tomorrow.*

[简体中文 README](README.zh-CN.md) · [Manning · *Designing AI Agents*](#book--column--newsletter) · [极客时间专栏](#book--column--newsletter) · [Newsletter](https://agentpatterns.substack.com) · [Author site](https://kage-ai.com)

---

## Why this exists

Most "agent architecture" guides give you a flat list — Reflection, ReAct,
Multi-Agent, Tree of Thoughts, Reflexive Metacognitive, and so on. A flat
list answers *what patterns exist*. It does not answer *where my problem
sits, and which pattern lives at that coordinate*.

A loan-evaluation agent crashes not because Reflection is missing but
because Perception-stage budget allocation dropped the disqualifying
document. A multi-agent code reviewer drifts not because ReAct is wrong
but because two Reflection critics contradict each other and there is no
governance gate to resolve it. These are not different patterns — they
are patterns sitting at *specific coordinates* in a structured design
space. Without the coordinates you can't see them.

This repo gives you the coordinates.

---

## The two-axis framework

Every agent pattern sits at the intersection of two orthogonal axes.

* **Cognitive function** — *what the agent is doing*
  ↳ perceive · remember · reason · act · reflect · collaborate · govern
* **Execution topology** — *how the work is laid out at runtime*
  ↳ single-step · sequential · parallel · loop · router · hierarchy

Seven × six = 42 cells. The 28 cells where interesting patterns live are
the chapters of *Designing AI Agents* (Manning) and the lectures of the
极客时间 column. The code in this repo is the third leg of the work.

The framework's claim is not that everything fits the matrix. The claim
is that **giving a pattern a coordinate forces an answer to "why is this
pattern here and not somewhere else"**. A flat list lets you skip the
question. A matrix does not.

---

## Hero example — a real failure and the 90-line fix

A production loan-evaluation agent. Eight documents on standard cases,
fine. Then a 43-document commercial loan arrives, the context window
can't hold it, the agent silently sorts by filename, drops a 2024
collateral appraisal, keeps a 2019 expired business registration, and
recommends approval. Two weeks later the loan defaults.

The reasoning was fine. **The agent never saw the disqualifying
document.** This is a Perception-stage budget allocation failure. The
Context Triage pattern is what it is for.

```python
from pattern import ContextItem, ContextTriage, Priority

triage = ContextTriage(budget=8_000)
items = [
    ContextItem("system_prompt", "...", priority=Priority.CRITICAL),
    ContextItem("tenant_identity", "tenant_id=acme-corp ...",
                priority=Priority.CRITICAL),
    ContextItem("error_trace", "TimeoutError: pool exhausted ...",
                priority=Priority.IMPORTANT, is_error=True),
    ContextItem("full_product_manual", long_manual,
                priority=Priority.SUPPORTING),
    ContextItem("ticket_archive", "handle: ticket://...",
                priority=Priority.DEFERRABLE),
    # ... 7 more candidates
]

selected, deferred, decision = triage.triage(items)
```

The pattern enforces two invariants regardless of budget pressure:

* **P3 deferrable items never pre-load** — they wait behind a handle
  and the agent fetches them only when needed
* **Error traces never get dropped** — even when budget overflows, the
  feedback loop survives

```
$ python perception/a-context-triage/example.py
Budget        : 8,000 tokens
Tokens used   : 4,770
Selected (10):
  - P0 system_prompt (17 tok)
  - P0 user_message (13 tok)
  - P0 tenant_identity (12 tok)
  - P1 recent_error_trace (42 tok) [ERROR-PROTECTED]
  - P1 product_config_snapshot (18 tok)
  - ...
Deferred (2): ['historical_ticket_archive', 'full_runbook_library']
Invariant check:
  All error items kept? True
  All P3 items deferred (not loaded)? True
```

Full code in [`perception/a-context-triage/`](./perception/a-context-triage/).
The OS-scheduling analogy in the pattern README explains why the four-tier
priority feels obvious in hindsight.

---

## The 28-pattern map

Patterns are released as the column publishes lectures. The matrix below
is the full target; cells with ✅ have runnable code, cells with 🟡 have
README scaffolding.

| Cognitive function | Patterns | Coverage |
|---|---|---|
| **Perception** · seeing the world | Context Triage ✅ · Semantic Compaction ✅ · Progressive Discovery 🟡 · Multi-Modal Fusion 🟡 | 2 of 4 |
| **Memory** · what carries across turns | Hierarchical Retention · RAG · Progress Tracking · Failure Journals | scaffolding |
| **Reasoning** · how decisions get made | Chain of Thought · Complexity-Based Routing · Parallel Exploration · Iterative Hypothesis Testing | scaffolding |
| **Action** · effecting the world | Tool Dispatch · Plan-and-Execute · Prompt Chaining · Guardrail Sandwich | scaffolding |
| **Reflection** · improving over time | Generator-Critic · Skill Package · Experience Replay · Self-Heal Loop | scaffolding |
| **Collaboration** · multi-agent work | Hierarchical Delegation · Fan-out & Gather · Adversarial Review · Handoff Chain | scaffolding |
| **Governance** · safety and control | Approval Gate · Blast Radius · Progressive Commitment · Observability Harness | scaffolding |
| **Composition** · putting it together | Pattern Selection Card · Six-Step Methodology · Argus (full case study) | scaffolding |

Each pattern folder follows the same shape: `pattern.py` (the minimal
honest reference, 50–250 lines), `example.py` (a real-scenario case that
runs without API keys), `test_pattern.py` (the invariants the pattern
must hold), and bilingual `README.md` / `README.zh-CN.md`.

---

## Engineering slices — verified, not hallucinated

Every pattern's README cites real production code. Citations are
file-and-line in upstream open-source projects, verified at the time of
writing. If you find a citation that no longer matches the upstream code,
open an issue — that's a bug, not a documentation choice.

| Pattern | Upstream slices cited |
|---|---|
| Context Triage | [Aider's RepoMap](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py), [Claude Code memory hierarchy](https://docs.claude.com/en/docs/claude-code/memory), [DeerFlow schema-driven triage](https://github.com/bytedance/deer-flow) |
| Semantic Compaction | [OpenHands condenser_config](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/core/config/condenser_config.py), [Aider history.py](https://github.com/Aider-AI/aider/blob/main/aider/history.py), [Manus Context Engineering blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) |

The eight production harnesses the framework tracks: **Claude Code,
Codex CLI, Aider, OpenCode, OpenClaw, Hermes Agent, DeepAgents, DeerFlow,
OpenHands**. Each pattern's README pulls from at least one of these to
show the pattern in real production form, not toy form.

---

## What this repo is not

* **Not a framework.** Use [LangGraph](https://github.com/langchain-ai/langgraph),
  [agno](https://github.com/agno-agi/agno),
  [DeerFlow](https://github.com/bytedance/deer-flow), or
  [OpenHands](https://github.com/All-Hands-AI/OpenHands) for a production
  runtime. This repo is the design vocabulary you apply on top of any of
  them. Switching frameworks does not change the matrix.
* **Not a flat catalog.** Flat lists ("17 agentic architectures") answer
  *what exists*. The matrix answers *where your problem lives* and *which
  patterns are wrong for that position*. The second question is the one
  that costs you when you ship.
* **Not toy code.** Every `pattern.py` is small (50–250 lines) on
  purpose, but it is honest code with real invariants and tests. Each
  `example.py` runs on data shaped like production. Engineering slices
  in the READMEs cite verified upstream files.

---

## Quickstart

```bash
git clone https://github.com/huangjia2019/agent-design-patterns.git
cd agent-design-patterns
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run a pattern's case
python perception/a-context-triage/example.py
python perception/b-semantic-compaction/example.py

# Run all invariant tests
pytest
```

Each pattern folder is self-contained. No central framework, no plugin
system to learn. Read the folder's README, look at `pattern.py`, run
`example.py`, read the tests.

---

## How to read a pattern folder

```
<pattern-folder>/
  README.md                # The why — what failure mode this pattern catches
  README.zh-CN.md          # 中文版
  pattern.py               # The minimal honest implementation
  example.py               # A runnable case on production-shaped data
  test_pattern.py          # The invariants the pattern must hold
```

Read the README first — it's the *why* and the upstream slice. Then read
`pattern.py` to see the smallest amount of code that solves it. Run
`example.py` to see it work on data with shape. Tests pin the invariants
you must not break when adapting.

---

## The thesis behind the framework

Three lines from the book that this repo is the practical face of:

* *Designing an agent is solving a constrained allocation problem.*
* *A fixed token budget must be distributed across competing cognitive
  demands under non-deterministic execution paths.*
* *The model is the spender. The harness is the budgeter. The patterns
  are the strategies.*

Every pattern in the matrix is a strategy for one of those three roles —
how the harness budgets, how the patterns allocate, how the model is
positioned to spend. The matrix is what makes the strategies discussable
as a system rather than as a flat list.

---

## Book · Column · Newsletter

| | |
|---|---|
| **Manning** · *Designing AI Agents* | English-language technical book. 28 patterns across 7 cognitive functions and 6 topologies. ISBN 9781633433632. MEAP launch May 2026. |
| **极客时间** · 《Agent 设计模式之美》 | Chinese-language video column. Pattern-by-pattern walkthrough with engineering slices from real production harnesses. |
| **Substack** · *[Agent Design Patterns](https://agentpatterns.substack.com)* | Free English newsletter, one essay every 1–2 weeks. Structural observation, not hype. |
| **极客时间** · *Claude Code 工程化实战* | Published Chinese-language video column on the engineering practice of building agents on Claude Code. |

This GitHub repo is the **third leg**. The book gives you the theory. The
column gives you the lectures. This repo gives you code you can clone and
read in 90 seconds.

---

## Author

[Jia Huang (黄佳)](https://kage-ai.com) — Lead Research Engineer at A*STAR
Singapore, formerly senior consultant at Accenture Singapore.
Twenty years across NLP, LLMs, and AI applications in MedTech and
FinTech. Author of two forthcoming English-language books (*Designing AI
Agents* with Manning, *RAG from First Principles* with Packt) and six
Chinese-language books on machine learning, GPT, AI agents, RAG, and
data analysis with cumulative readers in the hundreds of thousands.

The two-axis framework is the author's original contribution; the
constituent elements (seven cognitive functions, six execution
topologies) are not new — the contribution is the orthogonal organization.

[kage-ai.com](https://kage-ai.com) · [LinkedIn](https://www.linkedin.com/in/huangjia2019/) · [Substack](https://agentpatterns.substack.com) · [tohuangjia@gmail.com](mailto:tohuangjia@gmail.com)

---

## Contributing

Issues welcome. Particularly useful:

* **Citation drift** — a verified engineering slice in a README points at
  a file or line that no longer matches upstream
* **Invariant violations** — a test misses a case that you've seen the
  pattern fail in production
* **New language ports** — TypeScript / Go ports of any pattern, opened
  as a separate top-level folder
* **New engineering slices** — a production harness you've worked with
  shows the pattern in a form not yet documented in the README

Pull requests for new patterns: please open an issue first to discuss
where the pattern sits in the matrix.

---

## Citation

If you use the two-axis framework or any pattern in academic or
industrial work:

```bibtex
@misc{huang2026agentpatterns,
  author = {Jia Huang},
  title  = {Agent Design Patterns: A Two-Axis Framework},
  year   = {2026},
  url    = {https://github.com/huangjia2019/agent-design-patterns},
  note   = {Companion code to \emph{Designing AI Agents} (Manning, 2026)}
}
```

## License

MIT. See [LICENSE](LICENSE).
