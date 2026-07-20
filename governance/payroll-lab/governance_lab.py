"""Integrated payroll governance chain used by lectures 36-40.

The same accepted collaboration artifact is sent through two bridges:

* naive: ``AcceptanceReceipt.accepted`` is mistaken for payment authority;
* governed: proposal, approval, containment, authority, payment, and audit.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict
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
    "olivia": ("payroll-operator",),
    "sam": ("payroll-supervisor",),
    "frank": ("finance-controller",),
    "alice": ("payroll-controller",),
    "bob": ("treasury-controller",),
    "carol": ("governance-owner",),
    "dave": ("risk-owner",),
}
APPROVER_BY_ROLE = {
    role: approver_id
    for approver_id, roles in APPROVER_ROLES.items()
    for role in roles
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
    original_truth = bench.payroll_truth()
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
        changed_truth = bench.reinstate_reversed_payroll()
        changed = bench.release_proposal(version=2)
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
            "original_artifact_digest": proposal.artifact_digest,
            "changed_artifact_digest": changed.artifact_digest,
            "changed_amount": changed.amount,
            "changed_subject_count": changed.subject_count,
            "delta_amount": changed.amount - proposal.amount,
            "restored_ids": tuple(
                employee_id
                for employee_id in changed_truth.employee_ids
                if employee_id not in original_truth.employee_ids
            ),
            "old_approval_authorizes": allowed,
            "adapter_result": adapter_result,
        }
        result["timeline"] = (
            *result["timeline"],
            {
                "sequence": 4,
                "event_type": "approval.binding_rejected",
                "control": "payment-adapter",
                "decision": "denied",
                "summary": (
                    "E0007 and E0012 changed the accepted artifact "
                    "and the requested payment"
                ),
                "event_hash": changed.digest,
            },
        )
    result["state"] = bench.state()
    return result


def run_approval_policy_change() -> dict:
    """Approve a new ApprovalPolicy through the old policy before installing it."""
    bench.prepare()
    gate = approval_controller()
    next_policy = approval.ApprovalPolicy(
        version=2,
        auto_allow_max_amount=20_000.0,
    )
    proposal = approval.ActionProposal(
        proposal_id="approval-policy-update::v2",
        version=2,
        contract_digest="governance-policy-change::v1",
        artifact_id=next_policy.policy_id,
        artifact_digest=next_policy.ref.content_digest,
        requested_by="governance-agent",
        action="governance.approval-policy.update",
        resource_scope=(f"policy:{next_policy.policy_id}",),
        idempotency_key="approval-policy-update::v2",
        risk=approval.RiskLevel.CRITICAL,
        reversibility=approval.Reversibility.REVERSIBLE,
        subject_count=1,
        evidence_refs=("change-request://approval-policy/v2",),
    )
    bench.persist_proposal(proposal)
    routed = gate.evaluate(proposal, now=TIMES["proposal"])
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="carol",
        role="governance-owner",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="dave",
        role="risk-owner",
        approved=True,
        at=TIMES["approval_2"],
    )
    installed = gate.install_policy(
        next_policy,
        proposal=proposal,
        receipt=final.receipt,
        at=TIMES["authority"],
    )
    bench.persist_receipt(final.receipt)
    return {
        "mode": "approval-policy-change",
        "route": routed.route.value,
        "required_roles": routed.ticket.required_roles,
        "first_decision": first.receipt.decision.value,
        "final_decision": final.receipt.decision.value,
        "proposal_digest": proposal.digest,
        "approved_under_policy": final.receipt.policy_digest,
        "installed_policy_version": next_policy.version,
        "installed_policy_digest": installed.digest,
        "state": bench.state(),
    }


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


def run_blast_radius_retry_storm() -> dict:
    """Compare an unbounded executor with one-use permits on the same payroll."""
    bench.prepare()
    batches = bench.payroll_payment_batches()
    proposals = {
        department: bench.release_department_proposal(department)
        for department, _rows in batches
    }
    root_scope = f"payroll-window::{bench.MONTH}"
    approved = sum(
        amount
        for _department, rows in batches
        for _employee_id, amount in rows
    )
    subject_count = sum(len(rows) for _department, rows in batches)

    controller = blast.BlastRadiusController()
    controller.register_scope(
        blast.ContainmentScope(
            root_scope,
            blast.BlastBudget(
                approved,
                subject_count,
                subject_count,
                ("payroll.disburse",),
                (f"payroll:{bench.MONTH}:department:", "bank:"),
            ),
        )
    )
    for department, rows in batches:
        amount = sum(item[1] for item in rows)
        controller.register_scope(
            blast.ContainmentScope(
                f"department::{department.lower()}",
                blast.BlastBudget(
                    amount,
                    len(rows),
                    len(rows),
                    ("payroll.disburse",),
                    (
                        f"payroll:{bench.MONTH}:department:{department}",
                        "bank:payroll",
                    ),
                ),
                parent_id=root_scope,
            )
        )

    leases: dict[str, object] = {}
    envelope_rows: list[dict] = []
    for sequence, (department, rows) in enumerate(batches, start=1):
        proposal = proposals[department]
        lease = controller.reserve(
            proposal,
            scope_id=f"department::{department.lower()}",
            effect_count=len(rows),
            allowed_refs=tuple(employee_id for employee_id, _amount in rows),
            at=f"2026-07-17T10:04:{sequence:02d}+00:00",
        )
        leases[department] = lease
        envelope_rows.append(
            {
                "department": department,
                "amount": proposal.amount,
                "subject_count": proposal.subject_count,
                "effect_count": len(rows),
                "lease_id": lease.lease_id,
            }
        )

    retry_department = "Ops"
    extra_runs = 4
    unbounded_payments: list[tuple[str, str, float]] = []
    bounded_payments: list[tuple[str, str, float]] = []
    refusals: list[dict] = []
    for department, rows in batches:
        runs = 1 + (extra_runs if department == retry_department else 0)
        proposal = proposals[department]
        lease = leases[department]
        for run_number in range(1, runs + 1):
            for employee_id, amount in rows:
                unbounded_payments.append((department, employee_id, amount))
                try:
                    permit = controller.begin_effect(
                        lease,
                        proposal,
                        effect_ref=employee_id,
                        amount=amount,
                        idempotency_key=(
                            f"{proposal.idempotency_key}::{employee_id}"
                            f"::attempt-{run_number}"
                        ),
                        at="2026-07-17T10:06:00+00:00",
                    )
                except blast.ContainmentError as error:
                    refusals.append(
                        {
                            "department": department,
                            "employee_id": employee_id,
                            "run_number": run_number,
                            "reason": str(error),
                        }
                    )
                    continue
                if not controller.effect_authorizes(permit, proposal):
                    raise AssertionError("a newly issued permit must be live")
                bounded_payments.append((department, employee_id, amount))
                controller.confirm_effect(
                    permit.permit_id,
                    succeeded=True,
                    at="2026-07-17T10:06:01+00:00",
                )

    unbounded_total = sum(item[2] for item in unbounded_payments)
    bounded_total = sum(item[2] for item in bounded_payments)
    snapshot = controller.snapshot()
    bench.persist_budget(snapshot)
    timeline = [
        {
            "sequence": index,
            "event_type": "containment.envelope_committed",
            "control": f"department::{item['department'].lower()}",
            "decision": "committed",
            "summary": (
                f"{item['department']} consumed "
                f"{item['subject_count']} one-use permits"
            ),
            "event_hash": item["lease_id"],
        }
        for index, item in enumerate(envelope_rows, start=1)
    ]
    timeline.append(
        {
            "sequence": len(timeline) + 1,
            "event_type": "containment.retry_storm_blocked",
            "control": f"department::{retry_department.lower()}",
            "decision": "blocked",
            "summary": (
                f"{len(refusals)} repeated draws were refused; "
                f"bounded money out stayed at {bounded_total:,.0f}"
            ),
            "event_hash": "-",
        }
    )
    return {
        "mode": "blast-radius-retry-storm",
        "policy": {
            "digest": controller.policy_ref.digest,
            "root_scope": root_scope,
            "root_amount_limit": approved,
            "root_subject_limit": subject_count,
            "root_effect_limit": subject_count,
        },
        "retry": {
            "department": retry_department,
            "extra_runs": extra_runs,
        },
        "unbounded": {
            "approved_amount": approved,
            "payment_count": len(unbounded_payments),
            "money_out": unbounded_total,
            "overpay": unbounded_total - approved,
        },
        "bounded": {
            "payment_count": len(bounded_payments),
            "money_out": bounded_total,
            "refused_draws": len(refusals),
            "first_refusal": refusals[0],
        },
        "envelopes": envelope_rows,
        "timeline": tuple(timeline),
        "snapshot": snapshot,
        "state": bench.state(),
    }


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
    final = routed
    for index, role in enumerate(routed.ticket.required_roles, start=1):
        final = gate.attest(
            routed.ticket.ticket_id,
            approver_id=APPROVER_BY_ROLE[role],
            role=role,
            approved=True,
            at=TIMES[f"approval_{min(index, 2)}"],
        )
    radius = containment_controller()
    lease = radius.reserve(
        proposal,
        scope_id=f"month::{bench.MONTH}",
        at=TIMES["reserve"],
        allowed_refs=(proposal.artifact_id,),
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

    effect_permit = radius.begin_effect(
        lease,
        proposal,
        effect_ref=proposal.artifact_id,
        amount=proposal.amount,
        subject_count=proposal.subject_count,
        idempotency_key=f"{proposal.idempotency_key}::effect",
        at=TIMES["effect"],
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
        live_containment=(radius, effect_permit),
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

    containment_receipt = radius.confirm_effect(
        effect_permit.permit_id,
        succeeded=True,
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
    result = run_approval_gate(changed_after_approval=True)
    return {
        "mode": "changed-after-approval",
        **result["changed"],
        "state": result["state"],
    }
