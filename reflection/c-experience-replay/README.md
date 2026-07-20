# Experience Replay

> Lecture **06-04** · pattern · Reflect × Hierarchy
> [中文 README](README.zh-CN.md)

## Status

pattern.py landed (with lecture 29 / 06-04 of the 极客时间《Agent 设计模式之美》
column). The claim: **a lesson stays in the replay pool only as long as
reuse keeps proving it useful** — "the agent finds it useful" and
"downstream tasks succeed after it is injected" are different things,
and only the second is a signal. Experiences are layered (L0 raw traces
for audit / L1 per-task lessons for injection / L2 cross-task
heuristics); retrieval renders the hits into an upper context layer
the current decision runs under. Every reuse writes the downstream
outcome back (EMA); lessons reused enough that still sit below the
health line are archived out of the pool. Deterministically checkable
lessons explicitly marked as deterministically checkable and backed by
a proven track record graduate into pre-action guards
(lecture 25), and the soft lesson retires.

## Quick start

```bash
cd ../payroll-lab
python3 experience_replay_lab.py                # scene 1: recall changes the decision; scene 2: one signal archives the superstition and graduates the real lesson
python3 experience_replay_lab.py --no-feedback  # scene 3: no outcomes written back — the mis-attributed lesson is still in context in month 7
```

## Where this pattern sits

This pattern sits at the intersection of **Reflect** (cognitive function)
and **Hierarchy** (execution topology). See the
[two-axis matrix](../../README.md#the-28-pattern-map) for how it relates
to neighboring patterns.

## What this pattern covers

The pattern's working title is **Experience Replay** (Chinese: 经验回放).
Detailed treatment in the Manning book *Designing AI Agents* (Ch06)
and in the column.
