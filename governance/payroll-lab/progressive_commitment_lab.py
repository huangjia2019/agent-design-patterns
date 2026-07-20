"""Lecture 39 payroll lab: evidence-backed authority promotion and demotion."""
from __future__ import annotations

import sys

from governance_payroll_imports import load_local


governance_lab = load_local("governance_lab")
run_progressive_commitment = governance_lab.run_progressive_commitment


def main() -> None:
    result = run_progressive_commitment(
        incident=any(flag in sys.argv for flag in ("--incident", "--variant"))
    )
    print("== authority chain ==")
    for window in result["evidence_windows"]:
        print(
            f"   {window['from_level']}->{window['to_level']}: "
            f"runs={window['runs']} "
            f"slices={len(window['evaluation_slices'])} "
            f"success={window['success_rate']:.0%} "
            f"digest={window['evidence_digest']}"
        )
    shadow = result["shadow"]
    limited = result["limited"]
    print("\n== authority boundary ==")
    print(
        "   SHADOW: "
        f"simulation={shadow['simulation_decision']} "
        f"live={shadow['live_decision']}"
    )
    print(
        "   LIMITED canary: "
        f"amount={limited['canary_amount']:,.0f} "
        f"subjects={limited['canary_subjects']} "
        f"decision={limited['canary_decision']}"
    )
    print(
        "   LIMITED full payroll: "
        f"amount={limited['full_amount']:,.0f} "
        f"subjects={limited['full_subjects']} "
        f"decision={limited['full_decision']}"
    )
    print(f"   payment_effects={result['state']['payment_count']}")

    if result["incident"]:
        incident = result["incident"]
        print("\n== critical incident ==")
        print(
            f"   {incident['before']['level']} v{incident['before']['version']} "
            f"-> {incident['after']['level']} v{incident['after']['version']}"
        )
        print(f"   reason={incident['reason_code']}")
        print(
            f"   old_credential={incident['old_credential_decision']} "
            f"fresh_evidence_runs={incident['fresh_evidence_runs']}"
        )


if __name__ == "__main__":
    main()
