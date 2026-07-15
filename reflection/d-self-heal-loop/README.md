# Self Heal Loop

> Lecture **06-05** · pattern · Reflect × Loop
> [中文 README](README.zh-CN.md)

## Status

pattern.py landed (with lecture 30 / 06-05 of the 极客时间《Agent 设计模式之美》
column — the Reflection module finale). The claim: **a self-heal loop
is only as safe as its stopping machinery.** The loop itself is trivial
(red signal, diagnose, patch, re-run); what separates a production
healer from a main-branch incident is the triple stop: a hard round
budget (Aider's 3), an independent critic gate on every patch before
apply (which specifically blocks patches that weaken the tests instead
of fixing the code), and a regression check on failure signatures +
blast radius that rolls the whole commit stack back when "fixing" makes
things worse. The trigger is a deterministic test/lint/build/CI signal,
never the model's opinion of its own output. Exhausted rounds hand off
to a human with the full trace. A failure class healed repeatedly
graduates via `propose_guard` into a regression-test guard (lecture 25):
healing rescues this month, the guard blocks next month.

## Quick start

```bash
cd ../payroll-lab
python3 self_heal_lab.py             # scene 1: two real defects, two rounds, green + guard proposal; scene 2: cheating patch blocked
python3 self_heal_lab.py --meltdown  # scene 3: the naive loop re-enacts the incident vs. the triple stop rolling everything back
```

## Where this pattern sits

This pattern sits at the intersection of **Reflect** (cognitive function)
and **Loop** (execution topology). See the
[two-axis matrix](../../README.md#the-28-pattern-map) for how it relates
to neighboring patterns.

## What this pattern covers

The pattern's working title is **Self-Heal Loop** (Chinese: 自愈循环).
Detailed treatment in the Manning book *Designing AI Agents* (Ch06)
and in the column.
