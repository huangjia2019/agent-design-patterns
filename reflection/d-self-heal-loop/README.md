# Self-Heal Loop

Self-Heal Loop is a bounded repair transaction:

`diagnose -> fix -> review -> atomic apply -> verify -> compensate`

Generator-Critic evaluates a proposal once. Self-Heal starts from a deterministic
failure and may repeat repair, but only inside an explicit stability budget.

## Contract and safety proof

`Patch.digest` binds canonical touched paths to executable `payload`, never its
description. Every diagnose, fix, review, and verify call is bracketed by an
observational state digest. Atomic applies return a receipt; every non-success
path compensates addressable applies in reverse order and reads a final digest.
The trace only claims restoration when bound rollback receipts and final state
prove it. A missing proof or failed rollback truthfully becomes human handoff.

| Public item | Contract |
| --- | --- |
| `HealStatus` | `FIXED`, `BLOCKED_BY_CRITIC`, `ROLLED_BACK_REGRESSION`, `ROLLED_BACK_NO_PROGRESS`, `MAX_ROUNDS_HUMAN_HANDOFF`, `STAGE_ERROR_HUMAN_HANDOFF`, `ROLLBACK_FAILED_HUMAN_HANDOFF` |
| Receipts | `PatchReview`, `ApplyReceipt`, `VerificationReceipt`, `RollbackReceipt` |
| Trace records | `StageError`, `HealRound`, `HealTrace` |
| callbacks | `DiagnoseFn(FailureSignal)`, `FixFn(str)`, `ReviewFn(Patch, FailureSignal)`, `ApplyFn(Patch)`, `VerifyFn(ApplyReceipt)`, `RollbackFn(ApplyReceipt)`, `StateDigestFn()` |

The core permits a test-file patch after a bound review. The deterministic
example and payroll adapter reject it because reconciliation tests are an
application-owned safety policy.

## Files

- `pattern.py`: framework-neutral contract and transaction engine
- `test_pattern.py`, `test_transaction_contract.py`: behavioral and adversarial proof
- `example.py`: small deterministic source-only example
- `../payroll-lab/self_heal_lab.py`: snapshot-backed teaching scenarios

## Reference implementation

[`shared.py`](shared.py),
[`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb), and
[`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) provide the shared
deterministic fixtures and two framework views of this contract. Both notebooks
use the hardened receipt/digest contract and execute the same seven scenarios:
`convergence`, `critic_block`, `no_progress`, `regression`, `round_budget`,
`stage_error`, and `rollback_failure`.

## Notebook verification

`JUPYTER_PATH` pins `python3` to the project venv so a stale user-level
kernelspec cannot select an unrelated interpreter.

```bash
env JUPYTER_PATH="$PWD/.venv/share/jupyter" \
  MODEL_PROVIDER=ernie MODEL_NAME=ernie-5.1 \
  OPENAI_API_KEY= ANTHROPIC_API_KEY= ERNIE_API_KEY= \
  uv run pytest --nbmake --nbmake-kernel=python3 --nbmake-timeout=120 \
  reflection/d-self-heal-loop/langgraph/tutorial.ipynb \
  reflection/d-self-heal-loop/langchain/tutorial.ipynb
```

## Run and verify

```bash
uv run pytest reflection/d-self-heal-loop -q
uv run python reflection/d-self-heal-loop/example.py
uv run pytest reflection/payroll-lab/test_self_heal_lab.py reflection/payroll-lab/test_ui_service.py -q
uv run python reflection/payroll-lab/self_heal_lab.py
uv run python reflection/payroll-lab/self_heal_lab.py --meltdown
```
