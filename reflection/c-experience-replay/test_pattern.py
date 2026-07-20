"""Invariant tests for the Experience Replay reference pattern."""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import Experience, ExperienceStore  # noqa: E402


def experience(
    exp_id: str,
    *,
    task_kind: str = "batch",
    keywords: list[str] | None = None,
    hard_guard_eligible: bool = False,
) -> Experience:
    return Experience(
        exp_id=exp_id,
        task_kind=task_kind,
        outcome="success",
        lesson=f"lesson from {exp_id}",
        keywords=keywords or ["batch"],
        steps=[f"raw step from {exp_id}"],
        hard_guard_eligible=hard_guard_eligible,
    )


def test_retrieve_ignores_archived_entries_and_counts_exposure() -> None:
    store = ExperienceStore(top_k=2)
    active = store.record(experience("active"))
    archived = store.record(experience("archived"))
    archived.archived = True

    hits = store.retrieve("build batch")

    assert hits == [active]
    assert active.retrieval_count == 1
    assert archived.retrieval_count == 0


def test_render_keeps_raw_steps_out_and_limits_l2_to_hit_task_kind() -> None:
    store = ExperienceStore(min_l1_for_l2=2)
    batch_a = store.record(experience("batch-a"))
    store.record(experience("batch-b"))
    report = store.record(
        experience("report", task_kind="report", keywords=["report"])
    )
    store.distill("batch")

    batch_context = store.render([batch_a])
    report_context = store.render([report])

    assert "raw step" not in batch_context
    assert "[heuristic] [batch]" in batch_context
    assert "[heuristic] [batch]" not in report_context


def test_feedback_archives_a_reused_lesson_below_the_health_line() -> None:
    store = ExperienceStore()
    lesson = store.record(experience("weak"))

    for _ in range(5):
        archived = store.feedback([lesson], downstream_success=False)

    assert lesson.archived is True
    assert lesson.reuses == 5
    assert archived == ["weak"]


def test_graduation_requires_track_record_and_explicit_guard_eligibility() -> None:
    store = ExperienceStore()
    eligible = store.record(
        experience("eligible", hard_guard_eligible=True)
    )
    soft = store.record(experience("soft"))

    for _ in range(5):
        store.feedback([eligible, soft], downstream_success=True)

    assert eligible.effectiveness >= 0.7
    assert soft.effectiveness >= 0.7
    assert store.graduation_candidates() == [eligible]


def test_distill_waits_for_enough_same_kind_entries() -> None:
    store = ExperienceStore(min_l1_for_l2=2)
    store.record(experience("one"))

    assert store.distill("batch") is None

    store.record(experience("two"))
    heuristic = store.distill("batch")

    assert heuristic is not None
    assert heuristic.task_kind == "batch"
    assert heuristic.derived_from == ["one", "two"]
