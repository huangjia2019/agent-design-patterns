# d · Guardrail Sandwich

> Column lecture **05-05** · pattern · act × hierarchy
>
> [中文 README](README.zh-CN.md)

## The problem

A corporate-banking agent at a mid-size bank. Its job: triage email
transfer requests from relationship managers, parse out the
counterparty and amount, queue a SWIFT transfer if the request is
clean.

Week three. An email arrives: "Transfer ¥3.2M to account
...XX23." The agent parsed the last two digits as "32." The
`transfer_funds` tool ran. Twelve hours later, reconciliation
caught it. By then the recipient had withdrawn part of it.

Root cause: `transfer_funds` was a single tool call with no
pre-check (account whitelist? amount threshold? AML rules? OFAC
sanctions list?) and no post-check (did the funds land where
intended? was the receipt schema valid? any PII in the response?).
The agent's reasoning trace was clean; it was confidently wrong, and
nothing stood between the wrong reasoning and the wire.

After the rewrite: every destructive tool wrapped in a sandwich.

```
[pre-hooks]
  - account format check                  → block on bad shape
  - account whitelist                     → block when not corporate-list
  - amount threshold (>¥1M needs approval) → block for human review
  - blocklist (OFAC SDN)                  → block unconditionally
  - schema validation v2                  → block on shape drift
[transfer_funds]
  - actual SWIFT call inside sandbox
[post-hooks]
  - output schema verifies the receipt    → mark rollback if missing
  - funds-landed verification              → mark rollback if unconfirmed
  - PII redaction scan                    → mark rollback if leaked
  - AML post-scan                         → trigger compliance review
  - 7-year audit log                       → archived
```

Mis-transfer rate: 0.3% → **0.001%**. Latency +2–3s per transfer.
In a banking workflow that ratio is not a trade-off, it's a no-brainer.

The lecture's general claim, framed against due process in law:
**Guardrail Sandwich is procedural justice for agent actions.**
Pre-checks are the preliminary hearing. The tool call is the
judgment. Post-checks are the appeal / audit. Skip either bread
slice and you're back to "agent did what it wanted, hope it was
right."

## The pattern

Two classes and four hook factories:

| Construct | Role |
|---|---|
| `HookSpec` | One hook. `name` / `phase` (PRE or POST) / `fn` (callable) / `priority` / `blocks` / `applies_to`. Pre-hooks that BLOCK stop the tool. Post-hooks that BLOCK mark the trace for rollback. |
| `GuardrailSandwich` | Wraps every tool call in `pre_hooks → tool → post_hooks`. Records a `SandwichTrace` with every hook's verdict. Tools registered here are the *only* callable entry; bare handlers are not exposed (closes **composition bypass**). |
| `amount_threshold_hook` / `blocklist_hook` / `output_schema_hook` / `pii_redaction_hook` | Common factories. Real deployments have ~20-40 hooks; these are the ones you cannot avoid writing yourself. |

Three named failure modes from the lecture, each addressed:

| Failure mode | What it is | What addresses it |
|---|---|---|
| **Composition bypass** | Agent finds a path to call the tool that skips the sandwich (a sub-tool wraps it, or a raw HTTP call). | `register_tool` makes the sandwich the only entry. Tool handlers are private to the dispatcher; there's no public reference to call. |
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
records BLOCK as `[shadow] WARN` and lets execution continue. That
maps directly to the lecture's recommended three-phase rollout:
weeks 1-2 monitor mode (collect false-positive distribution); weeks
3-4 soft enforcement (block obvious violations, warn on edge cases);
month 2+ full enforcement. Going straight to full enforcement
typically blocks 30%+ of legitimate traffic on day one — operations
team kills the sandwich, you're back to square one.

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
| `example.py` | Corporate-banking scenario reproducing the ¥3.2M mis-transfer incident's fix |
| `test_pattern.py` | 23 invariants: each hook factory, duplicate-tool guard, unknown-tool handling, no-hooks passthrough, pre-block prevents tool, priority ordering, shadow mode, hook crash fails closed, post-block marks rollback, post-chain completeness, tool error skips post, `applies_to` scoping, trace timestamps |

## Engineering references (verified)

* **Claude Code** Hooks Pipeline — 12 lifecycle events; `PreToolUse`
  is the only hook that can `block` (exit code 2). `PostToolUse`
  cannot un-run the tool but can validate / scan / flag. The
  pattern's two-phase chain is a direct port.
* **OWASP** [*Top 10 for Agentic Applications
  (2026)*](https://genai.owasp.org/) — A1 *Agent Goal Hijack*, A2
  *Tool Misuse*, A3 *Prompt Injection* all map onto pre-hooks
  (whitelist, blocklist, schema). The 88% incident rate quoted in
  the lecture is from the OWASP industry survey.
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
* **Anthropic** [*Defense-in-depth* rollout
  guidance](https://www.anthropic.com/news/agent-security) — the
  three-phase rollout (monitor → soft → full enforcement) the
  shadow-mode feature was designed for.
* **arxiv:2509.23994** [*AI Agent Code of Conduct: Policy-as-Prompt
  Synthesis*](https://arxiv.org/abs/2509.23994) — a financial agent
  in monitor mode for 14 days: 47 rules trimmed to 21 (false-positive
  pruning), 13 new rules added (attack patterns surfaced in
  monitoring). This is the production calibration loop the shadow
  mode enables.

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
