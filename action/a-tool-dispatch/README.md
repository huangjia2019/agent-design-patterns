# a · Tool Dispatch

> Column lecture **05-02** · pattern · act × route
>
> [中文 README](README.zh-CN.md)

## The problem

A city-logistics agent for a mid-size delivery company. Seventeen
tools wired up: `query_orders`, `query_drivers`, `query_traffic`,
`get_eta`, `assign_driver`, `unassign_driver`, `notify_customer`,
`reroute`, `consolidate_orders`, `split_order`, … The team gave the
LLM all of them and let it figure out which to call.

10 AM Monday. 80 orders queued from the weekend. Five minutes after
the agent starts: **all 80 orders are assigned to `driver_007`**.
That driver is currently stuck in traffic on Chang'an Avenue.

The agent's reasoning trace shows what happened. It called
`query_drivers`, got twelve available drivers, picked the highest-
rated (driver_007, 4.9 stars), assigned the first order, told itself
*"driver_007 looks good, keep going,"* and dispatched
`assign_driver(order_N, driver_007)` 79 more times without ever
re-querying state. The dispatcher had no opinion about any of this.

Three root causes the team wrote up afterward:

1. **Wrong tool selection.** The agent jumped straight into
   assignment without calling `consolidate_orders` or `query_traffic`
   first.
2. **Parameter staleness.** The driver's `available` flag flipped to
   false after the first assignment, but the agent never refreshed it.
3. **Side-effect accumulation.** Eighty destructive writes ran with
   no quota, no inverse, no audit; rolling back was a 90-minute
   manual cleanup.

The lecture's broader claim: **LLMs are good at *using* tools (filling
parameters, reading results); they are bad at *selecting* tools.**
Selection is a harness responsibility. The dispatcher in this
pattern is what that responsibility looks like in code.

## The pattern

Three classes, one contract:

| Class | Role |
|---|---|
| `ToolMetadata` | Typed contract for one tool. Claude Code's 14-field schema trimmed to the ten that matter for the dispatcher: identity, when-to-use, when-not-to-use, exclusivity, five enforcement flags (read-only, concurrency-safe, destructive, requires-fresh-state, requires-approval), quota, rollback action. |
| `DispatchTrace` | The audit record for one call. Status is `success` / `failed` / `rejected`. `rejected` carries the *reason* — `tool_hallucination`, `quota_exceeded`, `stale_state_must_refresh`, `awaiting_approval`. |
| `ToolDispatcher` | The runtime. Registers tools, enforces the contract on every call, maintains the saga log, runs reverse rollback. |

Five non-negotiable enforcement points. The iron rule is the first:

| Point | What it does |
|---|---|
| Defaults are unsafe | `is_read_only` and `is_concurrency_safe` default to `False`. Silence means destructive. Forget to declare a tool safe and the dispatcher protects you anyway. |
| `quota_per_session` | Cap N calls per session × tool × primary-arg. The 80-orders-to-one-driver guard, encoded. |
| `requires_fresh_state` | Block destructive writes if the session hasn't done a read in `STATE_FRESHNESS_SECONDS`. Pairs with a successful read auto-refreshing the timestamp. |
| `requires_approval` | Short-circuits execution and returns `awaiting_approval`. Hands off to the Approval Gate pattern. |
| `rollback_action` | Records the inverse for the saga log. Destructive tools without a rollback name **cannot be registered** (raises `ToolDispatchError`). |

Two registration guards (raised at registration, not runtime):

* A destructive tool without a `rollback_action` cannot be registered.
* A tool cannot be both `is_read_only=True` and `is_destructive=True`.

## Quickstart

```bash
python action/a-tool-dispatch/example.py
pytest action/a-tool-dispatch/
```

The demo replays the city-logistics incident. The agent tries to
assign eight orders to driver_007. The first five succeed; the next
three are rejected as `quota_exceeded`. A halluciated tool name is
rejected as `tool_hallucination`. A stale-state write on a fresh
driver is rejected as `stale_state_must_refresh`. The saga rollback
unwinds all five committed assignments in reverse order.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `RiskLevel` + `ToolMetadata` + `DispatchTrace` + `ToolDispatcher` + `ToolDispatchError` (~230 lines) |
| `example.py` | City-logistics scenario reproducing the lecture-opening incident |
| `test_pattern.py` | 18 invariants: registration guards, quota scoping (per session × tool × primary arg), state-freshness window, approval short-circuit, hallucination rejection, saga rollback ordering, cross-session isolation, trace recording |

## Engineering references (verified)

* **Claude Code** [`Tool.ts:386-456`](https://docs.claude.com/en/docs/claude-code/) — the 14-field tool metadata schema. The pattern uses ten of them; the four left out (`aliases`, `prompt`, `interruptBehavior`, `shouldDefer`) are UI / progressive-disclosure concerns that don't change the dispatcher's contract.
* **Anthropic** [Programmatic Tool Calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) — the *engineering-driven* dispatch model the lecture argues for. The reference can run either way: `triggered_by="llm"` for free-form selection, `triggered_by="programmatic"` for engineer-defined sequences. The contract is the same; only the caller changes.
* **Codex CLI** `execpolicy` crate — an out-of-process policy engine in Rust. The reference embeds policy in the dispatcher; production deployments typically hoist it to a separate binary for tamper resistance.
* **arxiv:2602.14878** [*MCP Tool Descriptions Are Smelly*](https://arxiv.org/html/2602.14878v1) — measured 15–25pp accuracy lift from augmenting tool descriptions with selection guidance. The `when_to_use` / `when_not_to_use` fields exist for exactly this reason.
* **OWASP Top 10 for Agentic Applications (2026)** A2 *Tool Misuse* — names this pattern's failure mode and gives the production statistics: 88% of organizations report at least one agent-related security incident in the last year.
* **Manus** — Yichao "Peak" Ji's *Context Engineering for AI Agents*: **32 tools is the upper bound** before LLM selection accuracy collapses. The lecture cites GitHub Copilot's drop from 40 → 13 tools and Block's Linear MCP server's 30+ → 2 as further evidence.

## When this pattern doesn't apply

* **Agents with 1–2 tools.** The whole dispatcher is overhead. A
  bare function call is fine.
* **Pure conversation agents.** No tools, no dispatch.
* **All-read-only tool sets.** The risk surface is small; quota and
  rollback are theatre. A simple registry is enough.

The dispatcher's value is concentrated where *tool count*, *side
effects*, and *cost of error* all stack up. Drop any one of the three
and you're over-engineering.

## Honest limitations

The default quota key is `(session, tool, first-arg)`. That fits
"don't route 80 orders to one driver" cleanly but mis-fires on tools
where the primary resource isn't the first argument. Override
`_quota_key` for those cases, or pass a canonicalized first arg.

State freshness here is timestamp-based and global per session. Real
deployments often need per-resource freshness ("driver_007's state
must be re-read"; driver_012's older read is still fine). Wrap the
freshness check in a per-key version if the simple form is too
coarse.

The saga log is in memory. Production needs persistent storage so
crashes can replay the inverse chain. The contract (record an inverse
on destructive success; rollback in reverse) doesn't change — only
where the bytes live.
