"""Deterministic evidence-backed authority promotion example."""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    AuthorityLevel,
    ProgressiveCommitment,
    RunOutcome,
)


progressive = ProgressiveCommitment(
    role_resolver=lambda identity: (
        ("governance-owner",)
        if identity == "governance-admin"
        else (("incident-responder",) if identity == "incident-monitor" else ())
    ),
    outcome_verifier=lambda outcome: (
        outcome.recorded_by == "payroll-evaluator"
        and outcome.evidence_ref.startswith("eval://")
    ),
)
credential = progressive.enroll(
    "payroll-agent",
    at="2026-07-01T09:00:00+00:00",
)
print(f"enrolled={credential.level.name} version={credential.authority_version}")

for index in range(progressive.policy.min_runs):
    progressive.record_outcome(
        "payroll-agent",
        RunOutcome(
            f"shadow-{index}",
            success=True,
            blocker=False,
            evidence_ref=f"eval://shadow-{index}",
            evaluation_slice=f"payroll-slice-{index}",
            occurred_at=f"2026-07-{10 + index:02d}T09:00:00+00:00",
            recorded_by="payroll-evaluator",
        ),
    )

request = progressive.request_promotion(
    "payroll-agent",
    at="2026-07-17T10:00:00+00:00",
)
print(
    f"request={request.from_level.name}->{request.to_level.name} "
    f"runs={request.runs} success={request.success_rate:.0%}"
)

credential = progressive.approve_promotion(
    request,
    approver_id="governance-admin",
    role="governance-owner",
    at="2026-07-17T10:01:00+00:00",
)
assert credential.level is AuthorityLevel.RECOMMEND
print(f"promoted={credential.level.name} version={credential.authority_version}")
