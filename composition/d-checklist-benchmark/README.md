# Checklist Benchmark Case

> Lecture **09 Composition** companion case · Composition × mixed topologies
> [中文 README](README.zh-CN.md)

## What this is

An anonymized financial product-disclosure checklist benchmark. A strong assistant plus human review creates 12 Golden Rules. Several ordinary-model extraction strategies are then compared against the same schema and gold set.

## Why this case matters

The point is not that a model can extract rules. The point is that pattern composition turns a one-shot extraction task into a measurable, replayable, human-reviewable workflow.

| Strategy | Two-axis map | Match |
|---|---|---:|
| `single_pass` | Reasoning × Chain | 6 / 12 |
| `critique_repair` | Reflection × Chain | 7 / 12 |
| `iterative_self_refine` | Reflection × Loop | 7 / 12 |
| `candidate_guided_review` | Governance × Route | 9 / 12 |
| `coverage_preserving_union_queue` | Composite: Parallel -> Route | 10 / 12 |
| `orchestrated_consensus_refine` | Composite: Parallel -> Route -> Loop | 8 / 12 |

The design lesson: one-shot extraction recovers 6 of 12 rules. A candidate-guided review path reaches 9 of 12. A coverage-preserving union queue reaches 10 of 12 by keeping complementary candidate rules for human review. Compressing too early loses coverage.

## Files

| File | Purpose |
|---|---|
| `case-study.zh-CN.md` | Case narrative: 4 benchmark rounds + Pattern Selection Card walkthrough + 3 takeaways (Chinese) |
| `anonymized_case.json` | Static anonymized case data |
| `checklist_benchmark.ipynb` | Executed notebook showing the same benchmark table |

## Use

This is a document package, not a runnable pattern package. Read `case-study.zh-CN.md` first, then open `checklist_benchmark.ipynb` for the saved benchmark table.

## Engineering slice

This case aligns with current production-agent practice:

* Anthropic's *Building Effective Agents* recommends simple, composable workflows before adding more autonomy.
* OpenAI Agents SDK tracing and trace grading make agent runs inspectable and evaluable.
* LangGraph durable execution and human-in-the-loop support show why intermediate state must be preserved when humans approve or edit outputs.

The shared principle: a production agent is not a single answer. It is an auditable path.
