# Self-Heal Loop with LangChain

> A repair loop is safe only when every attempt is bounded, receipt-bound, and compensated before a non-success result escapes.


## What this pattern does

Self-Heal starts with a known failure, proposes one patch at a time, reviews it, applies it, and verifies the changed workspace. A passing verification commits the repaired state. Every other terminal path compensates newest-first and reports whether the original baseline was restored.

### Learning goals

By the end, you will be able to read the repair workflow as ordinary Python inputs and outputs, identify which decisions belong to models and which belong to deterministic code, and follow the receipts that make rollback provable.

### Who owns each decision?

| Decision | Owner | Why |
|---|---|---|
| Diagnose a failure | Swappable role, optionally a model | This is an interpretive task. |
| Draft a patch | Swappable role, optionally a model | This is a generative task. |
| Review, apply, and verify | Deterministic callbacks | Safety policy and workspace evidence must not depend on model judgment. |
| Retry, stop, or roll back | Deterministic transaction core | Bounds and compensation are transaction rules. |
| Choose a terminal presentation | Deterministic status rule | Rendering must not change the result. |

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



## LangChain and LCEL from basic Python

If you know how an ordinary Python function accepts an argument and returns a value, you have the starting point.

- A **runnable** is an object with `.invoke(input)`.
- LCEL is LangChain's composition syntax.
- `left | right` sends the left runnable's output into the right runnable.
- `RunnableLambda` wraps an ordinary Python function as a runnable.
- `RunnableBranch` selects one runnable from deterministic conditions.
- `ChatPromptTemplate` creates chat messages from named Python inputs.
- `FakeListChatModel` returns fixed replies in call order for offline examples.

LCEL makes the outer composition smaller, but it leaves the transaction internals inside one named runnable. The matrix and walkthroughs later in the notebook make those otherwise opaque transaction outcomes inspectable.

| | [`langgraph/`](../langgraph/tutorial.ipynb) (`StateGraph`) | `langchain/` (LCEL) |
|---|---|---|
| Repair stages | Explicit graph nodes and conditional edges | Runnable model roles around one named transaction |
| Deterministic roles | Plain callables from `new_runtime()` | Exact fake replies converted by runnable adapters |
| Business bound | `StabilityPolicy.max_rounds` | The same policy inside the sealed `SelfHealLoop` |
| Safety proof | Apply, verify, rollback receipts plus state digests | The same normalized `HealTrace` record |
| Trade-off | More code, every transition is inspectable | Smaller composition, transaction internals stay in Python |


## Setup

The deterministic section is fully offline. The setup searches upward for the pattern helpers and repository helpers, so execution works from the repository root, the notebook directory, `nbmake`, or JupyterLab without relying on `__file__` or a brittle relative path.



```python
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

# Find each helper's nearest ancestor so execution works from Jupyter,
# nbmake, or the repository root without relying on __file__.
for _marker in ("shared.py", "model_config.py", "nbtools.py"):
    _dir = next(
        path
        for path in (Path.cwd(), *Path.cwd().parents)
        if (path / _marker).exists()
    )
    sys.path.insert(0, str(_dir))

# Framework imports intentionally follow path setup; E402 marks that order.
from IPython.display import HTML, display  # noqa: E402
from IPython.utils.capture import capture_output  # noqa: E402
from langchain_core.language_models.fake_chat_models import (  # noqa: E402
    FakeListChatModel,
)
from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from langchain_core.runnables import RunnableBranch, RunnableLambda  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

# Local imports group model configuration, the sealed core, and shared fixtures.
from model_config import get_model  # noqa: E402
from nbtools import show_graph  # noqa: E402
from pattern import FailureSignal, HealStatus, Patch, SelfHealLoop  # noqa: E402
from shared import (  # noqa: E402
    RECORD_FIELDS,
    SCENARIO_ORDER,
    assert_expected_record,
    format_scenario_matrix,
    format_scenario_walkthrough,
    new_runtime,
    parse_diagnosis_json,
    parse_patch_json,
    run_core_reference,
    trace_record,
)
```

## LCEL pipeline

