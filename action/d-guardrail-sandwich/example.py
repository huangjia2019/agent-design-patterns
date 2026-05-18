"""Runnable demo for the Guardrail Sandwich pattern.

Replays the ¥3.2M mis-transfer incident from the lecture opening.
The corporate-banking agent receives an email request to transfer
funds. Its parse of the recipient account is off by two digits.
Without sandwich, the wrong account gets ¥3.2M and the error is
caught twelve hours later by reconciliation. With sandwich:

    [PRE]
      - account format check (IBAN/length)
      - blocklist check (OFAC sanctions)
      - amount threshold (>¥1M needs approval)
      - account whitelist (corporate counterparty list)
    [TOOL]
      transfer_funds(account, amount)
    [POST]
      - output schema verifies the receipt
      - PII redaction scan

This example shows three runs through the sandwich:

  1. Routine transfer (¥4,200) — passes all hooks.
  2. Mis-typed account — caught at PRE by whitelist.
  3. ¥5M transfer — caught at PRE by amount_threshold.

Plus one shadow-mode example showing soft enforcement (the lecture's
recommended rollout phase 2): block-level violation is logged but
not enforced.

Run:
    python action/d-guardrail-sandwich/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    GuardrailSandwich,
    HookPhase,
    HookResult,
    HookSpec,
    amount_threshold_hook,
    blocklist_hook,
    output_schema_hook,
)


# --- Tool handler ---------------------------------------------------------

def transfer_funds(account: str, amount: float, memo: str = "") -> dict:
    """Pretend to call the bank API. Returns a receipt."""
    return {
        "status": "executed",
        "account": account,
        "amount": amount,
        "memo": memo,
        "txn_id": f"TXN-{hash(account + str(amount)) & 0xFFFF:04X}",
    }


# --- Custom whitelist hook for this scenario -------------------------------

WHITELIST = {"DE-CORP-7710-2231", "DE-CORP-7710-1140", "DE-CORP-7710-9988"}


def account_whitelist_hook() -> HookSpec:
    def fn(tool_name, args, _output):
        account = args.get("account", "")
        if account in WHITELIST:
            return HookResult.PASS, f"account {account} on whitelist"
        return HookResult.BLOCK, f"account {account!r} not on corporate whitelist"
    return HookSpec(
        name="account_whitelist",
        phase=HookPhase.PRE,
        fn=fn,
        priority=50,    # runs early
    )


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _print_trace(trace) -> None:
    print(f"  tool         : {trace.tool_name}({trace.args})")
    print(f"  status       : {trace.final_status}")
    if trace.pre_outcomes:
        print(f"  pre-hooks    :")
        for o in trace.pre_outcomes:
            marker = {"pass": "✓", "block": "✗", "warn": "!"}[o.result.value]
            print(f"    {marker} {o.hook_name:20s} → {o.reason}")
    if trace.tool_output is not None:
        print(f"  tool output  : {trace.tool_output}")
    if trace.tool_error:
        print(f"  tool error   : {trace.tool_error}")
    if trace.post_outcomes:
        print(f"  post-hooks   :")
        for o in trace.post_outcomes:
            marker = {"pass": "✓", "block": "✗", "warn": "!"}[o.result.value]
            print(f"    {marker} {o.hook_name:20s} → {o.reason}")
    if trace.rollback_marked:
        print(f"  ⚠ ROLLBACK MARKED")


def main() -> None:
    sandwich = GuardrailSandwich()
    sandwich.register_tool("transfer_funds", transfer_funds)

    # --- Build the sandwich ---
    sandwich.add_hook(account_whitelist_hook())
    sandwich.add_hook(blocklist_hook(
        field="account",
        blocklist={"OFAC-SDN-1", "OFAC-SDN-2"},
        priority=10,    # runs before whitelist
    ))
    sandwich.add_hook(amount_threshold_hook(
        field="amount", max_amount=1_000_000, priority=100,
    ))
    sandwich.add_hook(output_schema_hook(
        required_keys=["status", "account", "amount", "txn_id"],
    ))

    # ------------------------------------------------------------------
    # Run 1: routine transfer — passes all hooks.
    # ------------------------------------------------------------------
    _print_section("Run 1 · routine: ¥4,200 to a whitelisted account")
    trace = sandwich.run("transfer_funds", {
        "account": "DE-CORP-7710-2231",
        "amount": 4200.0,
        "memo": "Q3 vendor invoice #4517",
    })
    _print_trace(trace)

    # ------------------------------------------------------------------
    # Run 2: mis-typed account — caught by whitelist before any money moves.
    # ------------------------------------------------------------------
    _print_section("Run 2 · mis-typed account: caught at PRE by whitelist")
    trace = sandwich.run("transfer_funds", {
        "account": "DE-CORP-7710-2213",     # last four digits transposed
        "amount": 3_200_000.0,
        "memo": "supplier final payment",
    })
    _print_trace(trace)

    # ------------------------------------------------------------------
    # Run 3: ¥5M — caught by amount threshold (would route to approval).
    # ------------------------------------------------------------------
    _print_section("Run 3 · large amount: caught at PRE by threshold")
    trace = sandwich.run("transfer_funds", {
        "account": "DE-CORP-7710-1140",
        "amount": 5_000_000.0,
        "memo": "quarterly settlement",
    })
    _print_trace(trace)

    # ------------------------------------------------------------------
    # Run 4: shadow-mode demo — add a hook in non-blocking mode.
    # In real rollouts, you start every new hook in shadow mode for
    # 1-2 weeks, watch the false-positive rate, then promote to enforce.
    # ------------------------------------------------------------------
    _print_section("Run 4 · shadow-mode hook: BLOCK becomes [shadow] WARN")
    shadow = GuardrailSandwich()
    shadow.register_tool("transfer_funds", transfer_funds)
    shadow.add_hook(amount_threshold_hook(
        field="amount", max_amount=1_000, priority=100, blocks=False,
        name="amount_threshold_shadow",
    ))
    trace = shadow.run("transfer_funds", {
        "account": "DE-CORP-7710-2231", "amount": 4200.0,
    })
    _print_trace(trace)
    print()
    print("  → tool executed even though threshold tripped, because")
    print("    `blocks=False`. The dashboard sees the [shadow] WARN")
    print("    so the operator can calibrate before promoting.")


if __name__ == "__main__":
    main()
