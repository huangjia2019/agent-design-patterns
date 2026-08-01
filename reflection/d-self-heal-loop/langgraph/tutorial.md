# Self-Heal Loop with LangGraph

> A repair loop is safe only when every attempt is bounded, receipt-bound, and compensated before a non-success result escapes.


## What this pattern does

Self-Heal starts with a known failure, proposes one patch at a time, reviews it, applies it, and verifies the changed workspace. A passing verification commits the repaired state. Every other terminal path compensates newest-first and reports whether the original baseline was restored.

### Learning goals

By the end, you will be able to read a repair workflow as ordinary Python functions connected by deterministic control flow, identify which decisions belong to models and which belong to deterministic code, and follow the receipts that make rollback provable.

### Who owns each decision?

| Decision | Owner | Why |
|---|---|---|
| Diagnose a failure | Replaceable Python function, optionally model-backed | This is an interpretive task. |
| Draft a patch | Replaceable Python function, optionally model-backed | This is a generative task. |
| Review, apply, and verify | Deterministic Python functions | Safety policy and workspace evidence must not depend on model judgment. |
| Retry, stop, or roll back | Deterministic Python control flow | Bounds and compensation are transaction rules. |
| Declare the final status | Deterministic result-building step | The result must follow from receipts and digests. |

### Five safety invariants

1. Every run captures its own baseline before any repair role runs.
2. Diagnose, draft, review, and verify are observationally pure: they may not mutate managed state.
3. The same `(failure.signature, patch.digest)` pair is never applied twice.
4. Apply, verification, and rollback evidence must bind to the patch or commit it describes.
5. A non-success result proves restoration or becomes human handoff.

### Two paths to keep in mind

A successful run can take more than one round:

```text
success:
failure₁ -> patch₁/c1 -> verify failure₂ -> patch₂/c2 -> verify success
```

A later regression compensates in reverse apply order:

```text
compensation:
c1 -> c2 -> regression -> rollback c2 -> rollback c1 -> baseline restored
```


## LangGraph from basic Python

LangGraph does not replace Python functions. It gives those functions a shared state dictionary and a visible map of what may run next.

- A **graph** is a workflow.
- **State** is the dictionary carried between steps.
- A **node** is a Python function that reads state and returns a state update.
- An **edge** chooses which node runs next.
- A **conditional edge** chooses among named routes using current state.
- `START` and `END` are the workflow's entry and exit markers.
- `StateGraph(GraphState)` checks the expected shape of state for readers and tools.

If you know a loop containing `if` statements, you already know the basic control flow. Here, each stage is a function, each returned dictionary updates only the keys that changed, and a routing function returns a short route name such as `"verify"` or `"rollback"`. The graph builder connects that name to the next Python function.

### Compare the two implementations

The sibling notebook uses LangChain. There, a **runnable** is an object called with `.invoke(input)`, and **LCEL** is LangChain's syntax for composing runnables. With the vocabulary on both sides now defined, the implementations compare like this:

| | `langgraph/` (`StateGraph`) | [`langchain/`](../langchain/tutorial.ipynb) (LCEL) |
|---|---|---|
| Repair stages | Explicit nodes and conditional edges | Runnables around an explicit loop driver |
| Deterministic roles | Plain Python callables | Python callables adapted as runnables |
| Business bound | A maximum-round rule represented in graph state | The same maximum-round rule inside the transaction |
| Safety proof | Apply, verify, and rollback receipts plus state digests | The same receipt-and-digest proof |
| Trade-off | More code, every transition is inspectable | Less graph ceremony, loop orchestration stays in code |


## Setup

The deterministic section is fully offline. The setup searches upward for the pattern helpers and repository helpers, so execution works from the repository root, the notebook directory, `nbmake`, or JupyterLab without relying on `__file__` or a brittle relative path.



```python
from __future__ import annotations

import html
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable, Iterable, TypedDict

# Search upward for repository helpers so this works from Jupyter, nbmake,
# the notebook directory, or the repository root.
for _marker in ("shared.py", "model_config.py", "nbtools.py"):
    _dir = next(
        path
        for path in (Path.cwd(), *Path.cwd().parents)
        if (path / _marker).exists()
    )
    sys.path.insert(0, str(_dir))

# Notebook display, message, graph, and schema tools used by the tutorial.
from IPython.display import HTML, display  # noqa: E402
from IPython.utils.capture import capture_output  # noqa: E402
from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

# Repository modules supply model setup, domain records, fixtures, and parsers.
from model_config import get_model  # noqa: E402
from nbtools import show_graph  # noqa: E402
from pattern import (  # noqa: E402
    ApplyReceipt,
    FailureSignal,
    HealRound,
    HealStage,
    HealStatus,
    HealTrace,
    Patch,
    PatchReview,
    RollbackReceipt,
    StageError,
    VerificationReceipt,
)
from shared import (  # noqa: E402
    RECORD_FIELDS,
    SCENARIO_ORDER,
    format_scenario_matrix,
    format_scenario_walkthrough,
    ScenarioRuntime,
    assert_expected_record,
    new_runtime,
    parse_diagnosis_json,
    parse_patch_json,
    run_core_reference,
    trace_record,
)
```

## Transaction state

`GraphState` is a `TypedDict`: at runtime it is still a normal Python dictionary. The annotation documents which keys may appear. `total=False` matters because each node returns only the keys it changes rather than rebuilding the whole transaction.

Mutable collections are created by `capture_baseline` for each invocation; no run shares attempts, receipts, or errors with another. The seven deterministic scenarios run in this locked order: `convergence`, `critic_block`, `no_progress`, `regression`, `round_budget`, `stage_error`, and `rollback_failure`.



```python
# Nodes read this shared dictionary and return only changed keys. LangGraph
# merges each partial update into the state already carried by the graph.
class GraphState(TypedDict, total=False):
    # Invocation inputs: supplied once by the caller.
    runtime: ScenarioRuntime
    diagnose_role: Callable[[FailureSignal], str]
    draft_role: Callable[[str], Patch]
    initial_failure: FailureSignal
    # Current round: replaced as the transaction advances.
    current_failure: FailureSignal
    baseline_digest: str
    round_no: int
    diagnosis: str
    patch: Patch
    attempt_keys: set[tuple[str, str]]
    commit_ids: set[str]
    radius_files: set[str]
    rounds: list[HealRound]
    # Receipt evidence: append-only proof of mutation and verification.
    apply_receipts: list[ApplyReceipt]
    rollback_receipts: list[RollbackReceipt]
    stage_errors: list[StageError]
    # Compensation proof and terminal result.
    status: HealStatus
    stop_reason: str
    final_digest: str | None
    baseline_restored: bool | None
    unaddressable_mutation: bool
    next_route: str
    trace: HealTrace

```

## Build the graph

We will define the workflow in small explain-then-code pairs. The main path is:

`START -> capture_baseline -> diagnose -> draft_patch -> duplicate_guard -> review -> apply -> verify -> decide`

`decide` may finish, begin another bounded round, or compensate. Any error or non-success stop routes through `rollback` before `finalize`.

Before the nodes, three helper groups establish the evidence rules they share.

### Digest reads and public stage errors

A digest is a compact fingerprint of workspace state. These helpers validate digest reads and convert callback exceptions into stable `StageError` evidence.



```python
# A digest observes managed workspace state without changing it; later checks
# use the value to detect hidden mutation or prove restoration.
def _read_digest(runtime: ScenarioRuntime) -> str:
    digest = runtime.workspace.state_digest()
    if not isinstance(digest, str) or not digest.strip():
        raise ValueError("state_digest must be a nonblank string")
    return digest


# Extract only expected fields instead of storing an entire callback object.
def _receipt_evidence(receipt: object, fields: Iterable[str]) -> tuple[str, ...]:
    return tuple(f"{name}={getattr(receipt, name, '<missing>')!r}" for name in fields)


# StageError is the public error record and keeps at most eight evidence fields.
def _stage_error(
    stage: HealStage,
    round_no: int | None,
    exc: BaseException,
    evidence: Iterable[str] = (),
) -> StageError:
    values = tuple(
        value for value in evidence if isinstance(value, str) and value.strip()
    )[:8]
    return StageError(
        stage,
        round_no,
        type(exc).__name__,
        str(exc) or repr(exc),
        values,
    )


# Turn digest callback failures into state so routing can handle them
# instead of raising out of the transaction.
def _digest_or_error(
    runtime: ScenarioRuntime,
    round_no: int | None,
) -> tuple[str | None, list[StageError]]:
    try:
        return _read_digest(runtime), []
    except Exception as exc:  # the runtime owns the state callback
        return None, [_stage_error(HealStage.STATE_CHECK, round_no, exc)]
```

### Pure-role guard

A role may calculate a value, but it may not quietly change the workspace. `_pure_role` reads the digest before and after a callback and reports both ordinary exceptions and forbidden mutation.



```python
# Invariant: a pure role must not mutate managed workspace state.
def _pure_role(
    runtime: ScenarioRuntime,
    stage: HealStage,
    round_no: int,
    callback: Callable[..., object],
    *args: object,
) -> tuple[object | None, bool, bool, list[StageError]]:
    # Capture the workspace fingerprint before the observational callback runs.
    before, errors = _digest_or_error(runtime, round_no)
    if before is None:
        return None, False, False, errors
    try:
        result = callback(*args)
    except Exception as exc:
        errors.append(_stage_error(stage, round_no, exc))
        # A callback that raises may still have changed state, so measure again.
        after, digest_errors = _digest_or_error(runtime, round_no)
        errors.extend(digest_errors)
        mutated = after is not None and after != before
        if mutated:
            errors.append(
                _stage_error(
                    stage,
                    round_no,
                    RuntimeError("callback mutated managed state"),
                    (f"before_digest={before!r}", f"after_digest={after!r}"),
                )
            )
        return None, mutated, False, errors
    # A normal return is accepted only when the after digest matches the before digest.
    after, digest_errors = _digest_or_error(runtime, round_no)
    errors.extend(digest_errors)
    if after is None:
        return result, False, False, errors
    if after != before:
        errors.append(
            _stage_error(
                stage,
                round_no,
                RuntimeError("callback mutated managed state"),
            )
        )
        return result, True, False, errors
    return result, False, True, errors
```

### Receipt validators

Receipts are useful only when they describe the exact patch or commit in this transaction. These pure helpers validate that binding without mutating graph state.



```python
# A typed, evidence-bearing review is valid only when it names this patch.
def _validate_review(receipt: object, patch: Patch) -> tuple[bool, tuple[str, ...]]:
    fields = ("patch_digest", "approved", "reason", "evidence")
    if not isinstance(receipt, PatchReview):
        return False, _receipt_evidence(receipt, fields)
    valid = (
        receipt.patch_digest == patch.digest
        and type(receipt.approved) is bool
        and isinstance(receipt.evidence, tuple)
        and any(
            isinstance(item, str) and item.strip()
            for item in receipt.evidence
        )
        and (
            receipt.approved
            or (isinstance(receipt.reason, str) and receipt.reason.strip())
        )
    )
    return valid, _receipt_evidence(receipt, fields)


# "addressable" means rollback can name a unique commit. "valid" also binds
# that commit to the patch digest and exactly the files the patch declares.
def _validate_apply(
    receipt: object,
    patch: Patch,
    seen: set[str],
) -> tuple[bool, bool, tuple[str, ...]]:
    fields = ("commit_id", "patch_digest", "changed_files")
    if not isinstance(receipt, ApplyReceipt):
        return False, False, _receipt_evidence(receipt, fields)
    addressable = (
        isinstance(receipt.commit_id, str)
        and bool(receipt.commit_id.strip())
        and receipt.commit_id not in seen
    )
    valid = (
        addressable
        and receipt.patch_digest == patch.digest
        and receipt.changed_files == patch.touches
    )
    return valid, addressable, _receipt_evidence(receipt, fields)


# Rebuilding the value reruns FailureSignal validation and catches malformed
# instances that still pass isinstance().
def _valid_failure_signal(value: object) -> bool:
    if not isinstance(value, FailureSignal):
        return False
    try:
        normalized = FailureSignal(
            value.kind,
            value.error_text,
            value.affected_files,
            value.code,
        )
    except (TypeError, ValueError):
        return False
    return (
        value.kind == normalized.kind
        and value.error_text == normalized.error_text
        and value.affected_files == normalized.affected_files
        and value.code == normalized.code
    )


# Verification must name the exact apply receipt; a reported failure must
# also be a valid FailureSignal for the next round.
def _validate_verify(
    receipt: object,
    applied: ApplyReceipt,
) -> tuple[bool, tuple[str, ...]]:
    fields = ("commit_id", "patch_digest", "failure", "check", "evidence")
    if not isinstance(receipt, VerificationReceipt):
        return False, _receipt_evidence(receipt, fields)
    valid = (
        receipt.commit_id == applied.commit_id
        and receipt.patch_digest == applied.patch_digest
        and (receipt.failure is None or _valid_failure_signal(receipt.failure))
        and isinstance(receipt.check, str)
        and bool(receipt.check.strip())
        and isinstance(receipt.evidence, str)
        and bool(receipt.evidence.strip())
    )
    return valid, _receipt_evidence(receipt, fields)
```

### Capture the baseline

**Input:** The caller-supplied runtime, initial failure, and role callables.

**Purpose:** Initialize fresh transaction collections and record the pre-repair workspace digest.

**Invariant:** No repair role runs before a valid baseline exists.

**Failure route:** A failed digest read goes directly to `finalize`; no rollback callback runs because no apply is known.



```python
def capture_baseline(state: GraphState) -> dict[str, object]:
    # No repair role or mutating callback may run until a baseline digest exists.
    baseline, errors = _digest_or_error(state["runtime"], None)
    # Fresh collections belong to this invocation, so separate runs share no evidence.
    initial: dict[str, object] = {
        "round_no": 1,
        "attempt_keys": set(),
        "commit_ids": set(),
        "radius_files": set(state["initial_failure"].affected_files),
        "rounds": [],
        "apply_receipts": [],
        "rollback_receipts": [],
        "stage_errors": errors,
        "unaddressable_mutation": False,
    }
    # Baseline failure happens before apply, so rollback has no known work to undo.
    if baseline is None:
        return {
            **initial,
            "status": HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
            "stop_reason": "stage_error:state_check",
            "final_digest": None,
            "baseline_restored": None,
            "next_route": "finalize",
        }
    # LangGraph merges this partial update with caller inputs such as runtime
    # and the role callables.
    return {
        **initial,
        "baseline_digest": baseline,
        "current_failure": state["initial_failure"],
        "next_route": "diagnose",
    }


# A route function returns a name; graph assembly later maps it to a node.
def route_after_capture(state: GraphState) -> str:
    return state["next_route"]
```

### Diagnose the current failure

**Input:** The current `FailureSignal` and `diagnose_role` callable.

**Purpose:** Produce one nonblank diagnosis for the current round.

**Invariant:** Diagnosis is observationally pure and must return `str`.

**Failure route:** Callback, type, digest, or mutation failure routes to `rollback` through `_role_failure`.



```python
# Convert a stage failure into shared state before routing through rollback.
def _role_failure(
    state: GraphState,
    stage: HealStage,
    errors: list[StageError],
    mutated: bool,
) -> dict[str, object]:
    last_stage = errors[-1].stage if errors else stage
    return {
        "stage_errors": [*state["stage_errors"], *errors],
        "unaddressable_mutation": state["unaddressable_mutation"] or mutated,
        "status": HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
        "stop_reason": f"stage_error:{last_stage.value}",
        "next_route": "rollback",
    }


def diagnose(state: GraphState) -> dict[str, object]:
    # _pure_role returns both the proposal and evidence that no mutation occurred.
    result, mutated, ok, errors = _pure_role(
        state["runtime"],
        HealStage.DIAGNOSE,
        state["round_no"],
        state["diagnose_role"],
        state["current_failure"],
    )
    # Deterministic Python checks the type; the role cannot declare itself valid.
    if ok and not isinstance(result, str):
        errors.append(
            _stage_error(
                HealStage.DIAGNOSE,
                state["round_no"],
                TypeError("diagnose must return str"),
            )
        )
        ok = False
    if not ok:
        return _role_failure(state, HealStage.DIAGNOSE, errors, mutated)
    # Only diagnosis and the next route change; every other state key remains.
    return {"diagnosis": result, "next_route": "draft_patch"}


def route_after_diagnose(state: GraphState) -> str:
    return state["next_route"]
```

### Draft one patch

**Input:** The diagnosis and `draft_role` callable.

**Purpose:** Create the round's candidate `Patch` and append its `HealRound` evidence.

**Invariant:** Drafting is observationally pure and must return `Patch`.

**Failure route:** Callback, type, digest, or mutation failure routes to `rollback`.



```python
def draft_patch(state: GraphState) -> dict[str, object]:
    # Drafting reuses the purity guard: the role may propose a Patch only.
    result, mutated, ok, errors = _pure_role(
        state["runtime"],
        HealStage.FIX,
        state["round_no"],
        state["draft_role"],
        state["diagnosis"],
    )
    if ok and not isinstance(result, Patch):
        errors.append(
            _stage_error(
                HealStage.FIX,
                state["round_no"],
                TypeError("fix must return Patch"),
            )
        )
        ok = False
    if not ok:
        return _role_failure(state, HealStage.FIX, errors, mutated)
    patch = result
    # Start this round's evidence record before review or workspace mutation.
    round_ = HealRound(
        state["round_no"],
        state["current_failure"],
        state["diagnosis"],
        patch,
    )
    return {
        "patch": patch,
        "rounds": [*state["rounds"], round_],
        "next_route": "duplicate_guard",
    }


def route_after_draft(state: GraphState) -> str:
    return state["next_route"]
```

### Reject duplicate work

**Input:** The current failure signature, patch digest, and prior attempt keys.

**Purpose:** Stop a loop that proposes the same patch for the same failure twice.

**Invariant:** A repeated failure-and-patch pair is never applied again.

**Failure route:** A duplicate routes to `rollback` with `no_progress_same_failure_and_patch`.



```python
# Invariant: the same failure and patch pair may never be applied twice.
def duplicate_guard(state: GraphState) -> dict[str, object]:
    attempt = (state["current_failure"].signature, state["patch"].digest)
    # Copy the set so this node returns new state instead of mutating the
    # collection already stored in shared state.
    attempts = set(state["attempt_keys"])
    if attempt in attempts:
        return {
            "status": HealStatus.ROLLED_BACK_NO_PROGRESS,
            "stop_reason": "no_progress_same_failure_and_patch",
            "next_route": "rollback",
        }
    attempts.add(attempt)
    return {"attempt_keys": attempts, "next_route": "review"}


def route_after_duplicate(state: GraphState) -> str:
    return state["next_route"]
```

### Review the patch

**Input:** The current patch, current failure, and deterministic review callback.

**Purpose:** Approve or reject the candidate with evidence bound to its patch digest.

**Invariant:** Review is pure, typed, and receipt-bound.

**Failure route:** Invalid review evidence routes to `rollback`; an ordinary rejection also rolls back with `blocked_by_critic`.



```python
def review(state: GraphState) -> dict[str, object]:
    # Review is observational: it may approve or reject, but it cannot mutate.
    result, mutated, ok, errors = _pure_role(
        state["runtime"],
        HealStage.REVIEW,
        state["round_no"],
        state["runtime"].review,
        state["patch"],
        state["current_failure"],
    )
    if not ok:
        return _role_failure(state, HealStage.REVIEW, errors, mutated)
    # A callback value is not evidence until it has the expected receipt type.
    if not isinstance(result, PatchReview):
        errors.append(
            _stage_error(
                HealStage.REVIEW,
                state["round_no"],
                TypeError("review must return PatchReview"),
                _receipt_evidence(
                    result,
                    ("patch_digest", "approved", "reason", "evidence"),
                ),
            )
        )
        return _role_failure(state, HealStage.REVIEW, errors, mutated)
    # Binding checks prove the receipt describes the current patch.
    valid, evidence = _validate_review(result, state["patch"])
    # Record the typed receipt before branching, so even invalid binding remains
    # visible in the terminal trace.
    updated_rounds = [
        *state["rounds"][:-1],
        replace(state["rounds"][-1], patch_review=result),
    ]
    if not valid:
        errors.append(
            _stage_error(
                HealStage.REVIEW,
                state["round_no"],
                ValueError("invalid review receipt"),
                evidence,
            )
        )
        failure = _role_failure(state, HealStage.REVIEW, errors, mutated)
        return {**failure, "rounds": updated_rounds}
    # A valid rejection is a policy result, not a stage error; it still rolls back.
    if not result.approved:
        return {
            "rounds": updated_rounds,
            "status": HealStatus.BLOCKED_BY_CRITIC,
            "stop_reason": "review_rejected",
            "next_route": "rollback",
        }
    return {"rounds": updated_rounds, "next_route": "apply"}


def route_after_review(state: GraphState) -> str:
    return state["next_route"]
```

### Apply atomically

**Input:** The reviewed patch and mutable workspace.

**Purpose:** Perform the mutation and retain an addressable apply receipt for later verification or compensation.

**Invariant:** Every accepted mutation has a unique nonblank commit ID bound to the patch and changed files.

**Failure route:** Apply, receipt, or digest failure routes to `rollback`; unaddressable mutation forces human handoff.



```python
# Invariant: every accepted mutation keeps a unique, patch-bound apply receipt.
def apply(state: GraphState) -> dict[str, object]:
    runtime = state["runtime"]
    # Snapshot state around the only forward callback allowed to mutate workspace.
    before, errors = _digest_or_error(runtime, state["round_no"])
    if before is None:
        return _role_failure(state, HealStage.STATE_CHECK, errors, False)
    try:
        receipt = runtime.workspace.apply(state["patch"])
    except Exception as exc:
        errors.append(_stage_error(HealStage.APPLY, state["round_no"], exc))
        # An exception does not prove nothing changed; read the digest again before
        # deciding whether rollback can address the mutation.
        after, digest_errors = _digest_or_error(runtime, state["round_no"])
        errors.extend(digest_errors)
        mutated = after is not None and after != before
        if mutated:
            errors.append(
                _stage_error(
                    HealStage.APPLY,
                    state["round_no"],
                    RuntimeError("callback mutated managed state"),
                    (f"before_digest={before!r}", f"after_digest={after!r}"),
                )
            )
        failure = _role_failure(state, HealStage.APPLY, errors, mutated)
        return {**failure, "stop_reason": "stage_error:apply"}

    valid, addressable, evidence = _validate_apply(
        receipt,
        state["patch"],
        state["commit_ids"],
    )
    applies = list(state["apply_receipts"])
    commits = set(state["commit_ids"])
    rounds = list(state["rounds"])
    # Store any unique commit receipt even when its other fields are invalid; this
    # keeps a potentially mutated, addressable commit available for terminal
    # evidence and rollback.
    if addressable and isinstance(receipt, ApplyReceipt):
        applies.append(receipt)
        commits.add(receipt.commit_id)
        rounds[-1] = replace(rounds[-1], apply_receipt=receipt)
    if not valid:
        errors.append(
            _stage_error(
                HealStage.APPLY,
                state["round_no"],
                ValueError("invalid apply receipt"),
                evidence,
            )
        )
    # Re-read the digest independently of receipt claims. If state changed without
    # a usable commit id, rollback cannot address that mutation.
    after, digest_errors = _digest_or_error(runtime, state["round_no"])
    errors.extend(digest_errors)
    unaddressable = state["unaddressable_mutation"]
    if not valid and not addressable and after is not None and after != before:
        unaddressable = True
    if not valid or after is None:
        reason = "stage_error:state_check" if after is None else "stage_error:apply"
        return {
            "apply_receipts": applies,
            "commit_ids": commits,
            "rounds": rounds,
            "stage_errors": [*state["stage_errors"], *errors],
            "unaddressable_mutation": unaddressable,
            "status": HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
            "stop_reason": reason,
            "next_route": "rollback",
        }
    radius = set(state["radius_files"])
    radius.update(state["patch"].touches)
    return {
        "apply_receipts": applies,
        "commit_ids": commits,
        "rounds": rounds,
        "stage_errors": [*state["stage_errors"], *errors],
        "radius_files": radius,
        "next_route": "verify",
    }


def route_after_apply(state: GraphState) -> str:
    return state["next_route"]
```

### Verify the applied commit

**Input:** The newest apply receipt and deterministic verification callback.

**Purpose:** Check the real workspace and bind the result to the exact commit and patch.

**Invariant:** Verification is pure and returns a valid `VerificationReceipt`.

**Failure route:** Callback, type, binding, digest, or mutation failure routes to `rollback`.



```python
def verify(state: GraphState) -> dict[str, object]:
    # Verification receives the latest accepted apply receipt, not a free-form patch.
    applied = state["apply_receipts"][-1]
    # _pure_role enforces that verification observes workspace state
    # without changing it.
    result, mutated, ok, errors = _pure_role(
        state["runtime"],
        HealStage.VERIFY,
        state["round_no"],
        state["runtime"].verify,
        applied,
    )
    if not ok:
        return _role_failure(state, HealStage.VERIFY, errors, mutated)
    if not isinstance(result, VerificationReceipt):
        errors.append(
            _stage_error(
                HealStage.VERIFY,
                state["round_no"],
                TypeError("verify must return VerificationReceipt"),
                _receipt_evidence(
                    result,
                    ("commit_id", "patch_digest", "failure", "check", "evidence"),
                ),
            )
        )
        return _role_failure(state, HealStage.VERIFY, errors, mutated)
    # Binding checks tie pass or failure evidence to this exact commit and patch.
    valid, evidence = _validate_verify(result, applied)
    # Record typed verification evidence before branching on whether it is valid.
    rounds = [
        *state["rounds"][:-1],
        replace(state["rounds"][-1], verification_receipt=result),
    ]
    if not valid:
        errors.append(
            _stage_error(
                HealStage.VERIFY,
                state["round_no"],
                ValueError("invalid verification receipt"),
                evidence,
            )
        )
        failure = _role_failure(state, HealStage.VERIFY, errors, mutated)
        return {**failure, "rounds": rounds}
    return {"rounds": rounds, "next_route": "decide"}


def route_after_verify(state: GraphState) -> str:
    return state["next_route"]
```