We first build two small model-role pipes: one diagnoses a failure and one drafts a patch. Both feed a single bounded transaction runnable. A terminal branch then normalizes the completed trace into the same public record regardless of status.

The offline fixtures use exact JSON strings; the optional real-model path uses provider-native structured output. Both paths cross the same strict shared parsers before reaching mutation authority.

### Prompts

A `ChatPromptTemplate` fills named placeholders from an input dictionary and produces chat messages. These prompts ask for diagnosis and patch content only; they do not approve, apply, verify, or roll back anything.



```python
# Named inputs become messages here; prompt text grants no policy authority.
diagnose_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Diagnose the failure. Return only JSON with key diagnosis."),
        ("human", "kind={kind}\ncode={code}\nerror={error_text}\nfiles={affected_files}"),
    ]
)
# The diagnosis string from the first pipe fills this template's only slot.
draft_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Draft one patch. Return only JSON with description, payload, and touches.",
        ),
        ("human", "diagnosis={diagnosis}"),
    ]
)

```

### Output schemas

The optional provider path asks for these exact Pydantic shapes. Shape validation reduces ambiguity, but it does not replace the repository's stricter patch rules.



```python
# Pydantic checks response shape and rejects undeclared fields here.
# It does not decide whether a patch is safe to apply.
class DiagnosisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnosis: str = Field(
        min_length=1,
        description="One concise diagnosis of the deterministic failure",
    )


# This nested set object matches the canonical payload shape used by the core.
class PatchPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    set: dict[str, str] = Field(
        min_length=1,
        description="Nonempty map of canonical relative paths to replacement text",
    )


# The shared parser later requires touches to match the payload keys exactly.
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

### Strict structured adapters

**Input:** A provider adapter result containing `parsed` data or a parsing error.

**Purpose:** Reduce provider output to the same strict diagnosis and patch types used by the offline path.

**Invariant:** Provider-controlled parser details and invalid field values never cross this schema-only boundary.

**Failure route:** The adapter raises a stable schema-only error; the sealed transaction records it as a stage error and compensates if needed.

Native structured output constrains the response shape. The strict shared parsers still enforce nonblank diagnosis text, canonical patch JSON, safe paths, and exact agreement between payload paths and `touches`.



```python
# Invariant: provider-controlled errors never cross this schema-only boundary.
# include_raw=True yields raw, parsed, and parsing_error fields; only the
# parsed Pydantic value is allowed beyond this helper.
def _parsed_structured(result: dict[str, object], schema):
    parsing_error = result.get("parsing_error")
    if parsing_error is not None:
        raise ValueError(f"{schema.__name__} structured parsing failed")
    parsed = result.get("parsed")
    if not isinstance(parsed, schema):
        raise TypeError(f"expected parsed {schema.__name__}")
    return parsed


# Both adapters reuse the shared strict parsers, so offline and live values
# receive the same domain checks.
def parse_structured_diagnosis(result: dict[str, object]) -> str:
    parsed = _parsed_structured(result, DiagnosisOutput)
    try:
        return parse_diagnosis_json(parsed.model_dump_json())
    except (TypeError, ValueError):
        raise ValueError("DiagnosisOutput strict validation failed") from None


def parse_structured_patch(result: dict[str, object]) -> Patch:
    parsed = _parsed_structured(result, PatchOutput)
    # Rebuild canonical JSON from parsed fields; ignore the raw provider response.
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
        return parse_patch_json(raw)
    except (TypeError, ValueError):
        raise ValueError("PatchOutput strict validation failed") from None
```

### Bind schemas to a live model

`with_structured_output(..., method="json_schema", include_raw=True)` asks the provider to return schema-bound values. Raw responses remain transient; only parsed, strictly validated values may enter the transaction.



```python
def build_structured_role_models(model):
    # Schema binding constrains response shape; it grants no transaction authority.
    # include_raw=True supplies the envelope consumed by _parsed_structured.
    return (
        model.with_structured_output(
            DiagnosisOutput, method="json_schema", include_raw=True
        ),
        model.with_structured_output(
            PatchOutput, method="json_schema", include_raw=True
        ),
    )
