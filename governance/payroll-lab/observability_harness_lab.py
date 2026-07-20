"""Lecture 40 payroll lab: compare a complete trace with a governed gap."""

from __future__ import annotations

import argparse
from dataclasses import asdict

from governance_payroll_imports import load_local


bench = load_local("bench")
governance_lab = load_local("governance_lab")
TIMES = governance_lab.TIMES
observability = governance_lab.observability
run_governed = governance_lab.run_governed
TRACE_ID = f"governance::{bench.MONTH}"


def _trace_policy():
    return observability.TracePolicy(
        required_event_types=(
            "proposal.created",
            "approval.pending",
            "approval.allowed",
            "containment.reserved",
            "authority.allowed",
            "effect.committed",
            "containment.committed",
        ),
        required_controls=(
            "governance-boundary",
            "approval-gate",
            "blast-radius",
            "progressive-commitment",
            "payment-adapter",
        ),
        required_edges=(
            ("proposal.created", "approval.pending"),
            ("approval.pending", "approval.allowed"),
            ("approval.allowed", "containment.reserved"),
            ("containment.reserved", "authority.allowed"),
            ("authority.allowed", "effect.committed"),
            ("effect.committed", "containment.committed"),
        ),
        required_decisions=(
            ("approval.pending", "pending"),
            ("approval.allowed", "allowed"),
            ("containment.reserved", "allowed"),
            ("authority.allowed", "allowed"),
            ("effect.committed", "allowed"),
            ("containment.committed", "allowed"),
        ),
        singleton_event_types=(
            "proposal.created",
            "approval.pending",
            "approval.allowed",
            "containment.reserved",
            "authority.allowed",
            "effect.committed",
            "containment.committed",
        ),
        receipt_event_types=(
            "approval.pending",
            "approval.allowed",
            "containment.reserved",
            "authority.allowed",
            "containment.committed",
        ),
    )


def _event_rows(records) -> list[dict]:
    return [
        {
            "sequence": record.sequence,
            "event_type": record.event.event_type,
            "control": record.event.control,
            "decision": record.event.decision,
            "summary": record.event.summary,
            "event_hash": record.event_hash,
        }
        for record in records
    ]


def run_incomplete_trace() -> dict:
    """Create a real payment whose trace omits all three governance controls."""
    bench.prepare()
    _contract, _artifact, acceptance = bench.reviewed_artifact()
    proposal = bench.release_proposal()
    payment = bench.unsafe_execute_from_artifact_acceptance(
        proposal,
        acceptance,
        at=TIMES["effect"],
    )

    harness = observability.ObservabilityHarness()
    harness.emit(
        observability.EventDraft(
            event_id="proposal-created",
            trace_id=TRACE_ID,
            span_id="proposal",
            parent_span_id=None,
            event_type="proposal.created",
            actor_id="payroll-agent",
            control="governance-boundary",
            proposal_digest=proposal.digest,
            policy_digest="governance-boundary-v1",
            occurred_at=TIMES["proposal"],
            summary="accepted payroll artifact requested a bank disbursement",
            evidence_refs=proposal.evidence_refs,
        )
    )
    harness.emit(
        observability.EventDraft(
            event_id="effect-committed",
            trace_id=TRACE_ID,
            span_id="effect",
            parent_span_id="proposal",
            event_type="effect.committed",
            actor_id="payment-adapter",
            control="payment-adapter",
            proposal_digest=proposal.digest,
            policy_digest="payment-adapter-v1",
            occurred_at=TIMES["effect"],
            decision="allowed",
            summary="payment exists but three governance controls are absent",
            evidence_refs=(f"payment://{payment['payment_id']}",),
        )
    )
    audit = harness.audit(TRACE_ID, _trace_policy())
    records = harness.replay(TRACE_ID)
    bench.persist_events(records)
    return {
        "mode": "incomplete-trace",
        "artifact_acceptance": acceptance.decision.value,
        "governance_receipts": 0,
        "payment": payment,
        "audit": asdict(audit),
        "events": _event_rows(records),
        "state": bench.state(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--variant",
        choices=("complete", "missing-controls"),
        default="complete",
    )
    args = parser.parse_args()
    result = run_incomplete_trace() if args.variant == "missing-controls" else run_governed()
    print("== semantic governance trace ==")
    for event in result["events"]:
        print(
            f"   {event['sequence']} {event['event_type']:<23} "
            f"{event['control']:<24} {event['decision'] or '-'}"
        )
    print("\n== trace audit ==")
    print(f"   events={result['audit']['event_count']}")
    print(f"   complete={result['audit']['complete']}")
    print(f"   hash_chain={result['audit']['chain_valid']}")
    print(f"   missing_controls={result['audit']['missing_controls']}")
    print(f"   payment_count={result['state']['payment_count']}")


if __name__ == "__main__":
    main()
