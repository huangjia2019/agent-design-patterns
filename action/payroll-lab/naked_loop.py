"""A ~50-line Perceive-Reason-Act loop with NO guardrails. Lecture 21 hands-on.

It works, and it is fast. That is exactly the problem: watch what else it
touches. Run `python db.py --diff` afterwards to see every row it changed.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "payroll.db"
MONTH = "2026-06"


def perceive(cur):
    approvals = cur.execute(
        "SELECT id, emp_id, type, amount FROM approvals WHERE status='APPROVED'").fetchall()
    drafts = cur.execute(
        "SELECT COUNT(*) FROM payroll WHERE month=? AND status='DRAFT'", (MONTH,)).fetchone()[0]
    print(f"[PERCEIVE] {len(approvals)} approved changes waiting, {drafts} draft payslips")
    return approvals, drafts


def reason(approvals, drafts):
    plan = [("apply_approval", a) for a in approvals]
    if drafts:
        plan.append(("pay_everyone", None))
    print(f"[REASON]   plan: {[step for step, _ in plan]}")
    return plan


def act(cur, step, arg):
    if step == "apply_approval":
        aid, emp, kind, amount = arg
        col = "bonus" if kind == "bonus" else "adjustment"
        cur.execute(f"UPDATE payroll SET {col}={col}+? WHERE month=? AND emp_id=?",
                    (amount, MONTH, emp))
        cur.execute("UPDATE approvals SET status='APPLIED' WHERE id=?", (aid,))
        print(f"[ACT] approval #{aid}: {emp} {col} += {amount}")
        # ---- "helpful" extras nobody asked for --------------------------------
        acct = cur.execute("SELECT bank_account FROM employees WHERE emp_id=?",
                           (emp,)).fetchone()[0]
        if "-" in acct:
            cur.execute("UPDATE employees SET bank_account=? WHERE emp_id=?",
                        (acct.replace("-", ""), emp))
            print(f"[ACT]   ...also normalized {emp}'s bank account format (nobody asked)")
        cur.execute("UPDATE payroll SET note='' WHERE month=? AND emp_id=?", (MONTH, emp))
        print(f"[ACT]   ...also cleared a 'redundant' note field (nobody asked)")
    elif step == "pay_everyone":
        n = cur.execute("UPDATE payroll SET status='PAID' WHERE month=? AND status='DRAFT'",
                        (MONTH,)).rowcount
        print(f"[ACT] marked {n} payslips PAID in one shot. No confirmation, no dry run.")


con = sqlite3.connect(DB)
cur = con.cursor()
for step, arg in reason(*perceive(cur)):
    act(cur, step, arg)
con.commit()
con.close()
print("[DONE] loop finished. Run `python db.py --diff` to see everything it touched.")
