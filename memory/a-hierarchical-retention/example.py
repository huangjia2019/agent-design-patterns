"""Runnable demo for the Hierarchical Retention pattern.

Scenario: a programming coach agent for an online Python school. Alice
is returning for her fourth 1-on-1 session. The agent needs to remember:

  USER layer    — Alice's profile (Python intermediate, prefers OOP)
  PROJECT layer — the Flask app she's been building for two weeks
  SESSION layer — last topic was decorators
  TURN layer    — just-defined helper function, expires when round ends

The demo shows three properties of the pattern:

  1. Layered context loads coarse → fine at session start
  2. Inner layers override outer layers on key conflict
  3. TURN layer auto-expires after its TTL

Run:
    python memory/a-hierarchical-retention/example.py
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import HierarchicalRetention, Layer   # noqa: E402


def main() -> None:
    # Alice's 4th session — restore prior state into the memory hierarchy
    mem = HierarchicalRetention(
        user_id="alice-991",
        project_id="flask-todo-app",
        session_id="sess-2026-05-18-evening",
    )

    # USER layer (persisted across sessions) — loaded from postgres
    mem.write(Layer.USER, "level", "intermediate Python, no JS")
    mem.write(Layer.USER, "preference", "prefers OOP examples over functional")
    mem.write(Layer.USER, "joined_weeks_ago", 6)

    # PROJECT layer (persisted with project) — loaded from file backend
    mem.write(Layer.PROJECT, "tech_stack", "Flask + SQLAlchemy + Postgres")
    mem.write(Layer.PROJECT, "scope", "personal todo app with multi-user auth")
    mem.write(Layer.PROJECT, "current_module", "user authentication")

    # SESSION layer (persisted in redis with 24h TTL) — loaded from prior session
    mem.write(Layer.SESSION, "last_topic", "decorators (functools.wraps)")
    mem.write(Layer.SESSION, "open_question", "why does my @login_required eat my route's docstring")

    # TURN layer (in-process memory, 5-min TTL) — populated during this turn
    mem.write(Layer.TURN, "just_defined", "helper function `decorator_with_args(...)`")

    print("=== Session opens — assembled prompt context (coarse → fine) ===")
    print(mem.assemble_prompt_context())
    print()

    # Demonstrate override semantics: agent had a session-level note that
    # for THIS session Alice wants a functional example as a contrast.
    # SESSION overrides USER for `preference`.
    mem.write(Layer.SESSION, "preference", "for this lesson only: contrast OOP vs functional decorator")
    val, where = mem.read("preference")
    print(f"=== Override semantics ===")
    print(f"  preference  →  '{val}'  (from {where.value if where else 'nowhere'})")
    print(f"  (USER had: '{mem.layers[Layer.USER].content['preference']}')")
    print()

    # Demonstrate TTL expiry on TURN layer using a tiny TTL for demo
    mem_short = HierarchicalRetention(
        user_id="alice-991",
        project_id="flask-todo-app",
        session_id="sess-tiny-ttl",
        layer_config={
            Layer.USER:    {"backend": "postgres", "ttl_seconds": None,   "token_budget": 2000},
            Layer.PROJECT: {"backend": "file",     "ttl_seconds": None,   "token_budget": 4000},
            Layer.SESSION: {"backend": "redis",    "ttl_seconds": 86400,  "token_budget": 8000},
            Layer.TURN:    {"backend": "memory",   "ttl_seconds": 1,      "token_budget": 2000},
        },
    )
    mem_short.write(Layer.TURN, "scratch", "just_defined_fn")
    print(f"=== TURN expiry (TTL=1s) ===")
    print(f"  before sleep: read('scratch') = {mem_short.read('scratch')}")
    time.sleep(1.1)
    print(f"  after  sleep: read('scratch') = {mem_short.read('scratch')}")
    print(f"  evict_expired() = {mem_short.evict_expired()}")
    print()

    print("=== Health report ===")
    report = mem.health_report()
    print(f"  user={report['user_id']}  project={report['project_id']}  session={report['session_id']}")
    for name, info in report["layers"].items():
        print(
            f"  {name:8s}  items={info['items']}  "
            f"backend={info['backend']:9s}  "
            f"ttl_seconds={info['ttl_seconds']}  "
            f"expired={info['expired']}"
        )


if __name__ == "__main__":
    main()
