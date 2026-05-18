# d · Iterative Hypothesis Testing

> Column lecture **04-05** · pattern · reason × loop
>
> [中文 README](README.zh-CN.md)

## The problem

03:47 AM. A polyethylene reactor at a mid-size chemical plant alarms:
temperature has climbed from 80°C (normal) to 92°C. The on-call agent
pushes a hypothesis list to the operator on shift, sorted by prior:

```
H1  78%   cooling-water pump failure
H2  12%   temperature sensor drift
H3   5%   feedstock recipe anomaly
H4   3%   catalyst activity spike
H5   2%   PID parameters tampered with
```

The operator checks cooling-water flow — normal. **H1 out.** Then the
redundant sensor — also reads 92°C. **H2 out.** Then the feedstock log
— within spec. **H3 out.** H4 needs a 30-minute lab run; the line has
been down for an hour already, and the CFO has posted "this line
loses ¥450k per hour stopped" in the group chat.

Then the operator flags something he just noticed: **"there's a remote
login at 02:33 modifying the PID logs."** He gives the agent that one
new fact. The agent does **not** try to fit the fact into the existing
hypothesis ranking. It resets:

```
new hypothesis tree (after fresh evidence at 02:33):
  H5' (95%): PID parameters tampered with at 02:33
    └─ drill: query the diff at 02:33
       └─ found: P-parameter changed from 0.8 to 2.5
          └─ confirms: that change overshoots, climbing temperature
            ✅ matches observed behavior
```

P was reverted at 04:51. Temperature back to normal at 05:14. Total
downtime: 87 minutes. The takeaway the on-call team wrote up
afterward had two parts:

1. **The initial 2% prior on H5 was just wrong.** The Planner needs
   to enumerate causally distinct alternatives, not just statistically
   probable ones.
2. **New evidence resets, doesn't refine.** When a piece of evidence
   reorders the hypothesis space, you re-propose, not edit. This
   matches Anthropic's 2026 three-agent harness research — they call
   it "context reset, not compaction."

## The pattern

Three classes, mirroring the three roles:

| Class | Role | Production tier |
|---|---|---|
| `Hypothesis` | One candidate with prior, posterior, status, accumulated evidence | data only |
| `HypothesisTree` | Working set across iterations; survivor count is the Popperian quantity | data only |
| `IterativeHypothesisLoop` | Runs Planner → Generator → Evaluator until convergence or cap | Anthropic 3-agent harness |

The loop's exit condition is **Popperian**: not "we found something
that fits" but "all strong alternatives have been falsified." That
reframe is the single most consequential design choice in the pattern.
The Evaluator's system prompt should literally read *"your job is to
falsify, not confirm."*

Convergence cases:

1. **Single confirmed survivor.** The textbook win. Loop exits.
2. **All falsified mid-loop.** Planner is invited next iteration to
   propose fresh hypotheses (the context-reset case).
3. **Cap reached, one survivor left.** No HITL — the survivor is the
   working answer with whatever confidence the evidence built.
4. **Cap reached, multiple survivors.** HITL. Hand off to a human
   with the full tree; do not majority-vote into a guess.

Five evidence effects:

