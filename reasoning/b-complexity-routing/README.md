# b · Complexity-Based Routing

> Column lecture **04-03** · pattern · reason × route
>
> [中文 README](README.zh-CN.md)

## The problem

A data-analysis agent for a mid-size SaaS company. Natural-language
queries from product, growth, and finance teams against the data
warehouse. The team defaulted everything to Claude Opus — "Opus is
strongest, just don't get it wrong." Quality was fine. SQL generation,
reports, attribution all worked.

Then finance flagged the bill: **¥480,000 in month one.** The team
sat down and traced what the queries actually were:

| Query shape | Share | What Opus is actually needed for |
|---|---:|---|
| "How many users signed up last week" | 41% | 0% — template SQL |
| "Group retention by region" | 22% | 30% — add a GROUP BY |
| "Why is GMV down 8% week-over-week" | 19% | 80% — multi-step attribution |
| "What if price moves up 10%, how does churn shift" | 4% | 100% — causal reasoning |
| Schema probes / intermediate tool steps | 14% | varies |

41% of traffic is a template fill. Opus at $15/$75 per million tokens
versus Haiku at $1/$5 is a **15× markup paid for nothing**. Three
weeks of work on a routing layer brought the bill to ~¥120k, with a
0.5% measured error rate.

The general claim: with GPT-4o-mini at roughly 16× cheaper than GPT-4o
and similar gaps across Claude tiers, routing 40-70% of traffic to a
cheaper tier typically halves the bill at no measurable quality loss
— **provided the routing is done with a real signal and the fallback
path is honest about when the cheap tier was wrong.**

## The pattern

Two classes, each with a single responsibility:

| Class | Role |
|---|---|
| `ComplexityRouter` | Picks an initial tier from the task shape using pluggable signals. Returns a `RoutingDecision` with `reason` and `score`. The reason is what an audit asks for first. |
| `FallbackChain` | Runs the chosen tier, validates the output, escalates to the next tier on `FallbackTriggeredError`. Records *why* each step failed so the audit log isn't just "tier=2 was used." |

Three tiers (`SIMPLE` / `MEDIUM` / `COMPLEX`) covers most production
needs. Hermes runs six. Most teams find three model tiers plus an off
switch is the sweet spot — more tiers add ops cost without quality
lift.

Pluggable signals: `length_signal`, `causal_keyword_signal`,
`template_query_signal`. The router takes the **strongest positive
signal** (not the average) — a single strong indicator like "prove" or
"why" is enough to escalate, no need to dilute it against a weak
length score. Negative signals (template patterns) are averaged and
subtracted, so a template pattern can pull a borderline task back to
SIMPLE.

The `FallbackTriggeredError` is a *semantic* exception — "quality not
good enough" — distinct from ordinary errors like network or auth
failures. Validators are pluggable. The chain has a hard escalation
ceiling (default 2 escalations = up to 3 tiers tried).

## Quickstart

```bash
python reasoning/b-complexity-routing/example.py
pytest reasoning/b-complexity-routing/
```

The demo runs six queries through the router and the full cascade.
Templates route SIMPLE and validate. Causal questions route COMPLEX
and skip the lower tiers. One escalating case shows the audit trail
with `fail_reason` recorded for each rejected step.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `ComplexityTier` + `RoutingDecision` + signal functions + `ComplexityRouter` + `FallbackChain` + `FallbackTriggeredError` (~220 lines) |
| `example.py` | Six-query data-analysis scenario with toy LLM + validator |
| `test_pattern.py` | 15 invariants: each signal function, router tier-picking, custom tier-model mapping, cascade escalation, fail_reason recording, COMPLEX entry skips lower tiers, exhaustion behavior |

## Engineering references (verified)

* **Claude Code** `FallbackTriggeredError` — the semantic exception
  that triggers tier escalation when output quality fails validation.
  The pattern's `FallbackTriggeredError` is a direct port of the
  shape: it's a *quality* signal, not a transport signal.
* **Hermes Agent** `ReasoningEffort` enum (six tiers: OFF / MINIMAL /
  LOW / MEDIUM / HIGH / MAX) — the finer-grained cousin. The case for
  six over three: each adjacent pair is ~3-5× cost apart, and `OFF`
  versus `MINIMAL` is meaningful when you have a class of
  zero-reasoning traffic.
* **Aider** `--model` + `--weak-model` flags — routes by *action type*
  rather than complexity. Git commit messages → weak model, code edits
  → main model. A different orthogonal: route by what the agent is
  doing, not by how hard the task is. Useful in narrow-domain agents.
* **Anthropic** [*Building Effective
  Agents*](https://www.anthropic.com/research/building-effective-agents)
  — the "use the cheapest model that works, escalate only when
  needed" framing.
* **Augment Code (2026)** [*AI model routing
  guide*](https://www.augmentcode.com/guides/ai-model-routing-guide)
  — role-based routing for coding agents: Opus orchestrates, Sonnet
  implements, Haiku navigates files, GPT-5.2 reviews.
* **Paxrel (2026)** [*AI agent cost
  optimization*](https://paxrel.com/blog-ai-agent-cost-optimization)
  — measured 47-80% cost reduction from good routing across
  production deployments, with sub-1% quality regression.

## Three production routes (pick one explicitly)

1. **Model-internal (OpenAI GPT-5 path).** The provider routes for
   you. Zero engineering, zero observability, single-vendor lock.
2. **Harness-explicit (this pattern + Hermes).** You own the policy
   and the audit. More work, but you can log every decision and
   change tiers across vendors. The honest choice for production.
3. **Third-party router (OpenRouter / LiteLLM).** Lowest engineering,
   adds a hop of latency and a data-flow concern. Reasonable for
   prototypes; risky for regulated workloads.

The pattern in this folder is route 2.

## When this pattern doesn't apply

* **Single-vendor, single-model deployments.** No tiers means no
  routing. Use the effort tier control from the
  [Chain-of-Thought pattern](../a-chain-of-thought/) instead.
* **Domain-narrow agents where the cheap tier already meets quality.**
  If Haiku is enough for translation or sentiment, escalation just
  burns money on speculative quality lift.
* **Hard real-time loops (<200 ms budget).** The cascade itself adds
  latency. Pick a tier statically and live with it.

## Honest limitations

The signal-based router is a heuristic. It will mis-classify some
queries either direction. The real product investment is in the
*validators*: a router that picks SIMPLE for a hard query is fine as
long as the validator catches the bad output and the chain escalates.
A router that picks COMPLEX for a simple query is wasteful but won't
be wrong. **Get the validators right before tuning the router.**

The cascade also assumes monotonic quality: tier N+1 is at least as
good as tier N. This is mostly true across Claude / GPT tiers but
breaks at the edges (a smaller model sometimes refuses a query the
larger one happily mishandles). Validators that reject *both* a
refusal and a hallucination are stronger than ones that only check
for one.
