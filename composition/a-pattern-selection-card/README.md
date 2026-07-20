# Pattern Selection Card

> Lecture **41** · composition method · [中文 README](README.zh-CN.md)

## Engineering definition

A **Pattern Selection Card is a versioned architecture decision artifact**. It
binds the problem boundary, smallest baseline, candidate pattern composition,
preconditions, rejected alternatives, pattern seams, and verification plan into
one auditable record.

The card does not auto-select patterns and does not treat a pattern name as
proof. It turns a proposed composition into a falsifiable architecture
hypothesis. A workload-bound comparison decides whether that hypothesis earns
adoption.

Composition sits outside the 28-pattern matrix. The matrix describes the
cognitive-function and execution-topology coordinate of one pattern. The card
governs decisions across coordinates.

## Why hand-picking is insufficient

A pattern catalog compresses experience and helps teams notice missing design
forces. It cannot prove that a composition meets the accuracy, latency, cost,
and risk constraints of one system.

This implementation therefore enforces three disciplines:

1. **Complexity needs a diagnosed failure.** Without an observed baseline
   failure, adding patterns lacks justification.
2. **Pattern preconditions need evidence.** Fan-out and Gather requires
   independent sources. The card must bind source-lineage evidence.
3. **Experiments own the decision.** The candidate must pass on the same
   representative workload as the baseline. If the baseline already passes,
   the additional complexity is rejected.

## Core objects

| Object | Role |
|---|---|
| `ProblemContract` | Bounds the problem, workload, dependency shape, and constraints before naming a pattern |
| `PatternSpec` | States what a pattern solves, its topology, and its preconditions |
| `ArchitectureCandidate` | Composes one or more patterns into a falsifiable candidate |
| `SeamContract` | Defines ownership, versioning, and mutation rules between patterns |
| `ExperimentPlan` | Binds workload, gates, disconfirming signals, and rollback |
| `TrialResult` | Stores measured baseline or candidate evidence |
| `PatternSelectionCard` | Reviews the hypothesis and accepts or rejects it from comparative evidence |

## Run

```bash
python3 composition/a-pattern-selection-card/example.py
uv run pytest -q composition/a-pattern-selection-card/test_pattern.py
```

The complete payroll scenario and Web workbench live in
[`composition/payroll-lab`](../payroll-lab/).
