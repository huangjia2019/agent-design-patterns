# c · Adversarial Review

> Pattern coordinate: **Collaborate × Loop**
>
> [中文 README](README.zh-CN.md)

## The problem

Adding a critic does not create a release control. Three gaps remain:

1. The author, reviser, and reviewer may still be the same actor.
2. A clean objection list says nothing about rules nobody checked.
3. A review of artifact `r0` may accidentally be used to release revised artifact
   `r1`.

Adversarial Review separates objection from admission. Reviewers report evidenced,
machine-readable faults. A deterministic gate releases only when the review covers
the versioned rubric, every assigned reviewer completed, and no blocker remains.

## The contract

The implementation carries one chain of durable objects:

```text
TaskContract
  -> ArtifactEnvelope
  -> ReviewRequest
  -> ReviewReceipt
  -> AcceptanceReceipt
```

`ReviewReceipt` binds the decision evidence to:

- the task-contract digest
- the exact artifact id, revision, and content fingerprint
- the rubric version
- checked and missing rule ids
- reviewer identities, failures, and objections

The review loop is `review -> revise -> review`. The last allowed round never
creates an unreviewed replacement artifact.

## Release rule

`ReviewGate` confirms only when all three conditions hold:

```python
receipt.complete and not receipt.blockers
```

`receipt.complete` means no required rule is missing and no reviewer failed. A
reviewer can object, but it cannot approve.

## Files

| File | What |
|:--|:--|
| [`pattern.py`](pattern.py) | Generic contract-bound review panel, gate, receipt, independence checks, and bounded repair loop. |
| [`example.py`](example.py) | Small travel example using the generic interface. No API key. |
| [`test_pattern.py`](test_pattern.py) | Invariants for coverage, identity, version binding, reviewer failure, repair, and escalation. |
| [`../payroll-lab/adversarial_review_lab.py`](../payroll-lab/adversarial_review_lab.py) | Lecture 34 lab: three payroll reviewers, a versioned rubric, a deterministic gate, and a double-pay blind spot. |
| [`langgraph/`](langgraph/) | Graph wiring example for an explicit review back-edge. |
| [`claude-agent-sdk/`](claude-agent-sdk/) | Subagent wiring example for an isolated model reviewer. |

## Run

```bash
python collaboration/c-adversarial-review/example.py
pytest collaboration/c-adversarial-review/test_pattern.py -q

python collaboration/payroll-lab/adversarial_review_lab.py
python collaboration/payroll-lab/adversarial_review_lab.py --blind-spot
pytest collaboration/payroll-lab/test_adversarial_review_lab.py -q
```

The blind-spot run is deliberate. A narrow rubric checks only payslip status and
therefore confirms a duplicated employee. Applying the release rubric with the same
lone reviewer holds the artifact for missing coverage. The lesson is precise: a
gate can enforce a rubric, but it cannot invent rules the rubric omitted.

## Production boundary

The reference implementation verifies declared actor ids and callable separation.
It does not prove process isolation, model independence, evidence authenticity, or
that a reviewer actually executed every declared check. Production systems should
add workload identity, signed evidence, policy governance, timeouts, retries,
telemetry, and human escalation.

## Where it sits

Adversarial Review is **Collaborate × Loop**. Generator-Critic in the Reflection
module evaluates and improves one agent's work. This pattern brings separate
reviewer identities and a release boundary to a shared artifact.