### Decide whether to finish or continue

**Input:** The newest verification receipt, stability policy, current radius, and round number.

**Purpose:** Choose success, another bounded round, regression stop, or round-budget handoff.

**Invariant:** Success is checked first, then blast radius, then round exhaustion, matching the sealed core.

**Failure route:** A non-success terminal decision routes to `rollback`; a digest failure does too.



```python
# Success requires receipt-bound verification.
# Every retry stays inside both radius and round limits.
def decide(state: GraphState) -> dict[str, object]:
    verification = state["rounds"][-1].verification_receipt
    assert verification is not None
    # A passing receipt still needs a readable final digest before success is public.
    if verification.failure is None:
        final, errors = _digest_or_error(state["runtime"], state["round_no"])
        if final is not None:
            return {
                "final_digest": final,
                "status": HealStatus.FIXED,
                "stop_reason": "verification_passed",
                "baseline_restored": None,
                "next_route": "finalize",
            }
        return {
            "stage_errors": [*state["stage_errors"], *errors],
            "status": HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
            "stop_reason": "stage_error:state_check",
            "next_route": "rollback",
        }

    current_failure = verification.failure
    # Expand the file radius with the new failure before enforcing blast-radius policy.
    radius = set(state["radius_files"])
    radius.update(current_failure.affected_files)
    baseline_radius = max(len(state["initial_failure"].affected_files), 1)
    limit = baseline_radius * state["runtime"].scenario.stability.max_radius_multiplier
    if len(radius) > limit:
        return {
            "current_failure": current_failure,
            "radius_files": radius,
            "status": HealStatus.ROLLED_BACK_REGRESSION,
            "stop_reason": "blast_radius_exceeded",
            "next_route": "rollback",
        }
    # Check the round budget only after ruling out a wider regression.
    if state["round_no"] == state["runtime"].scenario.stability.max_rounds:
        return {
            "current_failure": current_failure,
            "radius_files": radius,
            "status": HealStatus.MAX_ROUNDS_HUMAN_HANDOFF,
            "stop_reason": "round_budget_exhausted",
            "next_route": "rollback",
        }
    # Only a bounded retry increments round_no and returns to diagnosis.
    return {
        "current_failure": current_failure,
        "radius_files": radius,
        "round_no": state["round_no"] + 1,
        "next_route": "diagnose",
    }


def route_after_decide(state: GraphState) -> str:
    return state["next_route"]
```

### Roll back known applies

**Input:** All addressable apply receipts plus the baseline digest.

**Purpose:** Compensate newest-first and prove whether the original workspace was restored.

**Invariant:** Every known apply needs a valid rollback receipt and the final digest must equal the baseline.

**Failure route:** Rollback continues after individual failures, then reports `rollback_failed_human_handoff` when restoration is unproved.



```python
# Compensation runs newest-first.
# Restoration needs complete receipts, no unaddressable mutation, and a digest match.
def rollback(state: GraphState) -> dict[str, object]:
    errors = list(state["stage_errors"])
    receipts: list[RollbackReceipt] = []
    complete = True
    # A failed rollback marks proof incomplete, but older applies are still attempted.
    for applied in reversed(state["apply_receipts"]):
        try:
            receipt = state["runtime"].workspace.rollback(applied)
        except Exception as exc:
            errors.append(_stage_error(HealStage.ROLLBACK, None, exc))
            complete = False
            continue
        if not isinstance(receipt, RollbackReceipt):
            errors.append(
                _stage_error(
                    HealStage.ROLLBACK,
                    None,
                    TypeError("rollback must return RollbackReceipt"),
                    _receipt_evidence(
                        receipt,
                        ("commit_id", "patch_digest", "succeeded", "detail"),
                    ),
                )
            )
            complete = False
            continue
        receipts.append(receipt)
        # A success flag counts only with commit/patch binding and nonblank detail.
        valid = (
            receipt.commit_id == applied.commit_id
            and receipt.patch_digest == applied.patch_digest
            and receipt.succeeded is True
            and isinstance(receipt.detail, str)
            and bool(receipt.detail.strip())
        )
        if not valid:
            errors.append(
                _stage_error(
                    HealStage.ROLLBACK,
                    None,
                    ValueError("invalid rollback receipt"),
                    _receipt_evidence(
                        receipt,
                        ("commit_id", "patch_digest", "succeeded", "detail"),
                    ),
                )
            )
            complete = False
    # After all callbacks, read workspace state once more for restoration proof.
    final, digest_errors = _digest_or_error(state["runtime"], None)
    errors.extend(digest_errors)
    complete = complete and len(receipts) == len(state["apply_receipts"])
    restored = (
        complete
        and not state["unaddressable_mutation"]
        and final == state["baseline_digest"]
    )
    # Preserve the original outcome only after restoration is proved;
    # otherwise hand off.
    status = (
        state["status"]
        if restored
        else HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    )
    return {
        "rollback_receipts": receipts,
        "stage_errors": errors,
        "final_digest": final,
        "baseline_restored": restored,
        "status": status,
        "next_route": "finalize",
    }
```

### Finalize the public trace

**Input:** The terminal status, stop reason, rounds, receipts, errors, and digest proof.

**Purpose:** Construct one immutable `HealTrace` for callers.

**Invariant:** A non-success result without proved restoration becomes rollback-failed human handoff.

**Failure route:** This is the terminal node; it returns the authoritative status and trace.



```python
def finalize(state: GraphState) -> dict[str, object]:
    status = state["status"]
    # When a baseline exists, any non-success without restoration proof is upgraded
    # to rollback-failed human handoff.
    if (
        status is not HealStatus.FIXED
        and state.get("baseline_digest") is not None
        and state.get("baseline_restored") is not True
    ):
        status = HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    # Convert working lists to tuples so the public trace cannot append more evidence.
    trace = HealTrace(
        status,
        state["stop_reason"],
        tuple(state["rounds"]),
        tuple(state["apply_receipts"]),
        tuple(state["rollback_receipts"]),
        tuple(state["stage_errors"]),
        state.get("baseline_digest"),
        state.get("final_digest"),
        state.get("baseline_restored"),
    )
    # This partial update is the graph's authoritative terminal result.
    return {"status": status, "trace": trace}
```

### Assemble and inspect the transaction

**Input:** The node functions and route functions defined above.

**Purpose:** Register explicit nodes and named conditional edges, then compile one reusable graph.

**Invariant:** Node names, route names, `START`, `END`, and `GRAPH_ALT` remain stable public teaching surfaces.

**Failure route:** Framework recursion is a secondary guard; business stopping decisions remain inside `decide`.



```python
def build_self_heal_graph():
    # StateGraph declares the shared-state shape; registering nodes does not run them.
    builder = StateGraph(GraphState)
    # Stable node names make transaction stages visible in diagrams and traces.
    builder.add_node("capture_baseline", capture_baseline)
    builder.add_node("diagnose", diagnose)
    builder.add_node("draft_patch", draft_patch)
    builder.add_node("duplicate_guard", duplicate_guard)
    builder.add_node("review", review)
    builder.add_node("apply", apply)
    builder.add_node("verify", verify)
    builder.add_node("decide", decide)
    builder.add_node("rollback", rollback)
    builder.add_node("finalize", finalize)

    # START is unconditional. Each route function returns a name that its mapping
    # translates into the next node.
    builder.add_edge(START, "capture_baseline")
    builder.add_conditional_edges(
        "capture_baseline",
        route_after_capture,
        {"diagnose": "diagnose", "finalize": "finalize"},
    )
    builder.add_conditional_edges(
        "diagnose",
        route_after_diagnose,
        {"draft_patch": "draft_patch", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "draft_patch",
        route_after_draft,
        {"duplicate_guard": "duplicate_guard", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "duplicate_guard",
        route_after_duplicate,
        {"review": "review", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "review",
        route_after_review,
        {"apply": "apply", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "apply",
        route_after_apply,
        {"verify": "verify", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {"decide": "decide", "rollback": "rollback"},
    )
    builder.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "finalize": "finalize",
            "diagnose": "diagnose",
            "rollback": "rollback",
        },
    )
    # Rollback always finalizes, finalize reaches END, and compile enables .invoke().
    builder.add_edge("rollback", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


graph = build_self_heal_graph()
GRAPH_ALT = "Self-Heal transaction with bounded repair loop and compensation path"
# Capture the rendered graph so exported HTML keeps a descriptive image label.
with capture_output() as _graph_capture:
    show_graph(graph, alt=GRAPH_ALT)
_graph_png = next(
    output.data["image/png"]
    for output in _graph_capture.outputs
    if "image/png" in output.data
)
display(
    HTML(
        f'<img alt="{html.escape(GRAPH_ALT)}" '
        f'src="data:image/png;base64,{_graph_png}" />'
    )
)

```