```

### Build diagnosis and drafting pipes

`|` is evaluated left to right. The prompt creates messages, the model returns a response, and the final parser runnable converts that response into a plain Python `str` or `Patch`.

The offline builder parses text from `FakeListChatModel`. The live builder starts from provider-native structured output. Neither builder receives mutation authority.



```python
# Invariant: role pipes produce proposals only; deterministic callbacks
# retain all transaction authority.
def build_role_pipes(model):
    # diagnose: input dictionary -> chat messages -> model text -> Python string.
    diagnose_pipe = diagnose_prompt | model | StrOutputParser() | RunnableLambda(
        parse_diagnosis_json
    )
    # draft: diagnosis dictionary -> chat messages -> model text -> Patch.
    draft_pipe = draft_prompt | model | StrOutputParser() | RunnableLambda(
        parse_patch_json
    )
    return diagnose_pipe, draft_pipe


def build_structured_role_pipes(model):
    diagnosis_model, patch_model = build_structured_role_models(model)
    # Structured pipes replace model text with a validated Pydantic envelope,
    # then return the same Python domain values as the offline pipes.
    diagnose_pipe = diagnose_prompt | diagnosis_model | RunnableLambda(
        parse_structured_diagnosis
    )
    draft_pipe = draft_prompt | patch_model | RunnableLambda(
        parse_structured_patch
    )
    return diagnose_pipe, draft_pipe
```

### Convert a failure into prompt inputs

The transaction works with an immutable `FailureSignal`. This adapter exposes only its named fields as the dictionary expected by `diagnose_prompt`.



```python
def failure_input(failure: FailureSignal) -> dict[str, object]:
    return {
        "kind": failure.kind,
        "code": failure.code,
        "error_text": failure.error_text,
        "affected_files": list(failure.affected_files),
    }
