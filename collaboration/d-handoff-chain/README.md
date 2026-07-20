# d · Handoff Chain

> Pattern coordinate: **Collaborate × Chain**
>
> [中文 README](README.zh-CN.md)

## The problem

Specialist agents often work in a fixed order: intent, settlement, funding,
payment, receipt. A plain shared dictionary leaves four gaps:

1. a stage can forget a field and fail several steps downstream
2. an upstream field can satisfy a later stage's `provides` without that stage
   producing anything
3. a stage can mutate the shared object and bypass append-only checks
4. a key can exist with the wrong type, evidence, owner, or business value

Handoff Chain turns each seam into a commit boundary.

## The contract

```text
TaskContract
  -> immutable Baton r0
  -> StageDelta
  -> Baton r1 + StageReceipt
  -> ...
  -> AcceptanceReceipt
```

Each `StageSpec` declares `requires` and `provides`. Each provided key has one
`FactRule` that declares its producer, runtime type, evidence requirement, and
optional semantic validator.

A stage receives a detached, read-only `BatonView`. It can only propose a
`StageDelta`. The runner validates the delta before creating the next immutable
baton revision.

## Seam invariants

- Every required fact must already be committed.
- The current stage must itself return every promised fact.
- Undeclared fields are rejected.
- A fact has one producer and cannot be rewritten, even with the same value.
- Type, evidence, and semantic validators run at the producing seam.
- Every commit produces a `StageReceipt` bound to input and output fingerprints.
- Failure returns the prior checkpoint. Retrying resumes at the failed stage with
  the same `stage_run_id`.

## Files

| File | What |
|:--|:--|
| [`pattern.py`](pattern.py) | Generic immutable baton, fact ownership rules, seam validation, receipts, checkpoints, and bounded static chain. |
| [`example.py`](example.py) | Small travel example using the generic interface. No API key. |
| [`test_pattern.py`](test_pattern.py) | Invariants for exact delivery, ownership, read-only views, semantic checks, receipts, and retry. |
| [`../payroll-lab/handoff_chain_lab.py`](../payroll-lab/handoff_chain_lab.py) | Lecture 35 lab: intent to payroll receipt, plus the wrong-value experiment. |
| [`langgraph/`](langgraph/) | Wiring the same commit boundary into a linear graph. |
| [`claude-agent-sdk/`](claude-agent-sdk/) | Adapting specialist subagents to `StageFn`. |

## Run

```bash
python collaboration/d-handoff-chain/example.py
pytest collaboration/d-handoff-chain/test_pattern.py -q

python collaboration/payroll-lab/handoff_chain_lab.py
python collaboration/payroll-lab/handoff_chain_lab.py --wrong-value
pytest collaboration/payroll-lab/test_handoff_chain_lab.py -q
```

The wrong-value run first uses a thin contract. Every key, producer, type, and
evidence check passes, so a wrong payroll total is paid. The same stages under the
release contract fail at `settle`, because `net_total` does not match the controlling
ledger. The runner enforces declared semantics; it cannot invent a rule the contract
omitted.

## Static chain and dynamic handoff

This implementation is a statically wired specialist pipeline. A dynamic
conversational handoff additionally needs route allowlists, context filtering,
authority transfer, and active-agent lifecycle controls.

## Production boundary

`stage_run_id` is a stable idempotency key for retries from the same checkpoint, but
the reference runner does not provide a durable database, distributed lock, signed
evidence, compensation engine, or outbox. External side effects must consume the
idempotency key and persist their own result before returning a delta.
