"""Deterministic semantic trace example."""

from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    EventDraft,
    ObservabilityHarness,
    TracePolicy,
)


harness = ObservabilityHarness()
harness.emit(
    EventDraft(
        event_id="proposal-created",
        trace_id="payroll-2026-06",
        span_id="proposal",
        parent_span_id=None,
        event_type="proposal.created",
        actor_id="payroll-agent",
        control="governance-boundary",
        proposal_digest="proposal-a",
        policy_digest="boundary-v1",
        occurred_at="2026-07-17T10:00:00+00:00",
        summary="reviewed payroll artifact requested bank disbursement",
        evidence_refs=("artifact://payroll-2026-06",),
        attributes=(("bank_account", "6222020200009999"),),
    )
)
harness.emit(
    EventDraft(
        event_id="effect-committed",
        trace_id="payroll-2026-06",
        span_id="effect",
        parent_span_id="proposal",
        event_type="effect.committed",
        actor_id="payment-adapter",
        control="payment-adapter",
        proposal_digest="proposal-a",
        policy_digest="payment-v1",
        occurred_at="2026-07-17T10:01:00+00:00",
        summary="payment adapter accepted the idempotency key",
        evidence_refs=("payment://payroll-2026-06",),
    )
)

policy = TracePolicy(
    required_event_types=("proposal.created", "effect.committed"),
    required_controls=("governance-boundary", "payment-adapter"),
    required_edges=(("proposal.created", "effect.committed"),),
    singleton_event_types=("proposal.created", "effect.committed"),
)
audit = harness.audit("payroll-2026-06", policy)
print(f"events={audit.event_count} complete={audit.complete}")
print(f"chain_valid={audit.chain_valid} redacted={audit.redacted_fields}")
