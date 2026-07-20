"""Lecture 37 payroll lab: route, attest, and bind a high-risk approval."""
from __future__ import annotations

import sys

from governance_payroll_imports import load_local


bench = load_local("bench")
governance_lab = load_local("governance_lab")
run_approval_gate = governance_lab.run_approval_gate
run_approval_policy_change = governance_lab.run_approval_policy_change


def main() -> None:
    if "--policy-change" in sys.argv:
        result = run_approval_policy_change()
        print("== the approval gate changes only through its own gate ==")
        print(f"   route={result['route']}")
        print(f"   required_roles={list(result['required_roles'])}")
        print(
            "   decisions="
            f"{result['first_decision']} -> {result['final_decision']}"
        )
        print(
            f"   installed=v{result['installed_policy_version']} "
            f"policy={result['installed_policy_digest']}"
        )
        return

    result = run_approval_gate(changed_after_approval="--changed" in sys.argv)
    print("== approval route ==")
    print(f"   route={result['route']['name']}")
    print(f"   reasons={list(result['route']['reason_codes'])}")
    print(f"   decision={result['timeline'][0]['decision']}")
    print(f"   ticket_expires={result['ticket']['expires_at']}")

    print("\n== two-person review ==")
    print(
        "   approvers="
        + ", ".join(
            f"{item['approver_id']}:{item['role']}"
            for item in result["attestations"]
        )
    )
    print(f"   decision={result['final_receipt']['decision']}")
    print(f"   proposal_digest={result['proposal']['digest']}")

    if "changed" in result:
        print("\n== E0007 and E0012 restored after approval ==")
        print(
            "   restored="
            + ", ".join(result["changed"]["restored_ids"])
            + f" delta={result['changed']['delta_amount']:,.2f}"
        )
        print(
            "   artifact_digest="
            f"{result['changed']['original_artifact_digest']} -> "
            f"{result['changed']['changed_artifact_digest']}"
        )
        print(f"   changed_digest={result['changed']['changed_digest']}")
        print(
            f"   changed_scope={result['changed']['changed_subject_count']} subjects, "
            f"{result['changed']['changed_amount']:,.2f}"
        )
        print(
            "   old_approval_authorizes="
            f"{result['changed']['old_approval_authorizes']}"
        )
        print(f"   adapter={result['changed']['adapter_result']}")


if __name__ == "__main__":
    main()