* `supports` with delta — moves posterior up; ≥0.9 confirms.
* `refutes` with delta — moves posterior to 0; status flips to
  `FALSIFIED` immediately, regardless of magnitude. (Popperian
  asymmetry: one strong refutation kills a hypothesis; one piece of
  support doesn't confirm it.)
* `neutral` — no change. The Evaluator logs it for audit.

Hard caps:

* `max_iterations` default = 5. The Anthropic harness uses 5–10. Above
  10, you're not running an inference loop, you're losing your
  budget.
* The Generator pulls evidence per hypothesis per iteration. With
  three roles wired to Opus/Sonnet/Haiku the cost scales as
  `n_hypotheses × iterations × (~tier_cost)` — manageable.

## Quickstart

```bash
python reasoning/d-iterative-hypothesis/example.py
pytest reasoning/d-iterative-hypothesis/
```

The demo runs the chemical-plant incident end-to-end. Iteration 1
proposes the four sensor-team starting hypotheses and falsifies all
of them. Iteration 2 lets the planner propose the recovery
hypothesis (the operator's mid-flight fact); the evidence confirms
it; loop exits.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `Hypothesis` + `HypothesisStatus` + `Evidence` + `HypothesisTree` + `IterativeHypothesisLoop` (~210 lines) |
| `example.py` | Reactor temperature incident, six-hypothesis fan, mid-loop context reset |
| `test_pattern.py` | 13 invariants: evidence-driven status transitions, posterior clamping, tree dedup, survivor count, four loop outcome cases (converge, context-reset, HITL, single-survivor at cap), max_iterations guard, iteration recording |

## Engineering references (verified)

* **Anthropic (2026)** [*How we built our multi-agent research
  system*](https://www.anthropic.com/research/multi-agent-research) —
  the three-agent harness (Planner / Generator / Evaluator) and the
  "context reset, not compaction" rule. This pattern is a single-
  process port of that architecture.
* **Aider** `aider/coders/base_coder.py` — `max_reflections=3` is the
  same family of pattern in its smallest honest form (Self-Refine
  variety). Works for deterministic failures (lint, test) but doesn't
  generalize to fuzzy diagnostics — the reason this richer pattern
  exists.
* **Yao et al. (2022)** [*ReAct*](https://arxiv.org/abs/2210.03629) —
  the Reason → Act → Observe loop. Most flexible, most expensive in
  tokens. The "Generator + Evaluator" half of this pattern is what
  ReAct is when you split the responsibilities.
* **Xu et al. (2023)** [*ReWOO*](https://arxiv.org/abs/2305.18323) —
  plan first, run tools in parallel, synthesize at end. ~5× more
  token-efficient than ReAct but rigid. Use for tasks where the plan
  is unlikely to need mid-flight repair.
* **Madaan et al. (2023)** [*Self-Refine*](https://arxiv.org/abs/2303.17651)
  — generate, self-critique, refine, repeat. Doesn't fit incident
  diagnosis (no external evidence loop) but fits writing / code /
  summarization.
* **Karl Popper** *The Logic of Scientific Discovery* (1959) — the
  philosophical anchor: **a theory cannot be confirmed, only
  falsified.** The exit condition for the loop is a direct port.

## When this pattern doesn't apply

* **Single-pass tasks.** "What's today's date" doesn't need a hypothesis
  tree. The plumbing is overhead.
* **Closed-form answers (math, classification).** Use
  [Parallel Exploration](../c-parallel-exploration/) for the
  lucky-seed problem there. Iterative is for *open-set diagnosis*.
* **No tool floor.** The Generator needs real evidence — telemetry,
  logs, sensors, ground-truth tests. Without it the loop just
  hallucinates with extra steps.

## Honest limitations

The Planner's biggest failure mode is **prior bias**. The lecture-
opening incident shows it: H5 had a 2% prior because nobody had
recently tampered with PID logs, so the agent ranked it accordingly.
Production deployments need a way to inject *causally* distinct
hypotheses (not just statistically probable ones) — usually via a
fixed prior list per incident class, or via a "long-tail seed" prompt
that asks the Planner for at least one low-probability alternative.

The 90% confirmation threshold in `record_evidence` is a tunable
default. High-stakes contexts (medical / safety / fraud) should raise
it. Low-stakes contexts can lower it. **The threshold is product
economics, not arithmetic.**

The HITL handoff is meaningful only if there's a human to hand off
to. For unattended automation, the loop should down-grade gracefully:
take the highest-posterior survivor as a provisional answer, log the
multi-survivor state, and escalate asynchronously. Don't pretend you
converged when you didn't.
