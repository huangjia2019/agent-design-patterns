"""Observability Harness pattern.

The harness records semantic governance events in an append-only, hash-chained
trace. A trace carries proposal and policy identities, control decisions,
receipt digests, parent-child causality, timestamps, and durable evidence.
Raw hidden chain-of-thought is outside the contract; systems should record a
decision summary and the evidence that can be checked independently.

The harness must not:

* accept a child span whose parent is missing or belongs to another trace;
* silently mix proposal versions or policy versions inside one control;
* store known secrets or account identifiers without redaction;
* call a trace complete merely because some log lines exist.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


sys.path.insert(0, str(Path(__file__).parent.parent))

from boundary_contract import (  # noqa: E402
    ControlDecision as ControlDecision,
    GovernanceReceipt,
)


def _hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        raise ValueError("observability timestamps must include a timezone")
    return instant


@dataclass(frozen=True)
class RedactionPolicy:
    sensitive_keys: tuple[str, ...] = (
        "bank_account",
        "token",
        "secret",
        "password",
        "personal_id",
    )
    forbidden_keys: tuple[str, ...] = (
        "chain_of_thought",
        "hidden_reasoning",
    )
    replacement: str = "[REDACTED]"

    def apply(
        self,
        attributes: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]:
        forbidden = [key for key, _value in attributes if key in self.forbidden_keys]
        if forbidden:
            raise ObservabilityError(
                "hidden reasoning is outside the observability contract: " + ", ".join(forbidden)
            )
        redacted: list[tuple[str, str]] = []
        fields: list[str] = []
        for key, value in attributes:
            if key in self.sensitive_keys:
                redacted.append((key, self.replacement))
                fields.append(key)
            else:
                redacted.append((key, value))
        return tuple(redacted), tuple(fields)


@dataclass(frozen=True)
class EventDraft:
    event_id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    event_type: str
    actor_id: str
    control: str
    proposal_digest: str
    policy_digest: str
    occurred_at: str
    decision: str = ""
    summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    receipt_digest: str = ""
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        required = {
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "control": self.control,
            "proposal_digest": self.proposal_digest,
            "policy_digest": self.policy_digest,
            "occurred_at": self.occurred_at,
        }
        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        _instant(self.occurred_at)
        if len({key for key, _value in self.attributes}) != len(self.attributes):
            raise ValueError("event attribute keys must be unique")


@dataclass(frozen=True)
class EventRecord:
    sequence: int
    previous_hash: str
    event_hash: str
    event: EventDraft
    redacted_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class TracePolicy:
    required_event_types: tuple[str, ...]
    required_controls: tuple[str, ...]
    required_edges: tuple[tuple[str, str], ...] = ()
    required_decisions: tuple[tuple[str, str], ...] = ()
    singleton_event_types: tuple[str, ...] = ()
    receipt_event_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.required_event_types or not self.required_controls:
            raise ValueError("trace policy requirements must not be empty")
        sequences = (
            ("required_event_types", self.required_event_types),
            ("required_controls", self.required_controls),
            ("singleton_event_types", self.singleton_event_types),
            ("receipt_event_types", self.receipt_event_types),
        )
        for name, values in sequences:
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain blank values")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must contain unique values")
        pairs = (
            ("required_edges", self.required_edges),
            ("required_decisions", self.required_decisions),
        )
        for name, values in pairs:
            if any(not left.strip() or not right.strip() for left, right in values):
                raise ValueError(f"{name} must not contain blank values")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must contain unique values")
        if len({event_type for event_type, _decision in self.required_decisions}) != len(
            self.required_decisions
        ):
            raise ValueError("required_decisions must define each event type once")
        declared = set(self.required_event_types)
        referenced = {event_type for edge in self.required_edges for event_type in edge} | {
            event_type for event_type, _decision in self.required_decisions
        }
        referenced.update(self.singleton_event_types)
        referenced.update(self.receipt_event_types)
        if not referenced.issubset(declared):
            raise ValueError("strict trace requirements must reference required event types")


@dataclass(frozen=True)
class TraceAudit:
    trace_id: str
    complete: bool
    chain_valid: bool
    missing_event_types: tuple[str, ...]
    missing_controls: tuple[str, ...]
    broken_parents: tuple[str, ...]
    missing_edges: tuple[tuple[str, str], ...]
    decision_mismatches: tuple[str, ...]
    duplicate_event_types: tuple[str, ...]
    missing_receipts: tuple[str, ...]
    proposal_drift: bool
    policy_drift_controls: tuple[str, ...]
    redacted_fields: tuple[str, ...]
    event_count: int


class ObservabilityError(RuntimeError):
    """Raised when an event would break trace identity or causality."""


class InMemoryEventStore:
    """Append-only teaching store. Production supplies the same interface."""

    def __init__(self) -> None:
        self.records: list[EventRecord] = []
        self.event_ids: set[str] = set()

    def append(
        self,
        draft: EventDraft,
        *,
        redaction: RedactionPolicy,
    ) -> EventRecord:
        if draft.event_id in self.event_ids:
            raise ObservabilityError(f"duplicate event_id {draft.event_id!r}")
        trace_records = [
            record for record in self.records if record.event.trace_id == draft.trace_id
        ]
        if any(record.event.span_id == draft.span_id for record in trace_records):
            raise ObservabilityError(
                f"duplicate span_id {draft.span_id!r} in trace {draft.trace_id!r}"
            )
        parent = next(
            (record for record in trace_records if record.event.span_id == draft.parent_span_id),
            None,
        )
        if draft.parent_span_id is not None and parent is None:
            raise ObservabilityError("parent span is missing from this trace")
        if parent is not None and _instant(draft.occurred_at) < _instant(parent.event.occurred_at):
            raise ObservabilityError("child event predates its causal parent")

        attributes, fields = redaction.apply(draft.attributes)
        redacted_draft = EventDraft(
            **{
                **draft.__dict__,
                "attributes": attributes,
            }
        )
        previous_hash = trace_records[-1].event_hash if trace_records else "ROOT"
        sequence = trace_records[-1].sequence + 1 if trace_records else 1
        event_hash = self._event_hash(redacted_draft, sequence, previous_hash)
        record = EventRecord(
            sequence,
            previous_hash,
            event_hash,
            redacted_draft,
            fields,
        )
        self.records.append(record)
        self.event_ids.add(draft.event_id)
        return record

    def trace(self, trace_id: str) -> tuple[EventRecord, ...]:
        return tuple(record for record in self.records if record.event.trace_id == trace_id)

    @staticmethod
    def _event_hash(
        event: EventDraft,
        sequence: int,
        previous_hash: str,
    ) -> str:
        return _hash(
            {
                "sequence": sequence,
                "previous_hash": previous_hash,
                "event": {
                    "event_id": event.event_id,
                    "trace_id": event.trace_id,
                    "span_id": event.span_id,
                    "parent_span_id": event.parent_span_id,
                    "event_type": event.event_type,
                    "actor_id": event.actor_id,
                    "control": event.control,
                    "proposal_digest": event.proposal_digest,
                    "policy_digest": event.policy_digest,
                    "occurred_at": event.occurred_at,
                    "decision": event.decision,
                    "summary": event.summary,
                    "evidence_refs": event.evidence_refs,
                    "receipt_digest": event.receipt_digest,
                    "attributes": event.attributes,
                },
            }
        )


class ObservabilityHarness:
    """Semantic event emission, replay, hash verification, and completeness audit."""

    def __init__(
        self,
        store: InMemoryEventStore | None = None,
        redaction: RedactionPolicy | None = None,
    ) -> None:
        self.store = store or InMemoryEventStore()
        self.redaction = redaction or RedactionPolicy()

    def emit(self, draft: EventDraft) -> EventRecord:
        return self.store.append(draft, redaction=self.redaction)

    def record_receipt(
        self,
        *,
        event_id: str,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        receipt: GovernanceReceipt,
        actor_id: str,
        occurred_at: str,
        summary: str,
        event_type: str = "control.receipt",
    ) -> EventRecord:
        return self.emit(
            EventDraft(
                event_id=event_id,
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                event_type=event_type,
                actor_id=actor_id,
                control=receipt.control,
                proposal_digest=receipt.proposal_digest,
                policy_digest=receipt.policy_digest,
                occurred_at=occurred_at,
                decision=receipt.decision.value,
                summary=summary,
                evidence_refs=receipt.evidence_refs,
                receipt_digest=receipt.digest,
            )
        )

    def replay(self, trace_id: str) -> tuple[EventRecord, ...]:
        return self.store.trace(trace_id)

    def verify_hash_chain(self, trace_id: str) -> bool:
        previous = "ROOT"
        for expected_sequence, record in enumerate(
            self.store.trace(trace_id),
            start=1,
        ):
            if record.sequence != expected_sequence:
                return False
            if record.previous_hash != previous:
                return False
            expected_hash = self.store._event_hash(
                record.event,
                record.sequence,
                record.previous_hash,
            )
            if record.event_hash != expected_hash:
                return False
            previous = record.event_hash
        return True

    def audit(self, trace_id: str, policy: TracePolicy) -> TraceAudit:
        records = self.store.trace(trace_id)
        event_types = {record.event.event_type for record in records}
        controls = {record.event.control for record in records}
        records_by_span = {record.event.span_id: record for record in records}
        spans = set(records_by_span)
        broken_parents = tuple(
            record.event.event_id
            for record in records
            if record.event.parent_span_id is not None and record.event.parent_span_id not in spans
        )
        proposals = {record.event.proposal_digest for record in records}
        policy_by_control: dict[str, set[str]] = {}
        for record in records:
            policy_by_control.setdefault(record.event.control, set()).add(
                record.event.policy_digest
            )
        policy_drift = tuple(
            control for control, digests in sorted(policy_by_control.items()) if len(digests) > 1
        )
        missing_events = tuple(
            event_type
            for event_type in policy.required_event_types
            if event_type not in event_types
        )
        missing_controls = tuple(
            control for control in policy.required_controls if control not in controls
        )
        observed_edges = {
            (
                records_by_span[record.event.parent_span_id].event.event_type,
                record.event.event_type,
            )
            for record in records
            if record.event.parent_span_id in records_by_span
        }
        missing_edges = tuple(edge for edge in policy.required_edges if edge not in observed_edges)
        expected_decisions = dict(policy.required_decisions)
        decision_mismatches = tuple(
            record.event.event_id
            for record in records
            if record.event.event_type in expected_decisions
            and record.event.decision != expected_decisions[record.event.event_type]
        )
        duplicate_event_types = tuple(
            event_type
            for event_type in policy.singleton_event_types
            if sum(record.event.event_type == event_type for record in records) > 1
        )
        missing_receipts = tuple(
            record.event.event_id
            for record in records
            if record.event.event_type in policy.receipt_event_types
            and not record.event.receipt_digest
        )
        redacted = tuple(sorted({field for record in records for field in record.redacted_fields}))
        chain_valid = self.verify_hash_chain(trace_id)
        complete = not (
            missing_events
            or missing_controls
            or broken_parents
            or missing_edges
            or decision_mismatches
            or duplicate_event_types
            or missing_receipts
            or len(proposals) > 1
            or policy_drift
            or not chain_valid
        )
        return TraceAudit(
            trace_id=trace_id,
            complete=complete,
            chain_valid=chain_valid,
            missing_event_types=missing_events,
            missing_controls=missing_controls,
            broken_parents=broken_parents,
            missing_edges=missing_edges,
            decision_mismatches=decision_mismatches,
            duplicate_event_types=duplicate_event_types,
            missing_receipts=missing_receipts,
            proposal_drift=len(proposals) > 1,
            policy_drift_controls=policy_drift,
            redacted_fields=redacted,
            event_count=len(records),
        )