```

### Build an exact offline fake

`FakeListChatModel` returns its list entries in call order. Each scenario therefore interleaves one diagnosis reply and one patch reply per planned round. The transaction later asserts the exact diagnose/draft counts and the total response count, so a missing, extra, or cycled call fails visibly.



```python
# Invariant: responses follow the sealed loop's diagnose-then-draft call order exactly.
def fake_model_for(spec) -> FakeListChatModel:
    # A new reply list gives each scenario its own isolated model state.
    responses: list[str] = []
    for diagnosis, patch_plan in zip(spec.diagnoses, spec.patches, strict=True):
        patch = patch_plan.patch()
        responses.extend(
            [
                json.dumps(
                    {"diagnosis": diagnosis},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                json.dumps(
                    {
                        "description": patch.description,
                        "payload": patch.payload,
                        "touches": list(patch.touches),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ]
        )
    # The fake still traverses the real prompt, parser, and runnable composition.
    return FakeListChatModel(responses=responses)
```

### Normalize one terminal trace

**Input:** A completed scenario name and `HealTrace`.

**Purpose:** Produce and validate the ten-field public record.

**Invariant:** Rendering is observational only; it cannot change transaction state or terminal status. Offline fixtures also check their locked expected record; live runs check the same ten-field public shape without pretending a model proposal is predetermined.

**Failure route:** A malformed public record fails its assertion instead of being displayed as valid evidence.

The function returns the record without printing it. Default notebook output stays compact; `show_record(name)` later provides deliberate access to one full record.



```python
def render_record(item: dict[str, object]) -> dict[str, object]:
    # Read the completed trace only; this renderer cannot change the workspace.
    record = trace_record(item["scenario"], item["trace"])
    if item.get("validate_expected_record", True):
        # Offline fixtures have a locked result, so any drift fails visibly.
        assert_expected_record(record)
    else:
        # A live proposal is intentionally unpredictable, but its public shape is not.
        assert tuple(record) == RECORD_FIELDS
    return record
```

### Run one bounded transaction

**Input:** One fresh scenario runtime, one model runnable, and optionally a role-pipe builder.

**Purpose:** Adapt the two model roles, construct a fresh sealed `SelfHealLoop`, and execute exactly one repair transaction. The default builder keeps deterministic examples unchanged; the live section selects native structured output through the same input boundary.

**Invariant:** Exactly one role-pipe builder runs per transaction, model roles remain observational, and offline fake calls exactly match the interleaved response list.

**Failure route:** The sealed core records role, policy, mutation, verification, and compensation failures in its terminal trace.

The transaction remains one runnable because `SelfHealLoop` already owns the hardened round logic, receipt checks, decision precedence, and compensation. Reimplementing those internals as a second framework-specific loop would create another safety authority.



```python
# Build each role pipe once; the sealed core retains mutation
# and retry authority.
def invoke_transaction(inputs: dict[str, object]) -> dict[str, object]:
    runtime = inputs["runtime"]
    model = inputs["model"]
    # Validate presentation controls before model roles or mutation can run.
    validate_expected_record = inputs.get("validate_expected_record", True)
    if type(validate_expected_record) is not bool:
        raise TypeError("validate_expected_record must be a boolean")
    # Offline runs use text/JSON pipes. A live caller may inject the native
    # structured-output builder without receiving any mutation authority.
    role_pipe_builder = inputs.get("role_pipe_builder", build_role_pipes)
    if not callable(role_pipe_builder):
        raise TypeError("role_pipe_builder must be callable")
    diagnose_pipe, draft_pipe = role_pipe_builder(model)
    role_counts = {"diagnose": 0, "draft": 0}

    # These callbacks adapt the core's Python values to the two LCEL input shapes.
    def diagnose(failure: FailureSignal) -> str:
        role_counts["diagnose"] += 1
        return diagnose_pipe.invoke(failure_input(failure))

    def draft(diagnosis: str) -> Patch:
        role_counts["draft"] += 1
        return draft_pipe.invoke({"diagnosis": diagnosis})

    # LCEL supplies proposals; the loop owns review, apply, verify, bounds,
    # receipt checks, and compensation.
    loop = SelfHealLoop(
        diagnose=diagnose,
        fix=draft,
        review=runtime.review,
        apply=runtime.workspace.apply,
        verify=runtime.verify,
        rollback=runtime.workspace.rollback,
        state_digest=runtime.workspace.state_digest,
        stability=runtime.scenario.stability,
    )
    trace = loop.heal(runtime.scenario.initial_failure)
    # Offline only: prove that every planned fake reply was consumed exactly once.
    if isinstance(model, FakeListChatModel):
        assert role_counts == {
            "diagnose": len(runtime.scenario.diagnoses),
            "draft": len(runtime.scenario.patches),
        }
        assert sum(role_counts.values()) == len(model.responses)

    return {
        "scenario": runtime.scenario.name,
        "trace": trace,
        "validate_expected_record": validate_expected_record,
    }
```

### Name the transaction runnable

`RunnableLambda` gives the ordinary `invoke_transaction` function a runnable interface and a useful graph label.

There is deliberately no whole-transaction retry. Replaying a completed or partially compensated transaction could repeat model calls, duplicate mutation, and invalidate receipt evidence.



```python
# Do not retry this whole runnable: replay could duplicate mutation.
bounded_self_heal_transaction = RunnableLambda(
    invoke_transaction,
    name="bounded_self_heal_transaction",
)

```

### Build terminal renderers

Each terminal class uses the same record normalizer. Separate runnable names make the selected terminal route visible without giving presentation code authority over the trace.



```python
# Different names expose the selected terminal route; all three stay read-only.
render_fixed = RunnableLambda(render_record, name="render_fixed")
render_compensated = RunnableLambda(render_record, name="render_compensated")
render_handoff = RunnableLambda(render_record, name="render_handoff")

```

### Select the terminal renderer

**Input:** The already-completed transaction trace.

**Purpose:** Route fixed, compensated, and human-handoff outcomes to a named renderer.

**Invariant:** Conditions inspect terminal status only; the branch does not retry or mutate.

**Failure route:** Statuses not classified as fixed or handoff take the compensated renderer, matching the existing presentation contract.



```python
# Keep every human-handoff terminal status in one explicit routing set.
handoff_statuses = {
    HealStatus.MAX_ROUNDS_HUMAN_HANDOFF,
    HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
    HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF,
}
# Conditions run in order; the last renderer is the default.
# Each renderer reads the completed trace and cannot change its status.
terminal_branch = RunnableBranch(
    (lambda item: item["trace"].status is HealStatus.FIXED, render_fixed),
    (lambda item: item["trace"].status in handoff_statuses, render_handoff),
    render_compensated,
)

```

### Assemble and inspect the pipeline

The complete outer flow is intentionally small: run one bounded transaction, then choose a renderer. The runnable graph shows that boundary while the scenario walkthroughs expose the transaction's internal receipt sequence.



```python
self_heal_chain = bounded_self_heal_transaction | terminal_branch
```


```python
LANGCHAIN_GRAPH_ALT = (
    "Self-Heal LCEL model roles, transaction boundary, and terminal branch"
)
# Capture the generated graph first so the final image can carry useful alt text.
with capture_output() as _graph_capture:
    show_graph(self_heal_chain, alt=LANGCHAIN_GRAPH_ALT)
# A successful render emits PNG display data; an offline render emits ASCII stdout.
_graph_png = next(
    (
        output.data["image/png"]
        for output in _graph_capture.outputs
        if "image/png" in output.data
    ),
    None,
)
if _graph_png is None:
    # The offline fallback is ordinary stdout, which capture_output stored.
    # Replay it so readers still see the graph instead of a StopIteration error.
    print(_graph_capture.stdout, end="")
else:
    display(
        HTML(
            f'<img alt="{html.escape(LANGCHAIN_GRAPH_ALT)}" '
            f'src="data:image/png;base64,{_graph_png}" />'
        )
    )

```


<img alt="Self-Heal LCEL model roles, transaction boundary, and terminal branch" src="data:image/png;base64,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" />


## Deterministic scenarios

Each run gets a fresh runtime and a fake whose replies are the exact diagnosis/patch pairs for that scenario. The LCEL chain validates the locked record, then compares its complete ten-field result with another fresh runtime executed by the sealed `SelfHealLoop` core.

The notebook prints only a compact matrix. Complete records remain in `langchain_records`, and `show_record(name)` is available when you intentionally want one public record while debugging.



```python
# Give every scenario a fresh workspace and fake so state and replies cannot leak.
langchain_records = []
for scenario_name in SCENARIO_ORDER:
    runtime = new_runtime(scenario_name)
    model = fake_model_for(runtime.scenario)
    record = self_heal_chain.invoke({"runtime": runtime, "model": model})
    assert_expected_record(record)
    # Compare the LCEL result with a second fresh core run, field for field.
    core_trace, _core_runtime = run_core_reference(scenario_name)
    core_record = trace_record(scenario_name, core_trace)
    assert record == core_record
    langchain_records.append(record)

# Lock canonical row order and all ten field names before showing summaries.
assert [record["scenario"] for record in langchain_records] == list(SCENARIO_ORDER)
assert RECORD_FIELDS == (
    "scenario",
    "status",
    "stop_reason",
    "baseline_digest",
    "final_digest",
    "baseline_restored",
    "apply_receipts",
    "verification_receipts",
    "rollback_receipts",
    "stage_errors",
)
for record in langchain_records:
    assert tuple(record) == RECORD_FIELDS
    assert_expected_record(record)


# Full records stay in memory; lookup and printing are opt-in debugging aids.
def _record_named(scenario_name: str) -> dict[str, object]:
    try:
        return next(
            record
            for record in langchain_records
            if record["scenario"] == scenario_name
        )
    except StopIteration:
        raise ValueError(f"unknown executed scenario: {scenario_name}") from None


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


# Default output is one bounded matrix of the key outcomes.
print(format_scenario_matrix(langchain_records))

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
    f"{len(langchain_records)} scenarios matched the sealed core "
    f"across all {len(RECORD_FIELDS)} public fields"
)

```

    7 scenarios matched the sealed core across all 10 public fields


## Optional real model

Only diagnosis and patch drafting cross the model boundary. Native structured output constrains response shape, while strict parsing enforces canonical content and safe paths. The same bounded transaction still owns deterministic review, apply, verification, compensation, and terminal status.

`get_model()` returns `None` and prints one skip line when the configured provider has no API key. On a live run, the notebook keeps the full trace in `model_transaction` but displays only clipped diagnosis, patch, terminal result, and one deterministic review reason or evidence item. Raw provider messages remain transient.



```python
# A missing provider key returns None, so offline execution skips this block.
model = get_model()

if model is not None:
    # Select native structured output at the role boundary, then execute the
    # exact bounded transaction used by the deterministic LCEL examples.
    model_runtime = new_runtime("convergence")
    model_transaction = bounded_self_heal_transaction.invoke(
        {
            "runtime": model_runtime,
            "model": model,
            "role_pipe_builder": build_structured_role_pipes,
            # Live proposals are not expected to match a pre-scripted fixture result.
            "validate_expected_record": False,
        }
    )
    # Run the same terminal branch as self_heal_chain while retaining the trace
    # locally for a small, beginner-readable summary.
    model_record = terminal_branch.invoke(model_transaction)
    live_trace = model_transaction["trace"]
    assert model_record["status"] == live_trace.status.value

    # Normalize and clip parsed summaries so model text cannot flood saved artifacts.
    def _clip_summary(value: object, limit: int = 160) -> str:
        text = " ".join(str(value).split())
        return text if len(text) <= limit else f"{text[: limit - 3]}..."


    live_round = live_trace.rounds[-1] if live_trace.rounds else None
    diagnosis = live_round.diagnosis if live_round is not None else "unavailable"
    print(f"diagnosis: {_clip_summary(diagnosis)}")
    if live_round is not None:
        candidate_patch = live_round.patch
        print(
            "patch: "
            + _clip_summary(
                f"{candidate_patch.description}; files={list(candidate_patch.touches)}"
            )
        )
    print(f"result: {live_trace.status.value} ({live_trace.stop_reason})")

    # Prefer a human-readable deterministic reason. If the reason is empty on
    # approval, show the first nonblank policy evidence item instead.
    candidate_review = live_round.patch_review if live_round is not None else None
    if candidate_review is None:
        print("review: unavailable; transaction stopped before deterministic review")
    else:
        review_detail = candidate_review.reason.strip() or next(
            (
                item.strip()
                for item in candidate_review.evidence
                if item.strip() and "digest=" not in item
            ),
            "deterministic policy supplied no text detail",
        )
        decision = "approved" if candidate_review.approved else "rejected"
        print(f"review: {decision}; {_clip_summary(review_detail)}")
```

    Model: ernie:glm-5.1


    diagnosis: The CONVERGENCE_1 scenario failure indicates an iterative algorithm in app.py failed to converge within its expected tolerance or iteration limit. This is a ...
    patch: Fix CONVERGENCE_1 failure: correct the convergence check logic in the iterative solver. The primary bug is a flipped comparison operator in the convergence c...
    result: blocked_by_critic (review_rejected)
    review: rejected; patch content does not satisfy the current failure


## What to remember

- Self-Heal is a bounded transaction, not an open-ended autonomous retry loop.
- Models may diagnose and draft; deterministic callbacks own review, mutation, verification, rollback, and status.
- LCEL makes the outer composition small, while the sealed `SelfHealLoop` keeps transaction internals and receipt rules in one named runnable.
- Native structured output constrains shape; strict parsing and deterministic review still decide whether a candidate is acceptable.
- Exact fake-response accounting makes a missing, extra, or cycled model reply fail visibly.
- Restoration is a proof: every known apply must have a valid rollback receipt and the final digest must equal the baseline.
- The seven executed LCEL records match fresh sealed-core records across all ten public fields.


## Further reading

- [LangGraph tutorial](../langgraph/tutorial.ipynb) — the same transaction contract expressed with explicit graph stages
- [Pattern README](../README.md) — design rationale and framework-neutral public contract
- [Reference implementation guide](../../../REFERENCE_IMPL.md) — repository conventions and verification commands
- [LangChain Expression Language](https://python.langchain.com/docs/concepts/lcel/) — runnable composition concepts
