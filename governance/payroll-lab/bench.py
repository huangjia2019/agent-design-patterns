"""Shared data and SQLite evidence store for the Payroll Governance Lab."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
GOVERNANCE = HERE.parent
ACTION_LAB = ROOT / "action" / "payroll-lab"
REFLECTION_LAB = ROOT / "reflection" / "payroll-lab"
CONTROL_DB = HERE / "governance.db"
MONTH = "2026-06"

sys.path.insert(0, str(GOVERNANCE))

from boundary_contract import (  # noqa: E402
    ActionProposal,
    PolicyRef,
    Reversibility,
    RiskLevel,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reflection_bench = load_module(
    REFLECTION_LAB / "bench.py",
    "governance_lab_reflection_bench",
)
collaboration = load_module(
    ROOT / "collaboration" / "boundary_contract.py",
    "governance_lab_collaboration_contract",
)


@dataclass(frozen=True)
class PayrollReleaseArtifact:
    month: str
    employee_count: int
    amount: float
    exception_ids: tuple[str, ...]


@dataclass(frozen=True)
class PayrollDepartmentSlice:
    department: str
    employee_count: int
    amount: float


@dataclass(frozen=True)
class PayrollCohort:
    cohort_id: str
    employee_ids: tuple[str, ...]
    amount: float

    @property
    def employee_count(self) -> int:
        return len(self.employee_ids)


def prepare() -> dict:
    """Rebuild the known month-end payroll state and an empty control database."""
    with contextlib.redirect_stdout(io.StringIO()):
        payroll = reflection_bench.month_end_state()
    payroll.close()

    CONTROL_DB.unlink(missing_ok=True)
    with sqlite3.connect(CONTROL_DB) as con:
        con.executescript(
            """
            CREATE TABLE proposals (
                proposal_id TEXT PRIMARY KEY,
                proposal_digest TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                subject_count INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE control_receipts (
                receipt_id TEXT PRIMARY KEY,
                control TEXT NOT NULL,
                proposal_digest TEXT NOT NULL,
                policy_digest TEXT NOT NULL,
                decision TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                issued_at TEXT NOT NULL
            );
            CREATE TABLE authority_credentials (
                credential_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                level TEXT NOT NULL,
                authority_version INTEGER NOT NULL,
                policy_digest TEXT NOT NULL,
                issued_at TEXT NOT NULL
            );
            CREATE TABLE authority_transitions (
                transition_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                from_level TEXT,
                to_level TEXT NOT NULL,
                from_version INTEGER,
                to_version INTEGER NOT NULL,
                policy_digest TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                evidence_refs TEXT NOT NULL,
                decided_by TEXT NOT NULL,
                occurred_at TEXT NOT NULL
            );
            CREATE TABLE budget_usage (
                scope_id TEXT PRIMARY KEY,
                reserved_amount REAL NOT NULL,
                committed_amount REAL NOT NULL,
                reserved_subjects INTEGER NOT NULL,
                committed_subjects INTEGER NOT NULL,
                reserved_effects INTEGER NOT NULL,
                committed_effects INTEGER NOT NULL,
                killed INTEGER NOT NULL
            );
            CREATE TABLE governance_events (
                event_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                control TEXT NOT NULL,
                decision TEXT NOT NULL,
                summary TEXT NOT NULL,
                event_hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL
            );
            CREATE TABLE payment_effects (
                payment_id TEXT PRIMARY KEY,
                idempotency_key TEXT UNIQUE NOT NULL,
                proposal_digest TEXT NOT NULL,
                amount REAL NOT NULL,
                subject_count INTEGER NOT NULL,
                mode TEXT NOT NULL,
                committed_at TEXT NOT NULL
            );
            """
        )
        con.commit()
    return state()


def payroll_truth() -> PayrollReleaseArtifact:
    payroll_db = ACTION_LAB / "payroll.db"
    if not payroll_db.exists():
        prepare()
    with sqlite3.connect(payroll_db) as con:
        employee_count, amount = con.execute(
            "SELECT COUNT(*), SUM(e.base_salary) "
            "FROM payroll p JOIN employees e ON e.emp_id=p.emp_id "
            "WHERE p.month=? AND p.status='PAID'",
            (MONTH,),
        ).fetchone()
        exception_ids = tuple(
            row[0]
            for row in con.execute(
                "SELECT emp_id FROM payroll "
                "WHERE month=? AND status='REVERSED' ORDER BY emp_id",
                (MONTH,),
            )
        )
    return PayrollReleaseArtifact(
        MONTH,
        int(employee_count),
        float(amount),
        exception_ids,
    )


def payroll_department_slices(
    departments: tuple[str, ...] = (),
) -> tuple[PayrollDepartmentSlice, ...]:
    """Return real PAID-ledger totals grouped by department."""
    payroll_db = ACTION_LAB / "payroll.db"
    if not payroll_db.exists():
        prepare()
    with sqlite3.connect(payroll_db) as con:
        rows = con.execute(
            "SELECT e.dept, COUNT(*), SUM(e.base_salary) "
            "FROM payroll p JOIN employees e ON e.emp_id=p.emp_id "
            "WHERE p.month=? AND p.status='PAID' "
            "GROUP BY e.dept ORDER BY e.dept",
            (MONTH,),
        ).fetchall()
    by_department = {
        str(department): PayrollDepartmentSlice(
            str(department),
            int(employee_count),
            float(amount),
        )
        for department, employee_count, amount in rows
    }
    if not departments:
        return tuple(by_department.values())
    missing = set(departments) - set(by_department)
    if missing:
        raise ValueError(f"unknown payroll departments: {sorted(missing)}")
    return tuple(by_department[department] for department in departments)


def payroll_cohort(*, cohort_id: str, limit: int) -> PayrollCohort:
    """Return a deterministic PAID-ledger cohort for limited live authority."""
    if not cohort_id.strip() or limit < 1:
        raise ValueError("cohort identity and limit must be positive")
    payroll_db = ACTION_LAB / "payroll.db"
    if not payroll_db.exists():
        prepare()
    with sqlite3.connect(payroll_db) as con:
        rows = con.execute(
            "SELECT p.emp_id, e.base_salary "
            "FROM payroll p JOIN employees e ON e.emp_id=p.emp_id "
            "WHERE p.month=? AND p.status='PAID' "
            "ORDER BY p.emp_id LIMIT ?",
            (MONTH, limit),
        ).fetchall()
    if len(rows) != limit:
        raise ValueError("the PAID ledger does not contain the requested cohort")
    return PayrollCohort(
        cohort_id,
        tuple(str(employee_id) for employee_id, _amount in rows),
        float(sum(float(amount) for _employee_id, amount in rows)),
    )


def reviewed_artifact():
    """Create a real collaboration contract, artifact, and acceptance receipt."""
    truth = payroll_truth()
    contract = collaboration.TaskContract(
        contract_id=f"payroll-release::{MONTH}",
        version=1,
        objective="release the reviewed month-end payroll artifact to governance",
        output_schema="PayrollReleaseArtifact",
        accountable_owner="payroll-controller",
        input_refs=(f"sqlite://payroll.db?month={MONTH}",),
        constraints=(
            "release amount must match the PAID ledger",
            "reversed rows must remain outside the payment artifact",
        ),
        allowed_tools=("read_payroll_ledger",),
        authority_scope=("read:payroll", "propose:payment"),
        boundary="artifact acceptance grants no bank execution authority",
    )
    handoff = collaboration.HandoffEnvelope(
        handoff_id=f"handoff::{MONTH}::governance",
        sender="adversarial-review-panel",
        receiver="payroll-controller",
        contract=contract,
    )
    artifact = collaboration.ArtifactEnvelope.bind(
        handoff,
        artifact_id=f"payroll-release-artifact::{MONTH}",
        produced_by="payroll-controller",
        payload=truth,
        evidence_refs=(
            f"sqlite://payroll.db/paid?month={MONTH}",
            f"review://payroll-release/{MONTH}",
        ),
    )
    receipt = collaboration.AcceptanceReceipt(
        receipt_id=f"acceptance::{MONTH}",
        contract_digest=contract.digest,
        artifact_id=artifact.artifact_id,
        checked_by="collaboration-boundary",
        decision=collaboration.AcceptanceDecision.ACCEPTED,
    )
    return contract, artifact, receipt


def release_proposal(
    *,
    version: int = 1,
    amount: float | None = None,
    subject_count: int | None = None,
    execution_mode: str = "live",
) -> ActionProposal:
    contract, artifact, acceptance = reviewed_artifact()
    truth = artifact.payload
    proposal = ActionProposal(
        proposal_id=f"payroll-disbursement::{MONTH}",
        version=version,
        contract_digest=contract.digest,
        artifact_id=artifact.artifact_id,
        requested_by="payroll-agent",
        action="payroll.disburse",
        resource_scope=(f"payroll:{MONTH}", "bank:payroll"),
        idempotency_key=f"payroll-disbursement::{MONTH}::v{version}",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=truth.amount if amount is None else amount,
        subject_count=(
            truth.employee_count if subject_count is None else subject_count
        ),
        evidence_refs=(
            *artifact.evidence_refs,
            f"acceptance://{acceptance.receipt_id}",
        ),
        attributes=(("execution_mode", execution_mode),),
    )
    persist_proposal(proposal)
    return proposal


def release_department_proposal(department: str) -> ActionProposal:
    """Create one version-bound proposal from a real department ledger slice."""
    item = payroll_department_slices((department,))[0]
    contract, artifact, acceptance = reviewed_artifact()
    slug = department.lower()
    proposal = ActionProposal(
        proposal_id=f"payroll-disbursement::{MONTH}::{slug}",
        version=1,
        contract_digest=contract.digest,
        artifact_id=artifact.artifact_id,
        requested_by="payroll-agent",
        action="payroll.disburse",
        resource_scope=(
            f"payroll:{MONTH}:department:{department}",
            "bank:payroll",
        ),
        idempotency_key=f"payroll-disbursement::{MONTH}::{slug}::v1",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=item.amount,
        subject_count=item.employee_count,
        evidence_refs=(
            *artifact.evidence_refs,
            f"acceptance://{acceptance.receipt_id}",
            f"sqlite://payroll.db/paid?month={MONTH}&department={department}",
        ),
        attributes=(("department", department),),
    )
    persist_proposal(proposal)
    return proposal


def release_limited_proposal(*, limit: int = 20) -> ActionProposal:
    """Create a real low-volume proposal for the LIMITED authority profile."""
    cohort = payroll_cohort(cohort_id="limited-canary", limit=limit)
    contract, artifact, acceptance = reviewed_artifact()
    proposal = ActionProposal(
        proposal_id=f"payroll-disbursement::{MONTH}::{cohort.cohort_id}",
        version=1,
        contract_digest=contract.digest,
        artifact_id=artifact.artifact_id,
        requested_by="payroll-agent",
        action="payroll.disburse",
        resource_scope=(
            f"payroll:{MONTH}:cohort:{cohort.cohort_id}",
            "bank:payroll",
        ),
        idempotency_key=f"payroll-disbursement::{MONTH}::{cohort.cohort_id}::v1",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=cohort.amount,
        subject_count=cohort.employee_count,
        evidence_refs=(
            *artifact.evidence_refs,
            f"acceptance://{acceptance.receipt_id}",
            (
                f"sqlite://payroll.db/paid?month={MONTH}"
                f"&cohort={cohort.cohort_id}&limit={limit}"
            ),
        ),
        attributes=(
            ("cohort_id", cohort.cohort_id),
            ("execution_mode", "live"),
        ),
    )
    persist_proposal(proposal)
    return proposal


def persist_proposal(proposal: ActionProposal, status: str = "PROPOSED") -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        con.execute(
            "INSERT OR REPLACE INTO proposals VALUES (?,?,?,?,?,?,?)",
            (
                proposal.proposal_id,
                proposal.digest,
                proposal.artifact_id,
                proposal.action,
                proposal.amount,
                proposal.subject_count,
                status,
            ),
        )
        con.commit()


def persist_receipt(receipt) -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        con.execute(
            "INSERT OR REPLACE INTO control_receipts VALUES (?,?,?,?,?,?,?)",
            (
                receipt.receipt_id,
                receipt.control,
                receipt.proposal_digest,
                receipt.policy_digest,
                receipt.decision.value,
                receipt.decided_by,
                receipt.issued_at,
            ),
        )
        con.commit()


def persist_credential(credential) -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        con.execute(
            "INSERT OR REPLACE INTO authority_credentials VALUES (?,?,?,?,?,?)",
            (
                credential.credential_id,
                credential.agent_id,
                credential.level.name,
                credential.authority_version,
                credential.policy_digest,
                credential.issued_at,
            ),
        )
        con.commit()


def persist_transitions(transitions) -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        for transition in transitions:
            con.execute(
                "INSERT OR REPLACE INTO authority_transitions "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    transition.transition_id,
                    transition.agent_id,
                    (
                        transition.from_level.name
                        if transition.from_level is not None
                        else None
                    ),
                    transition.to_level.name,
                    transition.from_version,
                    transition.to_version,
                    transition.policy_digest,
                    transition.reason_code,
                    json.dumps(transition.evidence_refs),
                    transition.decided_by,
                    transition.occurred_at,
                ),
            )
        con.commit()


def persist_budget(snapshot: dict) -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        for scope_id, usage in snapshot.items():
            con.execute(
                "INSERT OR REPLACE INTO budget_usage VALUES (?,?,?,?,?,?,?,?)",
                (
                    scope_id,
                    usage["reserved_amount"],
                    usage["committed_amount"],
                    usage["reserved_subjects"],
                    usage["committed_subjects"],
                    usage["reserved_effects"],
                    usage["committed_effects"],
                    int(usage["killed"]),
                ),
            )
        con.commit()


def persist_events(records) -> None:
    with sqlite3.connect(CONTROL_DB) as con:
        for record in records:
            event = record.event
            con.execute(
                "INSERT OR REPLACE INTO governance_events VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    event.event_id,
                    event.trace_id,
                    record.sequence,
                    event.event_type,
                    event.control,
                    event.decision,
                    event.summary,
                    record.event_hash,
                    record.previous_hash,
                ),
            )
        con.commit()


def execute_payment(
    proposal: ActionProposal,
    *,
    receipts: tuple,
    active_policies: dict[str, PolicyRef],
    at: str,
    mode: str = "governed",
) -> dict:
    """Final adapter independently verifies all pre-effect control receipts."""
    required = {
        "approval-gate",
        "blast-radius",
        "progressive-commitment",
    }
    by_control = {receipt.control: receipt for receipt in receipts}
    missing = required - set(by_control)
    if missing:
        raise PermissionError(
            "payment adapter missing governance receipts: "
            + ", ".join(sorted(missing))
        )
    missing_policies = required - set(active_policies)
    if missing_policies:
        raise PermissionError(
            "payment adapter missing active policies: "
            + ", ".join(sorted(missing_policies))
        )
    invalid = [
        control
        for control in required
        if not by_control[control].authorizes(
            proposal,
            active_policies[control],
            at=at,
        )
    ]
    if invalid:
        raise PermissionError(
            "payment adapter rejected invalid receipts: "
            + ", ".join(sorted(invalid))
        )
    return _insert_payment(proposal, at=at, mode=mode)


def unsafe_execute_from_artifact_acceptance(
    proposal: ActionProposal,
    acceptance,
    *,
    at: str,
) -> dict:
    """Teaching anti-pattern: confuses artifact acceptance with action authority."""
    if acceptance.decision.value != "accepted":
        raise PermissionError("upstream artifact was not accepted")
    return _insert_payment(proposal, at=at, mode="naive-artifact-bridge")


def _insert_payment(
    proposal: ActionProposal,
    *,
    at: str,
    mode: str,
) -> dict:
    payment_id = f"payment::{proposal.idempotency_key}"
    with sqlite3.connect(CONTROL_DB) as con:
        existing = con.execute(
            "SELECT payment_id, amount, subject_count, mode "
            "FROM payment_effects WHERE idempotency_key=?",
            (proposal.idempotency_key,),
        ).fetchone()
        if existing:
            return {
                "payment_id": existing[0],
                "amount": existing[1],
                "subject_count": existing[2],
                "mode": existing[3],
                "duplicate": True,
            }
        con.execute(
            "INSERT INTO payment_effects VALUES (?,?,?,?,?,?,?)",
            (
                payment_id,
                proposal.idempotency_key,
                proposal.digest,
                proposal.amount,
                proposal.subject_count,
                mode,
                at,
            ),
        )
        con.execute(
            "UPDATE proposals SET status='PAID' WHERE proposal_id=?",
            (proposal.proposal_id,),
        )
        con.commit()
    return {
        "payment_id": payment_id,
        "amount": proposal.amount,
        "subject_count": proposal.subject_count,
        "mode": mode,
        "duplicate": False,
    }


def state() -> dict:
    if not CONTROL_DB.exists():
        return {
            "proposal_count": 0,
            "receipt_count": 0,
            "event_count": 0,
            "payment_count": 0,
            "payment_total": 0.0,
            "tables": {},
        }
    with sqlite3.connect(CONTROL_DB) as con:
        con.row_factory = sqlite3.Row
        counts = {}
        for table in (
            "proposals",
            "control_receipts",
            "authority_credentials",
            "authority_transitions",
            "budget_usage",
            "governance_events",
            "payment_effects",
        ):
            counts[table] = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        payment_count, payment_total = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payment_effects"
        ).fetchone()
    truth = payroll_truth() if (ACTION_LAB / "payroll.db").exists() else None
    return {
        "proposal_count": counts["proposals"],
        "receipt_count": counts["control_receipts"],
        "credential_count": counts["authority_credentials"],
        "scope_count": counts["budget_usage"],
        "event_count": counts["governance_events"],
        "payment_count": payment_count,
        "payment_total": float(payment_total),
        "payroll": (
            {
                "month": truth.month,
                "employee_count": truth.employee_count,
                "amount": truth.amount,
                "exception_ids": truth.exception_ids,
            }
            if truth
            else None
        ),
        "tables": counts,
    }


def table_rows(table: str, *, limit: int = 100) -> list[dict]:
    allowed = {
        "proposals",
        "control_receipts",
        "authority_credentials",
        "authority_transitions",
        "budget_usage",
        "governance_events",
        "payment_effects",
    }
    if table not in allowed:
        raise KeyError(table)
    with sqlite3.connect(CONTROL_DB) as con:
        con.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in con.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
        ]
