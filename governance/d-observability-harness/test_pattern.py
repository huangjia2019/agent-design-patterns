"""Invariants for the Observability Harness pattern."""

from __future__ import annotations

import os
import sys
from dataclasses import replace

import pytest


HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ControlDecision,
    EventDraft,
    GovernanceReceipt,
    ObservabilityError,
    ObservabilityHarness,
    TracePolicy,
)


TRACE = "payroll-2026-06"


def draft(
    event_id: str,
    span_id: str,
    *,
    parent: str | None = None,
    event_type: str = "proposal.created",
    control: str = "governance-boundary",
    proposal: str = "proposal-a",
    policy: str = "policy-a",
    occurred_at: str = "2026-07-17T10:00:00+00:00",
    attributes: tuple[tuple[str, str], ...] = (),
) -> EventDraft:
    return EventDraft(
        event_id=event_id,
        trace_id=TRACE,
        span_id=span_id,
        parent_span_id=parent,
        event_type=event_type,
        actor_id="payroll-agent",
        control=control,
        proposal_digest=proposal,
        policy_digest=policy,
        occurred_at=occurred_at,
        summary=event_type,
        evidence_refs=(f"evidence://{event_id}",),
        attributes=attributes,
    )


def receipt(control: str = "approval-gate") -> GovernanceReceipt:
    return GovernanceReceipt(
        receipt_id=f"{control}-receipt",
        control=control,
        proposal_digest="proposal-a",
        policy_digest=f"{control}-policy",
        decided_by=control,
        decision=ControlDecision.ALLOWED,
        issued_at="2026-07-17T10:00:00+00:00",
        evidence_refs=(f"{control}://evidence",),
    )


def complete_trace() -> tuple[ObservabilityHarness, TracePolicy]:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "proposal"))
    harness.record_receipt(
        event_id="e2",
        trace_id=TRACE,
        span_id="approval",
        parent_span_id="proposal",
        receipt=receipt("approval-gate"),
        actor_id="approval-panel",
        occurred_at="2026-07-17T10:01:00+00:00",
        summary="two reviewers approved",
    )
    harness.record_receipt(
        event_id="e3",
        trace_id=TRACE,
        span_id="containment",
        parent_span_id="approval",
        receipt=receipt("blast-radius"),
        actor_id="blast-radius-controller",
        occurred_at="2026-07-17T10:02:00+00:00",
        summary="budget reserved",
    )
    harness.emit(
        draft(
            "e4",
            "effect",
            parent="containment",
            event_type="effect.committed",
            control="payment-adapter",
            policy="payment-policy",
            occurred_at="2026-07-17T10:03:00+00:00",
        )
    )
    policy = TracePolicy(
        required_event_types=("proposal.created", "control.receipt", "effect.committed"),
        required_controls=(
            "governance-boundary",
            "approval-gate",
            "blast-radius",
            "payment-adapter",
        ),
        required_edges=(
            ("proposal.created", "control.receipt"),
            ("control.receipt", "effect.committed"),
        ),
        required_decisions=(("control.receipt", "allowed"),),
        singleton_event_types=("proposal.created", "effect.committed"),
        receipt_event_types=("control.receipt",),
    )
    return harness, policy


def test_append_builds_a_per_trace_hash_chain() -> None:
    harness = ObservabilityHarness()
    first = harness.emit(draft("e1", "root"))
    second = harness.emit(draft("e2", "child", parent="root"))

    assert first.sequence == 1
    assert first.previous_hash == "ROOT"
    assert second.sequence == 2
    assert second.previous_hash == first.event_hash
    assert harness.verify_hash_chain(TRACE)


def test_child_span_requires_an_existing_parent_in_the_same_trace() -> None:
    harness = ObservabilityHarness()

    with pytest.raises(ObservabilityError, match="parent span"):
        harness.emit(draft("e1", "child", parent="missing"))


def test_span_ids_are_unique_inside_one_trace() -> None:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "root"))

    with pytest.raises(ObservabilityError, match="duplicate span_id"):
        harness.emit(draft("e2", "root"))


def test_event_time_requires_a_timezone_and_cannot_precede_parent() -> None:
    with pytest.raises(ValueError, match="timezone"):
        draft("e1", "root", occurred_at="2026-07-17T10:00:00")

    harness = ObservabilityHarness()
    harness.emit(
        draft(
            "e1",
            "root",
            occurred_at="2026-07-17T10:01:00+00:00",
        )
    )
    with pytest.raises(ObservabilityError, match="predates"):
        harness.emit(
            draft(
                "e2",
                "child",
                parent="root",
                occurred_at="2026-07-17T10:00:00+00:00",
            )
        )


def test_event_ids_are_append_only_and_unique() -> None:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "root"))

    with pytest.raises(ObservabilityError, match="duplicate"):
        harness.emit(draft("e1", "other"))


def test_sensitive_attributes_are_redacted_before_storage() -> None:
    harness = ObservabilityHarness()

    record = harness.emit(
        draft(
            "e1",
            "root",
            attributes=(
                ("bank_account", "6222020200009999"),
                ("department", "engineering"),
            ),
        )
    )

    assert dict(record.event.attributes)["bank_account"] == "[REDACTED]"
    assert record.redacted_fields == ("bank_account",)


