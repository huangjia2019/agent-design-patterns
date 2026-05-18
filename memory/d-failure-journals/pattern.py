"""Failure Journals pattern.

Reference implementation of the cross-task failure log pattern from
column lecture 03-05. The pattern's claim: **erasing failure equals
erasing evidence — and without evidence the model cannot adapt**. (The
formulation is from Manus's *Context Engineering for AI Agents* essay.)

Most agent frameworks today handle failure at the "try-catch then retry
in this turn" level. The information dies with the session. Two weeks
later a different session in the same project repeats the same mistake
because the lesson was never written down anywhere the agent can pull
it back. Failure Journals fixes that by treating each failure as a
durable, schema-shaped artifact: classify it, record it with a stable
task signature, and proactively recall similar past failures before
the agent acts on a new task.

Four stages, after `arxiv:2509.25370` ("Where LLM Agents Fail"):

    Detection → Classification → Recording → Recall

Recording without Recall is just observability. Recall is what turns
the journal into experience.

The ten failure categories below are condensed from Hermes Agent's
thirteen FailoverReason enum (auth / billing / rate_limit / overloaded
/ etc.) plus three extras that matter for agents specifically:

* `SEMANTIC_DRIFT` — the agent stopped solving the user's task.
* `BOUNDARY_LEAK` — config/env/tenant slipped across a boundary that
  should have held (the lecture-opening incident: writing a test
  OAuth client_id into a production config file, twice, two weeks
  apart, on two unrelated tasks).
* `INDEX_LAG` — a new Boris-Cherny-era failure mode: the data exists
  on disk, but the retrieval index hasn't caught up, so the agent
  acts as if the data weren't there.

The journal supports two retention modes ("tiered retention", per
NeuralWired's 2026 production guidance): every entry counts against
`max_entries`, but entries with non-zero `access_count` (i.e. ones that
were actually recalled and helped) get retention priority on eviction.
This is the cheap version of the 48h/30d/90d tiered storage that
production deployments use.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable


class FailureCategory(Enum):
    """Failure taxonomy — condensed from Hermes' 13 FailoverReasons + 3 agent-era extras."""

    # === Model / API layer ===
    API_TRANSIENT     = "api_transient"      # 5xx / timeout / overloaded
    API_PERMANENT     = "api_permanent"      # auth / billing / model_not_found
    CONTEXT_OVERFLOW  = "context_overflow"   # context too large

    # === Tool / action layer ===
    TOOL_ERROR        = "tool_error"         # tool returned non-zero / raised
    SANDBOX_VIOLATION = "sandbox_violation"  # sandbox rejected the action
    PERMISSION_DENY   = "permission_deny"    # not authorized

    # === Task / semantics layer ===
    SEMANTIC_DRIFT    = "semantic_drift"     # agent left the user's task
    BOUNDARY_LEAK     = "boundary_leak"      # config/env/tenant crossed wrong boundary

    # === Retrieval / memory layer ===
    RETRIEVAL_MISS    = "retrieval_miss"     # RAG missed a relevant doc
    INDEX_LAG         = "index_lag"          # data written but not indexed