<img alt="Self-Heal transaction with bounded repair loop and compensation path" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAiUAAARmCAIAAABvE1JEAAAQAElEQVR4nOzdB3xOZ/8G8Dt7kYgkQsTesfcosfceVUXtvaq2UrsDpcNWRSlVtauoompvsYkVM4KQvcf/8pz+07xEZD1nPdf37SfvybPyyDi/c/+uc9/HMjExURARERmZuSAiIjI+1hsiIpID6w0REcmB9YaIiOTAekNERHJgvSEiIjlYCiIi+n93LkfePB8a+jI2MiwuMTYxUZiZmYlX/2cuEhOEhaWIjxPCTAjDRJJXNyYmmpmbJcZLnyYmJpi92rBITIw3k14wUXq4mTA33IAX+feJCbjx1f+k10/yxmv++5TEV69heIn//+pJzK3MbO0tHBwtCpbK5lUzm1ArM86/ISI6uz/40rGg8OA47Mwtrcys7czNzQ2VICHxVaFISJT2++aWIiFOJFUIs1cdIjN8TIgzfI5PpXJiaZYY9z+71lev9W+9STQ80Qwbr2qNoaIlLziv7hKGe+INj7T4dyPZV32j3lig0CXGxiTERCcmxCXYOlgWLp2tXmdXoTKsN0Rk0s7sCz63PzAhQbjls63a0CV/KRuhZcHP4o7tfP7wVgTGYQVLOzTr4S5Ug/WGiEzXTzP9IsMTSld3qtPeRejLtVNhx3Y+w5is36xCQh1Yb4jIRC0acyt3fruOI/IK/Tq0KfDS8ZfvtXKrUN9JKI31hohM0aLRtxp2zlOyuoMwAYvH3Oo2sZCTi4VQFOsNEZmYeLFo3K0hXxU1sxKmY9n4O1Uau1Zu5CiUw/k3RGRalky83ax7HpMqNjBwduETe569DIgRymG9ISITsmbWPfcC9kUqmkQb7TXVG7v8+s1DoRzWGyIyFad2vwwPje8wNI8wSVWa5rCxM9/0vWIlh/WGiEzFuYMvy72XQ5iwziPzPfGLEgphvSEik3BuX3BifOJ7bXIKE+bgZOHgaLl10WOhBNYbIjIJF44GuRe0F/Jq3Ljxo0ePRDrdvn27VatWwjjKvufk7xcplMB6Q0QmISIktmYLWRcR8Pf3f/nypUi/q1evCqOp0tgZHx/4RgjZcX1oItK/66dCzczN8hS2FkaQmJj4yy+/7Ny58969e4UKFapRo8bgwYPPnz8/aNAg3Nu2bdu6devOmzcPo5ZNmzadPn368ePHhQsXbteuXadOnaRXaNiwYb9+/Q4cOIBnffTRR2vXrsWNVapU+eSTT7p16yaymp2DxaUjYfmKyz3aY70hIv3zux5hbWusds6GDRtWrlw5cuTI99577+DBg4sWLXJwcOjdu/e3336LG7dv354376slc1ByUGkmTZpkZmbm5+c3e/bsPHny4Cm4y8rKauvWrdWqVUPVqVy5Mh6wd+9eFDBhHIhwXgQocNYA6w0R6V/oizhbe2Ot5nLu3DkvLy8pcWnfvn3VqlUjIlLoVn355Zfh4eEeHh7CMHbZsWPHsWPHpHqDAuPk5DRmzBghC0dXq8e3FIhwWG+ISP9iY+ItrYw1vilfvvyCBQtmzJhRsWJFb29vT0/PFB+GthtGQkePHkXbTbpFGvdIULGEXGxszeLiEoTsWG+ISP8SEoWZMNZakV27dkUD7Z9//pk+fbqlpWXjxo1HjBjh5ub2P28gIeHjjz+OiYkZNmwYBjfZs2fv27dv8gdYWxslW0qRmbkyZ4qx3hCR/llbm8fGGKvemJubtze4c+fOqVOnli9fHhYW9s033yR/zPXr169cubJ48WKENNItoaGhuXLlEkqIjow3MzcTsuP50ESkf/bZLCNC4oRxINi/ffs2NgoXLtylS5cPP/zwxo0brz0mKCgIH5MKzB0DoZDgZ3FW1grs/FlviEj/8hWzj4mKF8axZ8+esWPHHjp0KDg4+MiRIwcOHECig9sLFiyIj3/99dfly5dRitBqW7t2bUhIiJ+f39y5c2vUqOHv75/iC+bPn//58+cHDx5MSnqyVsjLGGcX+dp3SVhviEj/ytdzNDMzw3G9MILJkyejnIwaNaphw4YzZ86sW7fupEmTcLunp2fr1q2XLl26YMGC3Llzz5o169KlSw0aNPjkk0+GDh3aqVMn1KGkKTjJ1a5du0KFCmPGjPnzzz+FEcRExpeqll3IjtdbIyKTsHKqX+4Cdi36uAvTdv1U6L4NAcPmFxWy4/iGiExC4TIO92+ECZN3+q8XLnkUaKYJnp9GRCai3vtul48HXzwcXK6OU4oPQJqCqD/Fu7JlyxYWlnKtQidt5cqVwjhWG6R4F9qDb+tODRs2LMU2nSToeczALxQY3Aj204jIdPy17undK2EDviic4r1xcXFPnz5N8a6oqChbW9sU77K0tDTeac2hBineFRIS4ujomOJduB0FMsW7fv36YWJ8Ypfx+YQSWG+IyIQsn3incJlsjbopM/FFWQ9vRf++9OHgr4sIhTC/ISITMuDLwr4+ocJYU3FU7fflD2u2chXKYb0hItNSr4P70km3hYlZNe1egRLZK9RzEsphP42ITM7zxzEb5z8YolxnSWZLxt2u2yGXVw0F5twkx3pDRKbo7sXwnav8K9XP+V6bnEK/7l+L+mP1owIlHFr0yS2UxnpDRKYqXiyffMfK1rx5T4/cBZWZkmJU6+fcD34eW6etW5n3HIUKsN4QkUn7fZn/g1sRdtksSlRyqtXaWWjf5aMhFw4FBQXGOOey7jouv1AN1hsiIrHjhydP7kTExSZaWJk5OltZ2ZhZ21lYWJolxP93XTJzc5Fg+MzM3CwxITHp0383zIWZeHW74RazhITE/3+WGbak2y0sRfz/nxpnZpGYGG+W/MH4cvFx/z791TMSDHe9evKrq/eIxH8fKV1KwPAG/n2ipaVFbEx8WFB8ZHh8TFS8mZlwyWPz/lBPYSVUhfWGiOhfQc8Tz/71PNA/KvhFbHxsopmZWUKyy2BiPy7tL6WNFD599T+z5I+Utl9d2vNVxRAWFiI2NsHccLkzqWglf/B/9cxwbRrpNUVCYqKZ2f+8Adxu/j9vwMrKzNzSzNbOwtndqlSNHAVL2QpVYr0hIpJPo0aNNm/e7OSk5HnJSuH6aURE8omLi7O0NNEdL+sNEZF8WG+IiEgOrDdERGR0yMvj4+MtLCyESWK9ISKSiSkPbgTrDRGRbFhviIhIDqw3REQkh9jYWCsrlU36lxHrDRGRTDi+ISIiObDeEBGRHFhviIhIDqw3REQkB54vQEREcuD4hoiI5MB6Q0REcmC9ISIiObDeEBGRHFhviIhIDqw3REQkB9YbIiKSA+sNERHJgfM9iYhIDhzfEBGRHMzNzR0dHYWpYr0hIpIJ+mnh4eHCVJkLIiIi42O9ISIiObDeEBGRHFhviIhIDqw3REQkB9YbIiKSA+sNERHJgfWGiIjkwHpDRERyYL0hIiI5sN4QEZEcWG+IiEgOrDdERCQH1hsiIpID6w0REcnBLDExURARkdG0b98+wSA8PDw2NjZnzpzYjoiI2L9/vzAlvN4aEZFxlS5d+o8//rCwsJA+ffToEepNyZIlhYlhP42IyLh69OiRN2/e5LfY2tp27dpVmBjWGyIi4ypevHilSpWS31KgQIFWrVoJE8N6Q0RkdN27d3d3d5e2HRwcPvroI2F6WG+IiIwOQ5wqVapI2/nz52/RooUwPaw3RERykIY4GNxgQ5gknp9GRKoTH5f44klM6Mu4hAT9TNgwE3mql2n7+PHjIrnfu3UhTOiIg6Olq4eNlY1Z6g/j/BsiUhefg0HXzoSKROGW1zYqIl6Q6kVHxr98GlO0fLZ6ndxSeRjrDRGpyKk/X4a8iKvewk2Q1lw/HfzEL6J1vzxvewDrDRGpxfm/g54/ia3BYqNZt31Cn/iFN+uZO8V7eb4AEalCXGyi7/kwFhtNK1Ihe0Kimf/dqBTvZb0hIlV48SRGT2cHmCxLK7NA/+iU7xJERCoQFhTnmsdWkMblcLOJCE35LA/WGyJSBQxuoiN5NprmxcUmmL3ltAD204iISA6sN0REJAfWGyIikgPrDRERyYH1hoiI5MB6Q0REcmC9ISIiObDeEBGRHFhviIhIDqw3REQkB9YbIiKSA+sNEZHcNm/Z0LBxNWF806aPHzN2CDbu3LlVv2GVixfPC+Ww3hARvbJ128YvZ08VOpUjh3OPj/rlypVbKIfrQxMRvXLjxlWhXzlzuvTuNUgoivWGiDTs+PHD3y2Y/ezZ06JFirdr17l5sza4MSws7LdNP586fdzP77ZLTtdater26T3Y1vbVxXVatanb9cPeKC2HDh9wcHAoW7bipxNnZs+WfeSoARcunMMD9u79Y9nSn8+dO/XTmuW7/zgifZWAgCdduraaNWPee+/VnTptnIWFhbt7ng2/rpk+bY53nQYvXgQuXjL/8pULUVFRVavW7NG9X758Bd75zs3MzB77P1q5cvHJU0ddXXN9+EHPJk1apv7mQ8NCV61eevLEkZdBL0oU92rUqHnLFu2kV9vz5+87ft989+6tQoWKNqjfpGOHD/H6yb8c+ml9+3f57psfypWrOH3GBNzbqGHzr+ZMi4yM8PIqO2jAx6VKlUnjS2UY+2lEpFUoNp9NHdO3z9Cvvvy+du36c+bO2Ld/D27fsnXD+l9Wf9D5oy8+/3bgwI8P/vMXiof0FAsLy982rWvVqsOBfafnfLXw/n2/BQvn4vZv5y/HDhd7/L/3nylerGQqX9TKyurO3Vv47/OZ88uVrRgfH//J6IE+F85+MvLTlSt+dc6Rc8jQno8ePxRp8OVXUxo3bjlj+tdlSpdHK+/Bg3upv/k5c6ZfvXJx5MiJq1duwrv95tsvr1y5iNvxr549Zzre9vqfd/TrO3TT5vULF89L5etaWlpeuXrxr327li5Zi5pqY22T1EhM70ulC+sNEWkVDvYxvGjcqHnVKjU+6t4X++iIiHDc3vn97iuW/1KvbqOKFarUqV2/fr0mp04fS3oWRkJ4PI7ZcVzftk2ngwf/io2NTfsXxROfPHk8feqcWrW8EYpcuuSDooVBUvVqtdCzGjxopKNTjs2b17/zdVCoOrTvgmfhTQ4YMAI1YP+BP1N/8xcunvP2bog3nyuX+4D+wxctXO3i4obbd+3ahlHLyI8nODvnrFSxau+eg7Zt2/jy5YtUvnpkRMTYMVM88uTF123YoBlKXURERMZeKu3YTyMiTUpISLh95yZ6Skm3DBr4sbSBIcjpM8e/mj311m3fuLg43IK9Z9LDihYtkbSd1yMfis3jxw8LFCgk0qxA/kJSgwsuXfbBl8OuWfoU1ahC+cooDGl5nerV3pM20NArVLCI/5NHqb/5smUrbPzt5+DgoPLlKqFxV6J4Ken7gFZej4/6J71sxYpVcePFS+frejd825fOl7+gvb29tJ0tW3Z8DA0NwT8qAy+Vdqw3RKRJMTEx2BXa2Ni+edfyHxbgOB3NqKpVarq7517x46Jdu7cn3Zv8KbZ2dvgYHh4m0sPaxiZpOywsFBWrfsMqyR+AcU9aXidpjy+9k5CQ4NTf/Phx03bs2HTg7z9RdbI5Mm84CQAAEABJREFUZGvf/gPUBtQkvIEfVy7Gf8lfPPVBibl5Cs0tfEsz8FJpx3pDRJpkbW2NneabpSIxMfH3nZs7dezaqmV76RaUhOQPSP6UqMhIfLS1tUv1S4n4hPi33eXi4mpnZ/f5rG+S32hhbiHSICoqKmmchE5gnjx5U3/zjtkdu3fr061r78uXLxw+8vfan3/E0AT9N9StJo1bev/vEMQjj6dIJ7yZrHqpFLHeEJEmodiUKOGFdlbSLT+sWIgj9P79hkVGRrq65pJuxC3Hjh9K/sQLF84mbd+8dQMBRt68+V57cSsr6+joaAwdcC8+vX/vrniLIkWK48vlypU7r8e/O+XH/o9yOKVpfHPz5nW0yMSrYhNx795d7zoNMbx425sPDgnev39Pi+ZtURXwLPx369YN35vXpfcQGhaKvEd6JF7E3/8RMh6Rfln4Um/i+QJEpFVtW3c6ffr4rxvXnvc5s33Hpl82/FSoUBGMe/LnL7h7z45Hjx8i6pjz9YyyZSognAgPD5ee9ez50982rUNcj5x/5x9b6tdvYmPoj6HqXLt2+dz502gfeXmVxVBjz5+/C8PJ0Os3rH7be6hcqVq1arW+/nomHoYvt237b4MGf7Rnz453vnlUslWrl+I9oKr9uGoxPjao3ySVN29pYfnTmuXTZozH4ObFi8C9e/+4ees67sVL9e877OjRg2i7ocF46ZLPjJkTR40ZhFol0i8LX+pNrDdEpFVNm7YaOGDE2p9XjBo9CB8H9B+Ow3/c/tmkL2xtbHv17tS9RzvUg379huHT9h0b+T95jHvRqrpy5WKjJtV79u6E5H/4sLHSq7Vu2QFp/9hxQ2/fuVmqZOnBg0YuX/49gpkZsyb27f1qSRhUoBTfxpeff1u3biM8rF2HRlu2bmjUqHmHDl1Sf+fx8XH29g5ohY0cNaBx0xo+PmcmT/rc0zN/Km8+JDR4xrS5z58/Hf5x347vN92wcc2ggSNbt+ogDOcRLF+67uLF8+07Nh4zbggahrNmzrdJFjKlXRa+1JvM3vYdJCKS060LYddPh9V937gLrrRt37Bjhw97fNRPkHFcOvLSLDGhZiuXN+/i+IaIiOTA8wWIiLLexEkjL1/ySfGuFi3aoVknTA/rDRGZkO1b9wtZjBk1OSY25Zjd3s5emCTWGyKirOfi4irofzG/ISIiObDeEBGRHFhviIhIDqw3REQkB9YbIiKSA+sNERHJgfWGiIjkwHpDRERyYL0hIiI5cH0BIlIFKxsz22xpuiwmqZmllbmVtVmKd3F8Q0Sq4JLb5sGNcEEaF3AvwsnFKsW7WG+ISBWy5bB087AJeREnSMuiwuM9i6e8ICnrDRGphXcH14O/Pha8BqRm7Vv3uHJDZ2ublPtpvL4nEalI6Mu4n2b61WyVK7uzVfacVgkJ3EFpQHR4/MunMZeOvmj4gXu+4nZvexjrDRGpzsk9L/zvRsbHi4hgudtrIcEh2bJnNzc3E7KLiYlJSEiwtbUVWmPvZIFeaIV6zo45UzsHjfWGiOhfO3bssLa2btasmVBCbGyst7f38ePHhU6x3hARibNnz1auXDk0NDR79uxCOY8ePbK3t3d2dhZ6xPMFiMjUnTp1auXKldhQtthA3rx59VpsBOsNEVFUVNSiRYuEOgwcOPD27dtCj1hviMhEoXuGnTs2kJoI1WjZsuXvv/8u9Ij5DRGZqEmTJo0cOdLNzU2QLFhviMjk7N69u3nz5kKtHj16ZGdnlzNnTqEv7KcRkWn58ssvVX6cHRYWNmLECKE7rDdEZCoQ2OBj06ZNW7RoIVSsRIkSderUwShH6Av7aURkEg4ePHjlypWhQ4cKUgjHN0RkEvbs2aOtYrN8+XKhL6w3RKRz+/btw8evvvpKaEpgYODmzZuFjrDeEJFuxcfH16tXr2zZskKDhg0b5uHhIXSE+Q0R6VNAQIClpaWNjU22bNkEqQDHN0SkQ/PmzXv+/LmLi4umi82hQ4dWrFgh9IL1hoj05saNG+hElS5dWmict7c36k1cnE6usc1+GhHpx+3btxMSElBsHBwchC5ER0ebm5tbWVkJ7eP4hoh04sGDB5MmTSpatKhuig0gggoPDxe6wHpDRHqAccCLFy82bNhgZqbApaCNx8LCYuzYsefPnxfax3pDRNqGUKBHjx5oOpUvX17oUb9+/c6ePSu0j/kNEWnbsmXL6tSp4+XlJUjdWG+ISKt27NjRpk0bYQKuXr1qY2NTpEgRoWXspxGRJm3ZsuXevXvCNGTLlg0pjtA4jm+ISGMSEhKQ1vj4+FSoUEGYjF27dlWsWDFPnjxCs1hviEhjpk2bNnLkyBw5cgjSFPbTiEhjzp07FxERIUzM+fPn9+zZI7SM9YaINGbx4sW5cuUSJubOnTtan4XDfhoRkQbcvXs3KCgIEY7QLI5viEhjhgwZ8vTpU2FiChUqpOliI1hviEhzHj58qJslk9OO+Q0RkdyY32gU8xsiIg1gfkNEJDfmNxrFekNEGsP8RqNYb4hIY5jfaBTzGyIiDWB+Q0QkN+Y3GsV6Q0Qaw/xGo1hviEhjmN9oFPMbIiINYH5DRCQ35jcaxfENEWlD48aNLSwszMzMAgMDnZycpG001n766SdhAtBMCwgIaNasmdAsjm+ISBtsbW2fP3/+7NmzhISEly9fYjskJKRJkybCNOggv7EURERaUKpUqYcPH2JYk3RLwYIFO3ToIExDpUqVChcuLLSM9YaItKF79+7Xrl3z9/eXPrWxsWnZsqWdnZ0wDchvhMaxn0ZE2lCuXLmSJUsmfZovX7527doJk8H5N0RE8unWrZuLiws2LC0tW7RoYW9vL0yGDvIb1hsi0owKFSqUKVMGG3nz5n3//feFKUF+o+mT0wTzGyJKr8QEEfIiViikQ+vuvlcetm7WMSbcMiZcmbdh52BhbSf3wboO8hvOvyGitLp/I+L830EPb0a457eLCDW5FcySGPaaieW9c1Som0PIRQfzbzi+IaI0uekTfuFQUM1WuRp8aCVMXujL2Bsngw9uflavo5uQBfIbX19fTdcbjm+I6N18z4VdPRnSsKuHoGQu/PMiJjKuwQdyLB6qg/XTWG+I6B2wk9iy6FGTj/IKesPxnU/L1HT0KGwr6F14fhoRvUOgf0xUeLyglFhYmD17GCWMj/NviEj/ggNjPQqb0EyXdHHJaxseIkcx5vppRKR/CXEJpnw2WuriYhJiIhOE8XH9NCIikgPXTyMiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjkwvyEiIjnoIL9hvSEio/v74F/1G1YJCnqJ7bbtG65Zu0JQOiG/0fTF1gTzGyKS2QedP/IqVVZQOukgv2G9ISJZdf2wl6D0QzMtICBA00Mc1hsiMoqly77b+9cf9nb2DRs28/QskHQ7+mkdO3zY46N+2N6y9dcTJw5fu3bZ2samfLlKffsOzevhKT1sx++bN25cGxIaUqNG7b69h3Tp2mrypM8bNmi6ddvGtT+v+Hb+8qnTx/n53SlcuOj7nbo1a9paetbRo//8tGb5vft3nZxyFC1a4uPh493dc+P20LDQVauXnjxx5GXQixLFvRo1at6yRTvpKXv+/B1f6+7dW4UKFW1Qvwnem5mZmVAf5De+vr6arjfMb4go623fsWn7jt8+HjF+8eI1efLkXbP2hzcfc+mSz4KFc0uXLj9jxtcTxk9/+fLF519Mlu66dv3KN99+Wbduo7U/bann3WjGrIm40dz81f7KysoqLCz0+wVzxo7+7MC+03W9G82ZOyMg4AnuOnP25JRpY5s0ablxw66pn30VEOD/7fdfSS84Z870q1cujhw5cfXKTaVKlcGLX7lyEbfv279n9pzpxYuVXP/zjn59h27avH7h4nlClXSQ37DeEFHW27J1AypBXe+GjtkdMfioVLHqm4/x8iq76seN3br2rlihStUqNTq/3x0DneCQYNy1d+/OnDldevcahGFKrVreuDf5E2NjY3v2GICnYyDStEmrxMTEW7du4PaVq5Z412nQqWNXPKt06XJDBo86ceLI9RtXcdeFi+e8vRvidXLlch/Qf/iihatdXNxw+65d28qVqzjy4wnOzjnxJnv3HLRt20ZUPqE+yG8qVqwotIz1hoiyGArAo0cPChb8bzJ88eKl3nyYhYXF48cPJ376cas2des3rPLp5E9wY5BhX3/n7i2MQiwt/234e9dp+NpzS5YsLW1kz+6IjxjxvHrWnZtJtwP6Zvh4/foVfCxbtsLG335esvTbY8cOoVyVKF4qd+48CQkJl69cqFqlZtJTKlasihsvXlLjacc6mH/D/IaIslhkZGR8fLydnX3SLba2dm8+DFnL5CmjMb4ZOODjIkWKoRs2bvww6S7Uj1y5cic9EuOV1577ZsQSFhYWHR1tY2ObdIu9/as3EBERjo/jx03bsWPTgb//RNXJ5pCtffsPenzUPy4uDrXnx5WL8V/yl1Ln+EYH+Q3rDRFlMTs7O4xdoqOjkm6JjIx482E7d23FsAOpifSpNEaRoGygFCR9GvjiuXgXW9tXlSYqKjLplnBDpXHJ6YqPaOt179YHte3y5QuHj/y99ucfs2XLjg4ealKTxi3Rakv+Uh55PIX6cP00IqLXYfDh7p7nVSD//r+3nDh55M2HhYQE53bPk/Tp4cMHkrbz5s138+b1pE+PHj0o3gXNN3TJpLMAJNJ24SLFkAnt37+nRfO2qEmocPgPeY+v4fWLFCkeGhaKAEl6CoY7/v6PkPEI9eH6aUREKahfr/Ghwwf+PvgXtn/Z8NPVq5fefEzRIsVPnzlx3ucM+lq/bVon3fgkwB8f36tV9969u+t/WY0oCI+5dMknLV+0fbsPjhw9uHnzLyGhIXjZxUvmV6pYtVjREpYWlj+tWT5txngMbl68CNy794+bt66XLVMBT+nfdxiK2a7d2xHb4KvMmDlx1JhBMTExQn24fhoRUQq6d+vbskW7BQvn1m9Y5fiJw0MGjxKG8wiSP6ZPnyHVq9Wa/NmoJs1qBgQ8mTB+eskSXhMmjti3f493nQbt23VGkWjfsfHWbb/26/cq17Gyskr9izZp0rJvnyG//ra2bbsGs+dMK1e24pTPvsTtDg4OM6bNff786fCP+3Z8v+mGjWsGDRzZulUHYTiPYPnSdRcvnscXGjNuSHh42KyZ821sbIT66GD9NLPXfgOIiF5z83yo7/lw7465hVww4vHzu1O0aHHp02vXrwwZ2vOHZeuTblGPG2eCw17E1HvfTRjZ3bt3g4KCNH1KNPMbIlKdS5d9Ro0e1K7t+x907vHixfPvF8wpXbpckSLFhAnj+mlERFkPAf7oUZN279nRp1/nbNmyV6lcY9CgkepcZkY2XD+NiMgoWrVsj/8E/T/OvyEiIjlw/g0R6V9oaKhI5LmsCuP8GyLSpwcPHjx79gwb48aNW7BgQT1Jef8AABAASURBVKLgiawK4/wbItKPGzdu+Pn5YWPGjBkjRowICwvD9ujRoz/99FMTz+rVQAfzb9hPIzJp2IVZWlqWLVv2m2++OXPmzMSJr64088knn2TPnl16gLu7e8jjUEFKY35DRBoTHx9/8uTJuLg4b2/vNWvWHD58ePDgwbh92LBhSRP4k4oNqQfzGyLSgNjY2L/++mvr1q3Y3r9//6+//iot2dKjR48ffvgBB84iDavFkLKY3xCRSmEEs2PHjhUrVmD72rVrBw4cQGdMvFpkrMl3331XvXp1QZrC/IaIVCQxMXHDhg3YMU2aNOn58+cXLlyoW7cubi9nIEjLmN8QkfLWr19//Pjxb7/9NiEh4fHjxwhmcGPu3Lk/++wzQXrB/IaI5Iaigo/IYPr27evv/+pqMVFRUV27drWwsEAGM3r06Dp16ogsZWFl7uDIY9OUWVmb2zpYCONjfkNEcoiOjsbHzZs3o65cvnxZGK7ZPGLEiDx5Xl0fs0+fPjVr1hRGk8PV6uHNCEEpefYwysFJjnqjg/yG9YZIpUJCQvBx586d7dq1O3HihDBMhZk2bZqUxLRp06Z8+fJCFjlzW2N8kxAv6E3xcQnu+W2F8SG/0fRinYLXWyNSlYCAABSVAwcOzJ49e+jQoSgqGM04OzvnzZtXKMrvasTpvS+a9fYUlMzpPc+s7cxqt3EVlAasN0RKQhhz//79ggULHjt2bNy4cYMHD+7WrZufn1/27NldXFyEmjy6HfXP5mc1WuRydLGysTfp1khCfGKgf7Tv2WCX3FZVm+QUstDB9W9Yb4jkFhYWdvv2bXTDMHbpYzBo0KCnT586OTlJ0zBV69mj6PMHgu7dCLfPbhn2MlaoEnZp2K2Zm791wbe4uDgLC4vMrAhnbWueLYdl+To5ileWbyEGpHe+vr7SgkMaxXpDJIdnz55du3bN29v7wYMHH330ESKZkSNHovBky5ZNaFBMVKKaF/Bs3rz5b7/9luL39u7du/jOx8TE5MmTp23btuhYZqDwWFmbCdn/+XjnQUFBFStWFJrFekNkLGiUnT17tn379uHh4Z06dapXr9748eOxp7O2thZkTCjt5ubmJUqUSPFe/Cyw70Yn09bW1s3NrUWLFh06dMiVK5cgI2O9IcpKaJSdOnUKuzA0x7p3716qVKlJkyZh14bdnyB1mDBhwt69e5N+Ivjp5M2bF+OGGTNmCBXTQX7DvwGizEJXfcWKFdKVY5YvX/748WMcOGP7559/RrHBBouN/PCDQOFP8a4qVapYWv43fRU/HX9//wMHDgh14/ppRCbq5s2be/bsqVWrVuXKlXfv3o2c39X11Umxs2fPFqQCNWrU+Pbbb6tVq/bmXeizubi4SFcvFYbxjbu7O36IQt10sH4a+2lEaXXr1q3NmzeXLVsW7bL169fHxcUhcEbfTJAqRURE4DjAwuL1yf/4wSGwwTBUGIrNuXPnBMmCw3yi1CBYnjp16urVq6XtIkWKYEyD7a5du/bo0YPFRs1QaSIjI9+8Hc20/PnzS+cLoNjg57tv3z6helw/jUiHHj16NGbMmC+++ALbL1++RE+mffv22G7cuHGnTp1y5MghSAswuGndunVoaAoXw0YX1M7O7siRI9iePn06xjrPnz8X6qaD/Ib9NDJ18fHxOBAODAycMmUKPl20aBHGMffu3atataqDg4MgLduxYwdGM+h/Cu3j/BsiTQoPD0ctiYqKGjx4cFhY2G+//YZ6g3gGh73Jz1wi04FBLQ44fvzxR0FGw3pDpiIgICBnzpxWVlbdu3d/9uzZn3/+GR0d7evrW7ZsWUH6deLEibx58+bLl++dj7x27ZqPj8+HH34oVInzb4hUDS2I4OBgbAwYMKBv376xsa+W/Jo5cyaKjTD091lsdA85zbRp09LyyFKlSqm22AjmN0QqdOXKFUT6OKQdPXr0/fv3Fy5c6O7ujjRYmh9DJmjfvn3olDo7O6flwQsWLMCDpbMQVYX5DZHypCkU2bJlK1my5IwZM3AYOHXq1EKFCml3NUxS1ldffdWjRw8PDw9BWYr1hjQJ0Qv68tbW1jVr1lyyZMmFCxdGjBjh5eUlnWwmiP4XBruff/65tM6QRjG/IZIPasyePXt27tyJbWzs2LHD3t4e24MHD166dCmKjTBM8RNEbyhWrNjPP/+c9sf7+/tPnz5dqAnzGyLjQo35448/kPn37t0bAxoUm/bt26O9LojSAzu6ly9f5syZjmtxnjp16vTp00OHDhXqwPyGKOvFxcVt2LABB5hjx469ffv2xo0bGzVqVLVqVUGUCVFRUZYGghTCfhqpxbJly0aOHCkMkzGfP39et25dbBcpUmTixIksNpR5N27cGDhwoEindevWXbp0SagA108jyiAE+/i4cuXKXr16hYWFCcNlSHr06IENJycnFJ4UV5InyrDy5cvny5fv3r176XpWt27dVqxY8eDBA6E05jdE6SBdSvmnn35CDDN37tyCBQtu2bKlRIkSpUuXFkSUKh3kNxzfkHFJq/P+8ssvrVq1kvoSKDNz5szBR2x36NCBxYbktGvXLmmZiXRBgxejHKGoQoUKabrYCNYbMoanT5/i47Zt2+rXr3/69Glse3l54c9VOq8MwQz+cgSREtBPW7NmjUgnV1fXYsWKKXuGNPMboldwwIjmsjAsHFKjRo1jx45hu1y5cjt27GjQoIEwtM5z584tiJTWp0+fjF0lD8dJU6dOFcphfkMk/Pz8RowY0aVLl65duwYEBLi4uPCUU9Krv//+29PTE2MdITvOvyF6NV0GNL1SCJmUTZs2oWBgzC3Sb8qUKRjB6+MCbvJjP40yC6MZFhvSkIsXLz569EhkSNOmTUuVKiWUwPyG6FWHYebMmYJIIzp27JixwQ289957Sp3tooP8hn12yqzY2NjIyEhBpBEZLjbCsFBswYIFS5YsKWRXqVKlwoULCy1jvaHMatCggbe3tyDSiMzkN8eOHUtISFCk3uhgFgH7aZRZzG9IW5jfKIX1hjKL+Q1pC/MbpbCfRpnF/Ia0hfmNUlhvKLOY35C2ML9RCvtplFnMb0hbmN8ohfWGMov5DWkL8xulsJ9GmcX8hrSF+Y1SWG8os5jfkLYwv1EK+2mUWcxvSFuY3yiF9YYyi/kNaQvzG6Wwn0aZxfyGtIX5jVJYbyizmN+QtjC/UQrrDWVQ//79z5w5Y2ZmJn2KjcTERA8Pj507dwoiFUN+Y29vn7F6g/wGv+RCCWimBQQENGvWTGgW8xvKoN69e+fMmdP8/6He4GOdOnUEkboxv1EK6w1lUK1atYoXL578Fk9Pzw8//FAQqRuKTd68eUWGIL+5fv26UALyG00PbgTrDWXGRx995OTklPRpjRo18ufPL4jUDfnNhQsXRIYgv8E4QygB46qKFSsKLWO9oYzDEAe5q7TNwQ1pBeffKIX1hjKlZ8+e0hCnZs2aBQoUEESqx/xGKTw/jTIFZQZDnIcPH3JwQ1rB+TdKeXUOqyDVCw+JP/3ni0e3IxMSRERIrFCThAT8EiVYWFgIlcmZ28bWwcKrumORcg6C6P9lZv7NlClTkFO2aNFCUPpxfKMBgf4x25Y8qt4iV5EKTtlyWPEIIY3i4hKeP4zyPR8W/Dy2UoMcgsiA82+UwvGN2vnfjfr7t2etB+YTlFEn/nhmn83svTaugkiICxcuuLq6ZviUaKVs3rzZ19d34sSJQrNYb9Ru6+LH3h1zW9vyzI5MOf770zI1HT2KcB1ryhQF85u7d+8GBQVp+pRo7sVU7cWTmPCQOBabzLPNZvnodoQg4vwb5XBHpmovAmLyFWPWnQVyedpEhCUIIs6/UQ7rjarFxiREhscLyrT4eBH2Ul3n9ZFSOP9GKTw/jYhMC+ffKIX1hohMC69/oxT204jItDC/UQrrDRGZFuY3SmE/jYhMC/MbpbDeEJFpYX6jFPbTiMi0ML9RCusNEZkW5jdKYT+NiEwL8xulsN4QkWlhfqMU9tOIyLQwv1EK6w0RmRbmN0phvdG5vw/+Vb9hlaCgl+l6VkRExBdfTWnZ2nvc+GFCBT7/YvLwj/sKoqyAYpPhi61hhHH9+nWhBOQ3mr64p2C9oRRduuzz11+7evcaNKD/CHw6fcaEXbu3C+Mw6osTvYnXv1EK6w2lICIiHB8bNWxetGhxbNy4cVUYjVFfnOhNzG+UwvPTdGjpsu/2/vWHvZ19w4bNPD0LJN3etn3DHt37HTpy4OLF89u3HTA3M/9t08+nTh/387vtktO1Vq26fXoPtrW1XfHjonXrV+Hx7Ts2rlqlxukzJ7A99+uZS5Z+8/v2g6l83VZt6nb9sDfqx6HDBxwcHMqWrfjpxJnZs2UXry6Fe3vH75vOnT/95MnjggUKt2jRrm2bTrgdvb7XXvz48cPfLZj97NnTokWKt2vXuXmzNtKLW1la+fic/fzLyegN4q7hw8d5lSojiNIP+Y2rq6vIEOQ3QiEYV/n6+mq6pcZ6ozfbd2zavuO3CeOnV6xY9dixf9as/SHpLisrq527tlaqVO2j7v1Qjdb/shr/Tfp0lpNTjrCw0AUL51pYWAwcMKJf36FFihSfMXPi1s1/5cjhHB0d3azFe2PHfNaiedvUv7SFheVvm9ahxkybOvvatcuff/kZXvPTCTNw16LF81BpRo2aZGZmdv++33ffz3Z3z1Oj+nt7dh1N/uIoNp9NHTN+3DR83evXr8yZO8PKyrpRw1d/YAFPn6Bi4cUTEhIWL5k/9+sZK1f8ilcTROnE+TdKYb3Rmy1bN9T1blTXuyG2mzVtjf3+w4f3pbuwd3Z0dBo+dIz0aef3u+NhBQr8e7LN5csXTp0+hnojMgEjDwyJsOHlVRYjGAyVxo7+DHXus8++RI8uT24P3FWxQpU9e3bga6HevPb0VauXetdp0LhRc2zjdcLDw6TOHjx7FrB0yVpptNShfZev580KCQlGpRRE6cT5N0phvdGVxMTER48eJPWgoHjx/+k1lyjulbSNMnD6zPGvZk+9dds3Li4Otzg75xSZU7RoiaTtvB75YmNjHz9++KqkJSZu2bLh5KmjDx7ck+7Nk+f1E4TwZ3z7zs1GhmIjGTTw46RtDLmkYgNOjq/KTFRUlJOTIEqv27dvZ8+ePWP1pmXLlu7u7kIJyG8CAgLYTyO1iIyMjI+Pt7OzT7rF1tYu+QOsra2Ttpf/sGDXrm0DB35ctUpNd/fcGItk/jwxGxvb/7603asvjTEKCsmETz+OjY3p329YhQpVUDZSPLkZ9QOPTP4KyVla/ve7yjYaZQZ22RnOb6pXry4UwvyG1MXOzg4ZTHR0VNItkZERKT4SI6Hfd27u1LFrq5btpVsQ4YhMQ3VJ2o6KjBSGgud78zrCmK/nLq5cqVrS13JzzfXac21sbMzNzZO/ApExML9RCs+H1hUc+COHv3LlYtItJ04eSfGR6HRhMOT6/zv9mJiYY8cPiUy7cOFs0vbUiFSIAAAQAElEQVTNWzcwKMmbN19wcBA+TSowfn538N+bz0WlLFHC69Jln6RbflixcNHi+YIoS3H+jVJYb/Smfr3Ghw4f+PvgX9j+ZcNPV69eSvFhaKzlz19w954djx4/RD2Y8/WMsmUqhIaGhIeHv/ZIDDvc3HKdOXPivM8ZKeZJxbPnT3/btA49vfv3/Xb+saV+/SZ4esEChVF4ft24NiQ0BLcvWDi3apUaTwL833zxtq07nT59HI/Ep9t3bML7L1SoiCDKUpx/oxTWG73p3q1vyxbtsE+v37DK8ROHhwweJQzdszcf+dmkL2xtbHv17tS9Rzt0uvr1G4ZP23ds5P/k8WuP7Na1z7nzpz+bMjoyKjL1r47uHEZXjZpU79m7U4H8hYYPG4sbEQ5N+nTW1WuX2rZr8OnkT/r1HdqmTadr1y7jMa+9eNOmrQYOGLH25xWjRg/CxwH9h7/zJGyi9OL6aUoxS3FPRCpx7XTIvWtR77XNJbSgbfuGHTt82OOjfkJ97l8P97sc0rJvHkGUCQrmN3fv3g0KCtJ0S43nCxCRaeH8G6Ww3lA6tG5T7213jR8/TRBpAfIbe3v7jNUb5DceHh5CCZx/Q6Zl/frf33aXna3d9q37BZHqcf00pbDeUDokzfAn0i7Ov1EK6w0RmRbmN0rh+dBEZFo4/0YprDdEZFo4/0Yp7KcRkWlhfqMUjm/IVDx89GjXrl1ovgsybVw/TSmsN2QqsmfLduLEiRcvXmB7xYoVly9fFmSSmN8ohfWGTIWTk9OMGTOkiRcWFhYLFizARnBw8M6dO0NCQgSZDOY3SmG9IVPUu3fvZcuWiVeX57E9c+bM+PHjsf3w4UMfHx9BeodikzdvXpEhGGFcv35dKAH5jaYnewqeL6By5uZmNvY8JsgCFhZm9tlT+G23sbGZNm2atG1ubr5w4cJ8+fJNnTrVz88ve/bsLi4ugnSH82+Uwn2Zqjm5WD17ECUo04KexVjbvuMq1B4eHsh1Jk6ciO1nz55169Zt8+bNwjDuEaQjzG+Uwnqjajnz2FhYmgnKtOjI+Fz5bNPySGtra3ysWrUq/rbr1asnDIe0tWvXPnfuHLaDgoIEaRzzG6Xw+jdqd/FQ8GO/aK1cAkedHvqGXzsZ1GFYBlv2EB0djUrj7u4+ZcoUX1/f7777DtuCTA+vf5MZrDcacAEl525U9eZuVjYcj6YPfrvvXgq9fSGk/ZC8Zln0zbt9+3aOHDkQ7bRr1w6Hul9//TWCHzMzDkM1IzP5DQ44atSo0aJFC0Hpx/MFNKC8t5OVjdm+nx+Hh8a55LZBa0hkTmxcrJWlldA7lOeHtyLK1cqRmZHNm4oUKSJtbNmy5ejRowkGXbp0QWd/wIABglSP179RCsc3mpGQIMKD48KC4jL5I1u3bl316tWLFi0q9M7a1sLVw1rI4t69excuXGjTpg1GP+i2YejToEEDQaqEn5Srq2uGT4lWyubNm9HLlc5n0SjWG5ODoyStr4qhcseOHXv48GHnzp2xgQFQhw4dkoZEpHXMbzKDeYAJmTVrFj6y2BhbrVq1UGyE4VtdoECBs2fPYvvPP/9cv349FzJQA66fphTWG1MxevTo/v37C5KRnZ1dZwNslylT5smTJ4cPH8b2zp07scHWglI4/0Yp7KfpX3h4uIODQ1hYWLZs2QSpwKlTp3755ZcPPvigRo0aGPcUK1ZM6+vMawvzG6VwfKNzgYGB0uJgLDbqUa1atW+++QbFRhgmkE6YMMHf3x/bR44ciY2NFWRkXD9NKaw3OvfDDz8sXLhQkFphlLNx48ZcuV7N58VYRzqrLSoq6vbt24KMg/mNUthP0y2eh6ZdERERffr0cXFxWbRoEQZAyIFsbGwEZZHMzNk8evSoh4eHIkva6GD+Dcc3+nT58uXdu3cL0iZ7e/sNGzbMmDFDGDqiDRs2XLJkiTBcrUdQpnH9NKWw3ugTcsVPP/1UkJZJV0MoUqQIcp2mTZti+9y5czi8PXDgALaZ9GQY8xulsN7ozbp16/CxQ4cOgnREOoGtfv36+PnmyZNHGC6J3bdvXxxYCEon5jdK4fppunLo0KGEhARB+uVigI3Bgwdjpynlr5MmTTI3Nx8zZoyTk5Ogd+H6aUqxSLq4IenAixcvpMYLmYLcuXO7urpio2bNmjjOyJEjh6Oj47hx43AAjgNhVCBBKcmZMyfGi/heifTLnz+/s7OzUAKGVleuXKlTp47QLNYbnRg1ahQqjdRpIVNjZWVVrFgxaQeKrsu9e/dKlixpbW2NcQ/qEFdvew3qdMaKjTDkN3FxcVKZl5mdnZ2np6em/8Z5BKQHv//+e6dOnQSREEWLFu3fv780vbdu3brSGU2PHz9esmTJrVu3BDG/UQ7rjeZFRUXVqFGjVq1aguh/NWnSBO01bOB43MbGBvtZbF+9ehUHKOHh4cJUcf00pXC+p7Y1aNBg//79vLgkpd2zZ88WL16MhtInn3yCXRj2AJUqVRKmhOunKYX1RqvQl8fharNmzTLciSZC/vzdd9+h7datWzcfHx8PDw9pZR16G17/JjPYT9MkBMIvXrzo3Lkziw1lRunSpZcvX96lSxdso8XUq1evM2fOYPvGjRtCv5jfKIX1RnuCg4NHjRqlyBkypEsWFhb42LJly127dknhxI4dO957772nT58KQ/9N6AvzG6Wwn6YxiHkvX75cvXp1QWRM0dHR8fHx9vb2Xbt2xcavv/6Kj1Jl0jrmN0phvdESHH5mZuknooy5fft2kSJFIiMj69ev37ZtW+zyYmJirK2thelhfpMZ7Kdphr+//8mTJ1lsSH7SjFE7O7ujR482atRIGPZ9nTp12r59u9Ag5jdKYb3RhsePH6O/MX36dEGkHPTTqlatio0SJUp8/fXXOXLkwPbOnTuHDx/u4+MjNIL5jVK4XqcGoI2G8TsvcU+qUtAAG61atXJxcQkJCRGG5cmbNWsmrSiqWh07dszw6TbvvfeeUAhq5L1794SWcXyjAfgbRlQriNSqZs2a3t7e2Lh06ZJ0RrWaafT6N6VLl9b6MiIc32iAdEkbIvXr2rWr+meMIr8pVqxYxq5HgPwmISFBkfMFlLquaBbi+EYDYmNjeRohaUK5cuVy584t1I35jVJYbzSgV69evIwjacKGDRuwNxfqhvwmY4MbYchvlBpn3LlzR1rtW7tYbzTA2tqa184iTUB+4+/vL9RNo/lNpUqVNH1xT8H8RhNWrVoliLTggw8+YH5jJMxvSA7Mb0grmN8YD/MbkgPzG9IK5jfGw/yG5MD8hrSC+Y3xML8hOTC/Ia1gfmM8zG9IDsxvSCuY3xgP8xuSA/Mb0grmN8bD/IbkwPyGtIL5jfEwvyE5ML8hrWB+YzzMb0gOzG9IK5jfGA/zG5ID8xvSCuY3xsP8huTA/Ia0gvmN8TC/ISPCr5eZmRk6afjYpUsX3BIfH1+7du2FCxcKIlVifmM8zG/IiKpUqYJig5GN2f/DX3Lfvn0FkVoxvzEe5jdkRO+//76zs3PyW8qWLVuxYkVBpFbMb4yH+Q0ZUePGjQsWLJj0qYuLS/fu3QWRijG/MR4d5DesN6qG2MbBwUHa9vLy4uCGVA75TYaHDrJBfnPhwgWRIchvMM4QSsC4Sut7ANYbVUsa4ri6uvbs2VMQqRvzG+NhfkNGhx6anZ0dBjcVKlQQROrG/MZ4dJDfmOly4nrg4xjf86FhQXEhgbFC++4/eODm5mZnays0LruLlZWVmUdhuxJVsgvSo0mTJnl7e2MQIHQKIwy0HBQ5H/ru3btBQUGabqnpcP7NtZMh18+E5SpgV6C0oz5mSZYXLkIXLCzNA/2jnj6OvbLoUfshec3MBOkM598Yjw7m3+it3lw+HnLvemSj7h6CVMk1rw0++l0J27bkVckRpC/Ib4TqoeNnb2+fsXqDoZuHhzK7FzTTAgICNH2Kmq7ym0D/mFs+Yd4d3AWpW8HS2fKXyn581wtB+sL8xng4/0ZdbvqEuebVfMhhIjyL2l87FSxIXzj/xni4fpq6hAXF5SvBIFob7B0tHV2sIkPj7bJbCNIL5jfGw/XT1CXkRaw5913ageOD2Fhe10dXOP/GeDj/hojoP8xvjIf5DRHRf5jfGA/zGyKi/zC/MR7mN0RE/2F+YzzMb4iI/sP8xniY3xAR/Yf5jfEwvyEi+g/zG+NhfkNE9B/mN8bD/IaI6D/Mb4yH+Q0R0X+Y3xgP8xsiov8wvzEe5jdERP9hfmM8zG/0pnffzt9+95XIqM1bNjRqUl3abtu+4Zq1K4TJyOS3jvSB+Y3xML+ht/qg80flymb8SuPtOzZ+7J/BQzAipTC/MR7mN/RWXT/sJTLqyRP/oKCXgkhrmN8YD/MbzfPzuzNo8EfNW9aeOGnktWuXk26/dv1K/YZV8DHplu4ftVu85BtsbPzt53YdGh05crBDpyYNGlXt3qP93r1/vPnKyftp9+/7ffxJf7xgt+5tly77LiYmRrp9y9Zfx40f1rpNvY7vN50xc+Kjxw9x43mfMx92a40NPHjylNHYiIuLW7b8ezSsWrb2Hj9xxIkTR0QaXL16acDAbi1a1cFTrly5OPzjvt98+yVu3/DrGvx7kx4WEPAEb+zo0X9SeUvC0CrELUeOHmzYuNqCRV+n8q0jU8b8xniY32hbbGzs+InD3dzcV6/cNLD/COyIAwOfv/NZFhaW4eFh+w/sWbd2+7at+xs2aPrVnGkPHtx72+MxWBk2vHfZMhXmfb3kgw964InfL5gjXnUefBYsnFu6dPkZM76eMH76y5cvPv9iMm6vWKHKl59/i411P2+fNWMeNvD4TZvXt2/3wfp1v9f1bjh1+rh/Du1P/U1GRUV9OvkTZ+ecK1ds7NtnyKIl8589CzAzM0v9WW97S2BtbR0REb5jx6aJE2a0b9s5Y9860j3mN8ajg/zGpPtphw4fePo04LtvVri7vzoiGzF83PsfNE/LEzHg6NC+ix0Iu149B27ZsmH/gT979RyQ4oNRKmxsbXv3GmRhYVGpYlXsuG/cuIrbvbzKrvpxo6dnfkvLVz+FuNhYVIjgkGAnR6fkT4+Ojv5z705059q07ohPWzRve/nyhTVrf0DhSeUdnjh5JDg4aOCAj3PnzoP/+vcbNmr0IPEuqbwl1CrUsC5deuKfgLvw783Yt470DfmNs7MzRjlCxTJcbIQhvylYsKAi/TTkN4ULFxZaZtL15tGjB7a2ttgdS5+6uLjmyuWexucWL/7vmBo7Yg8Pz/v3777tkXfu3CxWrCSKjfRps6at8Z94NU6yePz44aLF865dvxweHi7dG/TyxWv1xtf3GvpvVavUTLqlQvnKu/fseLMyJXf37q1s2bIVLlxU+hRjpuzZHcW7vPMtlSxRWtrIzLeOdEz3+c21a9dwNMb8JmNMut6EhATb2dknv8XGxjaNz7Wxsflv29YWHba3PRJ35cjh/ObtiEwQz3Tr2hujkCJFip05kfn/1gAAEABJREFUexLByZsPCwsLxUekL6/d/vJFYCr1JjQs1N7eIfktKb6H9L4lDM6kjcx860jHVD6ykaDjZ29vn7F6U61aNQ8PD6EENNMCAgI0fYqaSdcbR0enyMiI5Lcgonjbg+Pi45J/isN/B4d/d+jRUVHOOXK+7YkODtnCU3rZnbu2li1boV/fodKnUl15k4urGz6OHjUpb958yW/PlSu1VNbWxjbprARJYOCzFB8ZnxCf3rck0vmtI9OB/MbLy0vlVQf5jaurq8gQ5DdCIchvfH19NV1vTPp8gdzueZBJ3LlzS/r01i3f58//3SnbWL8aviTtUsPCwpLukpz3OS1tIF+5/8CvUKEib/sqJUp4XblyAZGP9CmSjzFjh8THx2OI4Ob6X+fh8OEDKT7dM29+aSyFnpj0X8EChQvkL4QDNPF2KE5BaIS9CPz/d3smIuLff4uVlTXec9L7uX/vv05gGt+SSPVbR6aM82+MRwfzb0y63tSqVRcNoq/nz8KuE7vLGbMmOv5/hypfvgLZs2XftXt7YmIids1fzZmaPP8wNzffsmXD/ft+KBsrVy3B7rthg7f+HrRs0Q5DjfnffIH21OEjf/+wYgGGLEhKihYpfvrMCVQCvP5vm9ZJD34S8OpvNV/+gvh48OBfV69dRl3p1XPgmrU/XLrkg9f559D+MeOGvHMmf43qtfElFiyci3HYw0cP1q5d4eb2byHx8iqLf9SeP38XhpOh129YnfSsVN5S2r91ZMqQ32QmjZcH8psLFy6IDDl27BjGGUIJyG8qVsz4FHI1MOl6g0T9i8+/jY+La9Wmbq8+nTp17FqgwL+JnJWV1WeffXn9+pUGjap+2K11vbqN8+TJi920dK+ZmVnn97uPGjOoUZPqv+/cPGHcNNSnt30VT8/8X335vY/PmbHjhn7+xeTq1d4bNnQMbu/TZ0j1arUmfzaqSbOa2O9PGD+9ZAmvCRNH7Nu/J6+HZ7OmrVetXvrDDwvwyC4f9Bg7ZgoKQ+u29b77frZHHs/Royen/k9DgP/JyIkXLp7r+H6T2XOmde3aG3GLpaUV7ipVsvTgQSOXL/++fsMqqBN9ew/BjdI/LZW3lPZvHZkyzr8xHh3MvzFL2ofqwJZFj8rWzpm7oJ0wps1bNixeMn//X6eEuj16/BBjMkfDsAw/ZRSGPr0Gd+z4oVCNzd/7dRjq6ZiTi1zohybyGwxukN9kuKWmlM2bNyO/mThxotAs/qnrU3Bw0JChPdEf69t3qLNzzh9/XGRuZl6vXmNBZEycf2M8nH9Diln/y+pfflmd4l0FChZe+P3Kr7747ocVC6dMHRMTHV2qVJlFC1ejySaIjInrpxmPDubfsJ+mVREREa+dkZzE0tLSySmHUD3200gRU6ZMqVGjRosWLUT6HT161MPDQ5FdP+ffkGLsDQSRmnD+jfFw/g0R0X84/8Z4eP0bIqL/ML8xHl7/hojoP5x/Yzy8/g0R0X94/Rvj0cH1b1hviCjLML8xHuY3RET/YX5jPMxviIj+w/zGeJjfEBH9h/mN8TC/URdLK3MzMzNBGmFjY8Gfls4wvzEe5jfqYmtvHh4ci/8XpAUvnkY75GCCqCvMb4yH+Y26uOe3DXkRK0gLQl/E5sxjfv78WUE6wvzGeJjfqEt5b6frp4KiIxMEqd7pP58XLC+WL1++ZMkSfHrjxo3IyEhBGsf8xniY36hOlzH5969/HPYyTpCK/fPbk+KVs9VsVHjZsmX9+vUThr+lJk2aHD9+HNvPnz8XpE3Mb4xHB/mNrq5HIAkLitu7LiAqPD5PYft41h01QcAWcC/S0tqsSFmHMrWc3nxAYGCgi4vLjBkzsNtatGiR+pMAeg0GN/ipqbyllpn8JjPXMiAd1hvJ80fRgU9ioiPihZGFhoauXLly+PDh5uY8ufwdLKzMnFysXT1sbB3e8b26e/euo6Mjak/Xrl2xa5g6dSq/vZRVeP0bpei23sgD3z38/tWuXVuQcYSHhx88eBAhbWxs7NixY1u2bNm8eXNBaqWJ699cuHDB1dU1wy01pWzevNnX13fixIlCs3jMmHEff/wx6g2LjVE5ODigxlhaWtrZ2XXv3v3Bgwe48datW4sXL753754glWF+Yzw6yG9YbzJo4cKFH3zwAZs8ckIPZMCAAdjw9PS0tbX9/fffsX3u3LkDBw4kJPCkRFXAH0WGT/2SDfIbDHFEhhw7duzOnTtCCWjiVaxYUWiZxbRp0wSlB/Zu+MHjj0oH0680CsMd/OFVq1YN2+izrV+/3s/Pr3Llyj4+PrglW7ZsghTi7u6u/u8/mn5OTk7IBUX6WVtbFy5c2NnZWcgO+Q3KZNGiRYVm8fA8fTZu3HjlyhXxai0WG0EqkD9//jlz5kjjnhcvXvTr1+/IkSPYZrdNEZx/Yzycf2NC4uNfneqGtu/w4cMFqVKDBg127twp7Up+/fXXpk2bBgQECJIR8xvj4fwbU4FDtrVr186dO1eQdgQGBqLzhs4J/kpLlSo1f/583MgVXY2K828oFRzfpAnaaCw2muPi4oJiIwzHpB06dMChVUhISI8ePX777TdBxsH104xHB+un8XyBd9ixY0eJEiXQqBGkZQUKFMDIxtbWFj/Np0+fli5dGjncDz/84GYgKIsgv0lISHB3dxcqljNnTmT+jo6OIv2QFypysoAwnBqHX9o6deoIzeL45q1wONy4ceMyZcoI0hEvL6/OnTtjA4UH26dOnRKGv+StW7dGREQIyhzmN8bD/Ea3Hjx4gLZAWFiYUscyJKcnT578+OOPGAN1794dtQeNOFQjQenH/IZSwfFNCmbPno2Wi5WVFYuNicD+cdKkSSg22EY7aMaMGUePHsW2dO47pR3zG+Ph9W/0BqO9e/fuobdbuXJlQSapdu3a69atq1KlijDM7cXBLA4+sB0SEiLoXTj/xnh0MP+G/bT/+Pj4IFIuWbIk53JSkri4uJiYGHt7e+yknJycVq5cGR8fb2FhISglGCZ6e3tjECB0CiOMggULKnI96bt37wYFBWl6SRuOb/6FYc3ChQtx1MNiQ8lZWlqi2AjD6rwjR47EBlK9Nm3aoPAIegPXTzMeHayfxnrzSmhoaHR09IoVKwTR20nL7GOUs3TpUk9PT2yfPn163LhxZ8+eFWTA/MZ4mN9oXnh4ePPmzTGmKV68uCBKGw8PjyZNmmADMU+zZs38/PywvW/fvp9++gkdD2HCmN8YD9dP07ydO3euWbPG2tpaEKUfAr8GDRpg/4XtChUqhISEHDhwQBhqjzSzx9Rw/o3x6GD+jemuL7BkyZKqVauWKVPGwcFBEGUaYp7q1atLzZYXL16sWrXK0dGxQIECJ0+edHZ2NpFjGjc3tyJFiqj8kgTIb2JjYzPW98PhKfYYGbuWQSbhtyhPnjxCy0x0fLN8+XJXV1dBZBzosy1evLhWrVrCcMjfokUL6aTqhw8fCl1jfmM8OshvTO58aPRACxcujD97Ke8lkkd0dDRiwh49euDI+pdffomJidHliAf5jZeXl3RihWpduHABh5sZbqkpZfPmzb6+vhMnThSaZVrjm717965bt04YLkgsiGQknWePbszs2bOxERERUadOHYyBxP9fWkkfmN8Yjw7yG9OqN8+ePfvss88EkXLy58+Pjzly5MDRD/Yg2D579uzAgQOPHTsmtI/zb4yH82+0Ab0LhLfY6NatmyBSBzs7uxo1amCjWrVqAwYMkNbL2bZt2+nTp4VmaSK/wQDl8ePHIkOUzW9wjCK0zCTqza5du6QZEkTqVLlyZalVgn3ZlClThGZpYv5N69atM5wwKTv/Ruszi03ifIGnT5+GhoYWKVJEEKkb/h7Dw8NVfj5xKrh+mvHoYP00S2ECchkIItUzMzPTbrERhvxG/X9rmbn+DfKbhIQEReqNUuOqLGQS/bTjx4+vX79eEKnekydPPvzwQ6FZnH9jPFw/TRsCAgKUOqWEKF3QTwsLCxOaxfXTjIfXv9EG5jekFcxvVI75TWYwvyFSEeY3MmB+oxTmN0QqwvxGBsxvlML8hkhFmN/IgPmNUpjfEKkI8xuVY36TGcxviFSE+Y0MmN8ohfkNkYowv5EB8xulML8hUhHmNzJgfqMU5jdEKsL8RuWY32QG8xsiFWF+IwPmN0phfkOkIsxvZMD8RinMb4hUhPmNDJjfKEXP+U3z5s2R3CT9A9GpkLbPnTsniFSJ+Y3KMb/JDD2Pb9q1a2eeDOoNbpSu4EukTjrIbzI8dJAN8psLFy6IDEF+o1SzBOMqTRcboe9607lzZ09Pz+S3ODk59ezZUxCpFfMbGTC/UYqe642zs3OTJk2kYY2kdOnS1atXF0RqxfxGBsxvlKLz8wW6deuWP39+advR0bFHjx6CSMUwOPjll1+EZl26dMnf31+oG4pN3rx5RYZghHH9+nWhhEqVKjVr1kxomc7rDWoMhjgIb7Dt5eVVrVo1QaRizG9kwPxGKfo/H7pLly5IcbJnz96rVy9BpG7Mb2TA/EYpCq8vcPdyxHP/qMjQBGFM9coMefr0acT9gofuPxdGY5fdPIerdZFyDuYWZoIoQ3SQ36CRgKojVAz5jaurq8gQ5DdCIRhX+fr6arqlptj8m+iIhM0LHzq5WmfPaWVrbyG0D52Qpw8iXzyJbtzNPXcBW0GUfpx/o3Kcf5MZyoxvoiMTdv7oX7tdbmd3a6EjJas5JSaI/b88rtXSxb2AjSBKJ66fJgOun6YUZfKbbUseVW7kqrNiIzEzF426eWxa8CAhXhClF/MbGTC/UYoC9cb/bpSZuZmLh54P/72q5/A5FCSI0onzb2TA+TdKUaDeBPrHuOXVebzhktcu0D9aEKUT59/IgPNvlKJAfhMRGmdprfPzsG3szMKC4gRROjG/kQHzG6WYxPUIiLSC+Y0MmN8ohfWGSEWY38iA+Y1SWG+IVIT5jQyY3yhF4fUFiCg55jcyYH6jFI5viFSE+Y0MmN8ohfWGSEWY38iA+Y1SWG+IVIT5jQyY3yiF+Q2RijC/kQHzG6VwfEOkIsxvZMD8RimsN0QqwvxGBsxvlMJ6Q6QizG9kwPxGKcxviFSE+Y0MmN8oxVTGN1OnjRs9ZrAgUjfkN507dxaaxfzGeHSQ35jK+Mbbu2FsbIwgUjfkN5GRkUKzkN94eXmh6ggVQ37j6uoqMgT5jVAI8htfX19Nt9RMpd40bKDbC6qTnmBw8NtvvwnNQn7j7Oys8nqT4ZMFhCG/KViwoCL9NOQ3hQsXFlqmjX5a2/YNN2/+5eNP+tdvWCUkNAS37Pnz9yHDejVvWRsfN21ej6NC3Ljix0UtW3vHxsYmPXHDr2saN60RERGRvJ/24kXgrM8ndenaql2HRp9/+dmDB/dw4/37fnjxCxfOSY/Zt38PPt26baP0qXSvIDIy5De2thq+GiHym8zszeWB/ObChQsiQ5DfYJwhlID8pmLFikLLtFFvrKysdu7aWrRoiWMLY9UAABAASURBVLlzFtnb2aMYzJ4zvXixkut/3tGv71DUm4WL5+Fh9es1QWk5depY0hMPH/m7Zo069vb2SbfEx8d/Mnqgz4Wzn4z8dOWKX51z5BwytOejxw/z5y+YK5f7lav/nsp5+bKPu3vuq///6aXLPtkcNJziklYwv5EB8xulaKPe4KDP0dFp+NAxVSpXt7S03LVrW7lyFUd+PMHZOWelilV79xy0bdvGly9fFClSzMPDEzVGelZg4POrVy81+N9O2qVLPhisfDpxZvVqtXLmdBk8aKSjU47Nm9fjrooVql67dll62IWL55o1bY2PSc+qUqWGIDIyHeQ3nH9jJJx/I58Sxb2kjYSEhMtXLlStUjPprooVq+LGi5de/SQaN2p++MgBDGKwfejwATs7u9rv1Uv+OhipYLSEKiV9ikpWoXxlqa7gRulFgoOD/PzutGndCRUrIOCJ9KxKlaoJIiPTen6D8dmLFy+EumVm/s1ff/3F+TcZppnzBaytraWNmJgYJDQ/rlyM/5I/AOMbfGzUsPlPa344d/501So1jhz5u06dBhgPJX9YWFgonv5aGJMjhzM+Vq5cPSQkGKOfO3dvFStaAqMfL6+yFy+eq1at1uPHD6tVrSWIjEzr+U2DBg30Pf/m8OHDNWrU4PybjNHe+Wn4a0Qe06RxS2/vhslv98jjiY+envnRVTt69GDx4qUQ0nz15fevPd3FxRWDns9nfZP8RgtzC+muQoWKIMK5ddu3bLlXuVy5shXxqbmFhUeevIhzBJGRYXwwYsSIjRs3Cm1S+ZlpEnT8sA/JWL1BfuPh4SGUgGZaQEAAz4eWW5EixUPDQitW+HeMgvGKv/8jpP3Sp/XrNdm5c0uBAoUR+ST1zZI/F/3xXLly5/XwlG557P8oh5OztI3W3IUL5+7cudm9e198WrZMheUrFsTFxTG8IXlw/o0MOP9GKZpcX6B/32EYwezavR2xDZL8GTMnjhozCH026d569Ro/CfDfs2dH/fpNLCwsXntu5UrV0B/7+uuZCGaQ02zb/tugwR/hwdK9lSqg3px9Nb4pUwGflilT4d69u2fPnmR4Q/LQwfwbrp9mJMxvlFG2bIXlS9etW79q2fLvo6IiS3uVmzVzvo2NjXQvBi4lipe64XttxPBxKT79y8+/3fH75hmzJl69eilfvgKNGjXv0KGLdBfqCmpV/vwFnZ1z4tNs2bIVLFj4zp1bFd8YJxEZgw7m33D9NCPRQX5jJs2UlNOpP19ER4kK9XIK/Xp8J+Lq8Zfth2TwGIpMltbzG02YMmUKMv8WLVqI9Dt69CjyG0V2/TrIb3g9AiIV4fwbGXD+jVJYb4hUhPmNDJjfKIXXvyFSEeY3MmB+oxSOb4hUhOunyYDrpymF9YZIRZjfyID5jVJYb4hUhPmNDJjfKIX5DZGKML+RAfMbpXB8Q6QizG9kwPxGKaw3RCrC/EYGzG+UwnpDpCLMb2TA/EYpzG+IVIT5jQyY3yiF4xsiFWF+IwPmN0phvSFSEeY3MmB+oxQF6o1dNvP4WLkXpZZZbHRidmcrQZROzG9kwPxGKQrkNy55bK+feS507fnDKOdcrDeUbsxvZMD8RikKjG88CtvGxyUGPY0R+uV7PrhcnRyCKJ2Y38iA+Y1SlMlv2g3yOLn7WUhgrNCjfeset+7nYWVtJojSifmNDJjfKEWB63tKIsPiN33/0M3TLntOKzsHC6F9+EYG3AsPfBzTsEsujyJ2gij98PcYHR2t3ZbapEmTvL29MQgQOoURRsGCBRXpp929ezcoKKhixYpCsxSbf2OXzeKjTwvcuhD2/FF00NN0DHSOHz9eunRpR0dHoTIOjpbPI64+MjvnUWSsIMoQ5jcyYH6jFIXnexYtnw3/pf3xO3fuLNfQvHXrokKVqouGmzcHxcfHR0VFOTg4CKJ0Qn4zYsSIjRs3Cm1CfiNUDx0/e3v7jNUbDN08PDyEEtBMCwgI0PQpahpbX6BVq1ZC3dAaxsdz5849ePCga9eugig9dJDfeHl5qbzq4I/U1dVVZAjyG6EQ5De+vr6arjdamu/5/fffh4SECC2oU6cOjkRu3LghiNKD829kwPk3StFMvZk9e3aePHlUGNu8zSeffIJ9x9OnT9HwFURpo4P8JsOnfskG+c2FCxdEhuDPGeMMoQTkN5o+WUBopd4goBs9evT7778vNMXJyQnZKToMR44cEURpwPk3MuD8G6Voo978888/5uZaXeoNbUAUHmygwyaIUsX5NzLg/BulaGAnPm7cOPwRarfeQNmyZfFx2rRpBw4cEERvx/xGBsxvlKL2nTjaC3379m3QoIHQviVLluCfI4jejvmNDJjfKEXt9QadqBIlSgi9kM6Q/vLLL0+dOiWI3sD8RgbMb5Si6nqDkY2vr6/QnfHjx69evTohIUEQ/S/mNzJgfqMUxdZPe6cTJ05ERUXVq1dP6BS+80eOHClevLi7u7sgMuD6aSrH9dMyQ73rC9SoUUPoGjr1+NXp0qXLqlWr3NzcBBHXT5MF109Tikr7aThKevr0qdC7bNmy7dy5MywsLDg4WBAxv5EF8xulqLHerFy5slq1auo/SsoqOGzBIS36wuo/kZSMjfmNDJjfKEW9+Y2pQdceBy9t27YVZMKY36gc85vMUN34Zu3atbGx+rzuZ+psbGykYjN69Gi210wW59/IgPNvlKKuejN58mQk51ZWVsKEDR06dMaMGYJMEvMbGTC/UYqK6k14ePjIkSO1vmBD5hUuXHjevHnY2Lp1qyATw/xGBu+//36GBwrMbzJDLfUmISHh4cOHGb4Iki4VL168fv36gkwJ10+TQdmyZfPkySMyhOunZYZa6g2aSFq5lppsSpcuvWPHjvj4+Js3bwoyDcxvZICK7uPjIzKE+U1mqKLe3Lhxo1+/flWrVhX0v7Jnz25hYYF9UK9evVB4BOkd8xsZYBD2+PFjkSHMbzJDFfWmRIkSlStXFvQWRYsWHTt2LI7IoqKiBOka8xsZML9RivL1pn///n5+foJShd4aSnJMTMyUKVME6RfzGxkwv1GKxbRp04Rydu7ciQE4BzdpZGNjg4Pfo0ePVqhQQZAeoXdqaaneVQ3fyc3NrUiRItmyZRMqhooeGxubsb7fmjVrHBwcihUrJmTn7Oyc4TKpEgr/Zrdq1UpQerRo0YJdNR0LCAgYN27cTz/9JLQJh49C9W7duuXo6CgyBH+ASgVUaKbh10PTQxyF+2l79+6Ni4sTlB5o43799deC9CghIeHFixdCszSR3+AwN8N1sUaNGgULFhRKYH6TWbNmzUImISg9wsLClDojk4yN+Y0MmN8oReF+WtOmTTXdrVaEl5fX2LFjBekRr38jA1R0BDAZC0F5/ZvMUHh8M2nSJGtra0HpgTBWB795lCLOv5EB598ohfmN9ly9epX5jV5x/o0MOP9GKcxvtIf5jY4xv5EB8xulML/RHuY3Osb8RgbMb5TC/EZ7mN/oGPMbGTC/UQrzG+1hfqNjzG9kwPxGKcxvtIf5jY4xv5EB8xulML/RHuY3Osb8RgbMb5TC/EZ7mN/oGPMbGTC/UQrzG+1hfqNjzG9kwPxGKcxvtIf5jY4xv5EB8xulML/RHuY3Osb8RgbMb5TC/EZ7mN/oGPMbGTC/UYoyYws0T80MhKFhnXTjjz/+KOhdkN/s2rVrzJgxgnRHB/kNxt8qv+oa8htXV1eRIchvhELQRff19eX11tLNw8PD3NxcKjnmBu7u7v379xeUBsxvdIz5jQyY3yhFmXpTuXLlpGGNpGjRojVq1BCUBsxvdEwH+U358uWFuqGi+/j4iAxBfqPU0R666Bk+rU4llKk3H374YfLjCzc3t27duglKG+Y3Osb8RgbMb5SiTL3BDyx5oS5RogQHN2nH+Tc6xvk3MuD8G6Uodn5a9+7dpeMgR0dHDHcEpRnzGx1jfiMD5jdKUazeYEwjnf+OsU716tUFpRnzGx1jfiMD5jdKeff50Anx4tnDqODnsXGxiSJLNaza8+kt66Y1W109ESKylIWluWNOy5x5rG3sFJ5gZAzZDATpEfKbESNGbNy4UWiTys+ElmAQ5uDgkLH5nshvPDw8hBLQTAsICND0EOcd9ebm+bBLR4NjohPyFLKPCo8XWcypY8tBIlE8uBklspStg8WFI0GW1ubFyjuUfc9J6Avn3+gY59/IgPNvlJJavbl7OeLSsZDGH+UVmnV4SwBaFGXfcxQ6wvxGx3SQ3zg7O6u83iC/ERmF/KZgwYKKrGeD/KZw4cJCyyymTZuW4h2P70Qd3xXYrKeGiw0UKJXN5+BLMzPhkkc/q+Y4OTmhFYC/akG6g/xG0ysKurm5FSlSROX9XlT02NjYjJ23vWbNGvTiihUrJmSHP/kMn+agEm+NN87/HVS9uZvQvmrN3S4eCRZZnD0pifNvdIzzb2TA+TdKeWu9ue8b7uSqhzGBfXaLQP9oRFBCLzj/Rsc4/0YGnH+jlJTrTWR4QnZnK0srM6ELrnlsQl/q56puzG90jPNvZMD5N0pJuVOMOhMVpp8ddFRklp9ZpyTOv9ExXv9GBrz+jVJ0OD1F95jf6BjzGxkwv1EK6432ML/RMeY3MmB+oxTWG+1hfqNjzG9kwPxGKRo+099kMb/RMeY3MmB+oxSOb7SH+Y2OMb+RAfMbpbDeaA/zGx1jfiMD5jdKYb3RHuY3Osb8RgbMb5TC/EZ7mN/oGPMbGTC/UQrHN9rD/EbHmN/IgPmNUlhvtIf5jY4xv5EB8xulsN5oD/MbHWN+IwPmN0pRb34zbfr4sLDQr+cuFvS/mN/oGPMbGTC/UQrHN9rD/EbHmN/IgPmNUlhvtIf5jY4xv5EB8xulZGU/bcvWX0+cOHzt2mVrG5vy5Sr17Ts0r4cnbp/02SgrS6sCBQpt+HUNhqKFCxUdO2ZK0aLFU79Lgr+9Dp0ad+vap3u3PtIt8fHx7Ts2/nzm/LJlMzIc1gHmNzqmg/zG2dkZoxyhYshvREZhhFGwYEFF+mnIbwoXLiy0LMvGN5cu+SxYOLd06fIzZnw9Yfz0ly9ffP7FZOkuSwvL8z5nsLFn19GfVm/O6eI6ecoolI3U75LY2dnVr9dk3/7dSbfg8aGhIfkLmG5DifmNjukgvylfvrxQN1R0Hx8fkSHIb5Q62sO4KsPDMpXIsnrj5VV21Y8bu3XtXbFClapVanR+vzsGOsEhwdK9MTHRH3Xvh78ljzx5e/caFBDwBPXpnXdJWrZod+/e3Zu3bkif/vPPvpIlvJwcnYSpYn6jY8xvZMD8RilZ1k+zsLB4/PjhosXzrl2/HB4eLt0Y9PKFVBgKFSpqafnv1/LMmx8f792/W6FC5dTvkpQuXc7TM/++fbuLFS2B7vY/h/b36jlQmLDr168fOnRowIABgnQHv+Hq31+nYvv27UWKFClTpoxQMeQ3rq6uIkOQ3wiFPHr06P79+0LLsmx8c/ToPwhjSpTw+nbeWFj8AAAQAElEQVT+Dwf2nZ4ze2Hye21t/msRSO2C8PCwd96VpF2b9/f+9Qf+FNFMi4yMaNSouTBhISEhGe4GkMqh2MyZM0do1qlTp7BbFOqm0fk3pUuXrlmzptCyLKs3O3dtRYDfr+9QpP1ojoWFhSa/N3kJiYqKwkeb/y8zqdyVpHGTlnjBM2dPHjl6sFZNb8fsjsKEMb/RMeY3MmB+o5QsqzchIcFurv/N8zp8+EDye2/fuRkcHCRt+/pew8fChYu+864kKDD16jZCcnPgwJ+NG7UQpo35jY4xv5EB8xulZFm9KVqk+OkzJ9DviouL+23TOunGJwH/rmzh6Oj0/YI5IaEh+G/N2h/c3XOXK1vxnXcl16JFO+kstRo1agvTxvk3Osb5NzLg/BulZNn5An36DImICJ/82ahXM2bad5kwfrq//6MJE0dM+nQW7i1cqGjBgkU6f9A8Ojo6T26PWTPmW1hYSE9M5a7kKlaoYmlpicFN0skFJovzb3SM829kwPk3SsmyfbeTo5NUWpIsWbxG2kBvDUdtH3Xvi//efOLb7po2dXbyT2/4XouIiGjbppMwecxvdIzrp8mA66cpRQPr2dy65Xv06D9ffPnZh116enrmFyaP+Y2OMb+RAfMbpWig3iz/4fvJU0aXKOHVp/dgQcxvdI35jQyY3yhFjixk+rQ5GbgryWtTeYj5jY4xv5EB8xulmHr2rkXMb3SM+Y0MmN8ohdcj0B7mNzrG/EYGzG+UwnqjPcxvdIz5jQyY3yiF9UZ7mN/omA7yG39/f6FuGl0/DflNs2bNhJYxv9Ee5jc6xvxGBsxvlMLxjfYwv9Ex5jcyYH6jFNYb7WF+o2PMb2TA/EYprDfaw/xGx5jfyID5jVKY32gP8xsdY34jA+Y3SuH4RnuY3+gY8xsZML9RSsr1xtLKzMnNWuhFNidLS2szoRfMb3SM+Y0MmN8o5S31xtosOiI++Hms0L7Y6IQnfpFOLlZCL5jf6BjzGxkwv1GKxbRp01K8IzoyMTw4zjWvhlvJkgc3wh2cLAqWchB64eTkhNazs7OzIN1BfqPpKwq6ubkVKVIELV+hYqjosbGxGev7rVmzxsHBAfGPkB3+5DNcJlXirflN1SbOD2+F370YJrTs+cPoS4df1u3gJnSE+Y2OMb+RAfMbpaR2JNVuoMfWxY/CQ2Jss1nmzG2bkJAoNMLcQgQFxESFx9+5FPLB6HxCX5Df7Nq1a8yYMYJ0Rwf5jZeXl8qvR4D8xtXVVWQI8huhEHTRfX19Nd1SS3XkbibaD8177WToozsRT+9FBj2LSeWxsXFxoaGhOY3f5AkOCbaxsbW1sUnlMU6uVuYWZnkK2X44VofXA2V+o2O8/o0MeP0bpZjheEpkhbZt2/7888/Zs2cXxtekSRMc4Gu6zZ0ZqDfPnj1jS41U6OLFi7ly5VJ5Sy0z82+mTJlSo0aNFi1aCEq/LJt/s337dnmKDezdu9dki41gfqNrzG9kwPxGKVlQbx49enTs2DEhL3zrb968KUwS59/oGOffyIDzb5SS2XoTHx/fsWPHWrVqCXnh12X06NEZPkjRNOY3Osb5NzLg/BulZDa/uXfvnouLiyKn20dHRz948KBo0aLCxDC/IdVifkOpyNT4Jjw83NHRUam5XTY2NvjNDg4OFiaG+Y2OMb+RAfMbpWS83uAQu1OnTsrOcke1+/jjj69cuSJMCfMbHWN+IwPmN0rJeL05cuTImjVrhNKWLFly7tw5YUqY3+gY8xsZML9RSpbNvyHZML8h1WJ+Q6nIyPjm9u3baltM5fPPPz979qwwDcxvdIz5jQyY3yglI/Vm0aJFkydPFmry6aefLl68WJgG5jc6xvxGBsxvlJKRWfrz588XKmNmZvbjjz8K08D8Rse4fpoMuH6aUt56/ZsUYTe3f/9+Ly8voUp//vlneHi4+ofzmcTr3+gYr38jA17/Rinp66d17dq1ffv2Qq3QWh03blxgYKDQNeY3Osb8RgbMb5SSjnoTFRV15MgRCwsLoWK7du2ys7MTusb8RseY38iA+Y1S0lpvAgIC7t+/r/6RPsrhs2fPHjx4IPSL+Y2Ocf6NDDj/RilpqjchISEffvhh8eLFhRYUKFBg7Nixt27dEjqF/Az/QEF6hPzG1tZWaNYHH3xQvnx5oW6o6D4+PiJDjh07ptTRHsZVGR6WqUSa6g3q+ZYtW4R2rFq1Sv0HWRnG/EbHmN/IgPmNUt5db9BQrlKlSo4cOYR2IMKpXbt2QkKC0CPmNzrG/EYGzG+U8o56c/v27S5dupibZ9llQGWDvsSwYcNOnToldIf5jY4xv5EB8xulvKOQ/PHHH0uXLhXa9N133+3bt0/oDvMbHWN+IwPmN0rhep1EKoL8ZsSIERs3bhRkNJlZc/Po0aMeHh6KtNTQTAsICND0EOet4xtfX1+MD4T2rVmzRmddNeY3Osb8RgbMb5Ty1nozbty4gQMHCu3r0aPH7Nmzw8PDhV4wv9Ex5jcyYH6jFPbTtIfXvyHVQr1xdXVV+TJfmbn+zfz581GuGjduLCj9Uh7fvHz58sWLF0IvQkJCsIMWesH5Nzqm9fk3mRk6yCYz82+qV69etGhRoQTdzr9B/d+0aZPQiwMHDixbtkzoBfMbHWN+IwPmN0pJeT20nDlz6qnP5uTk5ObmJvSC+Y2O8fo3MuD1b5TC/EZ7mN+QamFwkytXLpUvaZOZ/CYz51IT8xvtYX6jY1w/TQZcP00pzG+0h/mNjjG/kQHzG6Uwv9Ee5jc6xvxGBsxvlML8RnuY35BqMb+hVDC/0R7mNzrG/EYGzG+UwvxGe5jf6BjzGxkwv1EK8xvtYX6jY8xvZMD8RinMb7SH+Q2pFvMbSgXzG+1hfqNjzG9kwPxGKcxvtIf5jY4xv5EB8xulML/RHuY3Osb8RgbMb5TC/EZ7mN+QajG/oVSkPL5BfoM6hFGO0LIOHTpERUVhIz4+3szMzNz8VfMQt6C9JrQsm4EgPUJ+M2LEiI0bNwptUvnIRoJBmIODQ8bqDfIbDw8PoQQ00wICAjR9iU895zfFixfHj+fp06eBgYHPnz9/auDi4iI0jvmNjjG/kQHzG6WkXG8wskETVmhct27dXrvUoLW1dZcuXYTGMb/RMR3kN/7+/kLdMnMRUuQ3169fF0pAfqPpwY14Wz+tU6dOQvvwW1W+fHk0KJJu8fT07Nixo9A4Ly+vsWPHCtIjNH5tbW2FZn3wwQfIb4S6ZSa/OXbsWEJCgiLnC+ggstX5/BuMZpKiSxsbG/wxCO3j/Bsd4/wbGXD+jVJ0Pv9GGuJI2xjcdOjQQWgf8xsdY34jA+Y3StFzfiP58MMP3dzcMLhBkxDNCqF9zG90jPmNDJjfKEVF82/wRsKD4yJC40VW++abbx49ejR37twsrzdWNubOuayEvDj/hlSL828oFSnXG/nn35w/GHTpSHBcXKJdNguhHXYOFv53I71qONbtoJ/1C0hBWp9/owmZqRlHjx718PBQ5GhPB/NvUj4/TRrRDxgwQMjiyPbA6KjElv3yWduZC62Jj030uxa26buHHYZ7msvy9pHf7Nq1a8yYMYJ0Rwf5jZeXl8pnfSK/cXV1FRmC/EYoBF10X19fHc73lDO/ObL9eXy8WbVmrlosNmBhZVakXPYytXNuWfhQyIL5jY4xv5EB8xulKJzfBPrHntgd6N1R7SdQpoXP3y/cPK1KVskujIz5DakW8xtKhcLzbwL9o3Rxytgrtg4WAfeihPFx/o2Ocf6NDDj/RikKz78JC47PmUfDs6mTc85tHRMlx2CR8290jPNvZMD5N0pR+Po3cTEJsdFCH+LjEsOCY4XxMb/RMV7/Rga8/o1S9Lx+ml5x/TQd4/ppMuD6aUrR+fppusT8RseY38iA+Y1SdL5+mi4xv9Ex5jcyYH6jFIXzG8oA5jc6xvxGBsxvlML8RnuY3+gY8xsZML9RCvMb7WF+o2PMb2TA/EYpzG+0h/mNjjG/kQHzG6Uwv9Ee5jc6xvxGBsxvlML8RnuY3+gY8xsZML9RCvMb7WF+o2PMb2TA/EYpzG+0h/mNjjG/kQHzG6Uof/0b+U2dNm70mMHS9pGjB/sP6Fq/YZUrV9T+R5KE+Y2O8fo3MuD1b5RiivmNt3fD2NgYafuXDT8lisT585YWKKCZII75jY4xv5EB8xulmGJ+07BB02ZNW0vbERHhZUqXr1ihCkIRoRHMb3SM+Y0MmN8oRWP5zfCP+44bPyz5LRMnjRwyrBc24uLili3/vnffzi1be4+fOOLEiSNJj2nbvuHmzb98/El/9M1CQkOkfhoej0/9/O5s37EJG7PnTG/Rqg5uTHoWntK4aQ2hPsxvdIz5jQyY3yhFY/lN/bqNz547FR4eLn0aFRV15syJRg1e9TS/XzBn0+b17dt9sH7d73W9G06dPu6fQ/ulh1lZWe3ctbVo0RJz5yyyt7OXbrS0tPx7/5mCBQu3bdMJG337DMHf+eEjfyd9rX8O76/9Xj2hPsxvdIz5jQyY3ygl5XqD/AaHAEJ96tZthObp4SMHpE+R9uPTevUaR0dH/7l3Z9cPe7Vp3dHJ0alF87YNGzRbs/YH6WHoiTs6Og0fOqZK5eooMym+squrW9UqNQ4c+FP6NDDw+aVLPk0atxTqw/xGx3SQ35QvX16oGyq6j4+PyBDkN0od7WFcleFhmUq8Nb8JDAwU6uPi4lqhfOWkUcjRowcrV6qWM6eLr++1mJiYqlVqJj0SD7tz51ZwSLD0aYniXu988RYt2p04eUR6ysF/9jk55ahWrZZQH+Y3Oob8pm/fvkKzNJHf3Lx5MyAgQGSIgvkNauRff/0ltOyt+c3mzZuFKmE0c+rUMXTSYmNjj584jE/FqxZTqDCkO0hipP++nD0Vt7x88W/VtLa2fucro3vm4JDtn3/2YfvQ4f0Y3FhYWAj1YX6jY8hvnj59KjRLE/lN69atM7zijoL5ze3bt8+cOSO0THvrp6HAIKo5dvwQSsirZlrdV/XGxdUNH0ePmpQ3b77kD86VKx2HWmi1NW/W5q99uxD/XLx4/uPh44UqMb/RMa6fJgOun6YU7c2/QTyDHhqGONHRUe/Vqmtv/yr/98yb38bGBhsVK1SRHvby5QuUTOnetGvZsv2GX9ds/O3n4sVKFi5cVKgS8xsd4/wbGXD+jVI0Of+mbt1GFy+eO3v2pNRMA9SVXj0Hrln7A0J+BDn/HNo/ZtyQb7/7SqSTZ958CH42b/mlaZNWQq2Y3+gY59/IgPNvlKLJ9dPQQwt4+iQuPg7jm6Qbu3zQY+yYKes3rG7dtt5338/2yOM5evRkkX61annHx8c3bKje8w6Z3+gY59/IgPNvlKLJ6984ODjs/+vUm7dXrVID/715+2+/7k7+6fRpc5K2V/248bUHnzt/un79Jk5OOYRaMb/RMeY3MmB+oxRe/+Zf2InfvHX9/PnTVy5fWPlGEVIV5jc6xvxGBsxv7fNz5QAAEABJREFUlMLr3/zr3r07o0YP2vPn79Onz3U1nO2mWsxvdIz5jQyY3yiF17/5V+nS5f7ef2bjhl1JZ7ipFvMbHWN+IwPmN0rRZH5j4pjf6BjzGxkwv1EK8xvtYX6jY8xvZMD8RinMb7SH+Y2OMb+RAfMbpTC/0R7mNzrG/EYGzG+UwvxGe5jf6BjzGxkwv1EK8xvtYX6jY8xvZMD8RinMb7SH+Y2OMb+RAfMbpTC/0R7mNzrG/EYGzG+UwvxGe5jf6BjzGxkwv1EK8xvtYX6jY8xvZMD8RikK5zfWduZWNuZCF8wtzJ1crITxMb/RMeY3MmB+oxSF8xvHnFZP72u4W53c84eRNvYWwviY3+gY8xsZML9RSsr1BvkNmrDC+HIXtEtM0ElQFBEa71nUThgf8xsd00F+4+/vL9QN+U2ePHlEhmCEcf36daEE5DfNmqn3OpBpYab4eQGXj4fcvhDe4MMM/vhV4uz+wLjo+EYfytG5Rr159uwZW2qkQhjcIL9ReUstM/nNlClTatSo0aJFC0Hpp/z8mzI1HcvWdty18uGjmxERIXGJCUJD/8VGJ/jfiTy155mVpZCn2AjmN7rG/EYGzG+UkvL5adKIfsCAAUIWhcs42Ge3OH8w6PjOqIjQOKEdbp62VjZmXtUcS1TJLuSC/GbXrl1jxowRpDs6yG+8vLxUfj408htXV1eRIchvhELQRff19dV0S00t829yF7Bt3jPdh0WhoaFt2rT5+++/RVYYMWJEly5datWqJdSN+Y2Ocf6NDDj/RinK5zeZ4efnZ2Njk+Ho7zXYj+MFy5QpI9SN+Q2pFvMbSoW210/DgUZWFRthyEXUX2wE8xtdY34jA+Y3StHw+mmLFi3K8jeJaGTo0KFC3Tj/Rsc4/0YGnH+jFIXn32RYRETEsWPHsnzdHUSd7u7uPj4+QsWY3+gY59/IgPNvlKLt/MY0Mb8h1WJ+Q6nQZH4THx9/4MABYTRnz54NDAwUasX8RseY38iA+Y1SNJnfILl5+PChMBpzc/MJEyYItWJ+o2PMb2TA/EYp2stvMLjBAVSPHj2E0eB3sUuXLk+fPhWqxPxGx5jfyID5jVKY32gP8xtSLeY3lAqN5TcY3AwcOFDIYs6cOTdv3hTqw/xGx5jfyID5jVI0lt8sX768evXqQhb16tX75ptvhPowv9Ex5jcyYH6jFLWsn5ZGffv2tba2FrKoVq0afinxfTAzMxNqwvxGx7h+mgy4fppStJTfSOcou7i4CLlERESgr+jp6SnUhPkNqRbzG0qFZvIbJDf4GctZbMDe3n7atGkXLlwQasL8RseY38iA+Y1SNJPfHDlyRJHQ4tNPP71y5YpQE+Y3Osb8RgbMb5Simfymbt26QgmFDYSaML/RMeY3MmB+oxRt5DfHjh2Li4vz9vYWSrh16xYOK3BMJNSB+Q2pFvMbSoU28pvRo0creNnNokWL7tixQ6lJxW9ifqNjzG9kwPxGKRrIb54/f759+3ZLS0uhnCVLlmAvL9SB+Y2OMb+RAfMbpWggv0E72MLCQigKxcbOzk6oA/MbHWN+IwPmN0pRe36zatWqiIgINVxz89ChQxhmzZs3TyiN+Q2pFvMbSoXa85vjx4/LtmBa6ry9vTHKuX//vlAa8xsdY34jA+Y3SlF1fpOQkLB8+XJlk5vkpk+fnj9/fqE05jc6xvxGBsxvlJJyvfHw8FDDQcqBAweGDBly9uxZoRo4vggODhaKwv4oOjpakB5pPb/B+EzNlwaWpPf6N2jp42NMTMyIESO6deuG42ChBB1c/ybloUOrVq2ECjRq1MjR0TE0NBTb69evDwgI6N69u5ubm1DO6tWrixYt6uTkJJRTokSJnDlzCtIjMzMzW1tboVkNGjRAfiPULS35DQYTnp6e1tbW2Oeg+YZjXww9u3TpUr58eXNzc6EEHXTR1Z7fVKtWrV69etho2bIlfo+vXbuG7bVr1+7atSs+Pl7IDt3bHDlyCEUxv9Ex5jcySDG/wSDm2LFj0n4PdWXChAlxcXHYnjVrFooNNmxsbGrVquXg4CAUwvxGPhhSYCQrLTGA3+kTJ04gxsD2li1bfH19hVx69+7t6uoqFMX8RseY38ggKb/x9/ffunXr3bt3sT127Nhff/1VuvjIypUrN27caG9vj+2CBQsKddBtfoN2jbOzs1ArDGlnzJghnUQfFRU1bdq0kJAQNFVxeCKMTA35Deff6JgO5t9gJy5U7Pbt20ePHn3w4AG2f/nlFxy9SVO5Fy1a9N1330n7PanSqI0O8hstXf8mFSg2ODAZOXLkjRs3UBJQfhDuGWMggoE2xteIcIRyOP+GVEud82/Qh8fAq3Llym3atMHABQem7du3V2oJYFOmmevfpA4JHuoNDk+k/mZ0dDRSvs8//xzbWTscYX5DRsX8JvOk08lQYwYPHrxgwQJhWBMLSXD9+vWxjW+vo6NjeHi40BrmNyrl5uaGH0yPHj2wjRFPo0aNdu/eLQwXbROZw/yGjIr5TcZI/TFEuR07dvzmm2+wbWFh0adPn0GDBmG7Tp06LVu2zJ49u/TgzMy/URDzG1XLly+fMJzhhtopXRN69erVQ4YMuXXrlsgo5jdkVMxv0gg9GGlm3r1792rVqrVmzRphOKto/vz5kyZNwnbx4sWrVq1qZWX15nPTO/9GJZjfaM+pU6dsbGzKly8/b948HAH17ds36agnLZjfEKXCqPkNehXXr19v27ZtYGAg/hIbNGgwceJEdMZQVKytrdP+OplZP40yQyf5TdphuINigw1029AZk47Fvv/+ezTc0lJ6md+QUTG/eQ2yfWQwsbGxaIbPnDnTz88PN+Jv8K+//kKxwbaDg0O6io3I3PppCmJ+o2HIeLp3745BN7arVKmCX+uQkBBhWJFa+p1OEfMbMirmN4CDv8mTJz99+hTbf/75J7pklpaW6Eb8/PPPH3/8sTBkMyITmN8oRc/5Tdqh/4tDJ2mVmoiICOnEtufPn785oYf5DRmVCeY30mKA27Zt69+//+XLl7EdEBBQu3ZtFxcXYVgkF60IaRpmVmF+oxSTy2/SDnXls88+i4uLW7x4MUbfGLNjZMP8higVacxv0LHHEe3GjRuR8yPer1mzJvpj+PuSZ9jB/EYpJpffpB2GO8h1pPP30WpD823lypXIb5RaHTYJ8xsd02t+gyMkadkY1BhkqFJfyMvLa8WKFSg22G7cuLFsPS7mN0ox3fwmjaROccmSJfGTbtmyJfIbDPmbNGly+vRpYVjXQMiO+Y2O6Sm/wcapU6ewsXXrVvTEpHkIderUOXHiRIMGDbBdpkwZRSaHMr9RSsrXI0B+wz7bm9zd3VF1GjZsWK9ePenkgqlTpwYFBaHtJuca7MxvdEzT+Q2SGLTF8MuJUQ4yf/xD0BXA7Tg+a9++vfQYNQQn0tKLmoP8pnDhwkLLmN+kz5v5zfHjxz09PfPlyzd69OiCBQsOHjzY2BckZX5D6oEag14Iws4hQ4ZcuHBh6dKlyLTbtm0rVIz5jVKY36TPm/Nv0H2WFjIYNWoUIh9pXSaMeKRrZhgD8xsd00R+Exsbi44uDrCE4TTOp0+fIpIRhoXblyxZovJiI5jfKIf5TfqkMv8mb968aFJLJ1V7e3ufPHlSGHYfa9asydpfbuY3OqbC/CbeABvjx4+XaklMTAzG9NLSZPi1/+STT6pUqSI9WFvXv9EWzr8xOWmcf9O4cWNp8jO+jXj8smXLhGExQakIZRLzGx1TSX7z6NEjaaSOWlKrVi1pikyLFi1WrlwpDFP60VhGS+rNJ6r/+jeC82+Uw/wmfTIz/+bBgwdfffVV/vz5cZx448YNjJOkGW3pxfyGshxGMEhfMFhxd3cfNmzYw4cPV6xYgV9RHCRJa3CkkTqvf/Ma5jdKYX6TPplZPw0xz6JFi8aOHSsMXe9u3brt3btXGI4l0/U6zG90TM78Bn/mu3btkq7LPmHCBET9cXFx2P7iiy+2bdsm9Y3TVWyEOq5/807Mb5TC/CZ9Mr9+mrn5q+/5e++9h18dqeu9fft2DJOlRdvScoUe5jc6Zuz8Bs2uVatWHTx4UBimXp44cQLNMWzPnTt3+fLlGN9g29HRUWQU8xvj4fwbk4MiUbNmTemkgMzD9xkfhwwZgkNaaeoo6hleHH/8tra2b3uWgvlNQrzI0oWsFPPqX6HKf4gx8pt79+6tX78ejVwMqc+cORMRESFFLwMHDhRZDUMHZJYY5QgV4/wbpTC/SR8Z1k87fvw4/lxx1Im9Q926dQcMGPDaA+TPb8JD4k/sDnxwI8LW3iLQP1pon3sBu9iYhGLls1VprLfzYmJiYqytrVFjvvnmG4QxEydORI3Bp/hdkmFpc+Y3lIqU6w0au7hdOvqm5NCLaN26tTyXJLh9+/apU6c+/PBDBDyLFy9u27atNMtBZkHPYjcveFinfe7sOa2y5TDuVFY5vfCPfvYo6u6l0Pc/9lTPWAf5zYgRI9DpStez8BuCVhg+jhkzBvt6VBq0Z5H544jY3t5e0P+aMmVKjRo1WrRoITQFzbSAgABNn6KWcr1BJxcf3zyyJkXgZ7R3714couIn4uPjs2/fPrT4P/vsM2F8zx/H7F7l325YAaFT966FXzn24oNR+YQ6IF/BT/n3339P/WHh4eE3btxAOXnx4kXHjh2xMW/ePGwHBgameJqybJDfeHl5qbyfhqYfDhk1d0r05s2bfX19pYkWGsX8Jn2yNr9JIzMzs6ZNm0rbaKNhn3LlyhVsI+zFRxypCaM5sSuw8UeeQr8KlHIID4q7eDi4XB1Zf6Zvk0p+gwOOCxcutGrVKj4+Hsfm+LmjzKDvumPHDuma6DkNhKKY3xiPDvKblOtNp06dBKVk9erVCG9krjfJ4UtPmjQJ+Q22sZdZsmQJdkMffPDBuXPnChYsmLW7m6jweH+/SAenTF1LUf2y57S8fTFEJfUGxxbJTxVBgcFRBX6+OXLkmDp1apEiRdDOtbS0/Oeff6QH2BgI1cBblXPt2ozRaH6jg1kQnH+TPpmZf5NVkubflC5deuHChdJ0DVSdLl26SKeiYltkhcAnMQVLZRN6l9PDRqhmNI/8BiOYmTNnIr3Dp2ismZubSxkMjnXQRDUzEGrF+TfGw/k3Jifz828y77X5N9Lep3379sh4cPyL7WXLljVv3jw0NFRk7go9CfGJoS9jhe4lvoqphEJiYl596f379w8dOvTYsWPoY0dERJQvX97T81Ubc/Lkyf3797e2thYawfk3xsP100xOGtdPM6pU5t9Ic/e++OKLNWvWSJdFqFu37rhx40TaZpKSPNA/wMc///wTjet9+/YJw0FDjx49qlevjsHBrl272rRpo6ouWdpx/TTj0cH6aRbTpk1781YvLy/0agS9AcebyGmVTWUR4aD1nPoBAQqPlZUVNvr06ePo6IiD5YCAABwpozlTqlSpFJ/Srl27X375BemUNMkcQgJjHzzrwtUAABAASURBVN+OKlI+47PNNSE2OuHW+ZCK9YzYJsUxyqNHj/BrgxrTq1cv7OzwU4iOjkYYU7VqVWFozeNnhJ8OCo+xr59kVG5ubhhko+UrVAz9m9jYWPX3/V6DP3ktlsnkmN+kj6rymzTCUbMwXFdx1qxZUmcGEfSUKVOkk9yS4CeOfSKOP/7++29BmXbjxo3jx49jA9/PDh06+Pj4CMMVYjCgwafCEL8VKPD6ieaauP5NKpjfGA/zG5Ojwvwm7TB2QRaNDRxTY5Tm6+srDF2dn3/+GQfgaNPhUwyD5syZ8875H/QmdCwPHTq0detWbJ88eXLGjBn4ZmK7WrVqiGc6duwoDKc7p7JSkVDl9W/ShfmN8XD9NJOjyPyb12R+/TQLC4ukydU44sY+Iun8Wnj27Nn3338fHh7+XqU2glKFGrNlyxaMC0eOHOnn57d9+/aGDRsKQ0Vft26d9BgpVEsjlVz/JsM4/8Z4uH6ayZFh/bR3Msb6acghnz9/nvwWDOM6NO/valGj8Ud5ha6Fh8TtXvmw99SCaX/KggULMDrER4wLly5disFi3bp1BXH9NEoV85v00WJ+kxZS50cYzp/GIQg+Pn36FF0gQf9/yvJXX33Vrl27qKgoYVixv1+/fsJw7sb48eOzsNgwv5EB8xulpNxPk0b0XD/tTchvhNKQ3+zatWvMmDEi6yBUQB21tLTEBvYXefPmRZrtaFUo8JYwQYGBgWg54hvyxRdf7NixA5FMnjx5MIj56KOPpPSlZ8+ewjh0kN+of/005DeKp7AZgC46RtWaPiWa+U366CO/eRMO0tEG8fT0zJ8/f9KND3wjAm+9FKbhypUr2bNnxz9/5syZR48eXbRoEeoNQv5x48ZJJyjXq1dPGB/zGxkwv1EK85v00Wt+kyLUm9N7X5pCfrNl0a2T/l9OnDixZMmS6CTzShwZxvyGUsH8Jn30mt+YODs7259++gnFRvz/RVeVwvxGBsxvlML5N+mj6fk38vv74F/1G1YJCspgU65t+4Zr1q5483a8IF4WLy50h/NvZMD5N0rh+mnpo/L103Tmg84flSurvf1CZuggv+H6aUaig/XTeP2b9FH8+jfCsLrd2LFjhQno+mEvYWJeu/6N5vD6N8ajgy56yvUG+Q3G9UxN36SS/EbN6yEuXfbd3r/+sLezb9iwmafn/6wPtufP33f8vvnu3VuFChVtUL9Jxw4fShdTiI+P/23Tup/WvLqKuVepsr16Dixb9tW+AP00PKbHR69muuw/8OeqVUtCQkNq1fL+4P2Pkr/slSsX8dzr16845XCuWaNOzx4D0jWlX1WQ34wYMWLjxo1Cm1R+ZpoEgzD8hmiu3qCZFhAQoOkhDvOb9GF+k7rtOzZt3/HbxyPGL168Jk+evGvW/pB01779e2bPmV68WMn1P+/o13fops3rFy6eJ921/IcF27f/NmP615M//dzNzX38xOH37/slf9k7d259/sXkJk1a/bx2W9MmrRYsnJt018NHD8aMGxIVHbVwwaqZ07++c+fmJ6MGxMXFCW1ifiMD5jdKYX6TPsxvUrdl64a63o3qejd0zO7YrGnrShWrJt21a9e2cuUqjvx4grNzTtzeu+egbds2vnz5IjgkeONvP3fp0rNqlRrvvVd3zOjJVSrXCHzxP4vroIa558qNgQ5etmKFKi1btk+6a9++3VaWVqg0+fMXLFiw8JjRn928dePI0YNCm5jfyID5jVKY36QP85tU4Nj80aMHzZv9t8pn8eL/XmsnISHh8pULPT7qn3RXxYpVcePFS+dzOL06silZ8t/rLVlaWs6YPve1V8bLFixUJOnTpAeLV820C/jUyenfJmfu3Hk8PDzxsvXqNhIaxPxGBsxvlML8Jn1atWqlbLERKs5voqKikMTY2dkn3WJraydtxMTExMbG/rhyMf5L/hSMbywtXv0S2tqktpMNCQn29Pxv4QO7/39Z8Wq0F3r9xtX6Dav8z8u+CBTahAb9qFGjktaW1hxN5De+vr7Zs2cXWqOD/Ibrp6VP9+7dhdKMsX5alsCBuYWFRXR0VNItkZERSXfZ29s3adzS27th8qd45PH093+EjYiI8FRe2dHRKSrZyyZ/cE4X17JlK/TuNSj5450cFT6nI8Mw5gsJCRGapYn109q0acP10xTB9dPSR6/rp2UJ9ILc3fNcuXJRvP/vLSdOHkm6t0iR4qFhoUhfpE8x3EGlyZXL3cEhG3poFy6eK1WqjDA05SZOGlm/buOmTVslPRcve+z4IeyLzc1fJY7HTxz+72ULF9v71x/ly1WS7gI/vzvJB0PawvXTZMD105SS8vkCyG/ef/99QW9AfvPs2TOhKDXPv6lfr/Ghwwekmf+/bPjp6tVLSXf17zvs6NGDu3ZvR9m4dMlnxsyJo8YMQp8NvcHGjVps3/7b7j07zvucWbBw7tmzJ6Xak6RevcZBQS9xF6oRHrNt23+nC3fq1A0vuHDxPHTzHjy4t2z59336fXDnrlbXtdZBflO+fHmhbqjo0uW9tQX5jRZPq0uO66elD9dPS133bn1btmiHwoBABaOQIYNHCcOQRbw6qKywfOm6ixfPt+/YeMy4IeHhYbNmzrexscFdH48YX6FClXnzPx81etCrUjRtbv78BZO/bNUqNQYN/PjUqWMNGlWdPWfahPHTk17WMbvjjyt+RaIzcHD3Hr06+lw4O3bMZ8WLlRTaxPXTZMD105SS8vrQy5e/mnnH/EadZMtvTGd96PRe39N4/P398Xf3+++/C23SRH6DeoP8RnOnRG/evBn5zcSJE4Vmcf5N+nD+DRkV59/IgPNvlML5N+nD+TdkVJx/IwPOv1EK85v0YX5DRsX8RgbMb5TC9dPSh+unkVFx/TQZcP00pTC/SR/mN2RUzG9kwPxGKcxv0of5DRkV8xsZML9RCvOb9GF+Q0bF/EYGzG+UwvwmfZjfkFExv5EB8xulML9JH+Y3ZFTMb2TA/EYpzG/Sh/kNGRXzGxkwv1EK85v0YX5DRsX8RgbMb5TC/CZ9mN+QUTG/kQHzG6Uwv0kf5jdkVMxvZMD8RinMb9LHpPIbM3OzbDmshN6ZmZs7u9sIdWB+IwPmN0phfpM+JpXf5HC1engrQuhdUECUSEwQ6sD8RgbMb5TC/CZ9TCq/yZbDMqe7dWy0zq8sHhYU51nMXqgD8xsZML9RCvOb9DG1/KZivRwHNmjvSDDtIkLiL/wTWKWRWn7bmd/IgPmNUlK+vie9TZcuXWbNmoUIRygH9ebZs2eyNXP9rkWe3P3Cu6M7hjtCR+JiEgPuRR7e+qTX1EJW1maCsgIGN8hvVN5S02h+owMp70GQ36AOYZQj6H+pJL8BIZeCpeysrHOe/evZ/RsReYvah72MFRkSn5Bgbm5uvP16guHIydwsTV/BCdHUzYiSVR37f15YqAnymxEjRmzcuFFok8qvJC3BIMzBwUFz9QbNtICAAE0PcVKuN9KIfsCAAYL+F/IboTTkN7t27RozZoyQS94idvgvPi4x6FkGiw36kE/9/Xv3NO53b8KECQMHDkzLyA+Fz9ldjafe6SC/8fLyUnnVQX6jeAqbAeii+/r66rDeYGTDPluKsN+sWbOmsudDKzX/xsLSzCWPtcgQO6e4T3r0s7CwEMa0fPU8HANm+E2qgQ7yG0S/Kq83yG+EBiG/KVxYXcPx9GJ+kz4mmN9oCwYHz58/z5cvnyAlML+hVHD+Tfpw/bT0io6O7tOnj5CLnZ3d33//vWDBAqFNnH8jA86/UQrn36QP109Lr8WLF7du3VrIqEePHtWrV1f/Wbkp4vwbGXD+jVKY36SPKec3GfPJJ58I2VWrVi0mJkZoEPMbGTC/UQrzm/RhfpMu169fd3Nzc3FxEbILCAjo27fvzp07BcmI+Q2lgvlN+jC/SbsrV6589dVXihQbcHd3/+abb3bt2iU0hfmNDJjfKIX5Tfowv0m7Bw8ezJ49WygHx7AtWrQQmsL8RgbMb5TC9dPSh9e/SbtmzZphkCGUNmHChGvXrgmN4PppMuD6aUphfpM+zG/SaOrUqQMHDvTw8BAqMHr06Llz55qbmwsyMuY3lArmN+nD/CYtdu/ejZ27SooNzJs3TyvFhvmNDJjfKIX5Tfowv0mL5s2bY3wj1OTgwYOaWAST+Y0MmN8ohflN+jC/eaeAgICHDx8KlalXrx6GDocPHxbqxvxGBsxvlML8Jn2Y37xT9erVjx07ZuylOUmdmN9QKpjfpA/zm9SdOnVq2bJlqi02aFUtXLhQqBjzGxkwv1EK85v0YX6TumrVqqn5sNHOzq58+fKKLLGTRsxvZMD8RilcPy19uH5aKtatW4eBV61atYSK1TEQasX102TA9dOUwvwmfZjfvM29e/dGjRq1efNmoQWHDh0qUaKEGqaj6gzzG0oF85v0YX7zNnnz5tXQgbm3tzeaKhEREUJlmN/IgPmNUpjfpA/zmxSFh4ffv39fWxP49+/fj+MqoTLMb2TA/EYpnH+TPpx/k6IRI0aEhoYKTbGysrK2tr5165ZQE86/kQHn3yiF+U36ML95E4rf5cuX27RpIzToiy++KFmyZIcOHQRlBeY3lArmN+nD/OZNhQsX1mixgU8//bRgwYLoBwp1YH4jA+Y3Skm53pw9e7Z///6BgYHYPnDggI+PT0JCgiBDfnPt2rWlS5f6+voKhWCXNGzYMGk1MMV7/ceOHdPcNc1egzZFUFDQqlWr1FB1bG1t8+fPLzRr69at169fF+qm0fzm0aNHt2/fFlqWcr1p1KjRlClT7OzshGGAvHDhQmm4069fP3Tqo6OjsX348OGbN28K04OxhaWlpdT3X7lyZdeuXQ8dOiQMJwQHBAQI48Px4yeffCKdtnD16tV69er98MMPwlCH5HkDyaH64h8uNM7d3T0iIuLLL78Uhr9qoRyMnidPniwMZ2wLDbKwsFD5uqhIEEqXLq3F/AZvW+WT294pffkN/hSxc6latSqy1kmTJqFx/9NPPyF0xVE/doL4c8WrnT59Oq+BMAH496Lo4m+sSJEi27dvx36/b9++7du3xyE/DpZRtmU47QJfCJUGbwCj0qlTpzZv3nzo0KE4SkDMgyN3HC8LY8KXjo+P19OPGzt6RHTz588vU6aMUA4Gjp9//vm2bdvwtya0A78MaIdUrlxZqFJwcHDHjh337dsnSAlZc74ADnIfPnzYuHFjtN3Q6nn+/DmOcaKionAYjmh99OjRMTExN27cQKNA2Zn5MoiNjcUOArt+/E5j5FG9enUk0tgpjxo1CjkBvkseHh5GPW8Y5cfBweHChQsYe+HPvkePHih+aI02a9bMzc1NUBpgNI+RYqlSpRYvXoxf4CZNmggl4D2gxxAaGoofHI7qBGUa/ig6dOigeASbMchv8Cuh6VPUjHh+Gl75zJkzT58+bdmyJZoVOOhGI279+vXPnj2bPXu2l5dXnz59ED9gX5wvXz50qIRO4ZDYCdXOAAAQAElEQVTqypUrBQoUwCAAQ0A0uNeuXVuiRIkdO3bg975mzZrGPoBF1LR7924EufXr18cOFD8RhHNZNSJBMcPBRLt27YQe4SAJI3j86uLbhdG8IquJhISEYBezYsUK/MkILUDii+/b4MGDBWWpzZs342954sSJQrMUOB86Li7uyJEjOGpr3bo1yjXGQzY2Nj///PP9+/fRj0KOhwOQcINcuXIJPcLID22uTZs2HT9+HP98BEKffvqpvb09hoMYmqA+GW8UiGJ/8uTJYsWKoeBhyIWRKHpHGHdi4OXp6SnS78cff0S90ffOBX8jZmZmCOpwYIRDJaEE/MnUrl3b399f/cEDfoHxJ7x//36hJjjkevDgwYABA4Rm3b17NygoSItnOiRR0fwb7IX//vtv7Lzatm2LY0nsiLEfXLp0KQISFPYqVaogDpHOIMJOWegL/o0YA2H8gUrzwQcfvHz5EmkQeik7d+5ENUJOKIzj6tWrbgYoeP/88w+6oDiQR4CBNCiNAyD95TepuH79esmSJZFQolnaq1cv+Xf948ePx4ECGgNC3dDPwEGkei5LgeB53bp148aNE6QoVc/3xI4Mv7LoJ+zduxeZBw6azp07h6Nyb2/vGTNmXL58+eDBgwhIqlatit9vjBi0tZ5KKpAfoPDg347+G1oTq1evRiw0YcIEFB7sa6Rvi8hq6HbilwHfxrlz5x49ehR9JLwHDF8wGMI3XND/w3cJTVEM0Hv27ImcDG0uOSN9HHsh8UaZV/M0F/yKIsrV1pkO6qeD/EbVO2hpr+ro6NipUydpBnilSpVQY6QOJo7Ks2XLJl26GEFRjRo1vv32W2z7+PggFcRwQRj2oUKDcubMKf3b8S9FscEG8q02bdpIf8BhYWHVqlX7+OOPhaF3gdogzZTKJByQSiezjR07dtu2bfi2C8OiLxhpCcPoc8yYMYjfhGGHm/Qs5Dd4sDAl6K3htxHFRhhmRqMYyznjBMVGGNZ0wFgHu3WhSvi1RGor1GHhwoVan7Yi0cH6aRbTpk0TWiPtdlFsKlSoUKpUKWwjjUcGjm3sMVFj8PePlAidB+wN+/Xrh511+fLlz549e/jw4ezZsyOlxx+qtgZD2McVLFgQ/wphmBLYt29f/GOdnZ0jIyMXLVqEXjn+vP38/JYsWYJ/OFpwmf8H4iviI75i06ZNhaH2oyAh/kH7GAdZPXr0ePr0KQaX+NLoKaP+CZOEHwp+wfDdxm8jRt4YdsizSgqSJPx88YNA6ib9pFQFrWD8DaLfqPgpkRimu7i4vPfee0L78F3Fj1uLM4eS6H/9NOyRkfq4urpeu3YNcQhaUi1atECbCHE9IiLsppGfY9eJPabWr4aCfylCUQxEkGxLc3EwJEJAir0SepJFixbNwh3T/fv3kb7izxgjy+HDh+Nb+tlnn2FviwNblHlhkvB9RgCG8oOSj2ZvzZo1hfGhbYXa//XXX6t/FRki012vE4fq+FtFjUH8i2EQ9g5NmjRBRw5jILSq0CQ5deoUOleVK1fW6Jwh7P2RAyFdQGtx1qxZxYsXnz59OsoDIoe6detm7ZKjyGPz5s1769YtDJdx6I3YCV8UrU4MgDQ61yEzYmJiRo8ejaPROXPmSOciCmPCSOKPP/7AVxRqgsTR19fXeKe6vBOOMn/55ReUf6EXnH+jN2iMYC+JHQTq0IEDB/bs2YMj93r16s2ePfvSpUsINtBfQh1CocKGtN6PtqAw7NixA8fC7du3x1/jn3/+2atXL/wDcTv+OciNRDq9Of9GOnsYvWYMItFuQp8TPbcbN27gO4lPhclAscf3c9++ffiGoxig5SuMbO7cuVWqVKlfv75QB3R9R4wYITWB5YfWBXJcPV3CVQfzbzSZ3xgPeuI4HkcvXhjWSWvcuLG0i8Sfcbly5aQzFNB/Q4SOLiqO6GfMmIG9NqIU7FnQwkJuj2axmpMhR0fHqlWrSqEXhj7ofSHQwr/rn3/+GTdunLW1dZkyZf7++2+MgXLlypWWgnro0CH00PCaSbdIXTtkSw0bNpTWNcHrIFvCAW+RIkVWrFixbt26/Pnz44vi2F/H83yl717hwoUxPpauH7F37178e4034MNPYdmyZWhyImxTwy8hmtj4hxcrVkzIDkeE3bp1k/6QdYP5jal7+fLl7du3sffE3hkHU+jFjRw5Egd0qOKhoaFjxozBLwdGwdjLY7+jwlz3NdHR0TY2NnjD6M9gt4Uj5e+///7evXuDBw9G/w1j+TePFtM7/wZdDvT0UJVR2NBuklYJQ9cF4yH8Lel71ZajR49+8803+FcbdZ0C1PWbN2/ih4gdrjBJGATgN7ls2bKCVIb1xijQnkKYgV0qdqzYxZw4cQIJCg70Jk+ejKqDOoRjXkTKOMZX+Xg/KCjo4sWLiGRweI5Q+tdff8UABQUVh+o4eKxWrVomByjoXlpZWeGbsGDBAowUpVVb0MlEnZYGYfoTERFhb2/f3ADtJmEc+K1DB0/x68jh9wRjXPwVCLlgaI7fJfwiCd1hfkPpgxgDB/IYOmDE8+mnn+JvY9WqVRgbYRt9rVGjRmF4gUKFW6TpL2qD35bIyEjsLtFKRgtu6NChGN5t2bIFpXTIkCH4J0irhYqMwoujabB69WpEPhgjov+GBhHGPfgbU89k9SwRFxe3c+dO5F7oNJ47dw5xWpYPf3GsgN4dht0KrkewZs0avA3jldU34RcSvzZCj7h+GmUN7HHu3r2LhNPW1nbAgAEoOehoYc+L8RCO/YcNGyYMYyZjry2dAT/++KO/vz9yoAYNGuAwtkuXLmFhYRipoPYgKsfAKJOnR+/atQuBGUaEeEF8H4oXL46dl3RKgtAFhFjz58/HoAcj4KdPn2b5moEYYSxfvnzTpk1CCfhl+PPPPzt27IiRFlqvGBBLk7KzUL169Q4ePChtX79+Hb9y+lvvSsL108i4EN0/ePCge/fu2MZfbGBgICIi9KalDAANemQn+BWUs1/xmjfzGwz5c+bMiS7Z7Nmz0YtDZwOFc9KkSTjqxIF2ZkoFqjKakD169MA+unXr1jVq1Jg5cya+GxhUZeDMOhXavXs3hiNfffVV1h6hx8TEIBg7dOgQcrLXflXwc0F+JowGv7TPnz9HlonhKX70PXv2zNqxDhoDqGcoMPjXzZ07F0nqBx98IEitdHt2kD4kP7c1adkYabmEZ8+eCUMDClUHXbjt27cHBwdj547WVps2bRAaowwYe+aHMFxs9LVbkhKp8ePHJ93YsGFD6YqoKA/YrlChwqJFi3BQj/qBIUsaT9mqZCAMKyxs3LhRurwsig0GVfhX4wWxa8MxYLly5fANERqERKdkyZLSorQYlOCnXL16dZFp0lkYGGh27doVvcqkE5xQsNG2RRWXvqtZq2bNmqhz0rGF1AvF722WnxSO/A9lDL9IVapU+emnnxSc7iMDrp9GCsBfLypK3759hWFRnz179khX8MVeGA039GSEYfJHo0aN+vfvLwwDjiVLlkjXJ0YdElkqjeunodsmLQWPN3ngwAHpIDchIQH7CKRW2H78+PHXX38tNUZw+ztf0NnZWVpEByMbtIxmzJghDNOnMD6QlgFGVPbrr79idCg0pVChQtJ1RRGzI/zAiBb/KOlq7pmE4wAMBZAb4XcAwSFqG7bxylne4JJ89NFHr52OjE+z9lxejK1DQkKSOsz4iq1atRL6xfXTSBWkk8TwsWzZstKxKv620bzy9vaWhjjY+eLYH3dhkIG/SQwCMMi4d+/ejh07sHPHXiDD6629Of8mLe/W1dVVGI67EVm1bdtWuhE5EIol2tMY9AwcOBC7EuxzscNFvXznZbnt7e2lfzX+ddiTCkPRwnvDvxFHvthYt26dk5OThmb/4dAB3xxpoNa+fXvsW7NkETB8E/CDRi6I3wRp8IGIBT8IDApFlsKvBNpo+CpJhzho5aHZlYWrdVy6dAkHW0lr8uKfg38LftC9e/cWeqSD+TesN3omFRvsTbATl+oQdvT4a0RZwq4Zh7dnzpxBXw53YQOHh6hJtWrVun37NnIjBDDYQbwzbsFuEQ2xzJ9Nhy+H43opC0VVqFOnDgYuaNahYTJx4kS8vcaNG6MOYf+CZn1a0ho8DDtoFBtso1+HfR92TEWLFl27du2CBQvwfUCwjOhLhpZjZpgb4EcjDV5PnDiB0SQ6Y5l52/iBYiiJn770KTbu37+PAWiWz45EMxDHIr6+vtLXwkEDBtxZeKLHkSNHks4UEIYjDPzm4BgFvypCj/AN1HSxEaw3Jgj7L2nPgjEB9ghSHULgj4NoqXIgP0C9kcZD+/fvHz58OPbUqAQYJJ0+fRoHWcmrC17KGKdu4zWlZAg1r3PnzhiNYT+FQRj6CS9fvkS9xMgM+TCKSuHChTEAQl1MJbPB3rlUqVLSknF4bsGCBfGvyJUrFxpuI0eOxO3Ima9fvy4t8yxUCcVGGNIyvM8rV67gR4MNaZiYXhgC4nuY/BYMJdFYQ8kRWQ0REX6RpFEOjs2zdj4QfnwoZvjFwE/fzc0NDWT0Zj/88EOhU/jlRyM0a1c+lBnrDf0L+2upcqDjgeGFVIewN8efMYYCGCJgJIS0BgMF5NhbtmzBbw4GJegp79u3D4Ft9uzZpaaWMUgHxfgSKJDSvHG8MUQdqDfYBeM4d9iwYXgzaAodO3YMbRbsiN+2GA9eCk+RTjuuUKFCp06d8K/G6yBVQgiEQBu1BzkH/rEqPPsc7wfvWfrRHD9+HBle/fr139lsfM28efOkfbQwTKiSNtC3xD/cGAvcYZSJYobqiF8b/C6JrLNs2TIUMxzyN2nSBIPgdu3aKX75A6PC7zYONfC3KTSL50NTRmAo4Ofnhw00NJCRYEiEzhUOLdevX4/y0717dxwsX7t2DbdjYCHPfAhpqum5c+e2b99es2bNZs2aLV++HL1B7JQxbpOWtnvni0gr+vzxxx9o3PXr1w+7yMWLF6MAoyyp8Jy3qKgotARRPsePH4/deps2bdL4xBUrViAqQ03F0UO4QWRkZJmCzVrU6x4fn/jiSYzIai9evLS0tMjaoTDGtfihZMuWHa+c9mflcLNGnfUobF+hrsbWfef8GzJ1r82/wW7r5s2bGOhg1I9StGHDBhzSYme9cuVKVAJER2ivoy+H37oiRYoY+3rDqDE+Pj5o4yDw+O677/Bmvv/+e+TYeGN4hxglpGUxnpMnT+K4EqUUu3WMojAwws5dbbUH39KNGzd+9tlnyEuQeGXgtOCtix+45nXI7mzl4mGT+O7TAzXM3MIs6Gl0REjcjTPBXcflt7DSycRhTWC9ITkgMMA+Ee0OlJmtW7du3ry5a9euLVq0QEtEGoKgJKDLjwqEro6R1g5AhIABAZpyGAChY4bhC0rO/PnzhWHlfAxipHmRqbwCcnUUMMTRaNZhPIGa+tNPP6HcYoRn1CU40w6NzSFDhhQrVmzSpEl4Y28uAoTWE/pOeEzyG3evPf29ggAAEABJREFUfpIzt61XTdO6UlHQ05gDGx73/Kyg0Aiun0am7s3r36QLhkdXr14tZLBq1aqdO3diDIFMYsmSJWj4YDyE8oOChGKQsWz8ndD0w58xviJigB49eiA5//HHH9F5O3z4MAZGeFepPBfNdIwk8M9H/xCNOJQxPB3jIXThsnxZmnR5/Pgxwie8nzNnzuD7mfwscAzvUHEHDBjQpUsX6ZbLx4KDAuPLe+thgYb0enAj4un9iHqdjPKrleW4fhqZOuydscMdPHiwyFJ37tzB3rxcuXII8L/99lukKV9++SU61wsWLMCX69WrF0oCGkf4mLVXvUt6za+++urs2bPIOVDqZs2alS9fPlSjVAZeUvCDIAQPxkfpOg67d++uVatWlk9tSTu8AQxxMKY5cOAABnM5cuRAPxP/CmxMmDBBSu+3Ln5UulbOPIW0d/HAzIuLSfx13p1BX2ljfU/mN2Tq0nv9mwxLSEgwNze/cOECxkP16tXDcAQto0OHDq1evRo9OtQh7FhRErJly4YYPGvPU9q7dy+agUOHDsUbwJcuVaoUhl/ozl26dAmdKwwXUnxWWFgYEiNURzSvTp06tWnTplatWnl7e8fFxcl/lTkMQ9E5xJfGu5JuwbcIpRHlZ/PCR/U/8LCyNtEY4+9fH3u3d8vhZtwokSSsN6RtUkpx9OhRlIS2bdtidDJw4EC0yNCaQ1MLdcjR0RFZEZIh7GozP70GYxf09zBkwYBm+PDhyKV+++23wMDAtWvXVqhQAdUoxWfhwXiH2N1jqIGx2g8//NCnT5+WLVuiNObMmVO2Sy1giJP8DG/pskN/Lk38cFxhk43Ndyy936xHbpc8GrjQ37lz53B4h9RTaBbXT6NMSeP6acYj7ayR3mMPLp3xvGzZshMnTkjbxYsXR6aCQQa2UXVQD6TlTxYtWoQBh3SwhYqV9i/n4OAg9cfQPVu+fDmKjTBMekW8dPnyZWzfvHmzY8eOeH1sBwcHP3r0SHpwgwYNUGywjbwXQw0pGTp9+jTeOfry2MbTpRVIjQTF+LXpRAif5bwyDWUS+mkY3wst4/rQlCn+/v7S3lxVknasTQ2k7R07dmB0Ip2E7ezsfOvWLWm1HkQsONLHvRh/oDuHxKhx48bpum4Cyol0zQhAhw3l5Pnz59jGx9GjR6PdN2/ePAy/cHxarVo1fJq0THILAwyPhGHvj7gIMT4KAzp4uKVOnTpZmE6h8qEniX+UtbW1ra0tXllq66Wr3JKC0PzU+qXkWG8oU9AU0tAOK2nmKcY6STeePHlSWlQbVQolB2Mj1JuIiAh8RFTz448/ohGHalS4cOEaNWqkpQ4VMMAG9g4Y/En12MnJ6fHjxwcPHsSN+/fvx+iqffv2GPGg2EjvqqGB9M1EJoR+IIZNqIXIiqQ3nMmVLmvXro0GI9p3OXLkQI8Rr+ZosGtRnCAtMMbqDzJjfkOUMtQJtMvz58+P2rN06dKoqKhPP/0Uo4RevXphmPL5559Ll7/DgCa98yvxymiM4E8Pr4PaM3Xq1L59+/bu3fvs2bN4TdyY/IJA165dO3bsGDqBKFQff/wxRieTJ09GtcjkpbuTLBl3m/kN8xt5cHxDmZLJ+Tdqhj07io0wLGwqXaRHGBY23bhxo3SxO0RHCF2uXr2KeoOqMHHiRIQxY8eORWfs4sWLiI7ednkxvHLSFRykYQ2SHmG4KMM///yD4VSHDh3WrVuH10SbDmMsDw8PaXAzbdo0Hx8f6RgR9QmjsZ9//hlvD18O7+Gd5x20atUqX75833zzjcpXxaYUIb/x9fXl+QJkuvwNhClB9oNaIgyXOcBQA4MebKMqLFq0SLreF2KSAwcOrF+/HtsYsnTr1m3lypXCkKBgpCKlNa+Rykn58uUxbJIWUUbshA6YdPGYNWvW1K1bF40+fGlkRbdv30alQdn79ttvpQwGPTc8QBhGTlu2bMEDUnzn0dHRaB6iNYeiJUhrkN9I13bSLvbTKFNkm3+jUfjm3Lp1C2WgbNmyN2/eXLBgAUYYGAMdOnQIVQTHqqguqEPPnz9HPvS2qTzCcB42ag8qHJKkP/74A4MbhEno8uFG1A8XFxdpfhK+3OzZs/GCKH4IpX766afq1at7e3tLL1KxYkWET3gkfl49e/bs3LmzYD9NO/00HeD1CChTjHT9G91ADXB1dZVWlEFVwPGpdJnO3Llzo8BgvIINDEcWLlyIYSJqw969e1GTrKyscO/Dhw9RzvHtRaNMOqkMTyxRokTr1q09PT2FodH34sWLPHnyoA71799/7dq1KC2oYW5ubjiOzJkzJ17Tz88PgRCaflOmTMEL4qXwlkJCQtAJfPz4cZ06dc789bLse87mFiZab26cCS5aPpt9dpmmQGUG8pvz588jLxSaxfENZYqO8xtFhIaGXrhwwc7ODs2TI0eOLF68uF69egMGDPj999+PHz+O7zOKhzSn580xJfr7qDQ4Apg7d+7Ro0cx+kExQ1qDavf++++jhzZo0CDp5DrpsjeoPRjxVMwxnuMbTYxvdLB+Gs8XoExR5/wb7UJLDbGNtF3bQNpG98zGQBiOc1esWIFGHHpiW7duxdilffv2Xl5eqFLS6dRjDaRDydKlS1+5cgV5z6xZs5JO5pa6aoBRTrmanH+jDZx/Q6ZOW/NvtAsDF2l5AmhtIG1jHyQMl1rAx7/++guBzYgRI9q0abNx40YMg6QpPniMpaUlumfJ1xfA4Ab1BnXISFd/oCyng/k3rDeUKejYCFJOfgNp+yMDqfaUL18eG9LqnGvWrEH5kRYXEIbT56SBDgIhPExt18ymt+H6aWTqFF8/jV4jLdhTokSJbt26lSlTBtuffPIJsh/UmKRKIwwttejo6IsXL8bHG+tynnfu3KrfsMqlS6/OvZ42ffyYsf9e5K1t+4Zr1q4QWUH6EhcvnhcmgOunkaljfqMVBQoUuHfvnhTqoJmWK1cujE3r1asXfpkHndrA/IZMHfMbrUBvDWUGNQZRUO3atVFppGtgLxl3W5AWML8hU8f8RitcXFw6d+6MSlOqVCmRCZu3bFj/y6pPRk6cOm1cu3adhw8dExERMf/bL3x8zoSGhhQsULh587bt2r7/ztfZum3jnj07Hj1+UKlitVGffJojhzNuPH788IG//7x46XxISHCpkmU++qhfxQpVpMeHhIYsW/bdrt3bnZxyVKlcvX+/4e7ur//uoU2H97Zm9ZZcudyF7jC/IVPH/EYrNmzY0L9//0wWG2FY/C0iInzHjk0TJ8xo3/bVCgUTPh3x+PHDmTPmbdywy9u74Xffz752/UrqL7J79/aXLwMHDRo5aeIsFKqFi77GjVFRUZ9/ORmp0oTx07/4/Nv8+QtOmvzJixevlv+Ji4ubMHHE88Bn8+ctHT5s7NNnAfiiuDH5a+7bv2fV6qWfTfpCl8VGML8hYn5jaszMzFAYunTpWaniqyVHT5w8eumSz8oVvxYq9Cpa6Na198lTR39as/yrL75L5UXs7O179/p38mmrVh02bV6P3yJbW9sVyzfY2dlhBIPbMb7ZvmPTpcs+db0bnjh55Nq1yz+t2oQihLvy5Suw8befpVIk8fE5O3vOtIEDRrz3Xl2hU8xvyNQxvzFNJUv8ewmGu3dvoU5IxUZSvFip/Qf2pP70KpVrJM378fIqG7shFmMXjzx5MXJa8eNCnwtnAwOfS/cGBb3Ex9u3b9rb20vFxvAlSk7+dJZ4FUqF4uP9B35Ll33bsEGzLh/0EPrF/IZMHfMb04SumrSBwmBr+z8XIUVhiIyMSP3p9vb/XbnHzs5evLr2dpCFucXHn/RDnIOeGIoQClLjpjWkx4SHh9nYvPUaCujgobeWM6eL0DXmN2TqmN+YOAcHh6ioyOS3hEeEu7q4pf6s5E9BLRGvrsiQ4+A/f6GrhvCmfPlKVlZW0thFgvqEGpaQkPJUoaZNWo0eNemXDT+dO39a6JcO8hvWG8oUE7z+DSVXorgX4pybt24k3YKgpWChd8QMt5I9/saNqxgtubnmCgkJzp7dEfmNdPs/h/YnPaZkiVdf5YbvNenT+/f9Ro4agCab9GmTxi1btWzvXafB519MDg4JFjqlg+vfsN5QpiC/adOmjSBTVa1aLQ8Pz/nzP79+4yoC/B9XLka9+eD9j1J/1l2/2wj8kfz53rz+596dKBWGSzAUQ3dux++b0Rw7eerYuXOnMOh5+vQJHl+lSo28efMtX/794SN/nz5z4tvvvnr2NKBAgULJX3Pc2KmWlpZfzZ4qdAr5TYUKFYSWsd5QpiC/4cXWTBl28bNmzHN0dBoytGfX7m3Onjs1c8bXZcumtluMi4t9v1O3K1cuNmpSfdTogWXLVBg2dAxub9ig6Ufd+65Z+wNim82b148YPq5xoxbrf1k9/5sv8FW+nrM4ITFhytSx48YPs7Wz+/KL76RrmyZBZ2/qZ1+dPHn08mVtN53eBvkN2tdCy3j9G8oUXv9G63h9T17/RjY8P40yhfNviOTB+Tdk6jj/hkgenH9Dpo7zb4jkwfk3ZOo4/4ZIHlw/jUwd8xsieTC/IVPH/IZIHsxvyNQxvyGSB/MbMnXMb4jkwfyGTB3zGyJ5ML8hU8f8hkgezG/I1DG/IZIH8xsydcxviOTB/IZMHfMbbUsU2XJYmvJhp52DhdAI5jdk6pjfaJuZMDMTYS/jnFythEl69jDKMac2doM6yG/YT6NM4fVvtC5vUfuQwFhhkiJC43N52lrZaGM3qIPr37DeUKYwv9G6ak1ynvgjQJik4zuflvPOITRCB/kN6w1lir+BIM1ycLJoOyjv9iX3YyIThCn5e4N/ySrZi5RzEBqB/KZ58+ZCy3h9T8qUJ0+eIL9hS03r/P2iTu55EfoiNn/JbBGhcUI2ia/2QGbm8l1d1C67hf/tSGtb89I1HEtWzS5IRqw3RPSvl09jXzyJiYuRb6Bz9uzZBw8eyHk9cnNLsxyuVi4eNuZaa+7oYP4Nz0+jTEF+ExMTI+f+gozHOZcV/hMyuvYwKPbZvRJVOM54N+Q3vr6+rDdkujj/hkgenH9Dpo7zb4jkwfXTyNRx/TQieXD9NDJ1nH9DJA+un0amjvkNkTyY35CpY35DJA/mN2TqmN8QyYP5DZk65jdE8mB+Q6aO+Q2RPJjfkKljfkMkD+Y3ZOqY3xDJg/kNmTrmN0TyYH5Dpo75DZE8mN+QqWN+QyQP5jdk6pjfEMmD+Q2ZOuY3RPJgfkOmjvkNkTyY35CpY35DJA/mN2TqmN8QyYP5DZk65jdE8mB+Q6aO+Q2RPJjfkKljfkMkDx3kN+ynUaYgv7l37x5G+oIo/ezt7a2srAS9S2xs7Pfff79v3z6hZaw3lFlxcXHjxo07e/Ystv38/ARRmn377be9e/cW9HYnT57Ex0OHDqFxXa9ePaFlZomJiYIo0yIjI+3s7KZOnXr+/Pn169dny5ZNEKVq/PjxTZs2bdCggaCUBAUFNW7ceDDijpoAABAASURBVODAgf369RO6wHpDWezx48c5cuRAnwTRTqtWrQYPHiyI3rB27doXL158/PHHgv7X0qVLN27ceODAAekYTugI+2mUxTw8PFBssLFmzZq8efNi4/bt27Nmzbp69aogMsAgGA0iFpskgYGBy5Ytu3btGrbxVyPNMdBZsREc35AM4uPjf//99ydPngwaNMjHxwddAq23oSkzEPjVrl37xIkTwuQFBwejH1CqVKlvvvkGLegePXrY2NgI/WK9IVk9evQIf1qFChUaOnQojuaKFStmacmT8k1L9+7dJ0+eXLJkSWHaMMKbMWPGF198Ua1aNWEaWG9IMTt37kSfDW2E8uXLR0dH6/vIjiRfffVV0aJFO3XqJExSeHj4nDlzwsLC5s2bFxAQ4O7uLkwJ6w0p7Pnz566ursOGDcP27NmzHRwcBOnUH3/8cerUqenTpwsTc/369X379uGXHOP7CxcuNG/e3MzMTJge1htSCzT0S5Qo4ezsjFZbgwYNOnbsKEhH7t27N2rUqM2bNwuTgepib2+PX+mBAwc2adKEv9KsN6Q6Pj4+R44cwcGgv7//X3/91axZs1y5cgnSuPr16+/YsSN79uxC72JiYqytrefPn4+EZuXKlTlz5hRkwHpD6oVQZ/ny5U+fPp05c+adO3dwS+HChQVp0IgRI7p06VKrVi2ha7dv3/7++++bNm3aokULPz8/Hax4lrVYb0gbbt269emnn7Zq1apHjx4mGLRqGg4a8HHAgAFCp44dO/bkyZMOHTr8888/VlZWui+rGcb5nqQNRYsW3bhxY+vWrbF94MABbCCDFaR62BdfvnxZl8XG19cXHy9cuLBhw4ZixYphu27duiw2qeD4hjQJ0U5UVFShQoUmTJiA/vjw4cP1NxlbB0JDQ9u0afP3338LHYmPjzc3N8dopnjx4rNnz8anFhYWgtKA9Ya0DXu03bt3165d28PDY+7cudioWbOmIHXo1KnTvHnzChQoIHRh3759P//887fffuvo6Pjo0aN8+fIJSg/200jbsmfP3rlzZxQbbJcuXVo63TYoKOjgwYOCFDV16tTevXvroNjs3btXupAzgsOxY8fmyJED4xsWmwxgvSH9aNGixddff40NGxubnTt3ShdWwT4iLi5OkPHh+5+0vWnTJnQ4W7ZsKTTr3r17+LhgwYJ//vnH09MT2926dcMxjaCMYr0hHcKeDoVn1apV2H727BmabFu2bBGGiRGCjGPHjh34Vr/33nvYvnHjxrZt2xCtCW26fft248aNz5w5g+1hw4Z9/vnnLi4ugjKNSyWSzpUpU+bEiRO3bt0ShmuunDt3bty4cbpJFNTj2rVrCQkJ0dHRlSpVsra2PnLkiNAUvPmVK1fevHlz9uzZGB9v3LjR2dkZt5vmwjNGwvENmYSiRYviY9++fXv06IF0Rxj6JBs2bIiPjxeUFVDRpZOPkG2g6rRt21ZoQXh4OEpLbGxsWFgY+q4jR47EjeieScWGshbrDZmW6tWrly9fHhuIFh4+fOjn54ft33777cGDB4IyKjQ09OnTp6g00qcWFhaIzVR+oejAwEB8HDhwIH4HLC0tHR0dBw0alCdPHkFGw3pDJqpw4cJjxowpUqQItkNCQkaMGIGNyMhI9O4FpRO+aRgoJL/F3t5eteuGbd26tWrVqtIw9+eff0Z/lU0zeXD+DdF/IiIievfujXbKvHnzsAPlxRHSaPv27V988QWak9ifODk5IV3v0KHDhx9+KFTj5cuXP/74Y65cudBQvXjxYtmyZVlj5MfzBYj+g6PyX3/99cmTJ8KwWsm0adOGDx/eqFEjQam6fPlyTEwM9ua5c+du165d+/bthTqgZYrq0qJFi0uXLuEwAu8NN5YrV06QEji+IXqrR48eIdepUaPG+vXrsYGhj8xXRnh4M/LJvaio8PiIUFWf13DlytWEhHiPPB4urmk6b9je0TKHq1XxStmsbY3S0sc4FYcO/v7+gwcP7t+/v6anAekJ6w3Ru0VFRf3+++9ubm716tXbuHEjjpRlWJZx34aniQlmVjbmrnlt4mN09XeakJj47EFUwP1I7/ZuBUrZiyz12WefnThx4q+//uJFytWG9YYofU6dOoWQeeDAgaVLl8Z+DaMfYQR///bMysaifF2dX6pr/y+PK9Z1LlAqs2utovmJMWiXLl1KlixpvB8KZRLrDVFGJCQkmJubf/nll1u2bDl+/Lh0o6Vl1gSiFw8HBz6Jq9LEJOa0b/7Wr8vY/Lb2GWmsXb9+PTIysmLFisuXL/fw8GjVqpUgFWO9Icos1B6k5Wi1dejQYdy4cVIpEpmwbvZ97w65c+SyFibg7F+B2Z3NKzdMx/zKly9fOjs779ixA71NdM9KlCghSAs4/4Yos1BdbG1t0caRzmQ7f/78sGHDpNW3MiA+VsTHJZpIsQGkU8HP/2dBVYT8TZs2TfHBgYGBffv2lS4YWrduXTQ2WWw0hOdDE2WZSpUq4WPlypVjY2MfP34sDEvZYxfZrl27VC4Hhyho2bJlSZ9GR8XHRicIk2FpbR76Mjbp05EjR54+ffq1xyD8P3r06LRp06Kjo0eMGCGtEOHk5CRIUzi+Icp6yKvbtGmDjQoVKqDw/Pnnn9g+dOjQo0eP3nwwdq8YDwkSYsKECdJCn1KfH0NGaRUAfOukc5oR0kjFhrSI9YbIiHLlyjV69GhpmiGS7aFDh167dg3bScu1oXGEdtzJkycxyhGmbcaMGf/884+0bWZmhpqNdpl0QvPMmTOrVq0qSONYb4hkgtKybds26VII33zzTYcOHdAdevHihTAczp87d65Pnz7CVM2ePRtNM/Qhk26JiYlZuHBhKn1I0hzWGyJZ2du/mt44f/78b7/9FkfxSRdEQMnx8fHp37+/MD0Y7e3YseO1FT9Jf1hviJSRP3/+tm3bJj9zGttnzpxB/02YGPzDixQpki9fvjx58ri5uWXLls3CwgLF2NvbW5CO8Pw0IsU8f/5cGKbvCMM+19ra2sHBISAgQOQWJiVv3rxrZq7BRlBQUGBg4JMnT7CBj3379hWkI6w3RIrBsTwKDI7l3d3dixcv7unpiVtccngc2WCis7BzGEgXJSL9Yb0hUsyuXbuCg4Nfm0diWAr6viDSHdYbIiVx0iKZDp4vQEREcmC9ISIiObDeEBGRHFhviPRgzdoVnTo3a9Ks5p07t+o3rHLx4nmRUdOmjx8zdgg2Mv9SRMnxfAEizYuOjl61emnTpq2aNWmdI4dzj4/65cqVBVN4svCliATrDZEOREZG4GP1au9VqFAZG717DRJZIWdOl6x6KSLBfhqR1t2/79e+Y2NszJg58bV+2tZtGzt0aoIH9O7bGTf27d9lz5+/S88KCwvDkGjw0J7NW9bu/lG7xUu+iYqKeu2Vk14qIiICG6/9t/OPrdLD8JpDhvXC6+Djps3recng/2PvzsOjqu89jv/O7Nkm+waBsIZ9CZHLpQoICrXClYdb4PF6rdxWRe+ttW7XxwX1orRaKPR5KvhYKl5FKYoPSlstVDCogAraihChRgiLJCEEkiHbrGdOf0NiCCRo/8g5PZnzfj3zTGZ+Zxn4Y85nvr9zzu+HS6G+AXq2vn37vbFxq4ycRx95cuqV02VItC9yOp1NTY2/fnrp/977yLBhI196ec3SZY8Xjx2fm5v3+huv/G79Cw8/tCQ1NU2u8/TKZXa7/baFd3b5EW63e8XyZ9vfvv32W1u3/amoaJh8ve2dLb9Yunj2dXN/9sSKI0cPL122uPpk1U9+fJ8AOqG+AeJZOBxecNPC4cNHKYry3RmzZPFx6NAXsn3+vBufW73+yilXF4+9bNIVU6deOWPPxx9caicyiuRqrY+UZO87pVvuvuvBosFDRWyIhE2jRxff9dMH0tMzxhWP/+GC2zdt2lBfXyeATqhvgDg3dOiI1hcpKV4R60lrFOdKn48/+fCpXzx26HB5JBKRLTIwvnVXsmNt0aP3zJg+c+a1sRnkotFo2eef3fSD83MoFBePl4379n86ZfJVArgQeQPEOVnZdG5c/dunZWly220/HX/ZRNm99tyaVX/a/Ptv25NY8vOHU71pspppfRsKhWT9tOb5Z+Sj42rUN+gSeQNYjuxV++ObG+d+/4ZZM+e0trQWPd/s1Q0vHTxYtvrZdQ5H23HD4/EkJibKcmfyhdVMr/wCAXRC3gCWI4sSv9+flZXT+laWKR98+P43b1JW9pksYn61/DfZ2Tkd2wcOLGpsapTnddr3XF1dmZOTK4BOuF4AsByXy9W3b7/NW/5QWXXi7Fnf0l8+Pmrk2MbGhkvN6Ozz1T+2+P4pU64OhUOf7v2k9dF6IdytN9+xa9e7si9OnrbZv3/v4088eM99t8sAE0An1DeAFT3y8M9XPbP8v344V/aJ/c9/3zN27GV79nww5/tXv/jCxs4r7969q67uzLZtm+WjvXHypGmL/2/pqFFjZQ/but/9/29W/zoQ8I8YPnrJEyvcbrcAOlG4OQswlZZGdf2y4/Pv7S+sofJQyxcf+2bf3ksg3tGfBgAwAnkDADACeQMAMAJ5AwAwAnkDADACeQMAMAJ5AwAwAnkDADACeQMAMAJ5AwAwAnkDADACeQMAMAJ5AwAwAvMRAOaSmGyPBKPCMoL+aHIqByJLoL4BTEYRGfnu+hqrTFlWfzKY2Zv5ciyBvAFMZ8zk1P0764QFaJoo+7B+7ORUAQtgvjXAjP5S6jtTHZ44K1vEr3Awun1D9ZQ52Vm9XQIWQN4AJrXnz3VnqkOKTckuSAgHVRFHNKGcOt7S7ItMvzE3m840yyBvAPOqrwnXHA80+SLypLrQmc/n++ijj6655hqhv4QUW0aOq3BYkkKPvpVwWQhgXum5TvkQhigvP7Nuy1uXX/efAtAHvy4AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARiBvAABGIG8AAEYgbwAARnAIABDCbrc7nU4B6Ia8ARAj86a5uVkAuiFvAMQ4HI5IJCIA3ZA3AGLIG+iNvAEQQ95Ab+QNgBjyBnojbwDEkDfQG3kDIIa8gd7IGwAx5A30Rt4AiJF5o6qqAHTDeDYA2tjtdiIH+iFvALShSw26Im8AtCFvoCvO3wBoQ95AV+QNgDbkDXRF3gBoQ95AV+QNgDbkDXTF9QIA2rTnzfXXX79w4UIBdCvqG8Dqxo0bJ58VRZHPc+bMsdlsqqrKyBFAt6K+AaxuwoQJytdk2MiWPn36kDfoduQNYHW33HJLZmZmx5bx48cXFhYKoFuRN4DVlZSUjBkzRtO01rc5OTnz588XQHcjbwCIBQsW5Ofnt76W8TNkyBABdDfyBoAYOXJkcXGxLHFkx9q8efMEoAOlvYgG0FPsfa/h5FG/v1EPGp89AAAHSElEQVSNhKOhwPkRnRW7UGxKNHz+Sx276MyuaJG2FptdRFW5mqKpF7WIoD9UXV3l9rjz8/LlUUHuJ3Z4UM/vJ9bYYcP2zeWyaKSLw4jTY3e5bWnZrv7DkgpHJghYHnkD9Bh/eLa6+lhABozNrtgdNsVuUzSZFh2+wjIVhKZoyiVb5F/tXIu4sEW5cKsY7VzIiI6ryQOGuGg1RbRu3/lfGwsneXiJaqoalYsTvY6i4pTv/FuGgFWRN0AP8Mryr06fCDrc9pTs5N5DMoRd9CzN9aHaI/UtZwOyaho63nvl3CwB6yFvAFPbs7l+z9Yz7kRn4bheroQef8L19JGG08d9Doe4ZUl/AYshbwDz2vCryjPVwb6j8pKy3CKOHN9X21TbfM1N+QNGJwpYBnkDmNSWtae+Km8ZfHkfEZcC4vNdR29+dIDHqwhYA3kDmNG6p040NUSHTOot4tqBd45OnZs77F+TBSyA+28A09n0TFVzYyTuw0YaflW/7a/VtJwVsALyBjCXijJ/ZYW/6Io47UbrJLMwbe2TFQIWQN4A5vL2S9VZfVOFZeQOTlMU2xurqgTiHXkDmMi29ac0oeQOThdW0n9c76oKv0C8I28AEzm0tym9l1dYjCvZ5nDZ5VkrgbhG3gBm8eWnzWpEyytKE2a17On/2PjHpUIH6b29J49R4sQ58gYwi0/f87k8Fp3iPWdgqhoRlV8GBOIXeQOYRX1NMCnDuuMo2522z3b4BOKXRX9MASakhrX0/BShD1WNbN727MHyXT7fyf6FY74zYd7wIZfL9uqaw8tX3nDnbc+Xvv9i2cH3Ur05Y0dNv3b6j+322JigJ09VvLLx8ZraI4MGlFw95UdCT84E59nTYYH4RX0DmIK/SWialpDuEvp4481f7vhw/RUT5j1076ZRI6atfeWBfWWlst1hd8rn137/ZPHo7z712M4b5i5+b9e6zz7fJhsjkfBza+9KS825/85XZ864492dLzc2nha6cbkcLU2qQPwibwBT8NWGhG7C4eAne9+aNmnBxH/596TE1Akl18l02frumvYVxoyYNmbkVQ6Hc2D/cZnpvU9U/k027j+w3Xe25rrv3Z2elpeXM2DOrPv8gUahG5vTFg5HBeIXeQOYghabZVOvkSu/qjoYiYSKBk1obxnYb1x1zaHmr0eSKeg1rH2Rx5PSmiunz3zlcnoy0vNb270pWWmpuUI/NkVhNMe4xvkbwBS86R6h29E2IHvrhFj13MKL2hubzthtsYOAonTx07PF3+ByXzBfgNPhEbqJhqM2O7+A4xl5A5hCcoYS1bRQi+pK7P7JO73e2Hyac2c/mJVxwbBs6al5DZc+JZOY4A0GWzq2BILNQjehgOr2kDfxjLwBzMLhUHyVDTk6DGaTndnX6YzN2DZoQElrS2NTnaZpblm+XPqMTHpafjgckN1u+bmD5NvK6vKGxlqhm7A/mFYQV9PK4SL8mgDMIsnrOFvbInQgc2XG1Fu3bl9TcWxvOBLaV1a6+oWfvP7mt4wUMGLYZIfD9dqmJ0OhwNmG2pc3LEpM1HEg0UhYHVqi1+XgMAPqG8AsBhen/KW0Tuhj6qQf9Mov2r5j7ZeHP/Z4kvv1GTVv9kPfvEmCJ/nmG1e89fbKRT+b5nJ6Zs6446/7/qzTJQ0NJ/02mzJiInkTz5jfEzCRVfce6jM615uTKCymfOcJd4JYsKhQIH7RnwaYSG6Bp/pvOt5TaVohf3j2zfE/n6nF0Z8GmMjcuwtW3nPI7wslpHU90MDK1beerO1iNsxoVJV9FXZ719/oB+7amJzUbcNOl77/YumOtZdYKPvbuu4yuf/OV70pWV0uOry7ypvuTMvncBTn6E8DzGXry6fK9zaOuKpfl0sDgWZN6/omfFWNXCpvEhK687xIOByMRLoeDSEY8rtdXQ856nYn2WxddKiEWtTyXcfvWDFIIN6RN4DpPP/YUZvT2a8kT1jAgdJjxVPSJs7KEIh3nL8BTOdHi/sFm0JVB+N/cP4vdpzILfQQNhZBfQOY1G8XHUlISSoYnSni1IF3jhVPy5x4rY739MBUqG8Ak7p1Sf9mX7M8ly7iTrBZPbj9WJ6sbAgbK6G+AUxt/dITdTWBzIK0vKHdP87NP0XFnupAY7BkWsaEa+Pkf4R/EHkDmN2B3U07Xj8VUbXktMSCMTn2nnnZcEON/1RFfbAllJrhvPGhvgLWQ94APcPuLfX73vcF/KrDYbO5HO5Ep8NlUxyKpp6/PFpROn2jNUV8+6wyipBbnRupRhOtf2Nz8XQ+NnSx/2/4BLmjsAgG1UggoqqqXMeb5fzegryMPKeAJZE3QA+zc1NdVUVLU0NEDWvRqBYJdcgbu9AumpHZpojoue/41zdi2pTYxAcdV7kgML5eTbGJzvf5tIXQhfd0dhlCsQ+yC6fL4fIoadmuQaNThk9MFrA28gYAYASuTwMAGIG8AQAYgbwBABiBvAEAGIG8AQAYgbwBABjh7wAAAP//KuYlTQAAAAZJREFUAwByOnMuhmxExQAAAABJRU5ErkJggg==" />


