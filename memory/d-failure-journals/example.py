"""Runnable demo for the Failure Journals pattern.

The scenario reproduces the lecture-opening incident. An engineer asks
two different Claude Code sessions, two weeks apart, on two unrelated
microservices, to fix an authentication bug. Both sessions fix the
main task correctly. Both sessions then commit a *test environment*
OAuth client_id into the *production* config file as a side effect.

Without Failure Journals the second session has no way to know that
"this exact mistake just happened on a sibling project." With Failure
Journals, the second session calls `recall_for_task` before touching
configuration, sees the prior boundary_leak entry, and the agent's
prompt is enriched with the lesson before any action is taken.

Run:
    python memory/d-failure-journals/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import FailureCategory, FailureEntry, FailureJournal   # noqa: E402


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    journal = FailureJournal(retention_days=90, max_entries=200)

    # ------------------------------------------------------------------
    # Session 1 — two weeks ago, auth-service: agent fixes the OAuth
    # callback bug but writes the test client_id into prod config.
    # The incident is caught at deploy time. Engineer records it.
    # ------------------------------------------------------------------
    _print_section("Session 1 (two weeks ago, auth-service)")
    sig1 = (
        "fix oauth callback bug in auth-service: 302 redirect loop on "
        "stale state token; touch config/oauth.yaml"
    )
    try:
        raise RuntimeError(
            "Test client_id 'test-acme-3489' written to config/prod/oauth.yaml; "
            "caught by pre-deploy diff review"
        )
    except RuntimeError as exc:
        entry1 = FailureEntry.from_exception(
            exc,
            category=FailureCategory.BOUNDARY_LEAK,
            task_signature=sig1,
            lessons=[
                "Always re-read the env header at the top of any config file before editing",
                "Test client_ids must never land in prod/*.yaml — keep them in test/*.yaml only",
                "After a focused bug fix, do a separate diff review on any unrelated config edits",
            ],
            tags=["auth", "oauth", "prod-config", "boundary"],
        )
        journal.record(entry1)

    print(f"recorded failure_id={entry1.failure_id}")
    print(f"category={entry1.category.value}")
    print(f"summary={entry1.summary}")

    # A few unrelated routine failures in the same period, to give the
    # journal realistic noise.
    _print_section("Routine noise during the two-week gap")
    for sig, exc, cat in [
        ("ticket-service: rate limited by jira /issue endpoint",
         TimeoutError("HTTP 429 from atlassian.net after 30s wait"),
         FailureCategory.API_TRANSIENT),
        ("ticket-service: tenant ACME query returned BETA documents",
         ValueError("retrieval returned 4 docs for tenant=BETA, expected ACME"),
         FailureCategory.RETRIEVAL_MISS),
        ("dashboard-service: dashboard render exceeded 32k context",
         OverflowError("context window 32768 exceeded by 1840 tokens"),
         FailureCategory.CONTEXT_OVERFLOW),
        ("billing-service: stripe webhook retry storm",
         RuntimeError("stripe webhook delivered 7x within 4s; idempotency key missing"),
         FailureCategory.TOOL_ERROR),
    ]:
        e = FailureEntry.from_exception(exc, category=cat, task_signature=sig)
        journal.record(e)
        print(f"  + {cat.value:18s}  {sig[:48]}")

    print(f"\n  journal size: {len(journal.entries)} entries")

    # ------------------------------------------------------------------
    # Session 2 — today, a different microservice. The agent is told
    # to fix a SimilarSounding-but-Unrelated auth bug. *Before* touching
    # config, it recalls relevant past failures.
    # ------------------------------------------------------------------
    _print_section("Session 2 (today, billing-service)")
    sig2 = (
        "fix oauth token refresh bug in billing-service: refresh fails "
        "silently when scope changes; touch config/oauth.yaml"
    )
    print(f"new task signature: {sig2}")
    print()

    recalled = journal.recall_for_task(
        task_signature=sig2,
        top_k=3,
        threshold=0.25,            # demo threshold; production uses embeddings
    )
    print(f"recalled {len(recalled)} past failure(s):")
    for e in recalled:
        print(f"  - [{e.category.value}] {e.summary[:80]}")
    print()

    prompt_block = journal.render_for_prompt(recalled)
    print("-- prompt block to inject before agent acts on the task --")
    print(prompt_block)

    # ------------------------------------------------------------------
    # Demonstrating the high-risk override: even a task signature with
    # zero word overlap should still trigger boundary_leak recall.
    # ------------------------------------------------------------------
    _print_section("Unrelated task — high-risk override still surfaces boundary_leak")
    unrelated = "generate quarterly revenue chart for sales dashboard"
    recalled2 = journal.recall_for_task(
        task_signature=unrelated,
        top_k=2,
        threshold=0.9,             # impossibly high — nothing matches by similarity
    )
    print(f"recalled {len(recalled2)} entries by high-risk override:")
    for e in recalled2:
        print(f"  - [{e.category.value}] {e.summary[:80]}")

    # ------------------------------------------------------------------
    # Health report — what the team would see on a daily dashboard.
    # ------------------------------------------------------------------
    _print_section("Health report (what gets dashboarded)")
    report = journal.health_report()
    print(f"total entries     : {report['total_entries']}")
    print(f"recall hit rate   : {report['recall_rate']}")
    print(f"high-risk entries : {report['high_risk_entries']}")
    print("by category:")
    for cat, n in sorted(report["by_category"].items(), key=lambda kv: -kv[1]):
        if n:
            print(f"  {cat:18s} {n}")


if __name__ == "__main__":
    main()