_HIGH_RISK_CATEGORIES = frozenset({
    FailureCategory.BOUNDARY_LEAK,
    FailureCategory.PERMISSION_DENY,
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FailureEntry:
    """One failure record.

    The schema is the point. Free-text logs cannot be retrieved or
    clustered. A typed entry can be filtered, recalled, and rendered
    back into prompts in a stable form.
    """

    failure_id: str
    timestamp: str
    task_signature: str              # used for recall — keep it human-readable
    category: FailureCategory
    summary: str                     # one-line — keep under ~200 chars
    root_cause: str                  # the exception class or short cause string
    stack_trace: str | None = None
    remediation: str | None = None   # what (if anything) fixed it at the time
    lessons: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    access_count: int = 0
    last_recalled_at: str | None = None

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        category: FailureCategory,
        task_signature: str,
        lessons: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> "FailureEntry":
        digest_source = f"{task_signature}|{category.value}|{exc!r}"
        return cls(
            failure_id=hashlib.sha256(digest_source.encode()).hexdigest()[:12],
            timestamp=_now_iso(),
            task_signature=task_signature,
            category=category,
            summary=str(exc)[:200],
            root_cause=type(exc).__name__,
            stack_trace=str(exc),
            lessons=lessons or [],
            tags=tags or [],
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


# Signature for swap-in similarity functions. Production deployments
# pass in an embedding-cosine version; the default is jaccard on words,
# which is honest demo behaviour.
SimilarityFn = Callable[[str, str], float]


def _jaccard_similarity(a: str, b: str) -> float:
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class FailureJournal:
    """Cross-task failure log with detection → classification → recording → recall.

    Storage is in-memory by default. A production deployment swaps
    `_load` / `_persist` for a real backend (sqlite, postgres, redis).
    The pattern is the contract — not where the bytes live.
    """

    def __init__(
        self,
        retention_days: int = 90,
        max_entries: int = 1000,
        similarity_fn: SimilarityFn | None = None,
    ) -> None:
        self.entries: dict[str, FailureEntry] = {}
        self.retention_days = retention_days
        self.max_entries = max_entries
        self.similarity_fn = similarity_fn or _jaccard_similarity

    # --- 1. Recording -----------------------------------------------------

    def record(self, entry: FailureEntry) -> str:
        """Store a failure. Same failure_id increments access_count instead of duplicating."""
        if entry.failure_id in self.entries:
            self.entries[entry.failure_id].access_count += 1
        else:
            self.entries[entry.failure_id] = entry
        self._evict_if_needed()
        return entry.failure_id

    # --- 2. Classification -----------------------------------------------

    def by_category(self, category: FailureCategory) -> list[FailureEntry]:
        return [e for e in self.entries.values() if e.category == category]

    def high_risk_entries(self) -> list[FailureEntry]:
        """Entries the lecture's customer-support scenario keeps forever and recalls every turn."""
        return [e for e in self.entries.values() if e.category in _HIGH_RISK_CATEGORIES]

    # --- 3. Recall -------------------------------------------------------

    def recall_for_task(
        self,
        task_signature: str,
        top_k: int = 5,
        threshold: float = 0.4,
        force_include_high_risk: bool = True,
    ) -> list[FailureEntry]:
        """Surface past failures that look like this task.

        High-risk entries (boundary_leak, permission_deny) are appended
        even if similarity is below threshold — they are the failures
        you cannot afford to miss recalling.
        """
        scored: list[tuple[FailureEntry, float]] = []
        for entry in self.entries.values():
            score = self.similarity_fn(task_signature, entry.task_signature)
            if score >= threshold:
                scored.append((entry, score))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        results = [entry for entry, _ in scored[:top_k]]

        if force_include_high_risk:
            already = {e.failure_id for e in results}
            for entry in self.high_risk_entries():
                if entry.failure_id not in already:
                    results.append(entry)

        now = _now_iso()
        for entry in results:
            entry.access_count += 1
            entry.last_recalled_at = now
        return results

    def render_for_prompt(self, entries: list[FailureEntry]) -> str:
        """Format recalled failures into a prompt block.

        This is the Contextual Experience Replay (arxiv:2506.06698)
        contract: feed past failures back to the agent as text in the
        prompt at the moment a similar task starts. No retraining,
        no model surgery — just disciplined recall.
        """
        if not entries:
            return ""
        lines = ["## Past failures relevant to this task (review before acting):"]
        for e in entries:
            lessons = "; ".join(e.lessons) if e.lessons else "n/a"
            lines.append(
                f"- [{e.category.value}] {e.summary}\n"
                f"    root cause: {e.root_cause}\n"
                f"    lessons: {lessons}"
            )
        return "\n".join(lines)

    # --- 4. Lifecycle ----------------------------------------------------

    def _evict_if_needed(self) -> None:
        if len(self.entries) <= self.max_entries:
            return
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        ranked = sorted(
            self.entries.values(),
            key=lambda e: (
                e.category in _HIGH_RISK_CATEGORIES,   # never evict high-risk
                e.access_count,
                e.timestamp,
            ),
            reverse=True,
        )
        keep: dict[str, FailureEntry] = {}
        for entry in ranked:
            if len(keep) >= self.max_entries:
                break
            ts = datetime.fromisoformat(entry.timestamp)
            recent = ts > cutoff
            ever_recalled = entry.access_count > 0
            high_risk = entry.category in _HIGH_RISK_CATEGORIES
            if recent or ever_recalled or high_risk:
                keep[entry.failure_id] = entry
        self.entries = keep

    # --- 5. Health -------------------------------------------------------

    def health_report(self) -> dict[str, Any]:
        """Per-category counts + recall hit rate. Mem0 2026 calls this the
        single most important metric for procedural memory health."""
        total = len(self.entries)
        recalled = sum(1 for e in self.entries.values() if e.access_count > 0)
        by_cat = {c.value: len(self.by_category(c)) for c in FailureCategory}
        return {
            "total_entries": total,
            "recall_rate": round(recalled / total, 3) if total else 0.0,
            "by_category": by_cat,
            "high_risk_entries": len(self.high_risk_entries()),
        }

    def export_json(self) -> str:
        return json.dumps(
            [e.to_dict() for e in self.entries.values()],
            ensure_ascii=False,
            indent=2,
        )