## Deterministic scenarios

Each run gets a fresh runtime and mutable workspace. The graph checks the locked scenario record, then compares the complete ten-field record with another fresh runtime executed by the sealed `SelfHealLoop` core. The notebook prints only a compact matrix; `show_record(name)` is available when you intentionally want one complete public record while debugging.



```python
# Give every scenario a fresh runtime and workspace so mutations cannot leak
# from one example into the next.
langgraph_records = []
for scenario_name in SCENARIO_ORDER:
    runtime = new_runtime(scenario_name)
    # invoke starts one complete transaction from the caller-supplied state.
    final_state = graph.invoke(
        {
            "runtime": runtime,
            "initial_failure": runtime.scenario.initial_failure,
            "diagnose_role": runtime.diagnose,
            "draft_role": runtime.fix,
        },
        {"recursion_limit": 64},
    )
    # Validate all ten public fields, not only the compact matrix shown below.
    record = trace_record(scenario_name, final_state["trace"])
    assert_expected_record(record)
    # Run the sealed core on another fresh runtime and require exact record parity.
    core_record = trace_record(
        scenario_name,
        run_core_reference(scenario_name)[0],
    )
    assert record == core_record
    langgraph_records.append(record)

assert [record["scenario"] for record in langgraph_records] == list(SCENARIO_ORDER)


def _record_named(scenario_name: str) -> dict[str, object]:
    try:
        return next(
            record
            for record in langgraph_records
            if record["scenario"] == scenario_name
        )
    except StopIteration:
        raise ValueError(f"unknown executed scenario: {scenario_name}") from None


# Full JSON stays opt-in so the default notebook output remains focused.
def show_record(scenario_name: str) -> None:
    """Opt in to one complete public record when debugging."""
    print(
        json.dumps(
            _record_named(scenario_name),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


print(format_scenario_matrix(langgraph_records))

```

    scenario          status                         apply  verify  rollback     restored  reason
    ----------------  -----------------------------  -----  ------  -----------  --------  ----------------------------------
    convergence       fixed                          2      2       -            -         verification_passed
    critic_block      blocked_by_critic              1      1       c1           yes       review_rejected
    no_progress       rolled_back_no_progress        1      1       c1           yes       no_progress_same_failure_and_patch
    regression        rolled_back_regression         2      2       c2 -> c1     yes       blast_radius_exceeded
    round_budget      max_rounds_human_handoff       2      2       c2 -> c1     yes       round_budget_exhausted
    stage_error       stage_error_human_handoff      1      0       c1           yes       stage_error:verify
    rollback_failure  rollback_failed_human_handoff  1      1       c1 (failed)  no        review_rejected


