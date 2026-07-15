"""Shared month-end bench state for the Reflection-module labs.

Rebuilds the Action module's payroll database into the known month-end
state the Reflection labs reflect on: 798 payslips PAID, 2 REVERSED
(E0007 and E0012 — the saga rollback from lecture 22).
"""
import sqlite3
import sys
from pathlib import Path

BENCH = Path(__file__).parent.parent.parent / "action" / "payroll-lab"
sys.path.insert(0, str(BENCH))
import db as action_db  # noqa: E402

MONTH = "2026-06"
REVERSED_IDS = ("E0007", "E0012")


def month_end_state() -> sqlite3.Connection:
    action_db.create()
    con = sqlite3.connect(BENCH / "payroll.db")
    con.execute("UPDATE payroll SET status='PAID' WHERE month=?", (MONTH,))
    con.execute(
        "UPDATE payroll SET status='REVERSED' WHERE month=? AND emp_id IN (?, ?)",
        (MONTH, *REVERSED_IDS))
    con.commit()
    return con
