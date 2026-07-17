"""Lecture 33 hands-on: three ledgers answer one question; the disagreement
points at the root cause.

Runs the pattern from ../b-fan-out-gather/pattern.py on the month-end
payroll bench (798 PAID, 2 REVERSED, both in Finance). Three source
agents answer the SAME question -- June's total pay per department --
each bound to one attributable data source:

    hr_payroll       what June obliged us to pay (all employees)
    bank_ledger      what actually left the bank (PAID payslips only)
    batch_artifacts  what lecture 32's batch workers reported

    scene 1  the three-layer sort: four departments agree; Finance
             splits two ways with a gap of exactly 38,444 -- the two
             REVERSED payslips (E0007 30,000 + E0012 8,444). The
             divergence does not get averaged away: it is reported as
             a located root cause, gross view vs net view, and the
             seam reviewer routes it for sign-off. A line item only
             one source knows goes to a human as single-source.
    scene 2  the compliance floor: the bank source dies. 2 of 3
             sources is below the floor, so the gather returns
             "insufficient_sources" instead of a verdict built on
             survivors.
    scene 3  run with --additive: the same three COMPETING answers fed
             through the ADDITIVE strategy. Sums of disagreements make
             a bigger number; the conflict disappears from the report.
             This is G2 in collaboration/stress_collab_gaps.py.

Everything is deterministic and reads the bench directly; no API key.
The Contractors line (184,000) is a teaching mock that exists only in
the HR view. Tolerance and the sign-off threshold are teaching values.

Run `python3 fan_out_gather_lab.py` (add --additive for scene 3).
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_fan = _load(HERE.parent / "b-fan-out-gather" / "pattern.py", "fanout_pattern")
AggregatorPolicy = _fan.AggregatorPolicy
FanOutGather = _fan.FanOutGather
Reconciler = _fan.Reconciler
SourceResult = _fan.SourceResult
Strategy = _fan.Strategy

sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402

SIGN_OFF_THRESHOLD = 10_000.0        # teaching value: root causes above it need sign-off
CONTRACTOR_POOL = 184_000.0          # teaching mock: exists only in the HR view


def month_end():
    return bench.month_end_state()


# ---- three sources, each bound to ONE attributable data boundary --------------

def gross_by_dept(con) -> dict[str, float]:
    """The obligation view: what June says we owe, everyone included."""
    return {d: float(s) for d, s in con.execute(
        "SELECT dept, SUM(base_salary) FROM employees GROUP BY dept")}


def net_by_dept(con) -> dict[str, float]:
    """The money-out view: only payslips that stayed PAID."""
    return {d: float(s) for d, s in con.execute(
        "SELECT e.dept, SUM(e.base_salary) FROM payroll p "
        "JOIN employees e ON e.emp_id = p.emp_id "
        "WHERE p.month = ? AND p.status = 'PAID' GROUP BY e.dept",
        (bench.MONTH,))}


def make_sources(con):
    async def hr_payroll(name, rows):
        items = gross_by_dept(con)
        items["Contractors"] = CONTRACTOR_POOL          # only HR tracks this pool
        return SourceResult(source=name, line_items=items)

    async def bank_ledger(name, rows):
        return SourceResult(source=name, line_items=net_by_dept(con))

    async def batch_artifacts(name, rows):
        # Lecture 32's workers computed full department batches; their
        # reported totals match the obligation view.
        return SourceResult(source=name, line_items=gross_by_dept(con))

    return {"hr_payroll": hr_payroll, "bank_ledger": bank_ledger,
            "batch_artifacts": batch_artifacts}


# ---- the gather, configured by the four questions ------------------------------

def sign_off_reviewer(report: dict) -> list[str]:
    """Q4: reads the assembled report, never a slice. Flags located root
    causes big enough to need a controller's signature."""
    flags = []
    for rc in report.get("root_causes", []):
        if abs(rc["gap"]) > SIGN_OFF_THRESHOLD:
            flags.append(f"root cause on '{rc['item']}' (gap {rc['gap']:,.0f}) "
                         f"exceeds sign-off threshold; route to controller")
    return flags


def competing_gather(con, sources=None) -> FanOutGather:
    policy = AggregatorPolicy(strategy=Strategy.COMPETING,
                              seam_reviewer=sign_off_reviewer)
    return FanOutGather(sources or make_sources(con),
                        Reconciler(policy), min_success_rate=0.95)


def additive_gather(con) -> FanOutGather:
    return FanOutGather(make_sources(con),
                        Reconciler(AggregatorPolicy(strategy=Strategy.ADDITIVE)),
                        min_success_rate=0.95)


TASK = [{"question": f"total pay per department, {bench.MONTH}"}]


def run_competing(con) -> dict:
    return asyncio.run(competing_gather(con).run(TASK))


def run_with_dead_bank(con) -> dict:
    sources = make_sources(con)

    async def dead(name, rows):
        raise RuntimeError("bank API down")

    sources["bank_ledger"] = dead
    return asyncio.run(competing_gather(con, sources).run(TASK))


def run_additive(con) -> dict:
    return asyncio.run(additive_gather(con).run(TASK))


# ---- scenes --------------------------------------------------------------------

def main() -> None:
    con = month_end()

    if "--additive" not in sys.argv:
        print("== scene 1: three sources, one question, the three-layer sort ==")
        report = run_competing(con)
        print(f"   agreed ({len(report['agreed_items'])}): {report['agreed_items']}")
        for rc in report["root_causes"]:
            print(f"   located root cause: '{rc['item']}' gap={rc['gap']:,.0f}")
            print(f"      low  {rc['low_sources']} -> {min(rc['by_source'].values()):,.0f}")
            print(f"      high {rc['high_sources']} -> {max(rc['by_source'].values()):,.0f}")
        for h in report["to_human"]:
            print(f"   to human: '{h['item']}' ({h['reason']})")
        for f in report.get("seam_findings", []):
            print(f"   seam reviewer: {f}")
        print("   -> the 38,444 gap is not an error to average away: it is the")
        print("      two REVERSED payslips (E0007 30,000 + E0012 8,444), located")
        print("      by the split between the obligation view and the money view.")
        print("      Which number the report should carry is a policy question;")
        print("      the gather's job was to surface it with evidence, not to")
        print("      pick a side silently.")

        print("\n== scene 2: the bank source dies; the floor holds ==")
        report = run_with_dead_bank(con)
        print(f"   {report}")
        print("   -> 2 of 3 sources is below the floor. No verdict gets built")
        print("      on survivors; absence of a source is itself a finding.")

    else:
        print("== scene 3 (--additive): competing answers, additive merge ==")
        report = run_additive(con)
        finance_sum = report["merged"]["Finance"]
        print(f"   merged['Finance'] = {finance_sum:,.0f} "
              f"(gross 2,764,781 + gross 2,764,781 + net 2,726,337)")
        print(f"   total = {report['total']:,.0f}")
        print(f"   keys in the report: {sorted(report.keys())}")
        print("   -> three answers to the SAME question were summed as if they")
        print("      were three facets of a whole. The Finance conflict is gone;")
        print("      no root_causes, no to_human, no seam to review. The number")
        print("      is big, wrong, and quiet. (G2 in stress_collab_gaps.py.)")


if __name__ == "__main__":
    main()