### What the matrix proves

- Convergence is the only scenario that leaves repaired state committed.
- Five of the six non-success scenarios prove restoration of the baseline.
- Rollback failure becomes human handoff because restoration cannot be proven.


### Walkthrough: convergence

Follow the two apply and verification receipts to see a second-round repair become the only committed success.



```python
print(format_scenario_walkthrough(_record_named("convergence")))
```

    scenario: convergence
    outcome: fixed (verification_passed)
    round 1: apply c1 patch dda1f6b5; verification failed e7e8a9de
    round 2: apply c2 patch f3926b7d; verification passed
    baseline restored: -


### Walkthrough: no progress

The second round repeats the same failure-and-patch pair, so the duplicate guard stops before another apply and compensation restores the baseline.



```python
print(format_scenario_walkthrough(_record_named("no_progress")))
```

    scenario: no_progress
    outcome: rolled_back_no_progress (no_progress_same_failure_and_patch)
    round 1: apply c1 patch 7bbc2763; verification failed 1e0be10a
    rollback c1: succeeded
    baseline restored: yes


### Walkthrough: rollback failure

The repair does not converge, and one failed rollback receipt means restoration cannot be proved.



```python
print(format_scenario_walkthrough(_record_named("rollback_failure")))
```

    scenario: rollback_failure
    outcome: rollback_failed_human_handoff (review_rejected)
    round 1: apply c1 patch bd0a4ab7; verification failed c924ae82
    rollback c1: failed
    baseline restored: no



