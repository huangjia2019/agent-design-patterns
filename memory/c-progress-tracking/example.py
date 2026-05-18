"""Runnable demo for the Progress Tracking pattern.

Scenario reproducing the lecture-opening incident: an agent is asked to
refactor a 600-line Python module into 4 files + tests, and the agent
goes on a 20-turn debug detour halfway through. With Progress Tracking,
the framework injects an escalating reminder when it sees a complex
task running with no active todos, and surfaces the forgotten 4th file
back into the conversation.

Run:
    python memory/c-progress-tracking/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import ProgressTracker, TodoStatus   # noqa: E402


def main() -> None:
    tracker = ProgressTracker()
    owner = "agent-claude-code-session-2026-05-18"

    print("=== Phase 1: agent receives the task and writes its plan ===")
    todos = tracker.get_list(owner)
    todos.add("Refactor 600-line module into 4 separate files",
              "Refactoring 600-line module into 4 separate files",
              tags=["plan"])
    todos.add("Migrate file 1 (utils.py) with backward-compat re-exports",
              "Migrating file 1 (utils.py) with backward-compat re-exports",
              tags=["migration"])
    todos.add("Migrate file 2 (parsers.py) with backward-compat re-exports",
              "Migrating file 2 (parsers.py) with backward-compat re-exports",
              tags=["migration"])
    todos.add("Migrate file 3 (renderers.py) with backward-compat re-exports",
              "Migrating file 3 (renderers.py) with backward-compat re-exports",
              tags=["migration"])
    todos.add("Migrate file 4 (validators.py) with backward-compat re-exports",
              "Migrating file 4 (validators.py) with backward-compat re-exports",
              tags=["migration"])
    todos.add("Write unit tests for the new 4-file structure",
              "Writing unit tests for the new 4-file structure",
              tags=["tests"])
    todos.add("Run existing CI and confirm green",
              "Running existing CI and confirming green",
              tags=["ci"])
    print(todos.render())
    print()

    # Look up todo_ids
    by_content: dict[str, str] = {it.content: it.todo_id for it in todos.items}

    print("=== Phase 2: agent works through items 1-3 ===")
    for content in [
        "Migrate file 1 (utils.py) with backward-compat re-exports",
        "Migrate file 2 (parsers.py) with backward-compat re-exports",
        "Migrate file 3 (renderers.py) with backward-compat re-exports",
    ]:
        todos.start(by_content[content])
        in_p = todos.in_progress_item()
        print(f"  in progress: {in_p.active_form}")
        todos.complete(by_content[content])
    print()

    print("=== Phase 3: agent goes on a debug detour for 25 turns ===")
    # Simulate: nothing in_progress, recent_messages full of debugging chatter
    debug_messages = [
        "the test for parsers.py fails on edge case",
        "let me trace through the parsing logic",
        "the issue is the regex doesn't handle empty input",
        "let me fix that and re-run",
        "now another edge case",
        "implementing then testing the fix",
    ] * 4   # 24 messages

    # The framework detects context loss and nudges
    if tracker.context_loss_detected(owner, debug_messages):
        print("⚠ Framework detected context loss — injecting nudge.")
    print(f"  nudge 1: {tracker.nudge_message(owner)[:80]}...")
    print()

    print("=== Phase 4: agent re-reads todos and resumes ===")
    rendered = todos.render()
    print("Current state:")
    print(rendered)
    print()

    # The forgotten 4th file pops back to the agent's attention
    print("Agent picks up the next pending item:")
    todos.start(by_content["Migrate file 4 (validators.py) with backward-compat re-exports"])
    print(f"  in progress: {todos.in_progress_item().active_form}")
    todos.complete(by_content["Migrate file 4 (validators.py) with backward-compat re-exports"])

    todos.start(by_content["Write unit tests for the new 4-file structure"])
    todos.complete(by_content["Write unit tests for the new 4-file structure"])

    todos.start(by_content["Run existing CI and confirm green"])
    todos.complete(by_content["Run existing CI and confirm green"])

    # Mark the top-level plan completed
    todos.start(by_content["Refactor 600-line module into 4 separate files"])
    todos.complete(by_content["Refactor 600-line module into 4 separate files"])

    print()
    print("=== Phase 5: all done — list auto-evicts ===")
    print(f"  all_done()       : {todos.all_done()}")
    print(f"  pending_count()  : {todos.pending_count()}")
    evicted = tracker.evict_if_all_done(owner)
    print(f"  evicted          : {evicted}")
    print(f"  fresh list       : {tracker.get_list(owner).render()}")


if __name__ == "__main__":
    main()
