"""Lecture 26 hands-on: self-grading vs. one external signal.

Reuses the payroll bench from ../../action/payroll-lab (the same SQLite
database the Action module built). Setup: month-end state, 798 payslips
PAID and 2 REVERSED (the saga rollback from lecture 22). The agent's
monthly report claims 800 paid, 0 reversed -- internally tidy, factually
wrong.

    run 1  an introspective critic reviews the report. No external data.
           It approves. Asked to double-check, it approves again.
    run 2  a reconciliation check: two SQL counts against the ledger.
           Both errors surface immediately.

The "model" here is mocked and deterministic (no API key). Its blind spot
is the realistic one: a critic that only re-reads the report can check
consistency, not truth. Pass --strict to make the self-critic harsher and
see what changes (spoiler: the score, not the findings).
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
BENCH = HERE.parent.parent / "action" / "payroll-lab"
sys.path.insert(0, str(BENCH))
import db as bench_db  # noqa: E402

MONTH = "2026-06"
STRICT = "--strict" in sys.argv


def month_end_state():
    """Rebuild the bench into a known month-end state: 798 PAID, 2 REVERSED."""
    bench_db.create()
    con = sqlite3.connect(BENCH / "payroll.db")
    con.execute("UPDATE payroll SET status='PAID' WHERE month=?", (MONTH,))
    con.execute("UPDATE payroll SET status='REVERSED' WHERE month=? "
                "AND emp_id IN ('E0007','E0012')", (MONTH,))
    con.commit()
    return con


con = month_end_state()

# The report the agent wrote for finance. The numbers are internally
# consistent with each other -- and wrong about the ledger.
REPORT = (f"MONTHLY-REPORT month={MONTH} paid=800 reversed=0 "
          f"exceptions=none conclusion=all-clear")


def self_grade(report, strict=False):
    """Introspective critic: the same mock model re-reads its own report.
    It can check format and internal consistency. It has no ledger access,
    so it cannot check truth. Strict mode lowers the score, not the blind spot."""
    notes = ["format complete", "numbers internally consistent",
             "conclusion follows from stated numbers"]
    if strict:
        notes.append("tone could be more cautious")
        return 88, notes
    return 96, notes


def reconcile(report):
    """External signal: two SQL counts against the ledger. Cheap, deterministic."""
    findings = []
    paid_db = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                          (MONTH,)).fetchone()[0]
    reversed_rows = con.execute(
        "SELECT emp_id FROM payroll WHERE month=? AND status='REVERSED'",
        (MONTH,)).fetchall()
    if "paid=800" in report and paid_db != 800:
        findings.append(f"report says paid=800, ledger counts {paid_db}")
    if "reversed=0" in report and reversed_rows:
        ids = ", ".join(r[0] for r in reversed_rows)
        findings.append(f"report says reversed=0, ledger has {len(reversed_rows)} "
                        f"REVERSED rows ({ids})")
    return findings, paid_db, [r[0] for r in reversed_rows]


print(f"== the report under review ==\n   {REPORT}")

print(f"\n== run 1: introspective critic (strict={STRICT}) ==")
for attempt in (1, 2):
    score, notes = self_grade(REPORT, strict=STRICT)
    label = "asked to double-check, same critic" if attempt == 2 else "first pass"
    print(f"   attempt {attempt} ({label}): APPROVED, score {score}/100")
    for n in notes:
        print(f"      - {n}")

print("\n== run 2: reconciliation against the ledger (two SQL counts) ==")
findings, paid_db, reversed_ids = reconcile(REPORT)
for f in findings:
    print(f"   REJECTED: {f}")

print("\n== the revision the external signal forces ==")
print(f"   MONTHLY-REPORT month={MONTH} paid={paid_db} "
      f"reversed={len(reversed_ids)} exceptions={','.join(reversed_ids)} "
      f"conclusion=exceptions-pending")

print(f"\n[VERDICT] same report: the self-critic approved it twice "
      f"(score {'88' if STRICT else '96'}/100), one reconciliation query "
      f"rejected it with {len(findings)} findings. The signal cost two SQL counts.")
