# a · Hierarchical Delegation

> Pattern · Collaborate × Hierarchy
>
> [中文 README](README.zh-CN.md)

## The problem

A payroll supervisor must settle 800 employees without loading every worker's
raw trace into one context. Splitting the roster is easy. Trustworthy delegation
also needs to answer:

1. Which exact task version did each worker receive?
2. Does the result cover the assigned roster slice?
3. Who admitted the result, using which evidence?
4. Did locally valid batches violate a portfolio-wide constraint?

## The pattern

The supervisor owns one root `TaskContract` and decomposes it into disjoint child
contracts. Each child crosses the shared collaboration boundary:

```text
TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt
```

The worker returns a `SalaryBatchResult` inside the artifact envelope. The
envelope binds the result to the child contract digest and the designated
receiver. `SafetyBoundary` checks that binding, durable evidence, roster count,
roster fingerprint, amount, confidence, review flags, and worker verdict. It
returns an `AcceptanceReceipt`, rather than a transient Boolean.

After batch admission, the supervisor creates a root portfolio artifact.
`PortfolioBoundary` checks facts no worker can see alone, including total roster
coverage, unresolved child batches, and the combined cash limit.

The topology keeps one strict role rule: the supervisor decomposes, dispatches,
synthesizes, and admits. It never computes line payroll.

## Public interface

| Object | Responsibility |
|---|---|
| `SalaryBatchResult` | Immutable business payload produced by one worker |
| `BatchAssignment` | One child handoff plus its exact roster rows |
| `SafetyBoundary` | Batch-level admission policy and receipt issuer |
| `PayrollPortfolioResult` | Supervisor synthesis over child artifacts and receipts |
| `PortfolioBoundary` | Root-level coverage and aggregate admission |
| `DelegationSummary` | Complete evidence for one delegation run |
| `SettlementSupervisor` | Hierarchical orchestration with a pluggable `dispatch` seam |

The cross-pattern transport objects live in
[`../boundary_contract.py`](../boundary_contract.py).

## Files

| File | What |
|---|---|
| [`pattern.py`](pattern.py) | Framework-agnostic pattern and two-level admission interface |
| [`example.py`](example.py) | Deterministic 800-employee run, no API key |
| [`test_pattern.py`](test_pattern.py) | Contract, evidence, isolation, concurrency, and portfolio invariants |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | Explicit graph implementation |
| [`claude-agent-sdk/tutorial.ipynb`](claude-agent-sdk/tutorial.ipynb) | Subagent implementation |

## Run

```bash
python collaboration/a-hierarchical-delegation/example.py
pytest collaboration/a-hierarchical-delegation/test_pattern.py -v
python collaboration/payroll-lab/hierarchical_delegation_lab.py
python collaboration/payroll-lab/hierarchical_delegation_lab.py --sum-blind
```

## Where this pattern sits

Collaborate × Hierarchy. Its neighbors are Fan-out / Gather for parallel
perspectives, Adversarial Review for independent challenge, and Handoff Chain
for staged responsibility transfer.
