# c · Parallel Exploration

> Column lecture **04-04** · pattern · reason × parallel
>
> [中文 README](README.zh-CN.md)

## The problem

A medical-imaging agent for a tier-three hospital reads CT scans to
mark suspicious lung nodules. The team validated it offline at 89%
accuracy with a single-chain CoT pipeline. Three weeks into the pilot
it issued a BI-RADS 3 read on a 12mm right-upper-lobe nodule. Three
months later the patient came back: the nodule was now 18mm and the
biopsy returned early-stage adenocarcinoma.

Reviewing the agent's reasoning trace, every step was internally
correct. The chain detected the 12mm nodule, evaluated edge
morphology as relatively smooth, found no obvious spiculation or
pleural retraction, and arrived at BI-RADS 3. The doctors who
re-read the scan agreed the spiculation was *faint* — a single chain
could plausibly miss it. **Run the same prompt five times and at
least one branch catches it.**

The team rewrote to N=5 parallel reads. Three branches still say
BI-RADS 3 (confidence ~0.85). Two catch faint spiculation /
pleural retraction and flag BI-RADS 4a (confidence ~0.74). Under
majority vote: still 3. The team's actual decision: **any branch
flagging 4a triggers human review.** That call moved the catch
three months earlier in the next analogous case.

| Reality | Engineering takeaway |
|---|---|
| A single CoT chain has lucky-seed bias | Same prompt, different samples → different reads |
| Majority vote is not the right aggregator everywhere | In medical reads, missing a real alarm costs more than a false alarm |
| 5× the tokens for 7pp of accuracy | Worth it when error cost is asymmetric |
| Branch isolation matters | Cross-branch event-loop bleed turns "independent samples" into "shared mistakes" |

## The pattern

One class, `ParallelExploration`. Run N branches in parallel, aggregate
with one of five strategies, keep all branches in the trace so the
audit replays the disagreement (not just the winner).

Five aggregators, picked by *business* error-cost shape, not by
engineering preference:

| Strategy | When it fits | One-line rule |
|---|---|---|
| `MAJORITY` | Discrete answers, symmetric error cost | Vote |
| `WEIGHTED` | Branches self-report confidence | Sum confidence per answer |
| `VERIFIER` | Open-ended answers (writing, code) | A judge function picks the best |
| `FIRST_CORRECT` | There's a cheap correctness check | First branch the checker accepts wins |
| `ANY_ALARM` | Asymmetric error (medical, fraud, safety) | Any flagged branch escalates |

The lecture's medical case is the textbook `ANY_ALARM` use. Most
production traffic is `MAJORITY` or `WEIGHTED`. `VERIFIER` is the
costliest and shines for open-ended generation.

Two production health metrics the pattern exposes:

* **`branch_agreement_rate`** — share of branches voting for the
  modal answer. Health-line 0.60–0.80. Too low (<0.50) means the task
  really is hard — parallel is paying its way. Too high (>0.90) means
  the branches are saying the same thing — N is overkill.
* **`effective_n`** — number of *distinct* answers. Close to N means
  prompt variation is doing its job. Close to 1 means the branches
  are wasted.

N is usually 3–5. Wang's 2024 CoT-PoT paper shows N=2 already gets
90% of the lift you'd get from N=10. Above 5 the marginal accuracy
returns drop sharply while cost goes linear.

## Quickstart

```bash
python reasoning/c-parallel-exploration/example.py
pytest reasoning/c-parallel-exploration/
```

The demo runs the CT scan scenario through all five aggregators on
the same set of five branches. Side-by-side output shows why aggregation
choice is the load-bearing decision: same data, five different verdicts.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `AggregationStrategy` enum, `BranchResult`, `ParallelTrace`, `ParallelExploration` (~180 lines) |
| `example.py` | Medical CT scan scenario — five reads, five aggregators side-by-side |
| `test_pattern.py` | 16 invariants: each aggregator, alarm escalation, confidence weighting, missing-function guards, fallback-to-majority on first_correct miss, metrics on empty traces |

## Engineering references (verified)

* **Wang et al. (2022)** [*Self-Consistency Improves Chain of Thought
  Reasoning in Language
  Models*](https://arxiv.org/abs/2203.11171) — N-sample + majority
  vote; raised GSM8K from 17.9% to ~58% on GPT-3.
* **Wang et al. (2023)** [*Universal
  Self-Consistency*](https://arxiv.org/abs/2311.17311) — extends SC to
  open-ended outputs via a judge LLM. That's `AggregationStrategy.VERIFIER`.
* **Yao et al. (2023)** [*Tree of
  Thoughts*](https://arxiv.org/abs/2305.10601) — extends N flat
  branches into a search tree. Game-of-24 from 7.3% (IO) → 74% (ToT-5)
  at ~25× tokens. Out of scope for this minimal pattern; relevant for
  combinatorial-search tasks specifically.
* **Wang et al. (2024)** [*CoT-PoT
  Ensembling*](https://arxiv.org/abs/2406.14833) — N=2 already
  captures ~90% of the N=10 lift. The argument for keeping N small.
* **DeerFlow** isolated-event-loop pattern — each branch in its own
  asyncio coroutine with its own LLM client and trace buffer, so
  branch failure doesn't cross-contaminate. The async runtime the
  reference would wrap in production.
* **Anthropic** sub-agent fan-out — same pattern, different units
  (sub-agents instead of reasoning branches). Most production parallel
  reasoning in 2026 lives inside multi-agent orchestrators rather
  than as a separate "parallel CoT" middleware.

## When this pattern doesn't apply

* **Cheap-tier-already-good tasks.** If single-chain accuracy is
  already at the business target, N branches just multiply the bill.
  Run [Complexity-Based Routing](../b-complexity-routing/) instead
  and keep parallel for the cases that actually need it.
* **Hard latency budgets.** Sync fan-out is N× the latency floor of
  one branch. Async fan-out is bounded by the slowest branch. Neither
  fits a <500 ms budget; pick a single tier and live with the noise.
* **Ultra-long context.** Each branch carries the full context.
  N=5 with a 200k context window costs 1M context tokens before any
  output. Either compress the context first (see [Semantic
  Compaction](../../perception/b-semantic-compaction/)) or live with
  N=2.

## Honest limitations

`branch_agreement_rate` and `effective_n` are useful health signals,
not safety claims. A 5-branch run where all branches confidently agree
on the wrong answer looks healthy by these metrics — that's the
"correlated lucky seeds" failure mode. Aggregation is statistics, not
ground truth. If the task carries real consequences, **add an external
verification step on top of aggregation, not under it.**

The reference uses synchronous sampling for clarity. Production
deployments wrap each branch in its own asyncio coroutine + isolated
LLM client (DeerFlow's pattern) so a slow branch can be cancelled
once the rest have agreed. Without isolation, "independent samples"
quietly become "shared mistakes" via shared buffers and shared
retry state.
