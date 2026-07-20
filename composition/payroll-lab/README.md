# Composition Selection Workbench

This lab supports lectures 41 through 43. It asks a concrete architecture question:
does hand-picking patterns from a catalog produce a useful system?

Pattern names can generate better architecture hypotheses. They do not validate
those hypotheses. The workbench therefore compares every proposal against the
smallest baseline on the same bound workload.

Lecture 41 runs the repository's real `Fan-out and Gather` and
`Iterative Hypothesis` implementations:

| Scenario | Data relationship | Baseline failure | Candidate |
|---|---|---|---|
| Independent ledgers | separately owned snapshots | one source cannot reveal disagreement | Fan-out and Gather |
| Shared carryover | every ledger depends on one prior checkpoint | parallel comparison creates false consensus | Iterative Hypothesis |

Lecture 42 runs the real `Plan and Execute` and `Handoff Chain`
implementations. It rejects a shared `net_amount` writer before trial, then
compares a mutable baseline, two candidates, and two removal ablations.

Lecture 43 assembles eight real module interfaces around one month-end run. Both
variants produce eight locally accepted receipts. The local-only wiring fails
system acceptance because lineage and artifact identity break at the seams. The
bound wiring reaches a SQLite endpoint that carries the exact reviewed and
approved report digest.

## CLI

```bash
python3 composition/payroll-lab/selection_card_lab.py
python3 composition/payroll-lab/six_step_lab.py
python3 composition/payroll-lab/capstone_lab.py --mode local-only
python3 composition/payroll-lab/capstone_lab.py --mode bound
```

## Web workbench

```bash
uv sync --extra ui
uv run uvicorn web_app:app --app-dir composition/payroll-lab --port 8041
```

Open:

- Lecture 41: `http://127.0.0.1:8041`
- Lecture 42: `http://127.0.0.1:8041/42`
- Lecture 43: `http://127.0.0.1:8041/43`
