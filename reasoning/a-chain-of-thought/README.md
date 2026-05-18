# a · Chain of Thought

> Column lecture **04-02** · pattern · reason × chain
>
> [中文 README](README.zh-CN.md)

## The problem

A small-claim auto-insurance agent gets upgraded from a non-reasoning
model to a reasoning model. The team adds the well-meaning prompt:

```
Please analyze this claim step by step:
1. Check policy applicability
2. Check amount against the limit
3. Check claim history
4. Then give the final decision
```

Two things happen. First, per-claim latency goes from 4s to 11s and
the monthly LLM bill triples. The team chalks it up to the new model
being expensive. Then the regulator pulls a denial letter from May 3rd
and asks for the agent's reasoning trail. **The thinking field on
that record is empty.**

Root cause: that request was rate-limited by Opus mid-stream and the
harness silently failed over to Sonnet. Sonnet rejected the
Opus-signed thinking blocks, the harness stripped them before
forwarding, and nothing wrote a structured record of what was
stripped. The model's reasoning was real; the audit trail of it was
not.

Two real lessons, neither of which is "add a step-by-step prompt":

1. **`Let's think step by step` is dead on reasoning models.** The
   model is already thinking. Stacking step instructions on top burns
   tokens and confuses the chain. Wharton 2025 measured the prompt
   trick on frontier models at a 2.9–3.1% lift — within noise.
2. **You still have to manage the thinking the model emits.** Storage,
   cross-model fallback signatures, audit redaction, effort tier
   control. These don't happen by themselves. The harness owns them.

## The pattern

A four-noun lifecycle:

```
emit  →  store  →  audit  →  migrate  →  control
```

The 2026 reframe: **Chain of Thought is not a prompt trick, it's the
audit log of the agent's reasoning trajectory, treated as first-class
structured data with lifecycle invariants enforced in the harness.**

The pattern is two classes:

| Class | Role |
|---|---|
| `ThinkingBlock` | One contiguous block emitted by a model. Carries the provider signature so cross-model fallback can decide if it's portable. |
| `CoTTrace` | One task's full trajectory. Knows its total thinking tokens, its reasoning-token ratio, and how to `strip_for_fallback(target_model)` without mutating itself. |
| `CoTManager` | Runtime entry point. Creates traces, picks effort tiers, normalizes provider-specific tags (`<reasoning>` / `<think>` / `<thought>`), and produces regulator-vs-customer audit views. |

Five effort tiers (`OFF`, `LOW`, `MEDIUM`, `HIGH`, `MAX`) — the
Anthropic-standard four plus `OFF` for the cases where the agent
shouldn't be thinking at all. Hermes uses six (adds `MINIMAL`); four
is the more common production choice and the one this reference ships.

## Quickstart

```bash
python reasoning/a-chain-of-thought/example.py
pytest reasoning/a-chain-of-thought/
```

The demo replays the lecture-opening incident. Two claims come in.
Claim 1 is routine. Claim 2 is ambiguous, mid-stream Opus
rate-limits, the trace gets stripped for fallback to Sonnet, Sonnet
emits a portable (unsigned) block, the customer audit view stays
redacted while the regulator view shows the full fallback chain.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `ThinkingEffort` + `ThinkingBlock` + `CoTTrace` + `CoTManager` (~230 lines) |
| `example.py` | Auto-insurance claim scenario with mid-stream provider fallback |
| `test_pattern.py` | 19 invariants: block portability, strip-for-fallback purity, token ratio, tag normalization across 3 providers, effort estimator branches, regulator vs customer audit views |

## Engineering references (verified)

* **Claude Code** `query.ts:151-163` — the "three iron rules":
  thinking signatures are model-bound (`strip_for_fallback`), thinking
  is paid tokens but not free quality (effort tier control surface),
  and thinking must survive trajectory serialization.
* **Hermes Agent** `agent/cli.py` `_strip_reasoning_tags` — the
  cross-provider tag normalizer. OpenAI `<reasoning>`, DeepSeek
  `<think>`, Google `<thought>`, Anthropic structured blocks. The
  pattern's `CoTManager.normalize_tags` is a minimal version of the
  same idea.
* **Anthropic Think-as-Tool** — wraps the thinking step as an explicit
  tool the agent can call. The Tau-bench airline benchmark reported
  ~20pp accuracy lift from this framing. Not implemented here but the
  audit-log shape is identical.
* **OpenAI (2026)** [*Reasoning models struggle to control their
  chains of thought*](https://openai.com/index/reasoning-models-chain-of-thought-controllability/)
  — controllability score 0.1–15.4% across frontier reasoning models.
  Implication: the model cannot self-redact, so the harness must.
* **OpenAI (2026)** [*Evaluating CoT
  monitorability*](https://openai.com/index/evaluating-chain-of-thought-monitorability/)
  — "Monitoring chains-of-thought is substantially more effective
  than monitoring actions and final outputs alone." This is the
  argument for treating CoT as audit data instead of throwaway.
* **Goodfire (2026)** [*Reasoning Theater: Performative
  CoT*](https://www.goodfire.ai/research/reasoning-theater) — CoT
  text sometimes diverges from the model's internal activations.
  Honest treatment of this is in the limitations section below.
* **Wharton (2025)** — prompt-trick CoT lift on reasoning models
  measured at 2.9–3.1%, within noise. The argument for retiring
  `Let's think step by step`.

## When this pattern doesn't apply

* **Ultra-low-latency interactive surfaces.** If the user needs a
  reply in <200 ms, extended thinking is not free. Use
  `ThinkingEffort.OFF` and keep the trace shell as the audit hook.
* **Classification / sentiment / trivial Q&A.** A reasoning model
  spending 800 thinking tokens on "is this comment positive or
  negative" is the wrong shape. Estimate-low or estimate-off.
* **Demos and prototypes with no audit consumer.** The full lifecycle
  is overhead. Keep `CoTTrace` for the shape, skip the regulator view.

## Honest limitations

CoT is the most useful observability signal available for agents in
2026 — and it cannot be fully trusted. Goodfire's *Reasoning Theater*
work showed that the textual chain a model emits is sometimes a
post-hoc justification rather than a faithful record of its internal
computation. Trace your CoT, dashboard it, alert on it. **For
high-stakes decisions, add an external verification layer (tool
checks, test cases, ground truth) instead of trusting the chain
alone.**

OpenAI's monitorability paper called this "a fragile opportunity":
future model generations may not emit visible CoT at all. Build the
audit infrastructure now while the window is open.
