"""Lecture 36 hands-on: the policies this course already shipped, and what
their runtime receipts can prove about them. Too little.

Three scenes on the month-end payroll world, no API key, no database
damage. Every import here is committed code; the four governance patterns
industrialize what scene 3 sketches.

    scene 1  the policy inventory: the last four lectures alone left six
             policy constants living in source code -- batch escalation
             line, portfolio cash line, sign-off threshold, source floor,
             the release rule catalog, the funding cap. For each one the
             lab re-reads the committed file and proves the literal is
             still there. The scan deliberately makes no claim about
             CODEOWNERS, branch protection, or external review. It proves
             a narrower point: the runtime contract carries no policy owner,
             version, change approval, or change trace.
    scene 2  the quiet widening: the same accepted June portfolio
             (13,706,097, 798 payable slips) hits the REAL committed
             PortfolioBoundary twice -- once with the 13,000,000 cash
             line (escalated), once after someone widens the limit to
             30,000,000 (accepted). The refusal receipt names the limit
             in its finding evidence; the acceptance receipt carries no
             trace of which policy judged it. A widened gate looks
             exactly like a healthy morning.
    scene 3  pinning the policy: a minimal PolicyCard gives the number
             an owner, a version, a change approver distinct from the
             proposer, and a content digest. Receipts pin the digest, so
             the widened limit shows up in every receipt it signs.
             Lecture 37 puts an approval gate on the change itself; 38
             bounds what one bad policy can spend; 39 makes authority
             something an agent earns in stages; 40 makes all of it
             replayable.

The claimed June total is computed from the bench ledger, not typed in.
PolicyCard is a teaching minimum and can still be bypassed by direct object
construction. It has no registry, mandatory mediation, distribution, cache
invalidation, or rollback. Those belong to the four patterns, not the intro.

Run `python3 ungoverned_policy_lab.py`.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, fields
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
REFLECTION_LAB = REPO / "reflection" / "payroll-lab"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_hd = load_module(
    REPO / "collaboration" / "a-hierarchical-delegation" / "pattern.py",
    "hd_pattern",
)
PayrollPortfolioResult = _hd.PayrollPortfolioResult
PortfolioBoundary = _hd.PortfolioBoundary

# The pattern imports the contract layer as a real package module; use the
# SAME module object so enum identities line up across the seam.
_bc = sys.modules["collaboration.boundary_contract"]
AcceptanceDecision = _bc.AcceptanceDecision
ArtifactEnvelope = _bc.ArtifactEnvelope
TaskContract = _bc.TaskContract

bench = load_module(
    REFLECTION_LAB / "bench.py",
    "_adps_governance_intro_reflection_bench",
)
_governance_contract = load_module(
    REPO / "governance" / "boundary_contract.py",
    "_adps_governance_intro_boundary_contract",
)
PolicyRef = _governance_contract.PolicyRef


# ---- scene 1: the inventory -----------------------------------------------------

INVENTORY = (
    ("collaboration/payroll-lab/hierarchical_delegation_lab.py",
     "amount_threshold=3_000_000", "单批工资总额升级线（32 讲）"),
    ("collaboration/payroll-lab/hierarchical_delegation_lab.py",
     "PortfolioBoundary(max_total_amount=13_000_000)", "整月组合现金线（32 讲）"),
    ("collaboration/payroll-lab/fan_out_gather_lab.py",
     "SIGN_OFF_THRESHOLD = 10_000.0", "对账分歧加签线（33 讲）"),
    ("collaboration/payroll-lab/fan_out_gather_lab.py",
     "min_success_rate=0.95", "来源成功率下限（33 讲）"),
    ("collaboration/payroll-lab/adversarial_review_lab.py",
     "REQUIRED_RULES = (", "打款放行必查规则目录（34 讲）"),
    ("collaboration/payroll-lab/handoff_chain_lab.py",
     "FUNDING_CAP = 14_000_000.0", "薪酬账户资金上限（35 讲）"),
)


def verify_inventory() -> list[dict]:
    rows = []
    for rel_path, literal, meaning in INVENTORY:
        source = (REPO / rel_path).read_text(encoding="utf-8")
        rows.append({"file": rel_path, "literal": literal,
                     "meaning": meaning, "found": literal in source})
    return rows


# ---- scene 2: the quiet widening ------------------------------------------------

def month_end():
    return bench.month_end_state()


def june_gross(con) -> float:
    return float(con.execute(
        "SELECT SUM(base + bonus + adjustment) FROM payroll "
        "WHERE month=? AND status='PAID'",
        (bench.MONTH,),
    ).fetchone()[0])


def root_contract(con) -> TaskContract:
    roster = tuple(str(e) for (e,) in con.execute(
        "SELECT emp_id FROM payroll "
        "WHERE month=? AND status='PAID' ORDER BY emp_id",
        (bench.MONTH,),
    ))
    return TaskContract(
        contract_id=f"payroll-{bench.MONTH}", version=1,
        objective="settle June payroll for all clients",
        output_schema="PayrollPortfolioResult",
        accountable_owner="settlement-supervisor",
        input_refs=roster,
    )


def june_portfolio(con) -> PayrollPortfolioResult:
    depts = [
        department
        for (department,) in con.execute(
            "SELECT DISTINCT e.dept "
            "FROM payroll p JOIN employees e ON e.emp_id=p.emp_id "
            "WHERE p.month=? AND p.status='PAID' ORDER BY e.dept",
            (bench.MONTH,),
        )
    ]
    gross = june_gross(con)
    employee_count = int(con.execute(
        "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
        (bench.MONTH,),
    ).fetchone()[0])
    return PayrollPortfolioResult(
        claimed_total_amount=gross,
        admitted_total_amount=gross,
        employee_count=employee_count,
        auto_approved=tuple(f"batch::{d}" for d in depts),
        human_review=(),
        child_receipt_ids=tuple(f"receipt::batch::{d}" for d in depts),
    )


def evaluate_with_limit(con, limit: float):
    root = root_contract(con)
    artifact = ArtifactEnvelope(
        artifact_id=f"portfolio-{bench.MONTH}",
        contract_digest=root.digest,
        schema=root.output_schema,
        produced_by="settlement-supervisor",
        payload=june_portfolio(con),
        evidence_refs=(f"sqlite://payroll.db?month={bench.MONTH}",),
    )
    return PortfolioBoundary(max_total_amount=limit).evaluate(root, artifact)


def policy_traces(receipt) -> list[str]:
    """Every place in a receipt where the judging policy left a mark."""
    marks = [f.evidence for f in receipt.findings if "limit=" in f.evidence]
    for f in fields(receipt):
        value = getattr(receipt, f.name)
        if isinstance(value, str) and "limit" in value:
            marks.append(value)
    return marks


# ---- scene 3: pinning the policy ------------------------------------------------

@dataclass(frozen=True)
class PolicyCard:
    """The minimum that turns a number into a governed object: an owner,
    a version, a reason, and a content digest receipts can pin."""

    policy_id: str
    version: int
    owner: str
    rule: str
    value: float
    reason: str

    @property
    def ref(self) -> PolicyRef:
        return PolicyRef.from_content(
            self.policy_id,
            self.version,
            {
                "owner": self.owner,
                "rule": self.rule,
                "value": self.value,
                "reason": self.reason,
            },
        )

    @property
    def digest(self) -> str:
        return self.ref.digest


def issue_policy(card: PolicyCard, *, proposed_by: str, approved_by: str) -> PolicyCard:
    """Change control in one sentence: the person who wants the new limit
    cannot be the person who approves it."""
    if proposed_by == approved_by:
        raise PermissionError(
            f"policy '{card.policy_id}' v{card.version}: proposer and approver "
            f"are the same actor ({proposed_by}); four-eyes required")
    return card


@dataclass(frozen=True)
class GovernedReceipt:
    """The same acceptance receipt, plus the identity of the policy that
    produced it. The widened limit now signs everything it touches."""

    receipt: object
    policy_id: str
    policy_version: int
    policy_digest: str


def evaluate_governed(con, card: PolicyCard) -> GovernedReceipt:
    receipt = evaluate_with_limit(con, card.value)
    return GovernedReceipt(receipt=receipt, policy_id=card.policy_id,
                           policy_version=card.version, policy_digest=card.digest)


# ---- scenes ---------------------------------------------------------------------

def run_policy_drift() -> dict:
    """Return the lecture-36 policy-drift experiment as structured evidence."""
    con = month_end()
    try:
        inventory = verify_inventory()
        gross = june_gross(con)
        strict = evaluate_with_limit(con, 13_000_000)
        loose = evaluate_with_limit(con, 30_000_000)
        v1 = issue_policy(
            PolicyCard(
                "cash-line",
                1,
                "finance-controller",
                "portfolio claimed total must stay under",
                13_000_000,
                "2026 annual budget line",
            ),
            proposed_by="finance-controller",
            approved_by="cfo",
        )
        v2 = issue_policy(
            PolicyCard(
                "cash-line",
                2,
                "finance-controller",
                "portfolio claimed total must stay under",
                30_000_000,
                "one-off retro payment window, expires 2026-07",
            ),
            proposed_by="finance-controller",
            approved_by="cfo",
        )
        governed_v1 = evaluate_governed(con, v1)
        governed_v2 = evaluate_governed(con, v2)
        return {
            "mode": "policy-drift",
            "inventory": {
                "count": len(inventory),
                "verified": sum(row["found"] for row in inventory),
                "items": tuple(inventory),
            },
            "portfolio": {
                "month": bench.MONTH,
                "claimed_total": gross,
                "employee_count": june_portfolio(con).employee_count,
            },
            "before": {
                "limit": v1.value,
                "decision": strict.decision.value,
                "raw_policy_marks": tuple(policy_traces(strict)),
                "policy_id": v1.policy_id,
                "policy_version": v1.version,
                "policy_digest": governed_v1.policy_digest,
            },
            "after": {
                "limit": v2.value,
                "decision": loose.decision.value,
                "raw_policy_marks": tuple(policy_traces(loose)),
                "policy_id": v2.policy_id,
                "policy_version": v2.version,
                "policy_digest": governed_v2.policy_digest,
            },
            "timeline": (
                {
                    "sequence": 1,
                    "event_type": "policy.inventory",
                    "control": "course-policy-scan",
                    "decision": "verified",
                    "summary": f"{sum(row['found'] for row in inventory)}/{len(inventory)} policy literals found",
                    "event_hash": "",
                },
                {
                    "sequence": 2,
                    "event_type": "policy.evaluated",
                    "control": "cash-line-v1",
                    "decision": strict.decision.value,
                    "summary": "13,000,000 limit appears only because the proposal was escalated",
                    "event_hash": governed_v1.policy_digest,
                },
                {
                    "sequence": 3,
                    "event_type": "policy.changed",
                    "control": "cash-line",
                    "decision": "approved",
                    "summary": "portfolio limit widened from 13,000,000 to 30,000,000",
                    "event_hash": governed_v2.policy_digest,
                },
                {
                    "sequence": 4,
                    "event_type": "policy.evaluated",
                    "control": "cash-line-v2",
                    "decision": loose.decision.value,
                    "summary": "raw acceptance receipt carries no policy identity",
                    "event_hash": governed_v2.policy_digest,
                },
            ),
        }
    finally:
        con.close()


def main() -> None:
    print("== scene 1: the policy inventory, last four lectures only ==")
    for row in verify_inventory():
        mark = "在" if row["found"] else "不在(!)"
        print(f"   [{mark}] {row['meaning']}")
        print(f"        {row['file']} :: {row['literal']}")
    print("   -> 本实验不推断 Git 外部审批。它只证明运行时契约里没有策略主人、")
    print("      版本、变更审批和变更轨迹。")

    result = run_policy_drift()
    print(
        "\n== scene 2: the quiet widening "
        f"(June claim {result['portfolio']['claimed_total']:,.0f}) =="
    )
    print(
        f"   limit 13,000,000 -> {result['before']['decision']}"
    )
    for mark in result["before"]["raw_policy_marks"]:
        print(f"      refusal names the policy: {mark}")
    print(f"   limit 30,000,000 -> {result['after']['decision']}")
    print(
        "      policy marks on the acceptance receipt: "
        f"{list(result['after']['raw_policy_marks'])}"
    )
    print("   -> 只有拦下时策略才现身。放行的回执里，闸门用的是哪一版尺度，")
    print("      一个字都没有。半夜把 13,000,000 改成 30,000,000，第二天")
    print("      所有回执照常 accepted，没有任何一张纸记得这件事。")

    print("\n== scene 3: pin the policy, the change signs its own name ==")
    print(
        "   v1 (13,000,000) "
        f"digest={result['before']['policy_digest']} -> "
        f"{result['before']['decision']}"
    )
    print(
        "   v2 (30,000,000) "
        f"digest={result['after']['policy_digest']} -> "
        f"{result['after']['decision']}"
    )
    print("   -> 同一份组合，两张回执钉着两个不同的策略摘要。放宽这件事")
    print("      第一次在放行的回执上留下了自己的名字、版本和理由。")
    try:
        issue_policy(
            PolicyCard("cash-line", 3, "finance-controller",
                       "portfolio claimed total must stay under", 99_000_000,
                       "why not"),
            proposed_by="night-shift-agent", approved_by="night-shift-agent")
    except PermissionError as err:
        print(f"   four-eyes: {err}")


if __name__ == "__main__":
    main()
