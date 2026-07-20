# Six-Step Methodology

> Composition module · evidence-driven architecture convergence
> [中文 README](README.zh-CN.md)

## Engineering definition

The **Six-Step Methodology** is an ordered, evidence-bound, reopenable process
for converging on an architecture. It starts with one bounded decision and the
smallest viable baseline, diagnoses the observed constraints, generates a small
candidate set, reviews pattern seams, and then uses same-workload comparisons
and ablations to adopt, reject, or keep the baseline.

The implementation does not map a business description to a supposedly correct
pattern bundle. The catalog generates candidates. Workload evidence judges them.

## The six steps

1. **Bound** the decision, representative workload, output, constraints, and
   excluded scope.
2. **Baseline** the smallest viable implementation and record its real failure.
3. **Diagnose** each binding constraint with a failed gate and evidence.
4. **Generate candidates** that target those observed diagnoses.
5. **Specify seams and trials**, including ownership, mutation, versioning, and
   one removal ablation per pattern.
6. **Decide and reopen** with a versioned receipt and explicit invalidation
   triggers.

## Key behavior

`SixStepSession` enforces evidence order. `SeamContract` defines the owner and
mutation policy for every cross-pattern artifact. `ExperimentCase` requires the
full bundle and, for a multi-pattern candidate, one ablation per pattern.

A candidate earns adoption only when the baseline fails, the full candidate
passes, and its removals expose a real loss. If several candidates pass, the
method returns `NEEDS_REVIEW` rather than hiding a cost-risk decision inside an
automatic score.

## Run

```bash
uv run python composition/b-six-step-methodology/example.py
uv run pytest composition/b-six-step-methodology -q
uv run python composition/payroll-lab/six_step_lab.py
```

Web workbench:

```bash
uv sync --extra ui
uv run uvicorn web_app:app \
  --app-dir composition/payroll-lab \
  --port 8041
```

Open `http://127.0.0.1:8041/42`.

## Boundary

This reference validates decision artifacts inside one process. It does not
replace production traffic replay, real external side effects, cross-service
signatures, cost attribution, or long-term drift monitoring. A decision receipt
is scoped evidence, not a claim that the architecture is permanently correct.
