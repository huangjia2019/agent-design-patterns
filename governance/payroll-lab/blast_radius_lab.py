"""Lecture 38 payroll lab: reserve a nested effect budget before payment."""
from __future__ import annotations

import sys

from governance_payroll_imports import load_local


governance_lab = load_local("governance_lab")
run_blast_radius = governance_lab.run_blast_radius
run_blast_radius_retry_storm = governance_lab.run_blast_radius_retry_storm


def main() -> None:
    if "--retry-storm" in sys.argv:
        result = run_blast_radius_retry_storm()
        print("== unbounded retry storm ==")
        print(
            f"   approved={result['unbounded']['approved_amount']:,.0f} "
            f"money_out={result['unbounded']['money_out']:,.0f} "
            f"overpay={result['unbounded']['overpay']:,.0f}"
        )
        print(
            f"   payments={result['unbounded']['payment_count']} "
            f"retry={result['retry']['department']} "
            f"x{result['retry']['extra_runs']}"
        )
        print("\n== one-use effect permits ==")
        print(
            f"   money_out={result['bounded']['money_out']:,.0f} "
            f"payments={result['bounded']['payment_count']} "
            f"refused_draws={result['bounded']['refused_draws']}"
        )
        first = result["bounded"]["first_refusal"]
        print(
            f"   first_refusal={first['employee_id']} "
            f"run={first['run_number']} reason={first['reason']}"
        )
        root = result["snapshot"][result["policy"]["root_scope"]]
        print(
            f"   root_committed={root['committed_amount']:,.0f} "
            f"unknown={root['unknown_amount']:,.0f}"
        )
        return
    result = run_blast_radius(include_third="--overflow" in sys.argv)
    policy = result["policy"]
    print("== containment hierarchy ==")
    print(
        f"   root={policy['root_scope']} "
        f"amount_limit={policy['root_amount_limit']:,.0f}"
    )
    print(
        "   leaf=department::* "
        f"amount_limit={policy['leaf_amount_limit']:,.0f} "
        f"subject_limit={policy['leaf_subject_limit']}"
    )
    print("\n== sibling reservations ==")
    for batch in result["batches"]:
        line = (
            f"   {batch['department']}: "
            f"amount={batch['amount']:,.0f} "
            f"subjects={batch['subject_count']} "
            f"leaf_legal={batch['leaf_legal']} "
            f"decision={batch['decision']}"
        )
        print(line)
        if batch["blocked_at"]:
            print(f"      blocked_at={batch['blocked_at']}")
        else:
            print(f"      root_reserved={batch['root_after']:,.0f}")
    print(f"   payment_effects={result['state']['payment_count']}")


if __name__ == "__main__":
    main()