```python
print(
    f"{len(langgraph_records)} scenarios matched the sealed core "
    f"across all {len(RECORD_FIELDS)} public fields"
)

```

    7 scenarios matched the sealed core across all 10 public fields


## Optional real model

Only diagnosis and patch drafting cross the model boundary. The provider returns schema-bound values; deterministic code still owns review, apply, verification, rollback, stability, and terminal status.

### Response schemas

These Pydantic models describe the only provider response shapes accepted by the adapter.



```python
# These schemas validate provider response shape; they neither approve a patch
# nor grant permission to mutate workspace state.
class DiagnosisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnosis: str = Field(
        min_length=1,
        description="One concise diagnosis of the deterministic failure",
    )


# Keep replacements under payload.set to match the strict patch contract.
class PatchPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    set: dict[str, str] = Field(
        min_length=1,
        description="Nonempty map of canonical relative paths to replacement text",
    )


# Shape validation happens here; parse_patch_json later enforces canonical paths
# and exact agreement between touches and payload keys.
class PatchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1, description="Patch intent")
    payload: PatchPayload = Field(
        description='Structured payload containing exactly one "set" object',
    )
    touches: list[str] = Field(
        min_length=1,
        description="Canonical relative POSIX paths matching payload keys exactly",
    )
```

### Parse schema output through the strict shared boundary

