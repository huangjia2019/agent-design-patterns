# Skill Package

> Lecture **06-03** · pattern · Reflect × Route
> [中文 README](README.zh-CN.md)

## Status

pattern.py landed (with lecture 28 / 06-03 of the 极客时间《Agent 设计模式之美》
column). The claim: **a skill enters the library only after it passes
external verification, and the router only ever routes to VERIFIED
skills.** Every skill enters as TRIAL — human-written or distilled — and
is promoted only when a set of golden questions (deterministic
input → expected-output checks) all pass. Post-reuse success rates feed
back: a verified skill that starts failing is demoted to TRIAL and must
re-verify, which is the staleness guard. Distillation thresholds follow
Hermes (enough distinct tool calls to be worth freezing); distillation
earns storage, never trust.

## Quick start

```bash
cd ../payroll-lab
python3 skill_package_lab.py             # scene 1: the gate catches the old policy year; scene 2: the router only sees VERIFIED
python3 skill_package_lab.py --no-gate   # scene 3: stored as trusted without the gate — 209 of 800 bases computed wrong
```

## Where this pattern sits

This pattern sits at the intersection of **Reflect** (cognitive function)
and **Route** (execution topology). See the
[two-axis matrix](../../README.md#the-28-pattern-map) for how it relates
to neighboring patterns.

## What this pattern covers

The pattern's working title is **Skill Package** (Chinese: 技能包).
Detailed treatment in the Manning book *Designing AI Agents* (Ch06)
and in the column.
