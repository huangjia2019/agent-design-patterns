"""Runnable demo for the Progressive Discovery pattern.

Scenario: a 200-file synthetic legacy e-commerce monolith. The bug we are
hunting for — order-confirmation emails occasionally mix in other
customers' orders — lives in a cache key that uses `order_id` but not
`customer_id`. The bug is across two files:

  * `mailers/order_confirmed.rb` — sends the confirmation
  * `cache/user_state.rb` — caches with a key missing the customer scope

A naive RAG semantic search misses it because the file with the actual
bug uses the variable name `merge_user_state` and never mentions "order"
or "email" in its comments. Progressive Discovery finds it in two cycles
because it follows the call chain from the mailer into the cache.

Run:
    python perception/c-progressive-discovery/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Candidate,
    ProgressiveDiscoverer,
    DiscoverySession,
)


# ───────────────────── synthetic codebase ─────────────────────

_FILES: dict[str, str] = {}


def _seed_codebase() -> dict[str, str]:
    """Build a 200-file synthetic monolith with two bug-relevant files."""
    files: dict[str, str] = {}
    # Bulk filler files: 100 random services, no bug-relevance
    for i in range(100):
        files[f"app/services/service_{i:03d}.rb"] = (
            f"class Service{i}\n  def call\n    'service {i} result'\n  end\nend\n"
        )
    # 50 controllers
    for i in range(50):
        files[f"app/controllers/controller_{i:02d}.rb"] = (
            f"class Controller{i} < ApplicationController\n  def index\n  end\nend\n"
        )
    # 30 random mailers
    for i in range(30):
        files[f"app/mailers/random_mailer_{i:02d}.rb"] = (
            f"class RandomMailer{i} < ApplicationMailer\nend\n"
        )

    # ─── The two bug-relevant files ───
    files["app/mailers/order_confirmed.rb"] = """
require 'cache/user_state'

class OrderConfirmedMailer < ApplicationMailer
  def send_confirm(order_id)
    user_state = Cache::UserState.fetch(order_id)
    # BUG: this uses the cached state, which may have leaked
    # from another customer's session.
    mail(to: user_state.email, subject: "Order #{order_id} confirmed")
  end
end
""".strip()

    files["app/cache/user_state.rb"] = """
module Cache
  class UserState
    # BUG: cache key uses only order_id, not customer_id.
    # If two customers' carts ever produce the same order_id
    # via the legacy import path, state merges across users.
    def self.fetch(order_id)
      key = "user_state:#{order_id}"   # ← missing customer_id
      Rails.cache.fetch(key) { merge_user_state(order_id) }
    end

    private

    def self.merge_user_state(order_id)
      # legacy import path that produced colliding order_ids
      ...
    end
  end
end
""".strip()

    # A red-herring file mentioning "order" + "email" in comments
    files["app/services/order_history_emailer.rb"] = """
# Sends monthly order history email. Unrelated to confirmation.
class OrderHistoryEmailer
  def call(customer_id)
    ...
  end
end
""".strip()

    # 17 more filler tests files
    for i in range(17):
        files[f"spec/services/service_{i:03d}_spec.rb"] = (
            f"describe Service{i} do\n  it 'works' do\n  end\nend\n"
        )
    return files


# ───────────────────── tool implementations ─────────────────────

def grep_tool(keyword: str) -> list[Candidate]:
    """Return file candidates where the keyword appears in path or content."""
    out: list[Candidate] = []
    kw = keyword.lower()
    for path, content in _FILES.items():
        if kw in path.lower():
            out.append(Candidate(
                path=path, snippet=path,
                reason=f"path matches '{keyword}'",
            ))
            continue
        for line in content.split("\n"):
            if kw in line.lower():
                out.append(Candidate(
                    path=path, snippet=line.strip()[:120],
                    reason=f"content matches '{keyword}'",
                ))
                break
    return out


def read_tool(path: str) -> str:
    """Resolve a logical import like 'cache/user_state' to the real file path.

    Real codebases route requires/imports through configured paths
    (Ruby autoload, Python sys.path, etc.). Production code uses the
    language server. Here we mimic Rails-style fallback: try the path
    as given, then under `app/`, then with `.rb` appended.
    """
    if path in _FILES:
        return _FILES[path]
    for prefix in ("app/", "lib/", ""):
        for suffix in (".rb", ".py", ""):
            candidate = f"{prefix}{path}{suffix}"
            if candidate in _FILES:
                return _FILES[candidate]
    return ""


def scorer(cand: Candidate, task: str) -> float:
    """Higher if path looks bug-relevant + matches task keywords."""
    score = 0.0
    if "mailer" in cand.path.lower():
        score += 1.5
    if "cache" in cand.path.lower():
        score += 1.3
    if "order_confirm" in cand.path.lower():
        score += 2.0
    if "spec/" in cand.path or "_spec.rb" in cand.path:
        score -= 1.0
    for word in task.lower().split():
        if word in cand.snippet.lower():
            score += 0.3
    return score


def signal_found(file_contents: dict[str, str], task: str) -> bool:
    """The bug is located when we've read both files needed to see the
    full picture: the mailer that calls the cache, and the cache layer
    whose key construction is the actual defect."""
    has_mailer = any("OrderConfirmedMailer" in v for v in file_contents.values())
    has_cache_layer = any("Rails.cache.fetch" in v for v in file_contents.values())
    return has_mailer and has_cache_layer


# ───────────────────── main ─────────────────────

def main() -> None:
    global _FILES
    _FILES = _seed_codebase()

    discoverer = ProgressiveDiscoverer(
        grep_tool=grep_tool,
        read_tool=read_tool,
        scorer=scorer,
        max_cycles=3,
        budget_per_cycle=30_000,
        signal_fn=signal_found,
        forage_top_k=30,
        focus_top_k=6,
        deepen_top_k=4,
    )

    task = "find why order confirmation emails sometimes show another customer's order"
    print(f"Codebase: {len(_FILES)} files")
    print(f"Task    : {task}")
    print("Initial keywords: ['send_confirm', 'order_confirmed', 'mail']")
    print()

    session: DiscoverySession = discoverer.discover(
        task=task,
        initial_keywords=["send_confirm", "order_confirmed", "mail"],
    )

    print(f"Cycles run     : {session.cycle_count}")
    print(f"Total tokens   : {session.total_tokens:,}")
    print(f"Final files    : {len(session.final_files)}")
    for p in session.final_files:
        marker = ""
        if p == "app/mailers/order_confirmed.rb":
            marker = " ← bug source 1 (mailer)"
        elif p == "app/cache/user_state.rb":
            marker = " ← bug source 2 (cache key)"
        print(f"  · {p}{marker}")
    print()
    print(f"Bug located    : {session.success}")
    print()
    print("Per-phase trace:")
    for e in session.events:
        print(
            f"  {e.phase.value:8s}  "
            f"candidates {e.candidates_in:>3} → {e.candidates_out:>2}  "
            f"files_read {e.files_read:>2}  "
            f"tokens {e.tokens_used:>5,}  "
            f"{e.wall_time_ms} ms"
        )
    print()
    print("Health check:")
    for k, v in discoverer.health_check(session).items():
        print(f"  · {k}: {v}")


if __name__ == "__main__":
    main()
