# Lightweight Collaboration Labs

These deterministic labs are short teaching entries for the collaboration
patterns. They complement the production-shaped implementations in the sibling
pattern directories.

## Clone and open the workbench

The workbench uses only the Python standard library:

```bash
git clone https://github.com/huangjia2019/agent-design-patterns.git
cd agent-design-patterns
python3 collaboration/light_labs/web_app.py
```

Open `http://127.0.0.1:8098`, select lessons 32 through 35 or bonus B1, and click
**Run comparison**. The page invokes the deterministic Labs and displays the
baseline, the pattern-enabled result, and the checks performed at each step.

## Editorial delegation

Three researchers prepare a one-page multi-agent framework brief. A vague
assignment sends all three toward the same topic. Scoped assignments divide the
brief into topology, state, and handoff lanes. The parent accepts the set only
when every lane appears once and every card names a source.

Run it without an API key:

```bash
python3 collaboration/light_labs/editorial_delegation_lab.py
```

Run its invariant tests:

```bash
pytest -q collaboration/light_labs
```

The scripted `research()` function keeps the failure reproducible. Replace that
function with a model or an agent framework to experiment with live workers.
The assignment and acceptance interfaces should remain unchanged.

## DeepSeek Harness adapter

DeepSeek AI released DeepSeek Harness in August 2026. It is currently labeled a
Developer Preview and follows an "everything is a plugin" architecture. Its
unified `ctx.subagents` seam supports providers including `spawn`, `fork`, ACP,
Codex, Claude Code, and the dsh SDK.

`dsh_editorial_delegation/` binds the same three responsibilities to isolated
DeepSeek Harness `spawn` subagents and adds a deterministic `brief_gate` tool.
The runtime owns child sessions and lifecycle. The gate still owns portfolio
coverage and duplicate detection.

After preparing a DeepSeek Harness source checkout, run:

```bash
DSH_SOURCE=/path/to/deepseek-harness bash collaboration/light_labs/dsh_editorial_delegation/run_web.sh
```

## The remaining collaboration patterns

The same editorial story continues through three focused labs:

```bash
python3 collaboration/light_labs/editorial_gather_lab.py
python3 collaboration/light_labs/editorial_review_lab.py
python3 collaboration/light_labs/editorial_handoff_lab.py
```

| Lab | Failure made reproducible | Contract introduced |
|---|---|---|
| Fan-out/gather | A flat majority vote erases a shared-workspace boundary | Typed evidence, coverage, conflict, and attribution |
| Adversarial review | Two blocker comments are recorded but publication continues | Structured objections and a version-bound review receipt |
| Handoff chain | A corrected claim is lost and the stale claim is published | Immutable baton, stage ownership, and content binding |

All four labs are deterministic. They demonstrate the coordination contract
without pretending that fixed fixtures measure a live model.

## Bonus: Harness concurrency versus business aggregation

`runtime_business_gather_lab.py` isolates a boundary that is easy to blur. A
Harness can start workers concurrently, wait for settlement, and report
timeouts. Payroll code must still decide whether the returned evidence earns a
business conclusion.

| Plane | Implementation | Responsibility |
|---|---|---|
| Runtime | `AsyncFanOutHarness` | Concurrency, timeouts, worker status, wall time |
| Evidence | `PayrollEvidenceGatherer` | Coverage, period/unit, lineage, amount and headcount invariants |

Run all five deterministic scenarios:

```bash
python3 collaboration/light_labs/runtime_business_gather_lab.py
```

Run the case where all three workers succeed but the business invariant fails:

```bash
python3 collaboration/light_labs/runtime_business_gather_lab.py --scenario unexplained-gap
```

An OpenAI Agents SDK, Anthropic subagent, or DeepSeek Harness integration only
replaces `EvidenceProvider.collect()`. The `EvidenceCard` and business gather
remain provider-neutral.

## Scope

These labs demonstrate responsibility coverage, evidence-preserving aggregation,
review enforcement, version-bound handoff, and the separation between runtime
settlement and a business verdict. They do not assess source
freshness, factual accuracy, model quality, or production authorization. The
DeepSeek Harness adapter demonstrates a real subagent integration seam, while
live model behavior still depends on credentials, providers, prompts, and
network conditions.
