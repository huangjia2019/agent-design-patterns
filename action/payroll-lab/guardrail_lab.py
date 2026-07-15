"""Lecture 25 hands-on: the payroll transfer wrapped in a Guardrail Sandwich.

Reuses the pattern from ../d-guardrail-sandwich/pattern.py. The one action
this module has been building toward -- pressing the transfer button -- is
finally wrapped: pre-hooks that can block, the tool, post-hooks that audit
and mark for rollback. Six scenes:

    scene 1  a normal transfer passes both layers
    scene 2  the fat-fingered 999999 from lecture 21 is caught PRE
    scene 3  a transfer to a risk-frozen account is caught PRE
    scene 4  the bank "succeeds" but returns no receipt -- caught POST,
             marked for rollback
    scene 5  an export whose content carries bank account numbers is
             caught POST (single calls all legal, the combination is not)
    scene 6  a new, stricter amount hook runs in SHADOW mode: it would
             block, but only logs -- the monitor -> enforce rollout path

Run `python3 db.py`, then `python3 db.py --inject-typo`, then
`python3 guardrail_lab.py`.
"""
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "d-guardrail-sandwich"))
from pattern import (  # noqa: E402
    GuardrailSandwich, HookPhase, HookResult, HookSpec,
    amount_threshold_hook, blocklist_hook, output_schema_hook, pii_redaction_hook,
)

DB = HERE / "payroll.db"
MONTH = "2026-06"
con = sqlite3.connect(DB)
FROZEN_ACCOUNTS = {con.execute(
    "SELECT bank_account FROM employees WHERE emp_id='E0300'").fetchone()[0]}
TYPO_APPROVAL = con.execute(
    "SELECT id, amount, status FROM approvals "
    "WHERE emp_id='E0099' AND type='adjustment' ORDER BY id DESC LIMIT 1"
).fetchone()
if TYPO_APPROVAL is None or TYPO_APPROVAL[2] != "APPROVED":
    raise RuntimeError(
        "scene 2 needs the approved E0099 typo; run "
        "`python3 db.py --inject-typo` before guardrail_lab.py"
    )


# ---- tools: calls below use the sandwich; production must hide bare handlers -

def transfer_salary(emp_id, amount, misbehave=False):
    con.execute("UPDATE payroll SET status='PAID' WHERE month=? AND emp_id=?",
                (MONTH, emp_id))
    con.commit()
    if misbehave:                       # bank accepted but no receipt came back
        return {"emp_id": emp_id, "paid": True}
    return {"emp_id": emp_id, "paid": True, "receipt": f"RCPT-{emp_id}-{MONTH}"}


def export_report(recipient, content):
    return {"recipient": recipient, "bytes": len(content), "content": content}


sandwich = GuardrailSandwich()
sandwich.register_tool("transfer_salary", transfer_salary)
sandwich.register_tool("export_report", export_report)

# ---- the two slices of bread ------------------------------------------------

account_of = {row[0]: row[1] for row in
              con.execute("SELECT emp_id, bank_account FROM employees")}


def frozen_account_fn(tool_name, args, _output):
    acct = account_of.get(args.get("emp_id", ""), "")
    if acct in FROZEN_ACCOUNTS:
        return HookResult.BLOCK, f"account of {args['emp_id']} is risk-frozen"
    return HookResult.PASS, "account clear"


sandwich.add_hook(amount_threshold_hook(
    "amount", 100000, name="amount<=100k", priority=10,
    policy_owner="finance-risk", policy_version="payroll-2026-06"))
sandwich.add_hook(HookSpec(name="frozen_account", phase=HookPhase.PRE,
                           fn=frozen_account_fn, priority=20,
                           applies_to={"transfer_salary"},
                           policy_owner="risk-operations",
                           policy_version="frozen-list-2026-07-12"))
receipt_hook = output_schema_hook(
    ["emp_id", "paid", "receipt"], name="receipt_present", priority=10,
    policy_owner="treasury-operations", policy_version="receipt-v1")
receipt_hook.applies_to = {"transfer_salary"}   # reads/exports owe no receipt
sandwich.add_hook(receipt_hook)
sandwich.add_hook(pii_redaction_hook(
    [r"62\d{2}-?\d{4}-?\d{4}"], name="no_bank_accounts_leave", priority=20,
    policy_owner="data-security", policy_version="dlp-2026-07"))
# Shadow mode: a stricter threshold being trialled. It only logs.
sandwich.add_hook(amount_threshold_hook(
    "amount", 50000, name="amount<=50k(shadow)", priority=30, blocks=False,
    policy_owner="finance-risk", policy_version="payroll-2026-07-candidate"))


def show(title, trace):
    print(f"{title}\n    -> {trace.final_status.upper()}"
          + ("  [rollback marked]" if trace.rollback_marked else ""))
    for o in trace.pre_outcomes + trace.post_outcomes:
        if o.result != HookResult.PASS:
            print(f"       {o.phase.value}-hook {o.hook_name}: "
                  f"{o.result.value} ({o.reason}; "
                  f"policy={o.policy_owner}@{o.policy_version})")


print("== scene 1: a normal transfer ==")
show("transfer_salary(E0012, 9600)  # Xiaoxue's bonus, verified in lecture 19",
     sandwich.run("transfer_salary", {"emp_id": "E0012", "amount": 9600}))

print("\n== scene 2: the 999999 from lecture 21, four lectures later ==")
approval_id, approved_amount, approval_status = TYPO_APPROVAL
print(f"    approval evidence: id={approval_id}, emp=E0099, "
      f"amount={approved_amount}, status={approval_status}")
show(f"transfer_salary(E0099, {approved_amount})  # sourced from approval #{approval_id}",
     sandwich.run(
         "transfer_salary",
         {"emp_id": "E0099", "amount": approved_amount},
     ))
status = con.execute("SELECT status FROM payroll WHERE month=? AND emp_id='E0099'",
                     (MONTH,)).fetchone()[0]
print(f"    ledger check: E0099 payslip status is still {status!r} -- "
      f"the tool never ran")

print("\n== scene 3: transfer to a risk-frozen account ==")
show("transfer_salary(E0300, 8000)",
     sandwich.run("transfer_salary", {"emp_id": "E0300", "amount": 8000}))

print("\n== scene 4: bank says ok, receipt is missing ==")
show("transfer_salary(E0021, 8800, misbehave)  # post-check reads the output",
     sandwich.run("transfer_salary",
                  {"emp_id": "E0021", "amount": 8800, "misbehave": True}))

print("\n== scene 5: each call legal, the combination is exfiltration ==")
acct = account_of["E0007"]
show(f"export_report(vendor@outside.example, '...{acct}...')",
     sandwich.run("export_report",
                  {"recipient": "vendor@outside.example",
                   "content": f"June payroll notes, account {acct} pending"}))

print("\n== scene 6: the stricter hook rides along in shadow mode ==")
show("transfer_salary(E0025, 60000)  # over 50k, under 100k",
     sandwich.run("transfer_salary", {"emp_id": "E0025", "amount": 60000}))

paid = con.execute("SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
                   (MONTH,)).fetchone()[0]
print(f"\n[LEDGER] {paid} payslips PAID this run.")
print("         PRE-blocked transfers never moved; POST-blocked actions remain "
      "changed until compensation runs.")
print("         Every hook decision above is in the SandwichTrace, timestamped.")
