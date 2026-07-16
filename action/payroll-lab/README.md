# Payroll Action Stress Workbench (`payroll-lab`)

[简体中文](README.zh-CN.md)

This is the hands-on workbench for lectures 21 through 25 of the Action module. It uses a local payroll system with a single SQLite database, 800 employees, one month of draft payslips, and two approved changes waiting to be applied. The data is synthetic, while the schema, state mutations, and payment ledger are directly inspectable.

The workbench needs no API key or cloud service. Deterministic attack fixtures make bad proposals reproducible, and the defended runs call the repository's real `pattern.py` APIs. Verdicts are derived from state diffs, action counts, and pattern traces rather than a model's claim of success.

## One workbench, three pressure layers

The browser and CLI use the same Stress Runners:

| Layer | Code | Question |
|:--|:--|:--|
| L0-L2 shared-stimulus ablation | `stress_ablation.py`, `stress_web_run.py` | What do Minimal Tool Set and Tool Dispatch stop independently? |
| V3-V5 before/after comparisons | `stress_vectors.py` | Does Plan-and-Execute, Prompt Chaining, or Guardrail Sandwich protect its own boundary? |
| S1-S4 production pressure | `stress_gaps.py` | What breaks under concurrency, TOCTOU, restart, and compensation failure? |

`stress_full.py` gathers the executed evidence for five failure vectors across six cumulative configurations. The matrix is a shared evaluation protocol. It does not claim that all five patterns already run inside one production transaction.

## Start the Web workbench

From the repository root:

```bash
uv sync --extra ui
uv run --extra ui python action/payroll-lab/web_app.py
```

Open `http://127.0.0.1:8765`. The console has three views:

- **Experiment** runs L0-L2, V3-V5, S1-S4, and the full matrix by lecture.
- **Database** inspects employees, payslips, approvals, policies, and baseline differences.
- **System structure** shows the controlled entry point, Stress Runners, evidence layer, and current integration boundary.

FastAPI accepts only allow-listed levels, vectors, and fixed experiments. It exposes no arbitrary shell or SQL endpoint. L0-L2 restore the baseline before writing, and V3-V5 reset the main database for a neutral display. S1-S4 and the matrix use separate evidence and do not mutate `payroll.db`.

## Reproduce from the CLI

```bash
uv run python action/payroll-lab/stress_ablation.py --walk L0
uv run python action/payroll-lab/stress_vectors.py --vector V3
uv run python action/payroll-lab/stress_vectors.py --vector V4
uv run python action/payroll-lab/stress_vectors.py --vector V5
uv run python action/payroll-lab/stress_gaps.py
uv run python action/payroll-lab/stress_full.py
```

L0-L2 share one north-star goal and one external note. The fixture extracts proposals from the note's content and has no knowledge of the installed defenses. Removing terms such as "retry payment" or "separator" removes the corresponding proposal. This tests containment after a bad proposal reaches the runtime. It does not estimate how often a live model follows a prompt injection.

V3-V5 use pressure matched to each boundary:

| Vector | Pressure | Pattern implementation | Primary evidence |
|:--|:--|:--|:--|
| V3-mid-run timeout followed by a full restart | A recovery note requests a full restart after a middle step times out | `b-plan-and-execute/pattern.py` | Per-employee payment counts and local replanning |
| V4-poisoned artifact propagation | A reconciliation artifact carries an abnormal total | `c-prompt-chaining/pattern.py` | External-ledger gate and chain status |
| V5-high-risk I/O | An abnormal amount reaches tool input and a full account number reaches an outbound result | `d-guardrail-sandwich/pattern.py` | PRE/POST outcomes and actual execution count |

## Code map

- `db.py`: builds `payroll.db` and its baseline snapshot, reports row-level diffs, and offers an optional `999999` data-fault injection.
- `stress_ablation.py`: L0-L2 shared-stimulus ablation on an in-memory ledger.
- `stress_web_run.py`: writes L0-L2 effects to SQLite and records payment calls.
- `stress_vectors.py`: V3-V5 before/after pattern comparisons.
- `stress_gaps.py`: S1-S4 production pressure.
- `stress_full.py`: five-vector by six-configuration matrix.
- `action_trace.py`: shared `ActionEvent` and `ActionTrace` observability skeleton.
- `ui_service.py`, `web_app.py`: controlled command service and FastAPI allow-list.
- `ui/`: browser interface with no build step.
- `test_stress_lab.py`, `test_ui_service.py`: causal-result, structured-evidence, and single-engine boundary tests.

## Current boundary

The repository has one teaching entry point and one evaluation protocol. L0-L2 write to the real `payroll.db`; V3-V5 are deterministic slices that call the native pattern APIs; S1-S4 expose gaps between the teaching implementation and production conditions.

Minimal Tool Set, Tool Dispatch, Plan-and-Execute, Prompt Chaining, and Guardrail Sandwich do not yet share one transaction or one persisted Plan, Artifact, Approval, Checkpoint, and ActionEvent stream. Production work still includes cross-process idempotency, entity versions, durable quotas and Saga state, a compensation-debt queue, and external settlement receipts.

## Verification

```bash
uv run pytest -q action/payroll-lab/test_stress_lab.py action/payroll-lab/test_ui_service.py
uvx ruff check action/payroll-lab
```
