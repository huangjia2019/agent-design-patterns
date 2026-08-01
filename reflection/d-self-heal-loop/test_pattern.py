"""Behavioral tests for the receipt-bound Self-Heal transaction."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ApplyReceipt,
    FailureSignal,
    HealStatus,
    Patch,
    PatchReview,
    RollbackReceipt,
    SelfHealLoop,
    StabilityPolicy,
    VerificationReceipt,
    propose_guard,
)


def signal(code: str, files: tuple[str, ...] = ("app.py",)) -> FailureSignal:
    return FailureSignal("test", f"failure {code}", files, code=code)


def payload(operation: str) -> str:
    return json.dumps({"operation": operation}, sort_keys=True, separators=(",", ":"))


@dataclass
class MemoryWorkspace:
    state: dict[str, bool] = field(default_factory=dict)
    snapshots: dict[str, dict[str, bool]] = field(default_factory=dict)
    next_commit: int = 0

    def state_digest(self) -> str:
        body = json.dumps(self.state, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(body.encode()).hexdigest()

    def apply(self, patch: Patch) -> ApplyReceipt:
        self.next_commit += 1
        commit_id = f"c{self.next_commit}"
        self.snapshots[commit_id] = dict(self.state)
        self.state[json.loads(patch.payload)["operation"]] = True
        return ApplyReceipt(commit_id, patch.digest, patch.touches)

    def rollback(self, receipt: ApplyReceipt) -> RollbackReceipt:
        self.state = dict(self.snapshots[receipt.commit_id])
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "restored exact pre-apply snapshot")


def approved(patch: Patch, _failure: FailureSignal) -> PatchReview:
    return PatchReview(patch.digest, True, "", ("policy=approved",))


def verification(receipt: ApplyReceipt, failure: FailureSignal | None) -> VerificationReceipt:
    return VerificationReceipt(receipt.commit_id, receipt.patch_digest, failure, "deterministic-ci", "green" if failure is None else f"red:{failure.code}")


def make_loop(workspace: MemoryWorkspace, failures: list[FailureSignal | None], *, fix=None, review=approved, stability=None) -> SelfHealLoop:
    remaining = iter(failures)
    return SelfHealLoop(
        diagnose=lambda failure: failure.code,
        fix=fix or (lambda diagnosis: Patch(f"fix {diagnosis}", payload(diagnosis), (f"{diagnosis}.py",))),
        review=review,
        apply=workspace.apply,
        verify=lambda receipt: verification(receipt, next(remaining)),
        rollback=workspace.rollback,
        state_digest=workspace.state_digest,
        stability=stability,
    )


def test_converging_repair_keeps_atomic_receipts() -> None:
    workspace = MemoryWorkspace()
    loop = make_loop(workspace, [signal("second"), None])
    trace = loop.heal(signal("first"))
    assert trace.status is HealStatus.FIXED
    assert tuple(item.commit_id for item in trace.apply_receipts) == ("c1", "c2")
    assert trace.rollback_receipts == ()
    assert trace.final_digest != trace.baseline_digest
    assert trace.baseline_restored is None
    assert workspace.state == {"first": True, "second": True}
    assert trace.stop_reason == "verification_passed"


def test_review_block_restores_any_prior_apply() -> None:
    workspace = MemoryWorkspace()
    loop = make_loop(
        workspace, [signal("unsafe")],
        review=lambda patch, failure: PatchReview(patch.digest, failure.code != "unsafe", "unsafe patch" if failure.code == "unsafe" else "", ("policy=approved",)),
    )
    trace = loop.heal(signal("first"))
    assert trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert tuple(item.commit_id for item in trace.rollback_receipts) == ("c1",)
    assert trace.baseline_digest == trace.final_digest
    assert trace.baseline_restored is True
    assert workspace.state == {}
    assert trace.stop_reason == "review_rejected"
    assert trace.applied_commits == ("c1",)


def test_review_block_before_apply_leaves_baseline_intact() -> None:
    workspace = MemoryWorkspace()
    loop = make_loop(workspace, [], review=lambda patch, _: PatchReview(patch.digest, False, "test patch", ("policy=tests",)))
    trace = loop.heal(signal("first"))
    assert trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert not trace.apply_receipts and not trace.rollback_receipts
    assert trace.baseline_digest == trace.final_digest and trace.baseline_restored is True
    assert workspace.state == {} and trace.stop_reason == "review_rejected"


def test_accumulated_radius_rolls_back_newest_first() -> None:
    workspace = MemoryWorkspace()
    loop = make_loop(
        workspace,
        [signal("next", ("a.py", "b.py")), signal("regression", ("a.py", "b.py", "c.py"))],
        fix=lambda diagnosis: Patch(f"fix {diagnosis}", payload(diagnosis), ("a.py",)),
    )
    trace = loop.heal(signal("first", ("a.py",)))
    assert trace.status is HealStatus.ROLLED_BACK_REGRESSION
    assert tuple(item.commit_id for item in trace.rollback_receipts) == ("c2", "c1")
    assert trace.baseline_restored is True
    assert workspace.state == {} and trace.baseline_digest == trace.final_digest
    assert trace.stop_reason == "blast_radius_exceeded"


def test_same_failure_and_patch_stops_as_no_progress() -> None:
    workspace = MemoryWorkspace()
    same = signal("same")
    trace = make_loop(workspace, [same], fix=lambda _: Patch("same patch", payload("same"), ("app.py",))).heal(same)
    assert trace.status is HealStatus.ROLLED_BACK_NO_PROGRESS
    assert len(trace.rounds) == 2 and trace.rounds[-1].apply_receipt is None
    assert trace.rounds[1].patch_review is None
    assert tuple(item.commit_id for item in trace.rollback_receipts) == ("c1",)
    assert workspace.state == {} and trace.baseline_digest == trace.final_digest
    assert trace.baseline_restored is True and trace.stop_reason == "no_progress_same_failure_and_patch"


def test_round_budget_rolls_back_before_human_handoff() -> None:
    workspace = MemoryWorkspace()
    trace = make_loop(workspace, [signal("second"), signal("third")], stability=StabilityPolicy(max_rounds=2, max_radius_multiplier=4)).heal(signal("first"))
    assert trace.status is HealStatus.MAX_ROUNDS_HUMAN_HANDOFF
    assert trace.stop_reason == "round_budget_exhausted"
    assert tuple(item.commit_id for item in trace.rollback_receipts) == ("c2", "c1")
    assert workspace.state == {} and trace.baseline_digest == trace.final_digest
    assert trace.baseline_restored is True


def test_failure_signature_uses_stable_code_and_guard_needs_distinct_runs() -> None:
    first = FailureSignal("test", "total off by 12", code="reconcile-total")
    second = FailureSignal("test", "total off by 99", code="reconcile-total")
    assert first.signature == second.signature
    assert propose_guard(first.signature, ["run-1"]) is None
    assert propose_guard(first.signature, ["run-1", "run-2"])["status"] == "proposed"


def test_fallback_signature_normalizes_volatile_numbers() -> None:
    assert FailureSignal("test", "reconcile total off by 19200 at line 81").signature == FailureSignal("test", "reconcile total off by 1088412 at line 104").signature


def test_test_file_detection_uses_paths_without_substring_false_positives() -> None:
    assert Patch("change test", payload("x"), ("tests/test_reconcile.py",)).touches_tests is True
    assert Patch("change test", payload("x"), ("test_payout.py",)).touches_tests is True
    assert Patch("change test", payload("x"), ("payout_test.py",)).touches_tests is True
    assert Patch("change code", payload("x"), ("latest_totals.py",)).touches_tests is False
    assert Patch("change code", payload("x"), ("src/contest_rules.py",)).touches_tests is False


def test_legacy_max_rounds_constructor_argument_is_rejected() -> None:
    workspace = MemoryWorkspace()
    with pytest.raises(TypeError):
        SelfHealLoop(diagnose=lambda _: "", fix=lambda _: Patch("x", payload("x"), ("a.py",)), review=approved, apply=workspace.apply, verify=lambda receipt: verification(receipt, None), rollback=workspace.rollback, state_digest=workspace.state_digest, max_rounds=2)
