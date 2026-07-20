# b · Fan-out / Gather

> Pattern · Collaborate × Parallel
>
> [中文 README](README.zh-CN.md)

## The problem

Parallel calls are easy. A trustworthy gather must still know:

1. whether results are competing answers or additive contributions;
2. which source, snapshot, period, and unit produced each value;
3. how identities and contributions merge;
4. how conflicts and cross-source seams are reviewed;
5. whether missing required sources invalidate the whole report.

## The pattern

One root `TaskContract` is fanned out into a `SourceSpec` per attributable
boundary. Every worker returns an `ArtifactEnvelope[SourceResult]`, and
`SourceAdmissionPolicy` verifies contract digest, source identity, snapshot,
period, unit, expected fields, evidence, confidence, and failure state.

The gather then follows an executable `AggregatorPolicy`:

| Question | Interface |
|---|---|
| Competing or additive? | `Strategy` |
| How are conflicts resolved? | `conflict_resolver` |
| How do identity and value merge? | `identity_key` + `ContributionRule` |
| Who reviews the assembled seams? | `seam_reviewer` |

Competing results become typed `LineItemVerdict` objects: agreement, attributable
divergence, or unexplained divergence. Additive results become `MergedItem`
objects that preserve every contribution and raw key. The final
`ReconciliationReport` is bound to the root contract and receives its own
`AcceptanceReceipt`.

The shared transport contract lives in
[`../boundary_contract.py`](../boundary_contract.py):

```text
TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt
```

## Public interface

| Object | Responsibility |
|---|---|
| `SourceSpec` | Source identity, snapshot, scope, and expected fields |
| `SourceResult` | Immutable reading from one source |
| `SourceAdmissionPolicy` | Source artifact admission and receipt |
| `AggregatorPolicy` | Executable gather semantics |
| `LineItemVerdict` | Competing evidence and optional resolution |
| `MergedItem` | Additive value with source contributions |
| `ReconciliationReport` | Typed assembled result |
| `FanOutGather` | Parallel dispatch, source floor, gather, and root receipt |

## Run

```bash
python collaboration/b-fan-out-gather/example.py
pytest collaboration/b-fan-out-gather/test_pattern.py -v
python collaboration/payroll-lab/fan_out_gather_lab.py
python collaboration/payroll-lab/fan_out_gather_lab.py --additive
```

The framework tutorials show LangGraph and Claude Agent SDK dispatch seams. The
pattern contract and deterministic gather remain framework-independent.

## Where this pattern sits

Collaborate × Parallel. Hierarchical Delegation gives different workers
different responsibility units. Fan-out / Gather gives independent sources the
same contracted question and treats their agreement and divergence as evidence.
