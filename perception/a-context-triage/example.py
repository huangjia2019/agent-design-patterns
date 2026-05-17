"""Runnable demo for the Context Triage pattern.

Scenario: a multi-tenant SaaS customer-service agent for tenant "acme-corp".
Twelve candidate items compete for the prompt window; only those whose
combined token estimate fits inside the budget make it in. One critical
error stack trace must be preserved even when the budget is tight.

Run:
    python perception/a-context-triage/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import ContextItem, ContextTriage, Priority   # noqa: E402


def _detect_error_keywords(item: ContextItem) -> bool:
    return any(token in item.content for token in ("Exception", "Traceback", "Error"))


def build_demo_items() -> list[ContextItem]:
    long_manual = "Product manual chapter " * 800   # ~6,400 tokens
    return [
        ContextItem(
            name="system_prompt",
            content="You are a customer-service agent. Never reveal data from other tenants.",
            priority=Priority.CRITICAL,
        ),
        ContextItem(
            name="tenant_identity",
            content="tenant_id=acme-corp, user_id=u-991, plan=enterprise",
            priority=Priority.CRITICAL,
        ),
        ContextItem(
            name="user_message",
            content="My API integration keeps returning 500. Please help.",
            priority=Priority.CRITICAL,
        ),
        ContextItem(
            name="recent_error_trace",
            content=(
                "Traceback (most recent call last):\n"
                '  File "app/api/handler.py", line 142, in dispatch\n'
                "    conn = pool.acquire(timeout=2.0)\n"
                "TimeoutError: pool exhausted after 30 retries"
            ),
            priority=Priority.IMPORTANT,
            is_error=True,
        ),
        ContextItem(
            name="current_ticket_context",
            content="Ticket #4421 - billing API 500 errors started 2026-05-12 14:00 UTC.",
            priority=Priority.IMPORTANT,
        ),
        ContextItem(
            name="product_config_snapshot",
            content="Plan=enterprise, modules=[Billing, Webhooks, Audit-log], region=us-east-1",
            priority=Priority.IMPORTANT,
        ),
        ContextItem(
            name="last_5_turns",
            content="User: tried restart. Agent: please share request id. User: req_abc123 ...",
            priority=Priority.IMPORTANT,
        ),
        ContextItem(
            name="manual_table_of_contents",
            content="1. Onboarding 2. Billing 3. Webhooks 4. Audit log 5. Troubleshooting",
            priority=Priority.SUPPORTING,
        ),
        ContextItem(
            name="similar_recent_tickets",
            content="3 similar tickets in last 30 days, all root-caused to webhook timeouts.",
            priority=Priority.SUPPORTING,
        ),
        ContextItem(
            name="full_product_manual",
            content=long_manual,
            priority=Priority.SUPPORTING,
        ),
        ContextItem(
            name="historical_ticket_archive",
            content="Handle: ticket://acme-corp/*",
            priority=Priority.DEFERRABLE,
        ),
        ContextItem(
            name="full_runbook_library",
            content="Handle: runbook://*",
            priority=Priority.DEFERRABLE,
        ),
    ]


def main() -> None:
    triage = ContextTriage(budget=8_000, error_detector=_detect_error_keywords)
    items = build_demo_items()

    selected, deferred, decision = triage.triage(items)

    print(f"Budget        : {decision.budget:,} tokens")
    print(f"Tokens used   : {decision.tokens_used:,}")
    print(f"Selected ({len(selected)}):")
    for item in selected:
        marker = " [ERROR-PROTECTED]" if item.is_error else ""
        print(f"  - P{4 - item.priority.value} {item.name} ({item.token_estimate} tok){marker}")
    print(f"Deferred ({len(deferred)}): {[i.name for i in deferred]}")
    print(f"Dropped  ({len(decision.dropped)}): {decision.dropped}")
    print()
    print("Invariant check:")
    error_items = [i for i in items if i.is_error]
    error_passed = all(i in selected for i in error_items)
    print(f"  All error items kept? {error_passed}")
    print(f"  All P3 items deferred (not loaded)? {len(deferred) == 2}")


if __name__ == "__main__":
    main()
