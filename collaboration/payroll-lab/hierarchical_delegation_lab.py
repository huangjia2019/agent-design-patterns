"""Lecture 32 hands-on: the delegation kit at work, and where its gate ends.

Runs the real pattern from ../a-hierarchical-delegation/pattern.py on the
month-end payroll bench (798 PAID, 2 REVERSED). A supervisor splits 800
employees into per-department batches, dispatches each to a worker in an
isolated context, reads back structured artifacts only, and gates them.

    scene 1  the kit at work: five dept batches, workers flag the two
             REVERSED employees they see in their rows, the gate routes
             those batches to a human and auto-approves the rest.
    scene 2  isolation pays: one worker dies mid-run. The exception
             never reaches the supervisor's loop; it degrades into a
             FAILURE artifact and costs exactly one batch.
    scene 3  the self-report seam: a buggy worker silently drops 12
             rows, reports SUCCESS with high confidence, and the gate
             approves it -- every field the gate reads is written by
             the worker itself. One deterministic roster-coverage
             check, owned by nobody's self-report, catches it.
    scene 4  run with --sum-blind: every batch is clean and under the
             per-batch threshold, so everything auto-approves. The sum
             crosses the month's cash line and no rule ever looks at
             it. The generic form of this gap is committed as G1 in
             collaboration/stress_collab_gaps.py.

Thresholds (3,000,000 per batch, 13,000,000 cash line) are teaching
values sized to this bench. Workers are deterministic mocks; dispatch is
the seam where a real framework plugs in.

Run `python3 hierarchical_delegation_lab.py` (add --sum-blind for scene 4).
"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "a-hierarchical-delegation"))
sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
from pattern import (  # noqa: E402
    SalaryBatchArtifact,
    SafetyBoundary,
    SettlementSupervisor,
    Verdict,
)
import bench  # noqa: E402

SUM_BLIND = "--sum-blind" in sys.argv

con = bench.month_end_state()
REVERSED_IDS = set(bench.REVERSED_IDS)

# Roster from the bench. The pattern batches by "client"; this bench's
# natural grain is the department, so dept plays the client role here.
roster = [{"id": e, "client": d, "base": b} for e, d, b in con.execute(
    "SELECT emp_id, dept, base_salary FROM employees ORDER BY emp_id")]


# ---- workers: deterministic mocks behind the dispatch seam -------------------

async def worker(spec, rows):
    """A diligent worker: computes its batch, flags the REVERSED payslips
    it can see in its own rows, and returns only the artifact."""
    flagged = [r["id"] for r in rows if r["id"] in REVERSED_IDS]
    return SalaryBatchArtifact(
        batch_id=spec.batch_id, verdict=Verdict.SUCCESS,
        employee_count=len(rows), total_amount=float(sum(r["base"] for r in rows)),
        needs_review=flagged, confidence=0.98)


def show(summary):
    print(f"   total (clean batches): {summary['total']:,.0f}")
    print(f"   employee_count: {summary['employee_count']}")
    print(f"   auto_approved: {summary['auto_approved']}")
    print(f"   human_review:  {summary['human_review']}")


BOUNDARY = SafetyBoundary(amount_threshold=3_000_000, min_confidence=0.85)

if not SUM_BLIND:
    print("== scene 1: the delegation kit at work ==")
    sup = SettlementSupervisor(worker, BOUNDARY)
    batches = sup.decompose(roster)
    print(f"   decomposed: {len(roster)} employees -> "
          f"{len(batches)} batches: {[s.batch_id for s, _ in batches]}")
    spec = batches[0][0]
    print(f"   every spec pins a boundary: '{spec.boundary}'")
    summary = asyncio.run(sup.run(roster))
    show(summary)
    print("   -> workers surfaced the REVERSED employees; those batches wait")
    print("      for a human. The supervisor computed nothing itself: it read")
    print("      five artifacts of six fields each, not 800 rows of work.")

    print("\n== scene 2: one worker dies; isolation pays ==")

    async def flaky(spec, rows):
        if spec.batch_id == "batch::Ops":
            raise RuntimeError("worker context blew up")
        return await worker(spec, rows)

    summary = asyncio.run(SettlementSupervisor(flaky, BOUNDARY).run(roster))
    show(summary)
    print("   -> the exception never reached the supervisor's loop. One dead")
    print("      batch degraded to a FAILURE artifact and costs exactly one")
    print("      batch; the other four are unaffected.")

    print("\n== scene 3: the self-report seam ==")

    async def dropper(spec, rows):
        if spec.batch_id == "batch::Engineering":
            kept = rows[:-12]                    # silently loses 12 employees
            return SalaryBatchArtifact(
                batch_id=spec.batch_id, verdict=Verdict.SUCCESS,
                employee_count=len(kept),
                total_amount=float(sum(r["base"] for r in kept)),
                confidence=0.99)
        return await worker(spec, rows)

    summary = asyncio.run(SettlementSupervisor(dropper, BOUNDARY).run(roster))
    show(summary)
    print("   -> batch::Engineering auto-approved: SUCCESS, high confidence,")
    print("      under threshold. Every field the gate read was written by")
    print("      the worker that made the mistake.")
    missing = len(roster) - summary["employee_count"]
    print(f"   roster coverage check (owned by no worker): "
          f"{summary['employee_count']} counted vs {len(roster)} on roster "
          f"-> {missing} employees missing")

else:
    print("== scene 4 (--sum-blind): every batch legal, the sum unwatched ==")
    CASH_LINE = 13_000_000.0                     # teaching mock: month's cash ceiling

    async def clean(spec, rows):                 # no flags this time: isolate the sum story
        return SalaryBatchArtifact(
            batch_id=spec.batch_id, verdict=Verdict.SUCCESS,
            employee_count=len(rows), total_amount=float(sum(r["base"] for r in rows)),
            confidence=0.98)

    summary = asyncio.run(SettlementSupervisor(clean, BOUNDARY).run(roster))
    show(summary)
    print(f"   every batch under the {BOUNDARY.amount_threshold:,.0f} threshold;")
    print(f"   the sum, {summary['total']:,.0f}, crossed the month's cash line")
    print(f"   of {CASH_LINE:,.0f} -- and no rule ever looked at it. The gate")
    print("   judges artifacts one at a time; nothing judges the portfolio.")
    print("   (Generic form: G1 in collaboration/stress_collab_gaps.py --")
    print("   sixty batches at 99,000 each, all auto-approved.)")
