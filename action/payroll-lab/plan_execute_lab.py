"""Lecture 23 hands-on: the 800-person payroll run as a Plan-and-Execute DAG.

Reuses the pattern from ../b-plan-and-execute/pattern.py and wires it to
payroll.db. The script walks the full arc:

    act 1  the Planner lays out the whole run as a DAG, a human approves it
    act 2  execution: prep steps run, verification runs, batch 3 of the
           transfers FAILS on a simulated bank timeout -- downstream steps
           cascade to SKIPPED, batches 1/2/4 stay PAID
    act 3  local replan: only the failed sub-DAG is patched (replan cap
           enforced), the retry succeeds, finished work is never redone
    act 4  reconciliation is gated on a human -- release it, run completes

Run `python3 db.py` first to reset the database, then `python3 plan_execute_lab.py`.
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "b-plan-and-execute"))
from pattern import (  # noqa: E402
    Executor, Plan, PlanStep, StepStatus, approve, release_blocked, replan_local,
)

DB = HERE / "payroll.db"
MONTH = "2026-06"
BATCHES = {"b1": (1, 200), "b2": (201, 400), "b3": (401, 600), "b4": (601, 800)}
con = sqlite3.connect(DB)

# Simulated bank outage: batch b3 times out on its first attempt only.
attempts: dict[str, int] = {}


# ---- handlers: (args, prior_outputs) -> output ------------------------------

def prep_payroll(args, prior):
    n = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='DRAFT'",
                    (MONTH,)).fetchone()[0]
    return {"draft_payslips": n}


def prep_accounts(args, prior):
    n = con.execute("SELECT COUNT(*) FROM employees WHERE bank_account != ''").fetchone()[0]
    return {"accounts": n}


def verify_four_elements(args, prior):
    # Four-element check: name, account, amount, payable status.
    bad = con.execute("""
        SELECT COUNT(*) FROM payroll p JOIN employees e ON p.emp_id = e.emp_id
        WHERE p.month=? AND (e.name='' OR e.bank_account='' OR p.base<=0)""",
        (MONTH,)).fetchone()[0]
    if bad:
        raise ValueError(f"{bad} payslips failed the four-element check")
    return {"verified": prior["prep_payroll"]["draft_payslips"]}


def gen_instructions(args, prior):
    return {batch: {"range": rng, "count": rng[1] - rng[0] + 1}
            for batch, rng in BATCHES.items()}


def transfer_batch(args, prior):
    batch = args["batch"]
    attempts[batch] = attempts.get(batch, 0) + 1
    if batch == "b3" and attempts[batch] == 1:
        raise TimeoutError("bank gateway timed out on batch b3")
    lo, hi = BATCHES[batch]
    n = con.execute(
        "UPDATE payroll SET status='PAID' WHERE month=? AND status='DRAFT' "
        "AND CAST(SUBSTR(emp_id, 2) AS INTEGER) BETWEEN ? AND ?",
        (MONTH, lo, hi)).rowcount
    con.commit()
    return {"batch": batch, "paid": n}


def reconcile(args, prior):
    paid = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                       (MONTH,)).fetchone()[0]
    return {"reconciled": paid, "exceptions": 800 - paid}


HANDLERS = {
    "prep_payroll": prep_payroll, "prep_accounts": prep_accounts,
    "verify": verify_four_elements, "gen_instructions": gen_instructions,
    "transfer": transfer_batch, "reconcile": reconcile,
}


# ---- the Planner: one payroll run as a DAG ----------------------------------

def payroll_planner(goal):
    plan = Plan(goal=goal)
    plan.add(PlanStep("prep_payroll", "read draft payslips", "prep_payroll"))
    plan.add(PlanStep("prep_accounts", "read bank accounts", "prep_accounts"))
    plan.add(PlanStep("verify", "four-element check on every payslip", "verify",
                      deps=["prep_payroll", "prep_accounts"]))
    plan.add(PlanStep("gen_instructions", "package transfers into 4 batches",
                      "gen_instructions", deps=["verify"]))
    for batch in BATCHES:
        plan.add(PlanStep(f"transfer_{batch}", f"execute transfers, batch {batch}",
                          "transfer", deps=["gen_instructions"], args={"batch": batch}))
    plan.add(PlanStep("reconcile", "match receipts, list exceptions [HUMAN]",
                      "reconcile", deps=[f"transfer_{b}" for b in BATCHES],
                      requires_human=True))
    return plan


def replanner(goal):
    # Local replan: re-propose ONLY the failed transfer step. The cap in
    # replan_local rejects any "fix" that tries to rewrite the whole plan.
    plan = Plan(goal=goal)
    plan.add(PlanStep("transfer_b3", "retry batch b3 after gateway recovery",
                      "transfer", deps=["gen_instructions"], args={"batch": "b3"}))
    return plan


def show(plan, title):
    print(f"\n-- {title} --")
    for step in plan.steps.values():
        mark = {"done": "DONE ", "failed": "FAIL ", "skipped": "SKIP ",
                "blocked": "BLOCK", "todo": "todo "}[step.status.value]
        note = f"  ({step.error})" if step.error else ""
        print(f"   [{mark}] {step.step_id:16s} {step.description}{note}")


print("== act 1: plan first, sign-off before any money moves ==")
plan = payroll_planner(f"pay 800 employees for {MONTH}")
plan.validate()
show(plan, "the plan, as reviewed by finance")
approve(plan, token="appr-pay-202606")
print("   approved: token appr-pay-202606")

print("\n== act 2: execute. batch b3 hits a bank timeout ==")
executor = Executor(HANDLERS)
plan = executor.run(plan)
show(plan, "state after the failure")
paid = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                   (MONTH,)).fetchone()[0]
print(f"   ledger check: {paid} of 800 already PAID -- finished batches stay finished")

print("\n== act 3: local replan patches ONLY the failed sub-DAG (cap=2) ==")
plan = replan_local(plan, replanner, "transfer_b3", cap=2)
plan = executor.run(plan)
show(plan, "state after the replan run")

print("\n== act 4: reconciliation waits for a human ==")
release_blocked(plan, "reconcile")
plan = executor.run(plan)
show(plan, "final state")
out = plan.steps["reconcile"].output
print(f"\n[LEDGER] reconciled={out['reconciled']}, exceptions={out['exceptions']}, "
      f"transfer attempts per batch: { {b: attempts.get(b, 0) for b in BATCHES} }")
