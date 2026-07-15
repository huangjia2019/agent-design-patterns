# a · Generator-Critic

> Column lecture **06-02** · pattern · Reflect × Chain
>
> [中文 README](README.zh-CN.md)

## The problem

An agent drafts a customer-facing incident update, or a month-end payroll report.
The prose sounds confident, but the important claims need external signals:
status-page incidents, schemas, SQL reconciliation, tests, or policy clauses. If
the same generation step is also allowed to say "looks good," the harness has no
real reflection. It has a model endorsing its own work.

Generator-Critic separates those jobs. The generator produces an artifact. The
critic produces evidence about that artifact: score, issues, blockers, warnings.
Then a deterministic policy decides whether the artifact can pass. The critic can
inform the gate; it cannot grant approval by vibes.

An actionable issue must name its `source` and carry `evidence`. Opinions without
evidence are retained in `dropped_issues` for audit, but they cannot trigger a
revision.

## The pattern

The topology is a short chain:

```text
generate -> critique -> gate -> optional revision draft
```

The important boundary is the last step. If a reviser drafts a better artifact, the
result is still `NEEDS_REVISION`; this pattern does not automatically accept the
revision without another critique. That keeps Generator-Critic distinct from
Self-Heal Loop, where the critique/revise cycle repeats until a stop condition.

The implementation has four named pieces:

- **Artifact** — the generated object under review.
- **Issue** — one finding with severity, message, location, named source, and
  evidence.
- **Critique** — score plus evidence-backed issues and dropped unevidenced
  opinions. It can report blockers and warnings, but it has no "approve" method.
- **AcceptancePolicy** — the deterministic gate. Blockers, warnings, and score
  thresholds are evaluated in code.

## Files

| File | What |
|---|---|
| [`pattern.py`](pattern.py) | Framework-agnostic reference: `Artifact`, `Issue`, `Critique`, `AcceptancePolicy`, and one-pass `GeneratorCriticChain`. |
| [`shared.py`](shared.py) | Shared parser, policy, mock data, reviser, and trace helpers used by both reference notebooks. |
| [`example.py`](example.py) | Runs an incident-update draft through a mock critic and optional reviser. No API key. |
| [`test_pattern.py`](test_pattern.py) | Tests covering score thresholds, evidence gate, blocker/warning gates, strict parser failure, trace order, and the no-auto-accept-after-revision invariant. |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | StateGraph implementation: explicit `generate -> critique -> gate -> revise` nodes plus conditional routing. |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | LangChain LCEL implementation: compact runnable pipe with the same shared parser and policy gate. |
| [`../payroll-lab/generator_critic_lab.py`](../payroll-lab/generator_critic_lab.py) | Lecture 27 Payroll Lab: wired external checks, rubber-stamp critic, and pass-budget exhaustion. Repeated passes are explicit runner behavior. |

## Run

```bash
python reflection/a-generator-critic/example.py
pytest reflection/a-generator-critic/test_pattern.py -v

# Payroll Lab scenes — no API key needed
python reflection/payroll-lab/generator_critic_lab.py
python reflection/payroll-lab/generator_critic_lab.py --stubborn

# reference notebooks — deterministic verification should run with provider API keys unset
pytest --nbmake --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## Where this pattern sits

Reflect (cognitive function) × Chain (execution topology). Its nearest neighbors
are Self-Heal Loop, which repeats the critique/revise path, and Adversarial Review,
which moves from self-reflection to an independent collaborating reviewer. See the
[two-axis matrix](../../README.md).
