"""Run the integrated Payroll Governance Lab."""
from __future__ import annotations

import argparse
import json

from governance_payroll_imports import load_local


governance_lab = load_local("governance_lab")
policy_lab = load_local("ungoverned_policy_lab")
run_changed_after_approval = governance_lab.run_changed_after_approval
run_governed = governance_lab.run_governed
run_naive = governance_lab.run_naive
run_policy_drift = policy_lab.run_policy_drift


RUNNERS = {
    "naive": run_naive,
    "governed": run_governed,
    "changed": run_changed_after_approval,
    "policy-drift": run_policy_drift,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Payroll Governance Lab.")
    parser.add_argument(
        "--mode",
        choices=tuple(RUNNERS),
        default="governed",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = RUNNERS[args.mode]()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.mode == "policy-drift":
        print("== same portfolio, changed policy ==")
        print(
            f"   inventory: {result['inventory']['verified']}/"
            f"{result['inventory']['count']} policy literals found"
        )
        print(
            f"   v{result['before']['policy_version']} "
            f"limit={result['before']['limit']:,.0f} -> "
            f"{result['before']['decision']} "
            f"policy={result['before']['policy_digest']}"
        )
        print(
            f"   v{result['after']['policy_version']} "
            f"limit={result['after']['limit']:,.0f} -> "
            f"{result['after']['decision']} "
            f"policy={result['after']['policy_digest']}"
        )
        print(
            "   raw acceptance policy marks: "
            f"{list(result['after']['raw_policy_marks'])}"
        )
    elif args.mode == "naive":
        print("== accepted artifact, unsafe bridge ==")
        print(f"   artifact acceptance: {result['artifact_acceptance']}")
        print(f"   governance receipts: {result['governance_receipts']}")
        print(
            f"   payment: {result['payment']['subject_count']} subjects, "
            f"{result['payment']['amount']:,.2f}"
        )
        print(f"   diagnosis: {result['diagnosis']}")
    elif args.mode == "changed":
        print("== approval cannot move to a changed proposal ==")
        print(f"   original: {result['original_digest']}")
        print(f"   changed:  {result['changed_digest']}")
        print(
            f"   restored: {list(result['restored_ids'])}, "
            f"delta={result['delta_amount']:,.2f}"
        )
        print(f"   old approval authorizes: {result['old_approval_authorizes']}")
        print(f"   adapter: {result['adapter_result']}")
    else:
        print("== accepted artifact, governed effect ==")
        print(
            f"   proposal: {result['proposal']['subject_count']} subjects, "
            f"{result['proposal']['amount']:,.2f}"
        )
        print(
            f"   approval: {result['approval']['route']} -> "
            f"{result['approval']['final']} {list(result['approval']['roles'])}"
        )
        print(
            f"   containment: {result['containment']['reservation']} "
            f"lease={result['containment']['lease_id']}"
        )
        print(
            f"   authority: {result['authority']['level']} "
            f"v{result['authority']['version']} -> "
            f"{result['authority']['decision']}"
        )
        print(
            f"   payment: {result['payment']['subject_count']} subjects, "
            f"{result['payment']['amount']:,.2f}"
        )
        print(
            f"   trace: {result['audit']['event_count']} events, "
            f"complete={result['audit']['complete']}, "
            f"hash_chain={result['audit']['chain_valid']}"
        )


if __name__ == "__main__":
    main()
