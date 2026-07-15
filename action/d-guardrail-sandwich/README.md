# d · Guardrail Sandwich

> Column lecture **05-05** · pattern · act × hierarchy
>
> [中文 README](README.zh-CN.md)

## The problem

The Payroll Lab injects an E0099 approval for 999999. The approval
record is valid, but its amount violates the payment policy. A
pre-hook blocks the exact amount read from that approval, and a
ledger check proves that the transfer handler never ran.

The same deterministic lab covers a frozen account, a missing bank
receipt, account data in an export, and a policy in shadow mode.
These are synthetic control-flow experiments, not claims about a
real bank's incident or error rate.

```
[pre-hooks]
  - account format check                  → block on bad shape
  - account whitelist                     → block when not corporate-list
  - amount threshold (>¥1M needs approval) → block for human review
  - blocklist (OFAC SDN)                  → block unconditionally
  - schema validation v2                  → block on shape drift
[transfer_funds]
  - controlled payment call (SQLite state change in this course)
[post-hooks]
  - output schema verifies the receipt    → mark rollback if missing
  - funds-landed verification              → mark rollback if unconfirmed
  - PII redaction scan                    → mark rollback if leaked
  - AML post-scan                         → trigger compliance review
  - 7-year audit log                       → archived
```

The sandwich provides defense in depth and explicit temporal states.
It proves which checks ran, whether the tool ran, and whether a
post-execution failure requires compensation. It does not promise
that model reasoning is always correct.

## The pattern

Two classes and four hook factories:

| Construct | Role |
|---|---|
| `HookSpec` | One hook. `name` / `phase` / `fn` / `priority` / `blocks` / `applies_to` plus `policy_owner` and `policy_version`. Pre-hooks that BLOCK stop the tool. Post-hooks that BLOCK mark the trace for rollback. |
| `GuardrailSandwich` | Wraps every tool call in `pre_hooks → tool → post_hooks` and records a `SandwichTrace`. The reference registry remains public; production must close bare-handler paths at the service or capability boundary. |
| `amount_threshold_hook` / `blocklist_hook` / `output_schema_hook` / `pii_redaction_hook` | Common factories. Real deployments have ~20-40 hooks; these are the ones you cannot avoid writing yourself. |

Three named failure modes from the lecture, each addressed:

| Failure mode | What it is | What addresses it |
|---|---|---|
| **Composition bypass** | Agent finds a path to call the tool that skips the sandwich (a sub-tool wraps it, or a raw HTTP call). | The reference demonstrates the risk but does not close it at the language level. Production exposes only a controlled proxy. |
| **Sandwich overhead tax** | Wrap *every* tool, including reads, and latency triples. | `applies_to` scopes a hook to specific tools. Reads skip the destructive sandwich; only writes pay the full toll. |
| **Schema drift** | Pre-hook validates against schema v1; the LLM starts emitting v2; the hook lets bad payload through. | `output_schema_hook` fails closed on unrecognized shapes — both `missing keys` and `not a dict` block. Versioned schemas live in the hook, not in scattered prompts. |

Three behavioral guarantees:

1. **Pre-hook BLOCK = tool never runs.** No retry, no warning, just
   refused. The audit trail names the hook that refused.
2. **Hook crashes fail closed.** If a hook itself raises, the
   sandwich treats it as a BLOCK. A buggy guardrail does not become
   an open door.
3. **All post-hooks run on success, not just up to the first
   block.** Audit completeness: every issue gets into the trace, not
   just the first one. The operator dashboards the lot.

Plus one production knob: **shadow mode**. A hook with `blocks=False`
records BLOCK as `[shadow] WARN` and lets execution continue. Teams
can measure match rate, false positives, and business impact before
enforcement. The observation window and acceptable false-positive
rate are business decisions, not universal constants.

## Quickstart

```bash
python action/d-guardrail-sandwich/example.py
pytest action/d-guardrail-sandwich/
```

