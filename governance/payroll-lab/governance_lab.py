"""Integrated payroll governance chain used by lectures 36-40.

The same accepted collaboration artifact is sent through two bridges:

* naive: ``AcceptanceReceipt.accepted`` is mistaken for payment authority;
* governed: proposal, approval, containment, authority, payment, and audit.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, replace
from pathlib import Path

from governance_payroll_imports import load_local


bench = load_local("bench")


HERE = Path(__file__).parent
GOVERNANCE = HERE.parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


approval = load_module(
    GOVERNANCE / "a-approval-gate" / "pattern.py",
    "governance_lab_approval",
)
blast = load_module(
    GOVERNANCE / "b-blast-radius" / "pattern.py",
    "governance_lab_blast",
)
progressive = load_module(
    GOVERNANCE / "c-progressive-commitment" / "pattern.py",
    "governance_lab_progressive",
)
observability = load_module(
    GOVERNANCE / "d-observability-harness" / "pattern.py",
    "governance_lab_observability",
)


TIMES = {
    "proposal": "2026-07-17T10:00:00+00:00",
    "approval_1": "2026-07-17T10:02:00+00:00",
    "approval_2": "2026-07-17T10:03:00+00:00",
    "reserve": "2026-07-17T10:04:00+00:00",
    "authority": "2026-07-17T10:05:00+00:00",
    "effect": "2026-07-17T10:06:00+00:00",
    "commit": "2026-07-17T10:07:00+00:00",
}
APPROVER_ROLES = {
    "alice": ("payroll-controller",),
    "bob": ("treasury-controller",),
}
GOVERNANCE_ROLES = {
    "governance-admin": ("governance-owner",),
    "incident-monitor": ("incident-responder",),
}


def approval_controller():
    return approval.ApprovalGate(
        role_resolver=lambda approver_id: APPROVER_ROLES.get(approver_id, ()),
    )


def progressive_controller(policy=None):
    return progressive.ProgressiveCommitment(
        policy,
        role_resolver=lambda identity: GOVERNANCE_ROLES.get(identity, ()),
        outcome_verifier=lambda outcome: (
            outcome.recorded_by == "payroll-evaluator"
            and outcome.evidence_ref.startswith("eval://payroll/")
        ),
    )


def _supporting_control(control: str, proposal) -> tuple[object, object]:
    policy = approval.PolicyRef.from_content(
        control,
        1,
        {"teaching_scene": "changed-proposal"},
    )
    receipt = approval.GovernanceReceipt(
        receipt_id=f"{control}::changed-proposal",
        control=control,
        proposal_digest=proposal.digest,
        policy_digest=policy.digest,
        decided_by=control,
        decision=approval.ControlDecision.ALLOWED,
        issued_at=TIMES["authority"],
        evidence_refs=(f"{control}://changed-proposal",),
    )
    return receipt, policy


def run_approval_gate(*, changed_after_approval: bool = False) -> dict:
    """Run the lecture-37 route, two-person review, and version-binding scene."""
    bench.prepare()
    proposal = bench.release_proposal()
    gate = approval_controller()
    routed = gate.evaluate(proposal, now=TIMES["proposal"])
    bench.persist_receipt(routed.receipt)
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    bench.persist_receipt(final.receipt)
    result = {
        "mode": "approval-gate",
        "proposal": {
            "digest": proposal.digest,
            "amount": proposal.amount,
            "subject_count": proposal.subject_count,
            "risk": proposal.risk.name,
            "reversibility": proposal.reversibility.value,
        },
        "route": {
            "name": routed.route.value,
            "reason_codes": routed.ticket.reason_codes,
        },
        "ticket": {
            "ticket_id": routed.ticket.ticket_id,
            "required_roles": routed.ticket.required_roles,
            "created_at": routed.ticket.created_at,
            "expires_at": routed.ticket.expires_at,
        },
        "attestations": (
            {
                "approver_id": "alice",
                "role": "payroll-controller",
                "decision": first.receipt.decision.value,
            },
            {
                "approver_id": "bob",
                "role": "treasury-controller",
                "decision": final.receipt.decision.value,
            },
        ),
        "final_receipt": {
            "decision": final.receipt.decision.value,
            "digest": final.receipt.digest,
            "proposal_digest": final.receipt.proposal_digest,
            "policy_digest": final.receipt.policy_digest,
            "expires_at": final.receipt.expires_at,
        },
        "timeline": (
            {
                "sequence": 1,
                "event_type": "approval.routed",
                "control": "approval-router",
                "decision": routed.receipt.decision.value,
                "summary": ", ".join(routed.ticket.reason_codes),
                "event_hash": routed.receipt.digest,
            },
            {
                "sequence": 2,
                "event_type": "approval.attested",
                "control": "payroll-controller",
                "decision": first.receipt.decision.value,
                "summary": "alice approved the bound proposal",
                "event_hash": first.receipt.digest,
            },
            {
                "sequence": 3,
                "event_type": "approval.allowed",
                "control": "treasury-controller",
                "decision": final.receipt.decision.value,
                "summary": "bob completed the second independent role",
                "event_hash": final.receipt.digest,
            },
        ),
    }
    if changed_after_approval:
        changed = replace(
            proposal,
            version=2,
            amount=proposal.amount + 1,
            idempotency_key=f"{proposal.idempotency_key}-changed",
        )
        allowed = gate.authorize(
            changed,
            final.receipt,
            at=TIMES["authority"],
        )
        supporting = (
            _supporting_control("blast-radius", changed),
            _supporting_control("progressive-commitment", changed),
        )
        try:
            bench.execute_payment(
                changed,
                receipts=(final.receipt, *(item[0] for item in supporting)),
                active_policies={
                    "approval-gate": gate.policy.ref,
                    **{item[0].control: item[1] for item in supporting},
                },
                at=TIMES["effect"],
            )
        except PermissionError as error:
            adapter_result = str(error)
        else:
            adapter_result = "unexpectedly paid"
        result["mode"] = "approval-changed"
        result["changed"] = {
            "original_digest": proposal.digest,
            "changed_digest": changed.digest,
            "changed_amount": changed.amount,
            "old_approval_authorizes": allowed,
            "adapter_result": adapter_result,
        }
    result["state"] = bench.state()
    return result


def containment_controller() -> object:
    controller = blast.BlastRadiusController()
    controller.register_scope(
        blast.ContainmentScope(
            "company-payroll",
            blast.BlastBudget(
                15_000_000,
                800,
                1,
                ("payroll.disburse",),
                ("payroll:", "bank:"),
            ),
        )
    )
    controller.register_scope(
        blast.ContainmentScope(
            f"month::{bench.MONTH}",
            blast.BlastBudget(
                15_000_000,
                800,
                1,
                ("payroll.disburse",),
                ("payroll:", "bank:"),
            ),
            parent_id="company-payroll",
        )
    )
    return controller


def department_containment_controller(
    departments: tuple[str, ...],
) -> object:
    """Create the lecture-38 shared window and its real department leaves."""
    controller = blast.BlastRadiusController()
    controller.register_scope(
        blast.ContainmentScope(
            f"payroll-window::{bench.MONTH}",
            blast.BlastBudget(
                8_000_000,
                600,
                3,
                ("payroll.disburse",),
                (f"payroll:{bench.MONTH}:department:", "bank:"),
            ),
        )
    )
    for department in departments:
        controller.register_scope(
            blast.ContainmentScope(
                f"department::{department.lower()}",
                blast.BlastBudget(
                    3_000_000,
                    200,
                    1,
                    ("payroll.disburse",),
                    (
                        f"payroll:{bench.MONTH}:department:{department}",
                        "bank:payroll",
                    ),
                ),
                parent_id=f"payroll-window::{bench.MONTH}",
            )
        )
    return controller


def run_blast_radius(*, include_third: bool = False) -> dict:
    """Reserve real department batches against one shared execution window."""
    bench.prepare()
    departments = ("Engineering", "Finance", "Ops")
    proposals = {
        department: bench.release_department_proposal(department)
        for department in departments
    }
    controller = department_containment_controller(departments)
    root_scope = f"payroll-window::{bench.MONTH}"
    selected = departments if include_third else departments[:2]
    batches: list[dict] = []
    timeline: list[dict] = []

    for sequence, department in enumerate(selected, start=1):
        proposal = proposals[department]
        root_before = controller.snapshot()[root_scope]["reserved_amount"]
        try:
            lease = controller.reserve(
                proposal,
                scope_id=f"department::{department.lower()}",
                at=f"2026-07-17T10:04:0{sequence}+00:00",
            )
        except blast.ContainmentError as error:
            decision = "blocked"
            blocked_at = str(error)
            receipt_digest = ""
            lease_id = ""
        else:
            receipt = controller.reservation_receipt(
                lease,
                proposal,
                at=f"2026-07-17T10:04:0{sequence}+00:00",
            )
            bench.persist_receipt(receipt)
            decision = "reserved"
            blocked_at = ""
            receipt_digest = receipt.digest
            lease_id = lease.lease_id
        root_after = controller.snapshot()[root_scope]["reserved_amount"]
        batch = {
            "department": department,
            "amount": proposal.amount,
            "subject_count": proposal.subject_count,
            "leaf_amount_limit": 3_000_000,
            "leaf_subject_limit": 200,
            "leaf_legal": (
                proposal.amount <= 3_000_000
                and proposal.subject_count <= 200
            ),
            "root_before": root_before,
            "root_after": root_after,
            "decision": decision,
            "blocked_at": blocked_at,
            "lease_id": lease_id,
        }
        batches.append(batch)
        timeline.append(
            {
                "sequence": sequence,
                "event_type": f"containment.{decision}",
                "control": f"department::{department.lower()}",
                "decision": decision,
                "summary": (
                    blocked_at
                    or f"{department} reserved {proposal.amount:,.0f}; "
                    f"root usage is {root_after:,.0f}"
                ),
                "event_hash": receipt_digest or "-",
            }
        )

    snapshot = controller.snapshot()
    bench.persist_budget(snapshot)
    result = {
        "mode": (
            "blast-radius-overflow"
            if include_third
            else "blast-radius"
        ),
        "policy": {
            "digest": controller.policy_ref.digest,
            "root_scope": root_scope,
            "root_amount_limit": 8_000_000,
            "root_subject_limit": 600,
            "root_effect_limit": 3,
            "leaf_amount_limit": 3_000_000,
            "leaf_subject_limit": 200,
        },
        "candidates": [
            {
                "department": department,
                "amount": proposal.amount,
                "subject_count": proposal.subject_count,
            }
            for department, proposal in proposals.items()
        ],
        "batches": batches,
        "timeline": timeline,
        "snapshot": snapshot,
        "state": bench.state(),
    }
    return result


def _record_level_evidence(progressive_control, credential) -> object:
    slices = bench.payroll_department_slices()
    day = credential.authority_version * 2
    for index, item in enumerate(slices, start=1):
        progressive_control.record_outcome(
            "payroll-agent",
            progressive.RunOutcome(
                (
                    f"{credential.level.name.lower()}-"
                    f"{credential.authority_version}-{item.department.lower()}"
                ),
                success=True,
                blocker=False,
                evidence_ref=(
                    f"eval://payroll/{credential.level.name.lower()}/"
                    f"{item.department.lower()}?amount={item.amount:.0f}"
                ),
                evaluation_slice=item.department,
                occurred_at=f"2026-07-{day:02d}T09:{index:02d}:00+00:00",
                recorded_by="payroll-evaluator",
            ),
        )
    return progressive_control.windows["payroll-agent"]


def _promote_to(progressive_control, target) -> tuple[object, list[dict]]:
    try:
        credential = progressive_control.credentials["payroll-agent"]
    except KeyError:
        credential = progressive_control.enroll(
            "payroll-agent",
            at="2026-07-01T09:00:00+00:00",
        )
    windows: list[dict] = []
    while credential.level < target:
        window = _record_level_evidence(progressive_control, credential)
        day = credential.authority_version * 2 + 1
        request = progressive_control.request_promotion(
            "payroll-agent",
            at=f"2026-07-{day:02d}T10:00:00+00:00",
        )
        windows.append(
            {
                "from_level": credential.level.name,
                "to_level": request.to_level.name,
                "runs": window.runs,
                "success_rate": window.success_rate,
                "blockers": window.blockers,
                "evaluation_slices": window.evaluation_slices,
                "evidence_digest": window.digest,
            }
        )
        credential = progressive_control.approve_promotion(
            request,
            approver_id="governance-admin",
            role="governance-owner",
            at=f"2026-07-{day:02d}T10:01:00+00:00",
        )
    return credential, windows


def autonomous_credential(progressive_control) -> object:
    credential, _windows = _promote_to(
        progressive_control,
        progressive.AuthorityLevel.AUTONOMOUS,
    )
    return credential


def _real_upstream_receipts(proposal) -> tuple[object, object]:
    gate = approval_controller()
    routed = gate.evaluate(proposal, now=TIMES["proposal"])
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    radius = containment_controller()
    lease = radius.reserve(
        proposal,
        scope_id=f"month::{bench.MONTH}",
        at=TIMES["reserve"],
        parent_receipts=(final.receipt.digest,),
    )
    reservation = radius.reservation_receipt(
        lease,
        proposal,
        at=TIMES["reserve"],
    )
    bench.persist_receipt(final.receipt)
    bench.persist_receipt(reservation)
    return final.receipt, reservation


def run_progressive_commitment(*, incident: bool = False) -> dict:
    """Run evidence-bound promotion, scoped authorization, and fast demotion."""
    bench.prepare()
    slices = tuple(item.department for item in bench.payroll_department_slices())
    policy = progressive.ProgressivePolicy(
        required_evaluation_slices=slices,
    )
    control = progressive_controller(policy)
    shadow_credential, windows = _promote_to(
        control,
        progressive.AuthorityLevel.SHADOW,
    )

    shadow_proposal = bench.release_proposal(execution_mode="shadow")
    live_proposal = bench.release_proposal(execution_mode="live")
    shadow_receipt = control.authorize(
        shadow_proposal,
        shadow_credential,
        at=TIMES["authority"],
    )
    shadow_live_receipt = control.authorize(
        live_proposal,
        shadow_credential,
        at=TIMES["authority"],
    )

    limited_credential, limited_windows = _promote_to(
        control,
        progressive.AuthorityLevel.LIMITED,
    )
    windows.extend(limited_windows)
    canary = bench.release_limited_proposal()
    canary_parents = _real_upstream_receipts(canary)
    canary_receipt = control.authorize(
        canary,
        limited_credential,
        at=TIMES["authority"],
        parent_receipts=canary_parents,
    )
    full_parents = _real_upstream_receipts(live_proposal)
    full_receipt = control.authorize(
        live_proposal,
        limited_credential,
        at=TIMES["authority"],
        parent_receipts=full_parents,
    )

    current = limited_credential
    incident_result = None
    if incident:
        demoted = control.demote(
            "payroll-agent",
            severity=progressive.IncidentSeverity.CRITICAL,
            reason_code="authority_boundary_violation",
            evidence_ref=f"authority-receipt://{full_receipt.digest}",
            decided_by="incident-monitor",
            role="incident-responder",
            at=TIMES["commit"],
        )
        stale = control.authorize(
            canary,
            limited_credential,
            at=TIMES["commit"],
            parent_receipts=canary_parents,
        )
        current = demoted
        incident_result = {
            "before": {
                "level": limited_credential.level.name,
                "version": limited_credential.authority_version,
            },
            "after": {
                "level": demoted.level.name,
                "version": demoted.authority_version,
            },
            "reason_code": "authority_boundary_violation",
            "evidence_ref": f"authority-receipt://{full_receipt.digest}",
            "old_credential_decision": stale.decision.value,
            "old_credential_findings": tuple(
                finding.code for finding in stale.findings
            ),
            "fresh_evidence_runs": control.windows["payroll-agent"].runs,
        }

    bench.persist_credential(current)
    for receipt in (
        shadow_receipt,
        shadow_live_receipt,
        canary_receipt,
        full_receipt,
    ):
        bench.persist_receipt(receipt)

    transitions = control.transition_history("payroll-agent")
    bench.persist_transitions(transitions)
    timeline = tuple(
        {
            "sequence": index,
            "event_type": "authority.transition",
            "control": "progressive-commitment",
            "decision": transition.reason_code,
            "summary": (
                f"{transition.from_level.name if transition.from_level is not None else 'NEW'} "
                f"-> {transition.to_level.name}; "
                f"authority v{transition.to_version}"
            ),
            "event_hash": transition.transition_id,
        }
        for index, transition in enumerate(transitions, start=1)
    )
    return {
        "mode": (
            "progressive-incident" if incident else "progressive-commitment"
        ),
        "profiles": tuple(
            {
                "level": profile.level.name,
                "live_effects": profile.live_effects,
                "max_amount": profile.max_amount,
                "max_subjects": profile.max_subjects,
                "required_controls": profile.required_controls,
            }
            for profile in control.policy.profiles
        ),
        "evidence_windows": tuple(windows),
        "shadow": {
            "credential_version": shadow_credential.authority_version,
            "simulation_decision": shadow_receipt.decision.value,
            "live_decision": shadow_live_receipt.decision.value,
            "live_findings": tuple(
                finding.code for finding in shadow_live_receipt.findings
            ),
        },
        "limited": {
            "credential_version": limited_credential.authority_version,
            "canary_amount": canary.amount,
            "canary_subjects": canary.subject_count,
            "canary_decision": canary_receipt.decision.value,
            "full_amount": live_proposal.amount,
            "full_subjects": live_proposal.subject_count,
            "full_decision": full_receipt.decision.value,
            "full_findings": tuple(
                finding.code for finding in full_receipt.findings
            ),
        },
        "incident": incident_result,
        "transitions": tuple(
            {
                "transition_id": item.transition_id,
                "agent_id": item.agent_id,
                "from_level": (
                    item.from_level.name if item.from_level is not None else None
                ),
                "to_level": item.to_level.name,
                "from_version": item.from_version,
                "to_version": item.to_version,
                "policy_digest": item.policy_digest,
                "reason_code": item.reason_code,
                "evidence_refs": item.evidence_refs,
                "decided_by": item.decided_by,
                "occurred_at": item.occurred_at,
            }
            for item in transitions
        ),
        "timeline": timeline,
        "state": bench.state(),
    }


def _emit(
    harness,
    *,
    event_id: str,
    span_id: str,
    parent_span_id: str | None,
    event_type: str,
    control: str,
    proposal,
    policy_digest: str,
    occurred_at: str,
    summary: str,
    decision: str = "",
    receipt_digest: str = "",
):
    return harness.emit(
        observability.EventDraft(
            event_id=event_id,
            trace_id=f"governance::{bench.MONTH}",
            span_id=span_id,
            parent_span_id=parent_span_id,
            event_type=event_type,
            actor_id="governance-runtime",
            control=control,
            proposal_digest=proposal.digest,
            policy_digest=policy_digest,
            occurred_at=occurred_at,
            decision=decision,
            summary=summary,
            evidence_refs=proposal.evidence_refs,
            receipt_digest=receipt_digest,
        )
    )


def run_naive() -> dict:
    bench.prepare()
    _contract, _artifact, acceptance = bench.reviewed_artifact()
    proposal = bench.release_proposal()
    payment = bench.unsafe_execute_from_artifact_acceptance(
        proposal,
        acceptance,
        at=TIMES["effect"],
    )
    return {
        "mode": "naive",
        "artifact_acceptance": acceptance.decision.value,
        "governance_receipts": 0,
        "payment": payment,
        "state": bench.state(),
        "diagnosis": (
            "accepted artifact was treated as execution authority; "
            "no approval, containment, authority credential, or complete trace"
        ),
    }


def run_governed() -> dict:
    bench.prepare()
    proposal = bench.release_proposal()
    harness = observability.ObservabilityHarness()
    trace_id = f"governance::{bench.MONTH}"
    _emit(
        harness,
        event_id="proposal-created",
        span_id="proposal",
        parent_span_id=None,
        event_type="proposal.created",
        control="governance-boundary",
        proposal=proposal,
        policy_digest="governance-boundary-v1",
        occurred_at=TIMES["proposal"],
        summary="accepted payroll artifact requested a bank disbursement",
    )

    gate = approval_controller()
    routed = gate.evaluate(proposal, now=TIMES["proposal"])
    bench.persist_receipt(routed.receipt)
    _emit(
        harness,
        event_id="approval-pending",
        span_id="approval-pending",
        parent_span_id="proposal",
        event_type="approval.pending",
        control=routed.receipt.control,
        proposal=proposal,
        policy_digest=routed.receipt.policy_digest,
        occurred_at=TIMES["proposal"],
        summary="critical payroll release routed to two-person review",
        decision=routed.receipt.decision.value,
        receipt_digest=routed.receipt.digest,
    )
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    bench.persist_receipt(final.receipt)
    _emit(
        harness,
        event_id="approval-allowed",
        span_id="approval-allowed",
        parent_span_id="approval-pending",
        event_type="approval.allowed",
        control=final.receipt.control,
        proposal=proposal,
        policy_digest=final.receipt.policy_digest,
        occurred_at=TIMES["approval_2"],
        summary="payroll and treasury controllers approved the same proposal digest",
        decision=final.receipt.decision.value,
        receipt_digest=final.receipt.digest,
    )

    radius = containment_controller()
    lease = radius.reserve(
        proposal,
        scope_id=f"month::{bench.MONTH}",
        at=TIMES["reserve"],
        parent_receipts=(final.receipt.digest,),
    )
    reservation = radius.reservation_receipt(
        lease,
        proposal,
        at=TIMES["reserve"],
    )
    bench.persist_receipt(reservation)
    bench.persist_budget(radius.snapshot())
    _emit(
        harness,
        event_id="containment-reserved",
        span_id="containment",
        parent_span_id="approval-allowed",
        event_type="containment.reserved",
        control=reservation.control,
        proposal=proposal,
        policy_digest=reservation.policy_digest,
        occurred_at=TIMES["reserve"],
        summary="15 million and 800-subject parent budget reserved before payment",
        decision=reservation.decision.value,
        receipt_digest=reservation.digest,
    )

    commitment = progressive_controller()
    credential = autonomous_credential(commitment)
    bench.persist_credential(credential)
    bench.persist_transitions(commitment.transition_history("payroll-agent"))
    authority_receipt = commitment.authorize(
        proposal,
        credential,
        at=TIMES["authority"],
        parent_receipts=(final.receipt, reservation),
    )
    bench.persist_receipt(authority_receipt)
    _emit(
        harness,
        event_id="authority-allowed",
        span_id="authority",
        parent_span_id="containment",
        event_type="authority.allowed",
        control=authority_receipt.control,
        proposal=proposal,
        policy_digest=authority_receipt.policy_digest,
        occurred_at=TIMES["authority"],
        summary="current autonomous credential accepted the bounded live effect",
        decision=authority_receipt.decision.value,
        receipt_digest=authority_receipt.digest,
    )

    payment = bench.execute_payment(
        proposal,
        receipts=(final.receipt, reservation, authority_receipt),
        active_policies={
            "approval-gate": gate.policy.ref,
            "blast-radius": radius.policy_ref,
            "progressive-commitment": commitment.policy.ref,
        },
        at=TIMES["effect"],
    )
    _emit(
        harness,
        event_id="effect-committed",
        span_id="effect",
        parent_span_id="authority",
        event_type="effect.committed",
        control="payment-adapter",
        proposal=proposal,
        policy_digest="payment-adapter-v1",
        occurred_at=TIMES["effect"],
        summary="payment adapter consumed three bound governance receipts",
        decision="allowed",
    )

    containment_receipt = radius.commit(
        lease.lease_id,
        at=TIMES["commit"],
    )
    bench.persist_receipt(containment_receipt)
    bench.persist_budget(radius.snapshot())
    _emit(
        harness,
        event_id="containment-committed",
        span_id="containment-commit",
        parent_span_id="effect",
        event_type="containment.committed",
        control=containment_receipt.control,
        proposal=proposal,
        policy_digest=containment_receipt.policy_digest,
        occurred_at=TIMES["commit"],
        summary="reserved budget moved to committed usage after the effect",
        decision=containment_receipt.decision.value,
        receipt_digest=containment_receipt.digest,
    )

    policy = observability.TracePolicy(
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
    )
    audit = harness.audit(trace_id, policy)
    records = harness.replay(trace_id)
    bench.persist_events(records)
    return {
        "mode": "governed",
        "proposal": {
            "id": proposal.proposal_id,
            "digest": proposal.digest,
            "amount": proposal.amount,
            "subject_count": proposal.subject_count,
            "artifact_id": proposal.artifact_id,
        },
        "approval": {
            "route": routed.route.value,
            "first": first.receipt.decision.value,
            "final": final.receipt.decision.value,
            "roles": final.ticket.approved_roles,
        },
        "containment": {
            "lease_id": lease.lease_id,
            "reservation": reservation.decision.value,
            "snapshot": radius.snapshot(),
        },
        "authority": {
            "level": credential.level.name,
            "version": credential.authority_version,
            "decision": authority_receipt.decision.value,
        },
        "payment": payment,
        "audit": asdict(audit),
        "events": [
            {
                "sequence": record.sequence,
                "event_type": record.event.event_type,
                "control": record.event.control,
                "decision": record.event.decision,
                "summary": record.event.summary,
                "event_hash": record.event_hash,
            }
            for record in records
        ],
        "state": bench.state(),
    }


def run_changed_after_approval() -> dict:
    bench.prepare()
    original = bench.release_proposal()
    gate = approval_controller()
    routed = gate.evaluate(original, now=TIMES["proposal"])
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    changed = replace(
        original,
        version=2,
        amount=original.amount + 1,
        idempotency_key=f"{original.idempotency_key}-changed",
    )
    allowed = gate.authorize(
        changed,
        final.receipt,
        at=TIMES["authority"],
    )
    supporting = (
        _supporting_control("blast-radius", changed),
        _supporting_control("progressive-commitment", changed),
    )
    try:
        bench.execute_payment(
            changed,
            receipts=(final.receipt, *(item[0] for item in supporting)),
            active_policies={
                "approval-gate": gate.policy.ref,
                **{item[0].control: item[1] for item in supporting},
            },
            at=TIMES["effect"],
        )
    except PermissionError as error:
        adapter_result = str(error)
    else:
        adapter_result = "unexpectedly paid"
    return {
        "mode": "changed-after-approval",
        "original_digest": original.digest,
        "changed_digest": changed.digest,
        "old_approval_authorizes": allowed,
        "adapter_result": adapter_result,
        "state": bench.state(),
    }
