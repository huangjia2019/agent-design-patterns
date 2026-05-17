"""Semantic Compaction pattern.

Reference implementation of the anchored iterative summarisation pattern
described in column lecture 02-03. Three observations the pattern is built on:

* The error trace is special. It is the agent's feedback loop and it must
  survive every level of compaction.
* "Summarise then re-summarise" drifts. Iterative compaction works by
  maintaining a small *anchor state* (intent / changes / decisions /
  excluded approaches / next steps) and merging new turns into it, rather
  than re-summarising from scratch.
* Triggering compaction at 95% window capacity is too late. Recent
  community guidance (Aider, OpenCode, Claude Code best-practices threads)
  is to trigger somewhere in the 55–70% range.

The pattern is callable with any LLM client through a single
``llm: Callable[[str], str]`` injection, so it stays runnable without API
keys when you swap in a stub.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Turn:
    """One turn of dialogue or one tool call/result."""

    role: str          # "user" / "assistant" / "tool_result" / "system"
    content: str
    tokens: int
    is_error: bool = False
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class CompactionAnchor:
    """The persistent state preserved across compactions.

    Five slots, deliberately. ``excluded_approaches`` is the slot that
    breaks the "agent keeps retrying ruled-out fixes" loop.
    """

    intent: str = ""
    changes_made: list[str] = field(default_factory=list)
    decisions_taken: list[str] = field(default_factory=list)
    excluded_approaches: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_summary(self) -> str:
        parts: list[str] = []
        if self.intent:
            parts.append(f"INTENT: {self.intent}")
        if self.changes_made:
            parts.append(f"CHANGES: {' | '.join(self.changes_made[-10:])}")
        if self.decisions_taken:
            parts.append(f"DECIDED: {' | '.join(self.decisions_taken[-10:])}")
        if self.excluded_approaches:
            parts.append(
                "EXCLUDED (do not retry): "
                + " | ".join(self.excluded_approaches)
            )
        if self.next_steps:
            parts.append(f"NEXT: {' | '.join(self.next_steps[-5:])}")
        return "\n".join(parts)


@dataclass
class CompactionEvent:
    """One atomic record of a compaction decision."""

    level: int                       # 1, 2, or 3
    turns_before: int
    turns_after: int
    tokens_before: int
    tokens_after: int
    error_traces_in: int             # count of is_error turns in the input
    error_traces_out: int            # count of is_error turns in the output
    timestamp: str = field(default_factory=_now_iso)

    @property
    def compression_ratio(self) -> float:
        return self.tokens_after / max(self.tokens_before, 1)

    @property
    def all_errors_preserved(self) -> bool:
        return self.error_traces_out >= self.error_traces_in


class SemanticCompactor:
    """Three-level cascading compactor with anchor state and error protection."""

    def __init__(
        self,
        llm: Callable[[str], str],
        anchor: CompactionAnchor | None = None,
        preserve_recent: int = 5,
        trigger_at_ratio: float = 0.60,   # community-recommended early trigger
    ) -> None:
        self.llm = llm
        self.anchor = anchor or CompactionAnchor()
        self.preserve_recent = preserve_recent
        self.trigger_at_ratio = trigger_at_ratio
        self.events: list[CompactionEvent] = []

    # ──────────────── public API ────────────────

    def should_compact(self, total_tokens: int, budget: int) -> bool:
        return total_tokens / max(budget, 1) >= self.trigger_at_ratio

    def compact(self, turns: list[Turn], target_tokens: int) -> list[Turn]:
        total = sum(t.tokens for t in turns)
        if total <= target_tokens:
            return turns

        boundary = max(0, len(turns) - self.preserve_recent)
        old = [t for t in turns[:boundary] if not t.is_error]
        errors = [t for t in turns[:boundary] if t.is_error]
        recent = turns[boundary:]
        errors_in = sum(1 for t in turns if t.is_error)

        # L1 — clear long tool outputs
        cleared = self._clear_tools(old)
        result = cleared + errors + recent
        if self._fits(result, target_tokens):
            self._log(1, len(turns), result, total, errors_in)
            return result

        # L2 — fold old turns into the anchor
        self._update_anchor(old)
        anchor_turn = Turn(
            role="system",
            content=f"[Anchor State]\n{self.anchor.to_summary()}",
            tokens=max(1, len(self.anchor.to_summary()) // 4),
        )
        result = [anchor_turn] + errors + recent
        if self._fits(result, target_tokens):
            self._log(2, len(turns), result, total, errors_in)
            return result

        # L3 — last resort: keep only the most recent error traces in full,
        # collapse the rest into a "do not retry" list. Use sparingly.
        recent_errors = errors[-3:]
        old_errors_summary = self._summarize_errors(errors[:-3])
        result = [anchor_turn, old_errors_summary] + recent_errors + recent
        self._log(3, len(turns), result, total, errors_in)
        return result

    def health_check(self) -> dict[str, str]:
        """Run nightly. The three things you actually want to watch."""
        report: dict[str, str] = {}
        if not self.events:
            return {"status": "no compaction events yet"}
        l3 = sum(1 for e in self.events if e.level == 3)
        if l3 / len(self.events) > 0.10:
            report["level_3_overuse"] = (
                f"Level 3 fired {l3}/{len(self.events)} times — drift risk"
            )
        avg_ratio = sum(e.compression_ratio for e in self.events) / len(self.events)
        if avg_ratio < 0.20:
            report["over_compression"] = (
                f"Average ratio {avg_ratio:.1%} — over-compressing"
            )
        violations = sum(1 for e in self.events if not e.all_errors_preserved)
        if violations > 0:
            report["error_loss_violation"] = (
                f"{violations} events dropped error traces — invariant violated"
            )
        return report

    # ──────────────── internals ────────────────

    def _clear_tools(self, turns: list[Turn]) -> list[Turn]:
        out: list[Turn] = []
        for t in turns:
            if t.role == "tool_result" and t.tokens > 500 and not t.is_error:
                out.append(Turn(
                    role="tool_result",
                    content=f"[Tool result cleared: {t.tokens} tokens. Re-run to retrieve.]",
                    tokens=25,
                ))
            else:
                out.append(t)
        return out

    def _update_anchor(self, turns: list[Turn]) -> None:
        text = "\n".join(f"[{t.role}]: {t.content[:300]}" for t in turns)
        existing = self.anchor.to_summary()
        prompt = (
            f"Existing anchor state:\n{existing}\n\n"
            f"New conversation chunk:\n{text}\n\n"
            "Given the existing anchor + new chunk, output the updated 5-field anchor:\n"
            "INTENT: ...\nCHANGES: ...\nDECIDED: ...\n"
            "EXCLUDED: ...\nNEXT: ...\n"
            "Hard rule: previously excluded approaches must remain; "
            "new decisions append, not overwrite."
        )
        updated = self.llm(prompt)
        self._parse_anchor(updated)

    def _parse_anchor(self, text: str) -> None:
        for raw in text.split("\n"):
            line = raw.strip()
            if line.startswith("INTENT:"):
                self.anchor.intent = line[7:].strip()
            elif line.startswith("CHANGES:"):
                self.anchor.changes_made.extend(
                    s.strip() for s in line[8:].split("|") if s.strip()
                )
            elif line.startswith("DECIDED:"):
                self.anchor.decisions_taken.extend(
                    s.strip() for s in line[8:].split("|") if s.strip()
                )
            elif line.startswith("EXCLUDED:"):
                self.anchor.excluded_approaches.extend(
                    s.strip() for s in line[9:].split("|") if s.strip()
                )
            elif line.startswith("NEXT:"):
                self.anchor.next_steps = [
                    s.strip() for s in line[5:].split("|") if s.strip()
                ]

    def _summarize_errors(self, errors: list[Turn]) -> Turn:
        if not errors:
            return Turn(role="system", content="[no old errors]", tokens=5)
        bullets = "\n".join(f"- {e.content[:200]}" for e in errors)
        return Turn(
            role="system",
            content=f"[Old errors (do not retry):\n{bullets}",
            tokens=sum(min(50, e.tokens) for e in errors),
        )

    def _fits(self, turns: list[Turn], target: int) -> bool:
        return sum(t.tokens for t in turns) <= target

    def _log(
        self,
        level: int,
        before_n: int,
        result: list[Turn],
        before_t: int,
        errors_in: int,
    ) -> None:
        self.events.append(CompactionEvent(
            level=level,
            turns_before=before_n,
            turns_after=len(result),
            tokens_before=before_t,
            tokens_after=sum(t.tokens for t in result),
            error_traces_in=errors_in,
            error_traces_out=sum(1 for t in result if t.is_error),
        ))
