# Generator-Critic

> Lecture **06-02** · pattern · Reflect × Chain
>
> [中文 README](README.zh-CN.md)

## Contract

Generator-Critic reviews one artifact in one bounded pass:

```text
generate -> critique -> policy gate -> optional revision draft
```

The critic reports evidence; it does not approve the artifact. A deterministic
`AcceptancePolicy` converts grounded issues and an evidence-backed score into
`ACCEPTED` or `NEEDS_REVISION`. An actionable issue needs both a named `check`
(called `source` in the notebook JSON schema) and `evidence`. Unsupported
opinions remain visible in `dropped_issues` but cannot trigger revision.
`Critique` snapshots and reclassifies both incoming issue collections as
immutable tuples, so callers cannot mutate or misbucket findings after the
evidence gate is constructed.

Low scores follow the same rule: when evidence is required, a low score is
actionable only when `Critique.score_evidence` records the rubric or check result
behind it.

Malformed critic output becomes a grounded parser blocker with diagnostic
evidence. It cannot be filtered out or accepted even when `min_score=0.0`.

If a reviser creates a new draft, that draft is explicitly unreviewed.
`ChainResult.reviewed_artifact` identifies what the current pass actually judged;
`ChainResult.revision_draft` must be submitted through `review()` in another
explicit pass before it can be accepted.

This keeps the topology honest. Repeating repair until a test, lint, build, or
CI signal turns green belongs to the sibling
[Self-Heal Loop](../d-self-heal-loop/README.md).

## Quick start

```bash
python3 reflection/a-generator-critic/example.py
python3 reflection/payroll-lab/generator_critic_lab.py
python3 reflection/payroll-lab/generator_critic_lab.py --rubber-stamp

uv run pytest reflection/a-generator-critic/test_pattern.py -q
```

The payroll lab reviews a report that claims 800 paid payslips while SQLite
contains 798 `PAID` and 2 `REVERSED`. The standard critic attaches ledger and
schema evidence, drafts a correction, and accepts it only in an explicit second
pass. The rubber-stamp contrast has no access to those facts and approves the
wrong report.

## Reference interface

| Type | Responsibility |
|---|---|
| `Artifact` | The generated object and its revision metadata. |
| `Issue` | A finding with severity, location, named check, and evidence. |
| `Critique` | Grounded issues, dropped opinions, summary, score, and score evidence. |
| `AcceptancePolicy` | The deterministic evidence and severity gate. |
| `ChainResult` | Separates the reviewed artifact from any unreviewed revision draft. |
| `GeneratorCriticChain` | Runs one pass from a prompt or explicitly reviews an existing artifact. |

## Files

| File | What it demonstrates |
|---|---|
| [`pattern.py`](pattern.py) | Framework-independent reference interface and one-pass boundary. |
| [`shared.py`](shared.py) | Shared JSON parser, policy, deterministic fixtures, reviser, and trace renderer. |
| [`example.py`](example.py) | Two explicit passes over a customer incident update; no API key required. |
| [`test_pattern.py`](test_pattern.py) | Evidence, score, parser, reviewed-version, and optional-dependency invariants. |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | StateGraph nodes and conditional routing for the same contract. |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | LCEL implementation using the same parser, policy, fixtures, and vocabulary. |
| [`../payroll-lab/generator_critic_lab.py`](../payroll-lab/generator_critic_lab.py) | Ledger-backed critique versus a rubber-stamp critic. |

## Notebook verification

Both notebooks run deterministic fake-model scenarios first and call
`get_model()` directly in the optional real-backend section. No separate
fake/real environment flag is required.
`JUPYTER_PATH` pins `python3` to the project venv so a stale user-level
kernelspec cannot select an unrelated interpreter.

```bash
env JUPYTER_PATH="$PWD/.venv/share/jupyter" \
  OPENAI_API_KEY= ANTHROPIC_API_KEY= ERNIE_API_KEY= \
  uv run pytest --nbmake --nbmake-kernel=python3 --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## Matrix position

This pattern sits at **Reflect × Chain**. See the
[two-axis matrix](../../README.md#the-28-pattern-map) for neighboring patterns.