def test_hidden_reasoning_is_outside_the_event_contract() -> None:
    harness = ObservabilityHarness()

    with pytest.raises(ObservabilityError, match="hidden reasoning"):
        harness.emit(
            draft(
                "e1",
                "root",
                attributes=(("chain_of_thought", "private model trace"),),
            )
        )


def test_complete_trace_passes_semantic_audit() -> None:
    harness, policy = complete_trace()

    audit = harness.audit(TRACE, policy)

    assert audit.complete
    assert audit.chain_valid
    assert audit.event_count == 4


def test_complete_requires_declared_causal_edges() -> None:
    harness = ObservabilityHarness()
    harness.emit(
        draft(
            "effect",
            "effect",
            event_type="effect.committed",
            control="payment-adapter",
        )
    )
    harness.emit(
        draft(
            "approval",
            "approval",
            parent="effect",
            event_type="approval.allowed",
            control="approval-gate",
            occurred_at="2026-07-17T10:01:00+00:00",
        )
    )
    policy = TracePolicy(
        required_event_types=("approval.allowed", "effect.committed"),
        required_controls=("approval-gate", "payment-adapter"),
        required_edges=(("approval.allowed", "effect.committed"),),
    )

    audit = harness.audit(TRACE, policy)

    assert not audit.complete
    assert audit.missing_edges == (("approval.allowed", "effect.committed"),)


def test_complete_checks_decisions_cardinality_and_receipts() -> None:
    harness = ObservabilityHarness()
    harness.emit(
        draft(
            "approval-1",
            "approval-1",
            event_type="approval.allowed",
            control="approval-gate",
        )
    )
    harness.emit(
        draft(
            "approval-2",
            "approval-2",
            event_type="approval.allowed",
            control="approval-gate",
        )
    )
    policy = TracePolicy(
        required_event_types=("approval.allowed",),
        required_controls=("approval-gate",),
        required_decisions=(("approval.allowed", "allowed"),),
        singleton_event_types=("approval.allowed",),
        receipt_event_types=("approval.allowed",),
    )

    audit = harness.audit(TRACE, policy)

    assert not audit.complete
    assert audit.decision_mismatches == ("approval-1", "approval-2")
    assert audit.duplicate_event_types == ("approval.allowed",)
    assert audit.missing_receipts == ("approval-1", "approval-2")


def test_strict_policy_references_declared_event_types() -> None:
    with pytest.raises(ValueError, match="reference required event types"):
        TracePolicy(
            required_event_types=("proposal.created",),
            required_controls=("governance-boundary",),
            required_edges=(("proposal.created", "effect.committed"),),
        )

    with pytest.raises(ValueError, match="define each event type once"):
        TracePolicy(
            required_event_types=("approval.allowed",),
            required_controls=("approval-gate",),
            required_decisions=(
                ("approval.allowed", "allowed"),
                ("approval.allowed", "denied"),
            ),
        )


def test_missing_control_is_reported_even_when_logs_exist() -> None:
    harness, _policy = complete_trace()
    strict = TracePolicy(
        required_event_types=("proposal.created", "effect.committed"),
        required_controls=(
            "governance-boundary",
            "approval-gate",
            "blast-radius",
            "progressive-commitment",
            "payment-adapter",
        ),
    )

    audit = harness.audit(TRACE, strict)

    assert not audit.complete
    assert audit.missing_controls == ("progressive-commitment",)


def test_proposal_drift_is_visible() -> None:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "root"))
    harness.emit(
        draft(
            "e2",
            "child",
            parent="root",
            proposal="proposal-b",
        )
    )
    policy = TracePolicy(
        required_event_types=("proposal.created",),
        required_controls=("governance-boundary",),
    )

    assert harness.audit(TRACE, policy).proposal_drift


def test_policy_drift_is_scoped_per_control() -> None:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "root", control="approval-gate", policy="policy-v1"))
    harness.emit(
        draft(
            "e2",
            "child",
            parent="root",
            control="approval-gate",
            policy="policy-v2",
        )
    )
    policy = TracePolicy(
        required_event_types=("proposal.created",),
        required_controls=("approval-gate",),
    )

    assert harness.audit(TRACE, policy).policy_drift_controls == ("approval-gate",)


def test_tampering_breaks_hash_verification() -> None:
    harness, policy = complete_trace()
    original = harness.store.records[1]
    harness.store.records[1] = replace(
        original,
        event=replace(original.event, summary="tampered"),
    )

    assert not harness.verify_hash_chain(TRACE)
    assert not harness.audit(TRACE, policy).complete


def test_record_receipt_binds_the_receipt_digest() -> None:
    harness = ObservabilityHarness()
    harness.emit(draft("e1", "root"))
    control_receipt = receipt()

    record = harness.record_receipt(
        event_id="e2",
        trace_id=TRACE,
        span_id="approval",
        parent_span_id="root",
        receipt=control_receipt,
        actor_id="approval-panel",
        occurred_at="2026-07-17T10:01:00+00:00",
        summary="approved",
    )

    assert record.event.receipt_digest == control_receipt.digest
    assert record.event.decision == "allowed"
    assert record.event.proposal_digest == control_receipt.proposal_digest
