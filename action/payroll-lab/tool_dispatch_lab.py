"""Lecture 22 hands-on: the payroll transfer tools, routed through ToolDispatcher.

Reuses the Tool Dispatch pattern from ../a-tool-dispatch/pattern.py and wires
it to payroll.db. Five scenes, one per enforcement point:

    scene 1  tool hallucination      -- a tool name that does not exist
    scene 2  stale state             -- transfer without a fresh read first
    scene 3  quota                   -- paying the same employee twice
    scene 4  approval gate           -- editing a bank account "helpfully"
    scene 5  saga rollback           -- reversing a batch after a mid-run stop

Run `python3 db.py` first to reset the database, then `python3 tool_dispatch_lab.py`.
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "a-tool-dispatch"))
from pattern import RiskLevel, ToolDispatcher, ToolMetadata  # noqa: E402

DB = HERE / "payroll.db"
MONTH = "2026-06"
con = sqlite3.connect(DB)


# ---- handlers: real writes against payroll.db ------------------------------

def query_payroll(emp_id):
    row = con.execute(
        "SELECT base, bonus, adjustment, status FROM payroll WHERE month=? AND emp_id=?",
        (MONTH, emp_id)).fetchone()
    return {"emp_id": emp_id, "base": row[0], "bonus": row[1],
            "adjustment": row[2], "status": row[3]}


def transfer_salary(emp_id):
    con.execute("UPDATE payroll SET status='PAID' WHERE month=? AND emp_id=?",
                (MONTH, emp_id))
    con.commit()
    return {"emp_id": emp_id, "paid": True}


def reverse_transfer(emp_id):
    con.execute("UPDATE payroll SET status='REVERSED' WHERE month=? AND emp_id=?",
                (MONTH, emp_id))
    con.commit()
    return {"emp_id": emp_id, "reversed": True}


def update_bank_account(emp_id, account):
    con.execute("UPDATE employees SET bank_account=? WHERE emp_id=?", (account, emp_id))
    con.commit()
    return {"emp_id": emp_id, "account": account}


# ---- registry: the metadata IS the discipline -------------------------------

dispatcher = ToolDispatcher()
dispatcher.register(ToolMetadata(
    name="query_payroll",
    description="Read one employee's payslip for the month.",
    when_to_use="Always call this right before any write that touches the same employee.",
    is_read_only=True, is_concurrency_safe=True,
    risk_level=RiskLevel.LOW,
), query_payroll)
dispatcher.register(ToolMetadata(
    name="transfer_salary",
    description="Execute the salary transfer for one employee. Irreversible money movement.",
    when_to_use="Only after the payslip has been verified this session.",
    when_not_to_use="Never twice for the same employee in the same payroll month.",
    is_destructive=True,
    requires_fresh_state=True,
    quota_per_session=1,               # one transfer per employee per session
    rollback_action="reverse_transfer",
    risk_level=RiskLevel.CRITICAL,
), transfer_salary)
dispatcher.register(ToolMetadata(
    name="reverse_transfer",
    description="Reversal (chongzheng) of a salary transfer. Saga inverse of transfer_salary.",
    when_to_use="Rollback only.",
    is_destructive=True, rollback_action="transfer_salary",
    risk_level=RiskLevel.HIGH,
), reverse_transfer)
dispatcher.register(ToolMetadata(
    name="update_bank_account",
    description="Change an employee's bank account. The field payroll depends on.",
    when_to_use="Only on an explicit HR request with a ticket id.",
    when_not_to_use="Never as a side errand of another task.",
    is_destructive=True,
    requires_approval=True,            # a human signs off, or it does not happen
    rollback_action="update_bank_account",
    risk_level=RiskLevel.CRITICAL,
), update_bank_account)


def show(title, trace):
    verdict = trace.status.upper()
    reason = f"  ({trace.rejected_reason})" if trace.rejected_reason else ""
    print(f"{title}\n    -> {verdict}{reason}")


S = "payday-2026-06"
print("== scene 1: the tool the model made up ==")
show("dispatch('transfer_money_fast', E0007)",
     dispatcher.dispatch("transfer_money_fast", {"emp_id": "E0007"}, S))

print("\n== scene 2: transfer on stale state ==")
show("dispatch('transfer_salary', E0007)  # no fresh read yet",
     dispatcher.dispatch("transfer_salary", {"emp_id": "E0007"}, S))
show("dispatch('query_payroll', E0007)   # read first, state now fresh",
     dispatcher.dispatch("query_payroll", {"emp_id": "E0007"}, S))
show("dispatch('transfer_salary', E0007)  # retry",
     dispatcher.dispatch("transfer_salary", {"emp_id": "E0007"}, S))

print("\n== scene 3: paying the same person twice ==")
show("dispatch('transfer_salary', E0007)  # again, same month",
     dispatcher.dispatch("transfer_salary", {"emp_id": "E0007"}, S))

print("\n== scene 4: the 'helpful' account cleanup from lecture 21 ==")
show("dispatch('update_bank_account', E0007, '622200070049')",
     dispatcher.dispatch("update_bank_account",
                         {"emp_id": "E0007", "account": "622200070049"}, S))

print("\n== scene 5: batch stops mid-run, saga rolls back ==")
show("dispatch('query_payroll', E0012)",
     dispatcher.dispatch("query_payroll", {"emp_id": "E0012"}, S))
show("dispatch('transfer_salary', E0012)",
     dispatcher.dispatch("transfer_salary", {"emp_id": "E0012"}, S))
print("    batch aborted by operator. rolling back this session:")
for entry in dispatcher.rollback_session(S):
    print(f"    <- {entry['tool']}: {entry['status']}")

paid = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                   (MONTH,)).fetchone()[0]
reversed_n = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='REVERSED'",
                         (MONTH,)).fetchone()[0]
print(f"\n[LEDGER] PAID={paid}, REVERSED={reversed_n}, "
      f"rejected={sum(t.status == 'rejected' for t in dispatcher.traces)} "
      f"of {len(dispatcher.traces)} dispatches. Every one of them is in dispatcher.traces.")
