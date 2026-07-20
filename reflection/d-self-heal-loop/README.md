# Self-Heal Loop

> Lecture **06-05** · pattern · Reflect × Loop
> [中文 README](README.zh-CN.md)

## Contract

Self-Heal Loop is a rollback-safe repair transaction driven by a deterministic
red signal:

```text
diagnose -> draft patch -> critic -> atomic apply -> verify -> repeat/stop
```

Repetition is structural here. The loop exits only when verification turns
green or one of three stop lines takes control:

1. The hard round budget is exhausted.
2. The patch critic blocks an unsafe change before apply.
3. Stability checks detect a regression or repeated no-progress attempt.

Each applied patch receives an atomic commit id. Every non-success terminal path
rolls the entire stack back in reverse order before handing the trace to a
human. A patch that weakens a test is blocked by policy rather than celebrated
as a green build.

## Quick start

```bash
python3 reflection/payroll-lab/self_heal_lab.py
python3 reflection/payroll-lab/self_heal_lab.py --meltdown
```

The default run repairs two payroll defects and then blocks a test-cheating
patch. `--meltdown` is a controlled incident re-enactment: it contrasts nine
overlapping edits in a naive retry loop with a bounded transaction that detects
expanding blast radius and restores the baseline.

## Reference interface

[`pattern.py`](pattern.py) makes the safety properties queryable:

- `FailureSignal.signature` identifies a stable failure class.
- `Patch.fingerprint` detects repeated no-progress attempts.
- `HealStatus` names every success and stop path.
- `HealTrace.baseline_restored` proves whether the baseline is intact.
- `propose_guard` lets a recurring failure graduate into a reviewed regression
  guard.

Run the invariant tests with:

```bash
uv run pytest reflection/d-self-heal-loop/test_pattern.py -q
```

## Matrix position

This pattern sits at **Reflect × Loop**. See the
[two-axis matrix](../../README.md#the-28-pattern-map) for neighboring patterns.
