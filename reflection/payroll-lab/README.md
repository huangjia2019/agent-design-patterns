# Payroll Lab · Reflection Module (Lectures 26—30)

[简体中文](README.zh-CN.md)

This directory reuses the SQLite payroll database from
[`../../action/payroll-lab/`](../../action/payroll-lab/) and rebuilds one
deterministic month-end scene: 798 payslips are `PAID`, while E0007 and E0012
are `REVERSED`. The agent's report incorrectly claims 800 paid and zero
reversed.

The state is a teaching fixture rebuilt by `bench.py`; it is not presented as
the naturally accumulated final state of the Action module's isolated labs.

## Web teaching console

From the repository root:

```bash
uv sync --extra ui
uv run --extra ui python reflection/payroll-lab/web_app.py
```

Open `http://127.0.0.1:8766`. The console can run all five lectures, show the
evidence timeline, inspect SQLite, rebuild the month-end state, and trigger one
contrast variant per pattern. Runs are serialized because the teaching labs
share one local database.

## Unified CLI

```bash
python3 reflection/payroll-lab/run_reflection_module.py --lecture 27
python3 reflection/payroll-lab/run_reflection_module.py --lecture 27 --variant
python3 reflection/payroll-lab/run_reflection_module.py --lecture all
```

| Lecture | Standard run | `--variant` contrast |
|:--|:--|:--|
| 26 Introduction | Introspection vs. SQL reconciliation | Stricter self-score, same blind spot |
| 27 Generator-Critic | One pass drafts; explicit second pass reviews | Rubber-stamp critic accepts the wrong report |
| 28 Skill Package | Verify, promote, then route | Skip the verification gate |
| 29 Experience Replay | Recall, feedback, archive, graduate | Disconnect downstream feedback |
| 30 Self-Heal Loop | Repair to green; block a cheating patch | Controlled runaway-loop re-enactment and rollback |

Direct lab commands remain available for teaching and debugging:

```bash
python3 reflection/payroll-lab/self_grade_lab.py
python3 reflection/payroll-lab/generator_critic_lab.py
python3 reflection/payroll-lab/skill_package_lab.py
python3 reflection/payroll-lab/experience_replay_lab.py
python3 reflection/payroll-lab/self_heal_lab.py
```

## Design boundary

The shared Runner only dispatches allow-listed commands. FastAPI serializes
runs and returns structured evidence. Each pattern keeps its own native state
machine and tests. In particular, lecture 27 never hides a retry loop inside
Generator-Critic; lecture 30 owns mandatory repetition, stop policies, and
rollback.

## Verification

```bash
uv run pytest reflection/a-generator-critic/test_pattern.py \
  reflection/d-self-heal-loop/test_pattern.py \
  reflection/payroll-lab/test_ui_service.py -q
```
