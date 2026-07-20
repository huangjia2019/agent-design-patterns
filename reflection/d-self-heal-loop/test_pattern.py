"""Invariant tests for the Self-Heal Loop reference implementation."""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    FailureSignal,
    HealStatus,
    Patch,
    SelfHealLoop,
    StabilityPolicy,
    propose_guard,
)


def signal(code: str, files: list[str] | None = None) -> FailureSignal:
    return FailureSignal("test", f"failure {code}", files or ["app.py"], code=code)


def test_converging_repair_keeps_atomic_commits() -> None:
    failures = iter([signal("second"), None])
    commits: list[str] = []
    rolled_back: list[str] = []

    def apply(_patch: Patch) -> str:
        commit_id = f"c{len(commits) + 1}"
        commits.append(commit_id)
        return commit_id

    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", [f"{diagnosis}.py"]),
        critic=lambda _patch, _failure: "",
        apply=apply,
        verify=lambda: next(failures),
        rollback=rolled_back.append,
    )

    trace = loop.heal(signal("first"))

    assert trace.status is HealStatus.FIXED
    assert trace.applied_commits == ["c1", "c2"]
    assert rolled_back == []


def test_critic_block_restores_any_prior_commit() -> None:
    failures = iter([signal("unsafe"), None])
    rolled_back: list[str] = []

    def critic(_patch: Patch, failure: FailureSignal) -> str:
        return "patch weakens tests" if failure.code == "unsafe" else ""

    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", [f"{diagnosis}.py"]),
        critic=critic,
        apply=lambda _patch: "c1",
        verify=lambda: next(failures),
        rollback=rolled_back.append,
    )

    trace = loop.heal(signal("first"))

    assert trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert rolled_back == ["c1"]
    assert trace.baseline_restored is True


def test_critic_block_before_apply_leaves_baseline_intact() -> None:
    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", ["tests/test_app.py"]),
        critic=lambda _patch, _failure: "patch touches the test",
        apply=lambda _patch: "must-not-run",
        verify=lambda: None,
        rollback=lambda _commit: None,
    )

    trace = loop.heal(signal("first"))

    assert trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert trace.applied_commits == []
    assert trace.baseline_restored is True


def test_regression_rolls_back_newest_commit_first() -> None:
    failures = iter(
        [
            signal("next", ["a.py", "b.py"]),
            signal("regression", ["a.py", "b.py", "c.py"]),
        ]
    )
    commits: list[str] = []
    rolled_back: list[str] = []

    def apply(_patch: Patch) -> str:
        commit_id = f"c{len(commits) + 1}"
        commits.append(commit_id)
        return commit_id

    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", ["app.py"]),
        critic=lambda _patch, _failure: "",
        apply=apply,
        verify=lambda: next(failures),
        rollback=rolled_back.append,
    )

    trace = loop.heal(signal("first"))

    assert trace.status is HealStatus.ROLLED_BACK_REGRESSION
    assert rolled_back == ["c2", "c1"]


def test_same_failure_and_patch_stops_as_no_progress() -> None:
    same = signal("same")
    rolled_back: list[str] = []
    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda _diagnosis: Patch("same patch", ["app.py"]),
        critic=lambda _patch, _failure: "",
        apply=lambda _patch: "c1",
        verify=lambda: same,
        rollback=rolled_back.append,
    )

    trace = loop.heal(same)

    assert trace.status is HealStatus.ROLLED_BACK_NO_PROGRESS
    assert len(trace.rounds) == 2
    assert rolled_back == ["c1"]


def test_round_budget_rolls_back_before_human_handoff() -> None:
    counter = {"n": 0}
    rolled_back: list[str] = []

    def apply(_patch: Patch) -> str:
        counter["n"] += 1
        return f"c{counter['n']}"

    def verify() -> FailureSignal:
        return signal(f"next-{counter['n']}")

    loop = SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", ["app.py"]),
        critic=lambda _patch, _failure: "",
        apply=apply,
        verify=verify,
        rollback=rolled_back.append,
        stability=StabilityPolicy(max_rounds=2, max_radius_multiplier=3),
    )

    trace = loop.heal(signal("first"))

    assert trace.status is HealStatus.MAX_ROUNDS_HUMAN_HANDOFF
    assert rolled_back == ["c2", "c1"]
    assert trace.baseline_restored is True


def test_failure_signature_uses_stable_code_and_guard_needs_distinct_runs() -> None:
    first = FailureSignal("test", "total off by 12", code="reconcile-total")
    second = FailureSignal("test", "total off by 99", code="reconcile-total")

    assert first.signature == second.signature
    assert propose_guard(first.signature, ["run-1"]) is None
    assert propose_guard(first.signature, ["run-1", "run-2"])["status"] == "proposed"


def test_fallback_signature_normalizes_volatile_numbers() -> None:
    first = FailureSignal("test", "reconcile total off by 19200 at line 81")
    second = FailureSignal("test", "reconcile total off by 1088412 at line 104")

    assert first.signature == second.signature


def test_test_file_detection_uses_paths_without_substring_false_positives() -> None:
    assert Patch("change test", ["tests/test_reconcile.py"]).touches_tests is True
    assert Patch("change test", ["test_payout.py"]).touches_tests is True
    assert Patch("change test", ["payout_test.py"]).touches_tests is True
    assert Patch("change code", ["latest_totals.py"]).touches_tests is False
    assert Patch("change code", ["src/contest_rules.py"]).touches_tests is False
