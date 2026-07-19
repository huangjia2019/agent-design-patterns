"""Deterministic hierarchical budget example."""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    ActionProposal,
    BlastBudget,
    BlastRadiusController,
    ContainmentScope,
    Reversibility,
    RiskLevel,
)


controller = BlastRadiusController()
controller.register_scope(
    ContainmentScope(
        "company",
        BlastBudget(
            15_000_000,
            800,
            4,
            ("payroll.disburse",),
            ("payroll:", "bank:"),
        ),
    )
)
controller.register_scope(
    ContainmentScope(
        "engineering",
        BlastBudget(
            6_000_000,
            350,
            1,
            ("payroll.disburse",),
            ("payroll:", "bank:"),
        ),
        parent_id="company",
    )
)

proposal = ActionProposal(
    proposal_id="engineering-payroll",
    version=1,
    contract_digest="contract",
    artifact_id="artifact-engineering",
    artifact_digest="artifact-engineering-content-v1",
    requested_by="payroll-agent",
    action="payroll.disburse",
    resource_scope=("payroll:2026-06", "bank:payroll"),
    idempotency_key="engineering-payroll-v1",
    risk=RiskLevel.CRITICAL,
    reversibility=Reversibility.IRREVERSIBLE,
    amount=5_000_000,
    subject_count=300,
    evidence_refs=("sqlite://payroll.db/engineering",),
)

lease = controller.reserve(
    proposal,
    scope_id="engineering",
    at="2026-07-17T10:00:00+00:00",
)
print(f"lease={lease.lease_id} authorized={controller.authorizes(lease, proposal)}")
print(f"reserved={controller.snapshot()['company']}")

receipt = controller.commit(
    lease.lease_id,
    at="2026-07-17T10:01:00+00:00",
)
print(f"decision={receipt.decision.value}")
print(f"committed={controller.snapshot()['company']}")