The demo runs four scenarios through the corporate-banking sandwich:
a routine ¥4,200 transfer (passes), a mis-typed account that the
whitelist catches (blocks at PRE before any money moves), a ¥5M
amount that the threshold catches (blocks at PRE; would route to
human approval), and a shadow-mode hook example (BLOCK downgraded to
[shadow] WARN; tool still runs while you tune).

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `HookPhase` + `HookResult` + `HookSpec` + `HookOutcome` + `SandwichTrace` + `GuardrailSandwich` + 4 hook factories + `GuardrailViolation` (~260 lines) |
| `example.py` | Synthetic corporate-payment scenarios for pre-blocking and shadow mode |
| `test_pattern.py` | 24 invariants: hook factories, registration guards, pre/post behavior, priority, shadow mode, fail-closed hook crashes, rollback markers, `applies_to` scoping, timestamps, and policy provenance |

## Engineering references (verified)

* **Claude Code** Hooks Pipeline — `PreToolUse` can deny a tool
  before execution. `PostToolUse` and `PostToolUseFailure` provide
  observation points after the action; they cannot undo a file write
  or network request that already happened.
* **OWASP** [*Top 10 for Agentic Applications
  (2026)*](https://genai.owasp.org/) — Agent Goal Hijack, Tool Misuse,
  and Prompt Injection all motivate controls outside model reasoning.
  This README cites the risk categories, not an unverified incident rate.
* **NVIDIA NeMo Guardrails** — programmable guardrails in the Colang
  DSL. The four-rail model (input / dialog / retrieval / output)
  maps onto pre-hook (input rail) and post-hook (output rail). GPU
  acceleration for ML-based rails.
* **GuardrailsAI** — RAIL spec for declarative guardrails. The
  self-correction loop (failed output → feedback → model retries)
  is what `blocks=False` could compose with — guardrail not as veto
  but as feedback.
* **Microsoft Guidance** — schema-as-constraint at the grammar
  level. Compile-time deterministic guardrails. Composes with this
  pattern: use Guidance for structural constraints, hooks for
  semantic ones.
* **Anthropic** [*Trustworthy agents in
  practice*](https://www.anthropic.com/research/trustworthy-agents)
  — high-autonomy systems need defense in depth, observability, and
  controllable boundaries. Shadow mode turns a proposed rule into an
  observable signal before it becomes enforcement.

## When this pattern doesn't apply

* **All-read-only tool sets.** No destructive surface, no need for
  bread on either side. The cost of wrapping reads in pre/post is
  pure latency tax.
* **Single-tool agents.** If there's only one thing the agent can do
  and it has its own native check infrastructure, the sandwich is
  duplicating work.
* **Real-time loops with <100ms budget.** Hooks are usually cheap
  but stack: 5 hooks at 5ms each is 25ms, and that's before you've
  called the tool. Pick a tier statically.

The sandwich's value is concentrated where *destructive surface*
meets *high cost of error*. Banking, healthcare, infrastructure
changes, anything that touches a customer's data. For pure
information retrieval, this is theatre.

## Honest limitations

The sandwich does not rollback. It *marks* a trace as needing
rollback (post-hook BLOCK sets `rollback_marked=True`); the actual
inverse-action saga lives in the [Tool Dispatch
pattern](../a-tool-dispatch/), which records the rollback action at
registration. In production you wire the two together: the saga log
from Tool Dispatch handles the un-doing; the sandwich's post-hook
chain decides *when* to call rollback.

The reference does not handle hook *order independence*. Today
priority is a manual integer. Production deployments often want
some hooks to declare "must run before X" or "must run after Y" as
a DAG; this reference's flat priority list is the minimum honest
form. Override `_applicable_hooks` to sort by dependency graph if
the simple form is too coarse.

Hooks here are synchronous. Real banking deployments often have
hooks that themselves call out (CSAI / DLP / SIEM / fraud-scoring
services). Wrapping each hook in `asyncio` is straightforward; the
contract (`HookFn` returns `(HookResult, reason)`) doesn't change.

Finally: a sandwich that blocks too much is worse than no sandwich.
Operations will disable it inside a quarter. The shadow-mode hook
exists precisely so you don't go from zero guardrails to "block
30% of legitimate traffic" overnight. Use it.
