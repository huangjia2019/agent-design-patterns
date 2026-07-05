# a · Generator-Critic

> Column lecture **06-02** · pattern · Reflect × Chain
>
> [中文 README](README.zh-CN.md)

## The problem

An agent drafts a customer-facing incident update. The prose sounds confident, but
the draft is missing a source for the impact claim. If the same generation step is
also allowed to say "looks good," the harness has no real reflection. It has a
model endorsing its own work.

Generator-Critic separates those jobs. The generator produces an artifact. The
critic produces evidence about that artifact: score, issues, blockers, warnings.
Then a deterministic policy decides whether the artifact can pass. The critic can
inform the gate; it cannot grant approval by vibes.

## The pattern

The topology is a short chain:

```text
generate -> critique -> gate -> optional revision draft
```

The important boundary is the last step. If a reviser drafts a better artifact, the
result is still `NEEDS_REVISION`; this pattern does not automatically accept the
revision without another critique. That keeps Generator-Critic distinct from
Self-Heal Loop, where the critique/revise cycle repeats until a stop condition.

The implementation has three named pieces:

- **Artifact** — the generated object under review.
- **Critique** — score plus concrete issues. It can report blockers and warnings,
  but it has no "approve" method.
- **AcceptancePolicy** — the deterministic gate. Blockers, warnings, and score
  thresholds are evaluated in code.

## Files

| File | What |
|---|---|
| [`pattern.py`](pattern.py) | Framework-agnostic reference: `Artifact`, `Issue`, `Critique`, `AcceptancePolicy`, and `GeneratorCriticChain`. |
| [`shared.py`](shared.py) | Shared parser, policy, mock data, reviser, and trace helpers used by both reference notebooks. |
| [`example.py`](example.py) | Runs an incident-update draft through a mock critic and optional reviser. No API key. |
| [`test_pattern.py`](test_pattern.py) | 8 tests covering score thresholds, blocker/warning gates, trace order, and the no-auto-accept-after-revision invariant. |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | StateGraph implementation: explicit `generate -> critique -> gate -> revise` nodes plus conditional routing. |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | LangChain LCEL implementation: compact runnable pipe with the same shared parser and policy gate. |

## Run

```bash
python reflection/a-generator-critic/example.py
pytest reflection/a-generator-critic/test_pattern.py -v

# reference notebooks — deterministic cells skip live model calls by default
pytest --nbmake --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## Where this pattern sits

Reflect (cognitive function) × Chain (execution topology). Its nearest neighbors
are Self-Heal Loop, which repeats the critique/revise path, and Adversarial Review,
which moves from self-reflection to an independent collaborating reviewer. See the
[two-axis matrix](../../README.md).
