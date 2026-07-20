"""Invariants for the Skill Package admission and routing boundary."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    GoldenQuestion,
    Skill,
    SkillLibrary,
    SkillStatus,
    distill_from_trace,
)


def skill() -> Skill:
    return Skill(
        name="social-base-adjust",
        description="Recalculate the social insurance base.",
        triggers=["social", "base", "adjust"],
        steps=["fetch_policy:2026", "clamp_base", "recalculate"],
    )


def runner(_skill: Skill, payload: dict[str, int]) -> int:
    return payload["actual"]


def test_new_skill_is_trial_and_invisible_to_router() -> None:
    library = SkillLibrary()
    added = library.add(skill())

    assert added.status is SkillStatus.TRIAL
    assert library.route("social base adjust").matched is None


def test_all_golden_questions_promote_skill() -> None:
    library = SkillLibrary()
    library.add(skill())
    goldens = [
        GoldenQuestion("floor", {"actual": 4880}, 4880),
        GoldenQuestion("cap", {"actual": 24402}, 24402),
    ]

    report = library.verify("social-base-adjust", goldens, runner)

    assert report.promoted is True
    assert report.failed == []
    assert library.skills["social-base-adjust"].status is SkillStatus.VERIFIED
    assert library.route("social base adjust").matched == "social-base-adjust"


def test_failed_reverification_removes_previous_badge() -> None:
    library = SkillLibrary()
    library.add(skill())
    library.verify(
        "social-base-adjust",
        [GoldenQuestion("2026 policy", {"actual": 24402}, 24402)],
        runner,
    )

    report = library.verify(
        "social-base-adjust",
        [GoldenQuestion("2027 policy", {"actual": 24402}, 25200)],
        runner,
    )

    stored = library.skills["social-base-adjust"]
    assert report.promoted is False
    assert report.failed
    assert stored.status is SkillStatus.TRIAL
    assert stored.verified_against == []
    assert library.route("social base adjust").matched is None


def test_empty_verification_suite_cannot_preserve_approval() -> None:
    library = SkillLibrary()
    library.add(skill())
    library.verify(
        "social-base-adjust",
        [GoldenQuestion("2026 policy", {"actual": 24402}, 24402)],
        runner,
    )

    report = library.verify("social-base-adjust", [], runner)

    assert report.promoted is False
    assert library.skills["social-base-adjust"].status is SkillStatus.TRIAL


def test_distillation_requires_a_successful_nontrivial_trace() -> None:
    calls = [
        {"tool": "fetch_policy"},
        {"tool": "clamp_base"},
        {"tool": "verify_group"},
        {"tool": "reconcile"},
        {"tool": "report"},
    ]

    failed = distill_from_trace(
        "monthly settlement",
        calls,
        "settlement",
        "Settle payroll.",
        ["settlement"],
        succeeded=False,
    )
    candidate = distill_from_trace(
        "monthly settlement",
        calls,
        "settlement",
        "Settle payroll.",
        ["settlement"],
        succeeded=True,
    )

    assert failed is None
    assert candidate is not None
    assert candidate.status is SkillStatus.TRIAL
    assert candidate.source_task == "monthly settlement"


def test_reuse_outcomes_are_scoped_to_the_latest_verification() -> None:
    library = SkillLibrary(demote_below=0.8, min_uses=2)
    library.add(skill())

    with pytest.raises(ValueError, match="VERIFIED"):
        library.record_use("social-base-adjust", success=True)

    goldens = [GoldenQuestion("current policy", {"actual": 24402}, 24402)]
    library.verify("social-base-adjust", goldens, runner)
    library.record_use("social-base-adjust", success=True)
    demoted = library.record_use("social-base-adjust", success=False)

    assert demoted.status is SkillStatus.TRIAL
    assert demoted.use_count == 2

    library.verify("social-base-adjust", goldens, runner)
    reverified = library.skills["social-base-adjust"]
    assert reverified.status is SkillStatus.VERIFIED
    assert reverified.use_count == 0
    assert reverified.success_count == 0
