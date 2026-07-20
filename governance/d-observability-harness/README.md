# d · Observability Harness

> Pattern · Govern × Orchestrate
>
> [中文 README](README.zh-CN.md)

## The problem

Having logs does not prove that a payment passed approval, budget, and authority
checks. Ordinary logs may mix proposal versions, omit controls, or store bank
accounts and hidden model reasoning in the audit system.

## The pattern

`ObservabilityHarness` writes semantic governance events. Each event binds:

- trace, span, and causal parent;
- proposal digest, policy digest, and control;
- decision, receipt digest, and durable evidence;
- previous and current event hashes.

`TracePolicy` defines the events, controls, direct causal edges, decisions,
cardinality, and receipt bindings required for completeness. Audits report
missing controls, broken causal edges, decision mismatches, duplicate singleton
events, proposal drift, per-control policy drift, broken parents, and hash
tampering. Span identities are unique inside a trace, and child timestamps
cannot precede their causal parents. Sensitive fields are redacted before
storage. Hidden chain-of-thought is outside the interface; record a publishable
decision summary and independently checkable evidence.

## Public interface

| Object | Responsibility |
|---|---|
| `EventDraft` | One semantic event before storage |
| `EventRecord` | Sequenced, hash-chained immutable record |
| `RedactionPolicy` | Pre-storage redaction and forbidden fields |
| `TracePolicy` | Required events, controls, causal edges, decisions, and receipts |
| `TraceAudit` | Completeness, drift, and hash result |
| `ObservabilityHarness` | Emit, record receipts, replay, and audit |

## Run

```bash
python3 governance/d-observability-harness/example.py
pytest governance/d-observability-harness/test_pattern.py -q
python3 governance/payroll-lab/observability_harness_lab.py
```

## Where this pattern sits

Govern × Orchestrate. It crosses approval, containment, authority, and the effect
adapter because no individual component sees the complete causal path.