Provider parsing errors are reduced to schema-only messages. Raw provider text and invalid paths never enter `StageError` or saved notebook output. The nested `payload.set` object is serialized locally, then the existing strict parser remains authoritative.



```python
# Invariant: provider-controlled errors never cross this schema-only boundary.
def _parsed_structured(result: dict[str, object], schema):
    # The adapter result may contain raw, parsed, and parsing_error entries; only
    # the validated parsed value may leave this helper.
    parsing_error = result.get("parsing_error")
    if parsing_error is not None:
        raise ValueError(f"{schema.__name__} structured parsing failed") from None
    parsed = result.get("parsed")
    if not isinstance(parsed, schema):
        raise TypeError(f"expected parsed {schema.__name__}") from None
    return parsed


# Re-serialize the Pydantic value so the shared strict parser stays authoritative.
def parse_structured_diagnosis(result: dict[str, object]) -> str:
    parsed = _parsed_structured(result, DiagnosisOutput)
    try:
        return parse_diagnosis_json(parsed.model_dump_json())
    except (TypeError, ValueError):
        raise ValueError("DiagnosisOutput strict validation failed") from None


def parse_structured_patch(result: dict[str, object]) -> Patch:
    parsed = _parsed_structured(result, PatchOutput)
    # Rebuild JSON from parsed fields locally; never forward raw provider text.
    payload = json.dumps(
        {"set": parsed.payload.set},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    raw = json.dumps(
        {
            "description": parsed.description,
            "payload": payload,
            "touches": parsed.touches,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    try:
        # The shared parser enforces canonical paths and payload/touches agreement.
        return parse_patch_json(raw)
    except (TypeError, ValueError):
        raise ValueError("PatchOutput strict validation failed") from None
```

