"""Lecture 31 hands-on: what leaks at the seam between two agents.

Reuses the month-end payroll bench (798 PAID, 2 REVERSED — the saga
rollback from lecture 22). A supervisor delegates one task to a worker:
write June's monthly payroll report. The worker is equally competent in
every scene; the only thing that changes is what crosses the seam.

    scene 1  bare handoff: the packet carries one sentence. The worker
             does exactly what it was told, reports all-clear, says
             "done" -- and the supervisor publishes on the worker's word.
             Wrong report shipped; nothing in the run knows.
    scene 2  a gate on the seam: same bare packet, but the artifact must
             pass an acceptance check before the supervisor takes it.
             The check is literally the two SQL counts lecture 26 used
             as its external signal. First attempt rejected with two
             findings; one redo with the findings attached comes back
             right.
    scene 3  full contract: the packet carries the objective, the
             constraint (REVERSED payslips are exceptions), the expected
             shape, and the acceptance check. Right on the first pass.

The "worker" is a deterministic mock: its behaviour is keyed to what the
handoff packet carries. That is the point of the demo -- same worker,
three packets, three outcomes. It shows the structure of the seam, not
any model's competence.

Run `python3 delegation_boundary_lab.py` (no API key needed).
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402

con = bench.month_end_state()
MONTH = bench.MONTH


# ---- the worker: same competence in every scene ------------------------------

def worker_write_report(packet: dict) -> str:
    """Deterministic stand-in for a worker agent. It answers exactly the
    task it was handed: with no constraint in the packet it counts the
    month's payslips and calls it a day; with the REVERSED constraint
    (or a rejection's findings) in context, it separates the exceptions."""
    knows_reversed = (
        any("REVERSED" in c for c in packet.get("constraints", []))
        or bool(packet.get("findings"))
    )
    if not knows_reversed:
        total = con.execute(
            "SELECT COUNT(*) FROM payroll WHERE month=?", (MONTH,)).fetchone()[0]
        return (f"MONTHLY-REPORT month={MONTH} paid={total} reversed=0 "
                f"exceptions=none conclusion=all-clear")
    paid = con.execute(
        "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
        (MONTH,)).fetchone()[0]
    rev = [r[0] for r in con.execute(
        "SELECT emp_id FROM payroll WHERE month=? AND status='REVERSED'",
        (MONTH,)).fetchall()]
    return (f"MONTHLY-REPORT month={MONTH} paid={paid} reversed={len(rev)} "
            f"exceptions={','.join(rev)} conclusion=exceptions-pending")


# ---- the acceptance check: lecture 26's two SQL counts, now on the seam ------

def acceptance(report: str) -> list[str]:
    """The same external signal lecture 26 aimed at the agent's own report,
    stationed at the delegation boundary. Cheap, deterministic."""
    findings = []
    paid_db = con.execute(
        "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
        (MONTH,)).fetchone()[0]
    rev = [r[0] for r in con.execute(
        "SELECT emp_id FROM payroll WHERE month=? AND status='REVERSED'",
        (MONTH,)).fetchall()]
    if f"paid={paid_db}" not in report:
        findings.append(f"report's paid count disagrees with the ledger ({paid_db})")
    if rev and "reversed=0" in report:
        findings.append(f"ledger has {len(rev)} REVERSED rows ({', '.join(rev)}); "
                        f"report lists none")
    return findings


def ledger_truth() -> tuple[int, int]:
    paid = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                       (MONTH,)).fetchone()[0]
    rev = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='REVERSED'",
                      (MONTH,)).fetchone()[0]
    return paid, rev


paid_truth, rev_truth = ledger_truth()
print(f"== ledger truth: paid={paid_truth}, reversed={rev_truth} ==")

# ---- scene 1: bare handoff — nothing guards the seam --------------------------

print("\n== scene 1: bare handoff, supervisor takes the worker's word ==")
packet = {"objective": f"summarize {MONTH} payroll into the monthly report"}
print(f"   packet crossing the seam: {packet}")
report = worker_write_report(packet)
print("   worker: done.")
print(f"   supervisor publishes without checking:\n      {report}")
wrong = f"paid={paid_truth}" not in report
print(f"   published report wrong: {str(wrong).lower()} "
      f"(claims paid=800, ledger says {paid_truth}). Every step reported success.")

# ---- scene 2: same packet, but an acceptance gate sits on the seam ------------

print("\n== scene 2: same bare packet, acceptance gate on the seam ==")
report = worker_write_report(packet)
findings = acceptance(report)
print(f"   attempt 1 -> REJECTED at the seam, {len(findings)} findings:")
for f in findings:
    print(f"      - {f}")
retry_packet = {**packet, "findings": findings}
report = worker_write_report(retry_packet)
print(f"   redo with findings attached -> {report}")
print(f"   acceptance: {'ACCEPTED' if not acceptance(report) else 'REJECTED'} "
      f"(cost: one redo)")

# ---- scene 3: the packet carries the contract ---------------------------------

print("\n== scene 3: the contract travels with the task ==")
contract_packet = {
    "objective": f"summarize {MONTH} payroll into the monthly report",
    "constraints": ["REVERSED payslips must be listed as exceptions",
                    "conclusion must reflect ledger facts"],
    "output_schema": "MONTHLY-REPORT month/paid/reversed/exceptions/conclusion",
}
print("   packet now carries objective + constraints + expected shape")
report = worker_write_report(contract_packet)
print(f"   worker's first pass:\n      {report}")
print(f"   acceptance: {'ACCEPTED' if not acceptance(report) else 'REJECTED'} "
      f"(cost: zero redos)")

print("\n[VERDICT] same worker, three packets. Bare handoff shipped a wrong")
print("report and nothing in the run knew. A gate on the seam caught it at")
print("the cost of one redo. A contract that travels with the task got it")
print("right the first time. The seam, not the worker, made the difference.")
