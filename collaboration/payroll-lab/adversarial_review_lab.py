"""Lecture 34 lab: challenge a pay run before money moves.

The author, reviewers, reviser, gate, and final controller are separate roles.
Every review receipt binds one contract, pay-run artifact, content fingerprint,
revision, and rubric version. Run:

    python3 adversarial_review_lab.py
    python3 adversarial_review_lab.py --blind-spot
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


review = load_module(
    HERE.parent / "c-adversarial-review" / "pattern.py",
    "review_pattern",
)
AdversarialReview = review.AdversarialReview
ArtifactEnvelope = review.ArtifactEnvelope
Objection = review.Objection
Outcome = review.Outcome
ReviewPanel = review.ReviewPanel
ReviewPolicy = review.ReviewPolicy
ReviewerSpec = review.ReviewerSpec
ReviserSpec = review.ReviserSpec
Severity = review.Severity
TaskContract = review.TaskContract

sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402


AUTHOR = "payroll-run-author"
REVISER = "payroll-run-reviser"
REQUIRED_RULES = (
    "payslip-status",
    "duplicate-line",
    "total-reconciliation",
)


@dataclass(frozen=True)
class PayLine:
    emp_id: str
    dept: str
    amount: float


@dataclass(frozen=True)
class PayRun:
    lines: tuple[PayLine, ...]
    declared_total: float


def month_end():
    return bench.month_end_state()


def june_contract() -> TaskContract:
    return TaskContract(
        contract_id=f"disburse-{bench.MONTH}",
        version=1,
        objective="release the June salary run",
        output_schema="PayRun",
        accountable_owner="finance-controller",
        input_refs=(f"sqlite://payroll.db/payroll?month={bench.MONTH}",),
        constraints=(
            "only PAID payslips may be disbursed",
            "every employee may appear at most once",
            "declared total must reconcile to the controlling ledger",
        ),
        allowed_tools=("read_payroll_ledger",),
        authority_scope=("read:payroll-ledger", "propose:pay-run"),
        boundary="reviewers may object; only the gate may release",
    )


def payrun_fingerprint(payrun: PayRun) -> str:
    payload = {
        "declared_total": payrun.declared_total,
        "lines": [
            {
                "emp_id": line.emp_id,
                "dept": line.dept,
                "amount": line.amount,
            }
            for line in payrun.lines
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def bind_payrun(
    payrun: PayRun,
    *,
    revision: int,
    producer: str,
) -> ArtifactEnvelope[PayRun]:
    return ArtifactEnvelope(
        artifact_id=f"payrun-{bench.MONTH}-r{revision}",
        contract_digest=june_contract().digest,
        schema=june_contract().output_schema,
        produced_by=producer,
        payload=payrun,
        evidence_refs=(f"sqlite://payroll.db?month={bench.MONTH}",),
    )


def draft_from_obligation(con) -> PayRun:
    lines = tuple(
        PayLine(emp_id, department, float(amount))
        for emp_id, department, amount in con.execute(
            "SELECT emp_id, dept, base_salary "
            "FROM employees ORDER BY emp_id"
        )
    )
    return PayRun(
        lines=lines,
        declared_total=round(sum(line.amount for line in lines), 2),
    )


def draft_with_duplicate(con, emp_id: str = "E0100") -> PayRun:
    lines = [
        PayLine(employee, department, float(amount))
        for employee, department, amount in con.execute(
            "SELECT e.emp_id, e.dept, e.base_salary FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID' ORDER BY e.emp_id",
            (bench.MONTH,),
        )
    ]
    duplicate = next(line for line in lines if line.emp_id == emp_id)
    lines.append(duplicate)
    return PayRun(
        lines=tuple(lines),
        declared_total=round(sum(line.amount for line in lines), 2),
    )


def make_reviewers(con) -> tuple[ReviewerSpec[PayRun], ...]:
    statuses = {
        emp_id: status
        for emp_id, status in con.execute(
            "SELECT emp_id, status FROM payroll WHERE month = ?",
            (bench.MONTH,),
        )
    }
    bank_total = float(
        con.execute(
            "SELECT SUM(e.base_salary) FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID'",
            (bench.MONTH,),
        ).fetchone()[0]
    )

    async def review_status(request):
        payrun = request.artifact.payload
        return tuple(
            Objection(
                code="reversed_in_run",
                rule_id="payslip-status",
                severity=Severity.BLOCKER,
                field=line.emp_id,
                claim=(
                    f"payslip status is "
                    f"{statuses.get(line.emp_id, 'MISSING')}"
                ),
                evidence_refs=(
                    f"sqlite://payroll/{bench.MONTH}/{line.emp_id}"
                    f"?status={statuses.get(line.emp_id, 'MISSING')}",
                ),
            )
            for line in payrun.lines
            if statuses.get(line.emp_id) != "PAID"
        )

    async def review_duplicates(request):
        seen: set[str] = set()
        objections: list[Objection] = []
        for line in request.artifact.payload.lines:
            if line.emp_id in seen:
                objections.append(
                    Objection(
                        code="duplicate_payline",
                        rule_id="duplicate-line",
                        severity=Severity.BLOCKER,
                        field=line.emp_id,
                        claim="employee appears more than once in the pay run",
                        evidence_refs=(
                            f"artifact://{request.artifact.artifact_id}"
                            f"/employee/{line.emp_id}",
                        ),
                    )
                )
            seen.add(line.emp_id)
        return tuple(objections)

    async def review_total(request):
        payrun = request.artifact.payload
        line_sum = round(sum(line.amount for line in payrun.lines), 2)
        objections: list[Objection] = []
        if abs(payrun.declared_total - line_sum) > 0.005:
            objections.append(
                Objection(
                    code="declared_total_mismatch",
                    rule_id="total-reconciliation",
                    severity=Severity.BLOCKER,
                    field="declared_total",
                    claim=(
                        f"declared={payrun.declared_total:.2f} "
                        f"line_sum={line_sum:.2f}"
                    ),
                    evidence_refs=(
                        f"artifact://{request.artifact.artifact_id}/line-sum",
                    ),
                )
            )
        if abs(line_sum - bank_total) > 0.005:
            objections.append(
                Objection(
                    code="bank_total_mismatch",
                    rule_id="total-reconciliation",
                    severity=Severity.BLOCKER,
                    field="declared_total",
                    claim=f"line_sum={line_sum:.2f} bank={bank_total:.2f}",
                    evidence_refs=(
                        f"sqlite://payroll.db/paid-total?month={bench.MONTH}",
                    ),
                )
            )
        return tuple(objections)

    return (
        ReviewerSpec(
            reviewer_id="status-reviewer",
            actor_id="ledger-status-agent",
            rule_ids=("payslip-status",),
            evidence_scope=("read:payroll-status",),
            review=review_status,
        ),
        ReviewerSpec(
            reviewer_id="duplicate-reviewer",
            actor_id="duplicate-control-agent",
            rule_ids=("duplicate-line",),
            evidence_scope=("read:candidate-paylines",),
            review=review_duplicates,
        ),
        ReviewerSpec(
            reviewer_id="reconciliation-reviewer",
            actor_id="ledger-reconciliation-agent",
            rule_ids=("total-reconciliation",),
            evidence_scope=("read:paid-total",),
            review=review_total,
        ),
    )


async def revise_payrun(request, blockers):
    drop = {
        objection.field
        for objection in blockers
        if objection.code == "reversed_in_run"
    }
    deduplicate = {
        objection.field
        for objection in blockers
        if objection.code == "duplicate_payline"
    }
    seen: set[str] = set()
    lines: list[PayLine] = []
    for line in request.artifact.payload.lines:
        if line.emp_id in drop:
            continue
        if line.emp_id in deduplicate and line.emp_id in seen:
            continue
        seen.add(line.emp_id)
        lines.append(line)
    revised = PayRun(
        lines=tuple(lines),
        declared_total=round(sum(line.amount for line in lines), 2),
    )
    return bind_payrun(
        revised,
        revision=request.artifact_revision + 1,
        producer=REVISER,
    )


def full_policy() -> ReviewPolicy:
    return ReviewPolicy(
        rubric_version="payroll-release-v1",
        required_rule_ids=REQUIRED_RULES,
        max_rounds=3,
    )


def status_only_policy() -> ReviewPolicy:
    return ReviewPolicy(
        rubric_version="status-only-v1",
        required_rule_ids=("payslip-status",),
        max_rounds=1,
    )


def run_reviewed(
    payrun: PayRun,
    panel: ReviewPanel[PayRun],
    policy: ReviewPolicy,
    *,
    reviser: ReviserSpec[PayRun] | None,
    author_actor_id: str = AUTHOR,
):
    system = AdversarialReview(
        panel,
        policy,
        author_actor_id=author_actor_id,
        fingerprint=payrun_fingerprint,
        reviser=reviser,
    )
    return asyncio.run(
        system.run(
            june_contract(),
            bind_payrun(payrun, revision=0, producer=author_actor_id),
        )
    )


def full_panel(con) -> ReviewPanel[PayRun]:
    return ReviewPanel("payroll-review-panel", make_reviewers(con))


def reviser() -> ReviserSpec[PayRun]:
    return ReviserSpec(
        reviser_id="payroll-run-reviser",
        actor_id=REVISER,
        revise=revise_payrun,
    )


def main() -> None:
    con = month_end()

    if "--blind-spot" not in sys.argv:
        print("== scene 1: the run that would repay two reversed payslips ==")
        draft = draft_from_obligation(con)
        print(
            f"   draft: {len(draft.lines)} lines, "
            f"declared {draft.declared_total:,.2f}"
        )
        result = run_reviewed(
            draft,
            full_panel(con),
            full_policy(),
            reviser=reviser(),
        )
        for item in result.rounds:
            receipt = item.receipt
            print(
                f"   round r{receipt.artifact_revision}: "
                f"checked={len(receipt.checked_rule_ids)} "
                f"objections={len(receipt.objections)} "
                f"blockers={len(receipt.blockers)}"
            )
        payrun = result.artifact.payload
        print(
            f"   outcome={result.outcome.value}  "
            f"receipt={result.acceptance_receipt.decision.value}"
        )
        print(
            f"   final: {len(payrun.lines)} lines, "
            f"total {payrun.declared_total:,.2f} "
            "(38,444 stayed in the bank)"
        )
        latest = result.latest_review
        print(
            f"   bound review: artifact={latest.artifact_id} "
            f"fingerprint={latest.artifact_fingerprint} "
            f"rubric={latest.rubric_version}"
        )

        print("\n== scene 2: reviewer and reviser share one actor ==")
        status = make_reviewers(con)[0]
        self_panel = ReviewPanel(
            "self-review-panel",
            (
                ReviewerSpec(
                    reviewer_id=status.reviewer_id,
                    actor_id=REVISER,
                    rule_ids=status.rule_ids,
                    evidence_scope=status.evidence_scope,
                    review=status.review,
                ),
            ),
        )
        result = run_reviewed(
            draft,
            self_panel,
            status_only_policy(),
            reviser=reviser(),
        )
        print(
            f"   outcome={result.outcome.value}  "
            f"receipt={result.acceptance_receipt.decision.value}"
        )
        print(
            "   findings: "
            f"{[finding.code for finding in result.run_findings]}"
        )

    else:
        print("== scene 3: a narrow rubric approves a double pay ==")
        draft = draft_with_duplicate(con)
        status = make_reviewers(con)[0]
        narrow = ReviewPanel("status-only-panel", (status,))
        result = run_reviewed(
            draft,
            narrow,
            status_only_policy(),
            reviser=None,
        )
        duplicates = sum(
            1
            for line in result.artifact.payload.lines
            if line.emp_id == "E0100"
        )
        print("   required rules: ['payslip-status']")
        print(
            f"   outcome={result.outcome.value}  "
            f"receipt={result.acceptance_receipt.decision.value}"
        )
        print(
            f"   E0100 lines={duplicates} "
            "(double pay, 11,700 extra)"
        )
        print(
            "   -> every component followed the rubric; "
            "the rubric was incomplete."
        )

        print("\n   release rubric with the same lone reviewer:")
        result = run_reviewed(
            draft,
            narrow,
            full_policy(),
            reviser=None,
        )
        print(
            f"   outcome={result.outcome.value}  "
            f"missing={list(result.latest_review.missing_rule_ids)}"
        )

        print("\n   full panel over the same run:")
        result = run_reviewed(
            draft,
            full_panel(con),
            full_policy(),
            reviser=reviser(),
        )
        payrun = result.artifact.payload
        print(
            f"   round r0 blockers={len(result.rounds[0].receipt.blockers)} "
            f"outcome={result.outcome.value} "
            f"receipt={result.acceptance_receipt.decision.value}"
        )
        print(
            f"   final: {len(payrun.lines)} lines, "
            f"total {payrun.declared_total:,.2f}"
        )


if __name__ == "__main__":
    main()