### Bind schemas to the provider model

`include_raw=True` keeps the raw response transiently available to the provider adapter, while the notebook saves only bounded summaries.



```python
# include_raw=True asks the model adapter for a raw/parsed/parsing_error envelope;
# the strict adapters inspect errors but never expose raw provider content.
def build_structured_role_models(model):
    return (
        model.with_structured_output(
            DiagnosisOutput, method="json_schema", include_raw=True
        ),
        model.with_structured_output(
            PatchOutput, method="json_schema", include_raw=True
        ),
    )


# Prompts request diagnosis and patch proposals, never transaction decisions.
DIAGNOSIS_SYSTEM_PROMPT = (
    "You diagnose a deterministic CI failure.\n"
    "Return one concise diagnosis through the supplied response schema."
)

PATCH_SYSTEM_PROMPT = (
    "You draft one atomic patch from a diagnosis.\n"
    "Use the supplied response schema with one nested payload.set object; "
    "payload paths and touches must match exactly."
)

```

### Run the same graph with model roles

`get_model()` returns `None` and prints one skip line when the configured provider has no API key. On a live run, only clipped diagnosis, patch, and result summaries are displayed; the complete trace remains available in `model_state` for deliberate inspection.



```python
# Missing credentials return None, so the same notebook remains runnable offline.
model = get_model()

if model is not None:
    diagnosis_model, patch_model = build_structured_role_models(model)

    # The model receives failure facts and may return diagnosis content only.
    def model_diagnose(failure: FailureSignal) -> str:
        result = diagnosis_model.invoke(
            [
                SystemMessage(content=DIAGNOSIS_SYSTEM_PROMPT),
                HumanMessage(
                    content=json.dumps(
                        {
                            "kind": failure.kind,
                            "error_text": failure.error_text,
                            "affected_files": failure.affected_files,
                            "code": failure.code,
                        }
                    )
                ),
            ]
        )
        return parse_structured_diagnosis(result)

    # Drafting receives the diagnosis and returns a proposal; it never applies it.
    def model_draft(diagnosis: str) -> Patch:
        result = patch_model.invoke(
            [
                SystemMessage(content=PATCH_SYSTEM_PROMPT),
                HumanMessage(content=diagnosis),
            ]
        )
        return parse_structured_patch(result)

    # The unchanged graph still owns review, mutation, verification, and rollback.
    model_runtime = new_runtime("convergence")
    model_state = graph.invoke(
        {
            "runtime": model_runtime,
            "initial_failure": model_runtime.scenario.initial_failure,
            "diagnose_role": model_diagnose,
            "draft_role": model_draft,
        },
        {"recursion_limit": 64},
    )

    # Bound saved provider text so the teaching result stays compact and skimmable.
    def _clip_summary(value: object, limit: int = 160) -> str:
        text = " ".join(str(value).split())
        return text if len(text) <= limit else f"{text[: limit - 3]}..."


    live_trace = model_state["trace"]
    print(f"diagnosis: {_clip_summary(model_state.get('diagnosis', 'unavailable'))}")
    candidate = model_state.get("patch")
    if isinstance(candidate, Patch):
        print(
            "patch: "
            + _clip_summary(
                f"{candidate.description}; files={list(candidate.touches)}"
            )
        )
    print(f"result: {live_trace.status.value} ({live_trace.stop_reason})")

```

    Model: ernie:glm-5.1


    diagnosis: CONVERGENCE_1 failure in app.py: an iterative process (e.g., optimization loop, numerical solver, or training step) failed to converge within the allowed ite...
    patch: Fix CONVERGENCE_1 failure: increase max iteration limit from 100 to 1000, relax convergence tolerance from 1e-10 to 1e-6, add stall detection with best-resul...
    result: blocked_by_critic (review_rejected)


### Compose as a subgraph

The compiled graph is a normal LangGraph runnable. A parent workflow can place it behind a deterministic failure detector and inspect `trace.status` before deciding whether to continue, ask a human, or halt deployment. The parent should pass fresh role callables and runtime state for each repair transaction.

```python
parent = StateGraph(DeploymentState)
parent.add_node("detect_failure", detect_failure)
parent.add_node("self_heal", graph)
parent.add_conditional_edges("detect_failure", route_failure, {
    "repair": "self_heal",
    "healthy": END,
})
```

The same graph shape supports deterministic fixtures and real model roles because policy authority never moves into the model.


## What to remember

- Self-Heal is a bounded transaction, not an open-ended autonomous retry loop.
- Models may diagnose and draft; deterministic callbacks own review, mutation, verification, rollback, and status.
- A duplicate `(failure.signature, patch.digest)` proves no progress before another mutation occurs.
- Addressable apply receipts are retained even when their binding is invalid, so compensation can still run.
- Restoration is a proof: every known apply must have a valid rollback receipt, no mutation may be unaddressable, and the final digest must equal the baseline.
- The seven executed graph records match fresh sealed-core records across all ten public fields.


## Further reading

- [LangChain tutorial](../langchain/tutorial.ipynb) — the same transaction contract expressed with LCEL stages
- [Pattern README](../README.md) — design rationale and framework-neutral public contract
- [Reference implementation guide](../../../REFERENCE_IMPL.md) — repository conventions and verification commands
- [LangGraph `StateGraph` reference](https://docs.langchain.com/oss/python/langgraph/graph-api)
