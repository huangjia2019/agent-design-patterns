"""Transaction-bound contract tests for the Self-Heal Loop."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import FrozenInstanceError, dataclass, field
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ApplyReceipt, FailureSignal, HealStage, HealStatus, Patch, PatchReview,
    RollbackReceipt, SelfHealLoop, StabilityPolicy, VerificationReceipt,
)


def payload(operation: str) -> str:
    return json.dumps({"operation": operation}, sort_keys=True, separators=(",", ":"))


def test_inputs_snapshot_collections_and_freeze_identity() -> None:
    """Mutating caller-owned lists cannot change a committed identity."""
    files = ["b.py", "a.py", "a.py"]
    evidence = ["policy=test-files-blocked"]
    signal = FailureSignal("test", "red", files, code="RED")
    patch = Patch("repair red", payload("repair"), files)
    review = PatchReview(patch.digest, True, "", evidence)
    receipt = ApplyReceipt("c1", patch.digest, files)

    files.append("later.py")
    evidence.append("later mutation")

    assert signal.affected_files == ("a.py", "b.py")
    assert patch.touches == ("a.py", "b.py")
    assert review.evidence == ("policy=test-files-blocked",)
    assert receipt.changed_files == ("a.py", "b.py")
    with pytest.raises(FrozenInstanceError):
        signal.code = "CHANGED"  # type: ignore[misc]


def test_patch_digest_uses_payload_and_canonical_paths_not_description() -> None:
    """Labels and caller ordering cannot evade deterministic patch identity."""
    first = Patch("first label", payload("repair"), ("b.py", "a.py"))
    relabeled = Patch("second label", payload("repair"), ("a.py", "b.py"))
    changed = Patch("first label", payload("different"), ("a.py", "b.py"))

    assert first.digest == relabeled.digest
    assert first.fingerprint == first.digest
    assert changed.digest != first.digest
    assert len(first.digest) == 64


@pytest.mark.parametrize(
    "path",
    ["", "/tmp/a.py", "../a.py", "./a.py", "a/../b.py", "a/./b.py", "a//b.py", "a/", "a\\b.py", "C:/repo/a.py"],
)
def test_paths_reject_noncanonical_or_non_posix_values(path: str) -> None:
    """Patch identity only admits stable repository-relative POSIX paths."""
    with pytest.raises(ValueError):
        FailureSignal("test", "red", (path,))


def test_patch_requires_nonblank_utf8_payload() -> None:
    """A patch must carry executable, serializable intent."""
    with pytest.raises(ValueError, match="nonblank"):
        Patch("empty", "   ", ("a.py",))
    with pytest.raises(ValueError, match="UTF-8"):
        Patch("surrogate", "\ud800", ("a.py",))


@dataclass
class TransactionWorkspace:
    state: dict[str, bool] = field(default_factory=dict)
    snapshots: dict[str, dict[str, bool]] = field(default_factory=dict)
    number: int = 0

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.state, sort_keys=True).encode()).hexdigest()

    def apply(self, candidate: Patch) -> ApplyReceipt:
        self.number += 1
        commit = f"c{self.number}"
        self.snapshots[commit] = dict(self.state)
        self.state[json.loads(candidate.payload)["operation"]] = True
        return ApplyReceipt(commit, candidate.digest, candidate.touches)

    def rollback(self, receipt: ApplyReceipt) -> RollbackReceipt:
        self.state = dict(self.snapshots[receipt.commit_id])
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "snapshot restored")


def transaction_loop(workspace: TransactionWorkspace, *, review=None, apply=None, verify=None, rollback=None, digest=None, diagnose=None, fix=None) -> SelfHealLoop:
    def default_fix(code: str) -> Patch:
        return Patch("repair", payload(code), ("app.py",))
    return SelfHealLoop(
        diagnose=diagnose or (lambda failure: failure.code), fix=fix or default_fix,
        review=review or (lambda candidate, _: PatchReview(candidate.digest, True, "", ("policy=approved",))),
        apply=apply or workspace.apply,
        verify=verify or (lambda receipt: VerificationReceipt(receipt.commit_id, receipt.patch_digest, None, "ci", "green")),
        rollback=rollback or workspace.rollback, state_digest=digest or workspace.digest,
    )


def test_review_without_evidence_fails_closed() -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(workspace, review=lambda candidate, _: PatchReview(candidate.digest, True, "", ())).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.apply_receipts == () and trace.baseline_restored is True


@pytest.mark.parametrize("bad_evidence", [None, "character-by-character"])
def test_forged_review_evidence_fails_closed(bad_evidence: object) -> None:
    """Only a tuple containing at least one nonblank evidence item is valid."""
    workspace = TransactionWorkspace()

    def review(candidate: Patch, _failure: FailureSignal) -> PatchReview:
        receipt = object.__new__(PatchReview)
        object.__setattr__(receipt, "patch_digest", candidate.digest)
        object.__setattr__(receipt, "approved", True)
        object.__setattr__(receipt, "reason", "")
        object.__setattr__(receipt, "evidence", bad_evidence)
        return receipt

    trace = transaction_loop(workspace, review=review).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:review"
    assert trace.apply_receipts == ()
    assert trace.baseline_restored is True


def test_rejected_review_requires_reason() -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(workspace, review=lambda candidate, _: PatchReview(candidate.digest, False, "", ("policy=blocked",))).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF


def test_review_digest_substitution_fails_closed() -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(workspace, review=lambda _candidate, _: PatchReview("other", True, "", ("policy=approved",))).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.stage_errors[-1].stage is HealStage.REVIEW
    assert "patch_digest='other'" in trace.stage_errors[-1].evidence


def test_blank_apply_id_after_no_mutation_is_stage_error() -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(workspace, apply=lambda candidate: ApplyReceipt("", candidate.digest, candidate.touches)).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.rollback_receipts == () and trace.baseline_restored is True


def test_blank_apply_id_after_mutation_is_unaddressable() -> None:
    workspace = TransactionWorkspace()
    def bad_apply(candidate: Patch) -> ApplyReceipt:
        workspace.state["changed"] = True
        return ApplyReceipt("", candidate.digest, candidate.touches)
    trace = transaction_loop(workspace, apply=bad_apply).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF and trace.baseline_restored is False


def test_unique_mismatched_apply_receipt_is_compensated_unchanged() -> None:
    workspace = TransactionWorkspace()
    returned = ApplyReceipt("c2", "wrong-digest", ("wrong.py",))
    seen: list[ApplyReceipt] = []
    def apply(_candidate: Patch) -> ApplyReceipt:
        workspace.snapshots["c2"] = dict(workspace.state)
        workspace.state["changed"] = True
        return returned
    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        seen.append(receipt)
        workspace.state = dict(workspace.snapshots["c2"])
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "restored untrusted addressable apply")
    trace = transaction_loop(workspace, apply=apply, rollback=rollback).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert seen[0] is returned and trace.apply_receipts[-1] is returned
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:apply"
    assert trace.rolled_back == ("c2",)
    assert trace.baseline_digest == trace.final_digest
    assert trace.baseline_restored is True and workspace.state == {}
    assert trace.stage_errors[-1].evidence == (
        "commit_id='c2'", "patch_digest='wrong-digest'", "changed_files=('wrong.py',)"
    )


def test_verify_receipt_substitution_fails_closed() -> None:
    workspace = TransactionWorkspace()
    seen: list[ApplyReceipt] = []
    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        seen.append(receipt)
        return workspace.rollback(receipt)
    trace = transaction_loop(workspace, rollback=rollback, verify=lambda receipt: VerificationReceipt("other", receipt.patch_digest, None, "ci", "green")).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF and trace.baseline_restored is True
    assert trace.stop_reason == "stage_error:verify" and workspace.state == {}
    assert trace.baseline_digest == trace.final_digest and seen[0] is trace.apply_receipts[0] and len(seen) == 1
    assert trace.stage_errors[-1].evidence[0] == "commit_id='other'"


def test_verify_patch_digest_substitution_fails_closed() -> None:
    workspace = TransactionWorkspace()
    seen: list[ApplyReceipt] = []
    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        seen.append(receipt)
        return workspace.rollback(receipt)
    trace = transaction_loop(
        workspace,
        rollback=rollback,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, "wrong-digest", None, "ci", "green"
        ),
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:verify"
    assert trace.baseline_restored is True and workspace.state == {}
    assert trace.baseline_digest == trace.final_digest and seen[0] is trace.apply_receipts[0] and len(seen) == 1
    assert trace.stage_errors[-1].evidence[1] == "patch_digest='wrong-digest'"


def test_malformed_post_apply_failure_signal_is_compensated() -> None:
    """An invalid red signal must not escape after leaving an applied mutation."""
    workspace = TransactionWorkspace()

    def verify(receipt: ApplyReceipt) -> VerificationReceipt:
        malformed = FailureSignal(
            "test",
            "still red",
            ("app.py",),
            code=1,  # type: ignore[arg-type]
        )
        return VerificationReceipt(
            receipt.commit_id,
            receipt.patch_digest,
            malformed,
            "ci",
            "red",
        )

    trace = transaction_loop(
        workspace,
        diagnose=lambda _failure: "repair",
        fix=lambda _diagnosis: Patch("repair", payload("repair"), ("app.py",)),
        verify=verify,
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:verify"
    assert trace.applied_commits == ("c1",)
    assert trace.rolled_back == ("c1",)
    assert trace.baseline_restored is True
    assert trace.baseline_digest == trace.final_digest
    assert workspace.state == {}


def test_forged_failure_signal_is_fully_validated_after_apply() -> None:
    """Type identity alone must not let malformed nested fields cross verify."""
    workspace = TransactionWorkspace()
    malformed = object.__new__(FailureSignal)
    object.__setattr__(malformed, "kind", "test")
    object.__setattr__(malformed, "error_text", "still red")
    object.__setattr__(malformed, "affected_files", ("app.py", 1))
    object.__setattr__(malformed, "code", "MALFORMED")

    trace = transaction_loop(
        workspace,
        diagnose=lambda _failure: "repair",
        fix=lambda _diagnosis: Patch("repair", payload("repair"), ("app.py",)),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id,
            receipt.patch_digest,
            malformed,
            "ci",
            "red",
        ),
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:verify"
    assert trace.applied_commits == ("c1",)
    assert trace.rolled_back == ("c1",)
    assert trace.baseline_restored is True
    assert workspace.state == {}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kind", 1),
        ("error_text", 1),
        ("code", 1),
    ],
)
def test_failure_signal_rejects_non_string_scalars(field: str, value: object) -> None:
    """Every scalar used by failure identity must be validated at construction."""
    values: dict[str, object] = {
        "kind": "test",
        "error_text": "red",
        "affected_files": ("app.py",),
        "code": "RED",
    }
    values[field] = value

    with pytest.raises((TypeError, ValueError)):
        FailureSignal(**values)  # type: ignore[arg-type]


def test_initial_digest_failure_runs_no_roles() -> None:
    workspace = TransactionWorkspace()
    calls: list[str] = []
    loop = transaction_loop(workspace, digest=lambda: "", diagnose=lambda _: calls.append("diagnose") or "red")
    trace = loop.heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.baseline_digest is trace.final_digest is trace.baseline_restored is None and calls == []


def test_initial_digest_exception_runs_no_roles() -> None:
    workspace = TransactionWorkspace()
    calls: list[str] = []

    def digest() -> str:
        raise RuntimeError("digest backend unavailable")

    trace = transaction_loop(
        workspace, digest=digest, diagnose=lambda _: calls.append("diagnose") or "red"
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:state_check"
    assert trace.baseline_digest is trace.final_digest is trace.baseline_restored is None
    assert calls == []


@pytest.mark.parametrize("role", ["diagnose", "fix", "review", "verify"])
def test_pure_role_mutation_is_always_unaddressable(role: str) -> None:
    workspace = TransactionWorkspace()
    def mutate(*args):
        workspace.state[role] = True
        if role == "diagnose":
            return "RED"
        if role == "fix":
            return Patch("repair", payload("RED"), ("app.py",))
        if role == "review":
            return PatchReview(args[0].digest, True, "", ("policy=approved",))
        return VerificationReceipt(args[0].commit_id, args[0].patch_digest, None, "ci", "green")
    kwargs = {role: mutate}
    trace = transaction_loop(workspace, **kwargs).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stage_errors[-1].stage is HealStage[role.upper()]


def test_apply_exception_after_mutation_is_rollback_failed() -> None:
    workspace = TransactionWorkspace()
    def apply(_candidate: Patch):
        workspace.state["orphan"] = True
        raise RuntimeError("late failure")
    trace = transaction_loop(workspace, apply=apply).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF


def test_rollback_exception_continues_to_older_receipts() -> None:
    workspace = TransactionWorkspace()
    reds = iter([FailureSignal("test", "next", ("app.py",), "NEXT"), FailureSignal("test", "third", ("app.py",), "THIRD")])
    seen: list[str] = []
    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        seen.append(receipt.commit_id)
        if receipt.commit_id == "c2":
            raise RuntimeError("cannot revert c2")
        return workspace.rollback(receipt)
    loop = transaction_loop(workspace, verify=lambda receipt: VerificationReceipt(receipt.commit_id, receipt.patch_digest, next(reds), "ci", "red"), rollback=rollback)
    loop.stability = StabilityPolicy(max_rounds=2, max_radius_multiplier=4)
    trace = loop.heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert seen == ["c2", "c1"] and trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    rollback_errors = [error for error in trace.stage_errors if error.stage is HealStage.ROLLBACK]
    assert [error.message for error in rollback_errors] == ["cannot revert c2"]
    assert trace.stop_reason == "round_budget_exhausted"


def test_radius_has_priority_over_round_budget() -> None:
    workspace = TransactionWorkspace()
    next_failure = FailureSignal("test", "wide", ("a.py", "b.py", "c.py"), "WIDE")
    loop = transaction_loop(workspace, verify=lambda receipt: VerificationReceipt(receipt.commit_id, receipt.patch_digest, next_failure, "ci", "red"), fix=lambda _: Patch("repair", payload("x"), ("a.py",)))
    loop.stability = StabilityPolicy(max_rounds=1, max_radius_multiplier=2)
    trace = loop.heal(FailureSignal("test", "red", ("a.py",), "RED"))
    assert trace.status is HealStatus.ROLLED_BACK_REGRESSION and trace.stop_reason == "blast_radius_exceeded"


def test_post_apply_digest_failure_compensates_addressable_apply() -> None:
    """An unavailable post-apply proof must stop before an unverifiable green."""
    workspace = TransactionWorkspace()
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("post-apply digest unavailable")
        return workspace.digest()

    def apply(candidate: Patch) -> ApplyReceipt:
        nonlocal fail_next_digest
        receipt = workspace.apply(candidate)
        fail_next_digest = True
        return receipt

    trace = transaction_loop(workspace, digest=digest, apply=apply).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:state_check"
    assert trace.applied_commits == ("c1",)
    assert trace.rolled_back == ("c1",)
    assert trace.baseline_restored is True
    assert workspace.state == {}


def test_post_exception_digest_failure_is_not_observed_mutation() -> None:
    """Missing proof after an exception differs from a proven state change."""
    workspace = TransactionWorkspace()
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("post-diagnose digest unavailable")
        return workspace.digest()

    def diagnose(_failure: FailureSignal) -> str:
        nonlocal fail_next_digest
        fail_next_digest = True
        raise RuntimeError("diagnose failed")

    trace = transaction_loop(workspace, digest=digest, diagnose=diagnose).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.baseline_restored is True
    assert workspace.state == {}


def test_duplicate_apply_id_after_mutation_is_unaddressable() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    calls = 0

    def apply(candidate: Patch) -> ApplyReceipt:
        nonlocal calls
        calls += 1
        if calls == 1:
            return workspace.apply(candidate)
        workspace.state["orphan"] = True
        return ApplyReceipt("c1", candidate.digest, candidate.touches)

    trace = transaction_loop(
        workspace,
        apply=apply,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))

    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.applied_commits == ("c1",)
    assert trace.rolled_back == ("c1",)
    assert trace.baseline_restored is False


@pytest.mark.parametrize("check,evidence", [("", "green"), ("ci", "")])
def test_green_verification_requires_named_evidence(check: str, evidence: str) -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(
        workspace,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, None, check, evidence
        ),
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.baseline_restored is True and workspace.state == {}


def test_receipt_field_types_fail_closed() -> None:
    failure = FailureSignal("test", "red", ("app.py",), "RED")
    workspace = TransactionWorkspace()
    review_trace = transaction_loop(
        workspace,
        review=lambda patch, _: PatchReview(patch.digest, "yes", "", ("policy",)),
    ).heal(failure)
    assert review_trace.stop_reason == "stage_error:review"

    workspace = TransactionWorkspace()
    apply_trace = transaction_loop(
        workspace,
        apply=lambda patch: ApplyReceipt(1, patch.digest, patch.touches),  # type: ignore[arg-type]
    ).heal(failure)
    assert apply_trace.stop_reason == "stage_error:apply"

    workspace = TransactionWorkspace()
    verify_trace = transaction_loop(
        workspace,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, "red", "ci", "red"  # type: ignore[arg-type]
        ),
    ).heal(failure)
    assert verify_trace.stop_reason == "stage_error:verify"

    workspace = TransactionWorkspace()
    red = FailureSignal("test", "next", ("app.py",), "NEXT")
    rollback_seen: list[ApplyReceipt] = []
    returned_rollback: list[RollbackReceipt] = []

    def non_boolean_rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        rollback_seen.append(receipt)
        workspace.state = dict(workspace.snapshots[receipt.commit_id])
        returned = RollbackReceipt(
            receipt.commit_id,
            receipt.patch_digest,
            "yes",  # type: ignore[arg-type]
            "restored",
        )
        returned_rollback.append(returned)
        return returned

    rollback_trace = transaction_loop(
        workspace,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        rollback=non_boolean_rollback,
    )
    rollback_trace.stability = StabilityPolicy(max_rounds=1)
    result = rollback_trace.heal(failure)
    assert result.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert result.stop_reason == "round_budget_exhausted"
    assert result.baseline_restored is False
    assert workspace.state == {}
    assert result.baseline_digest == result.final_digest
    assert len(rollback_seen) == 1 and rollback_seen[0] is result.apply_receipts[0]
    assert result.rollback_receipts[0] is returned_rollback[0]
    assert result.stage_errors[-1].stage is HealStage.ROLLBACK
    assert result.stage_errors[-1].evidence == (
        "commit_id='c1'",
        f"patch_digest={result.apply_receipts[0].patch_digest!r}",
        "succeeded='yes'",
        "detail='restored'",
    )


def test_digest_failure_before_later_role_compensates_prior_applies() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    digest_phase = "normal"
    diagnose_calls: list[str] = []

    def digest() -> str:
        nonlocal digest_phase
        if digest_phase == "round-one-post-verify":
            digest_phase = "round-two-pre-diagnose"
        elif digest_phase == "round-two-pre-diagnose":
            digest_phase = "complete"
            raise RuntimeError("round-two pre-diagnose unavailable")
        return workspace.digest()

    def verify(receipt: ApplyReceipt) -> VerificationReceipt:
        nonlocal digest_phase
        digest_phase = "round-one-post-verify"
        return VerificationReceipt(receipt.commit_id, receipt.patch_digest, red, "ci", "red")

    def diagnose(failure: FailureSignal) -> str:
        diagnose_calls.append(failure.code)
        return failure.code

    trace = transaction_loop(
        workspace,
        digest=digest,
        verify=verify,
        diagnose=diagnose,
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert [(error.stage, error.round_no, error.message) for error in trace.stage_errors] == [
        (HealStage.STATE_CHECK, 2, "round-two pre-diagnose unavailable")
    ]
    assert diagnose_calls == ["FIRST"]
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:state_check"
    assert trace.applied_commits == ("c1",) and trace.rolled_back == ("c1",)
    assert trace.final_digest == trace.baseline_digest
    assert trace.baseline_restored is True and workspace.state == {}


def test_digest_failure_after_pure_role_records_state_check() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("post-review unavailable")
        return workspace.digest()

    def review(candidate: Patch, failure: FailureSignal) -> PatchReview:
        nonlocal fail_next_digest
        if failure.code == "SECOND":
            fail_next_digest = True
        return PatchReview(candidate.digest, True, "", ("policy=approved",))

    trace = transaction_loop(
        workspace,
        digest=digest,
        review=review,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert trace.stop_reason == "stage_error:state_check"
    assert len(trace.apply_receipts) == 1 and trace.baseline_restored is True
    assert workspace.state == {}


def test_digest_failure_during_apply_error_check_uses_final_proof() -> None:
    workspace = TransactionWorkspace()
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("post-apply-error unavailable")
        return workspace.digest()

    def apply(_patch: Patch) -> ApplyReceipt:
        nonlocal fail_next_digest
        fail_next_digest = True
        raise RuntimeError("atomic apply failed")

    trace = transaction_loop(workspace, digest=digest, apply=apply).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert {error.stage for error in trace.stage_errors} == {HealStage.APPLY, HealStage.STATE_CHECK}
    assert trace.baseline_restored is True and workspace.state == {}


def test_final_digest_failure_makes_restoration_unprovable() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    seen: list[ApplyReceipt] = []
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("final proof unavailable")
        return workspace.digest()

    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        nonlocal fail_next_digest
        seen.append(receipt)
        returned = workspace.rollback(receipt)
        fail_next_digest = True
        return returned

    trace = transaction_loop(
        workspace,
        digest=digest,
        review=lambda patch, failure: PatchReview(
            patch.digest, failure.code != "SECOND", "blocked", ("policy",)
        ),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        rollback=rollback,
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stop_reason == "review_rejected"
    assert trace.applied_commits == ("c1",) and trace.rolled_back == ("c1",)
    assert seen[0] is trace.apply_receipts[0] and len(seen) == 1
    assert workspace.state == {} and trace.final_digest is None
    assert trace.baseline_restored is False
    assert trace.stage_errors[-1].stage is HealStage.STATE_CHECK
    assert trace.stage_errors[-1].message == "final proof unavailable"


@pytest.mark.parametrize("stage", ["diagnose", "fix", "review"])
def test_stage_exceptions_before_apply_return_traces(stage: str) -> None:
    workspace = TransactionWorkspace()

    def boom(*_args: object) -> object:
        raise RuntimeError(stage)

    trace = transaction_loop(workspace, **{stage: boom}).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.apply_receipts == () and trace.baseline_restored is True


def test_apply_exception_with_unchanged_state_is_stage_error() -> None:
    workspace = TransactionWorkspace()
    trace = transaction_loop(
        workspace, apply=lambda _patch: (_ for _ in ()).throw(RuntimeError("atomic"))
    ).heal(FailureSignal("test", "red", ("app.py",), "RED"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.baseline_restored is True and workspace.state == {}


def test_apply_exception_compensates_older_valid_receipt() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    calls = 0

    def apply(candidate: Patch) -> ApplyReceipt:
        nonlocal calls
        calls += 1
        if calls == 1:
            return workspace.apply(candidate)
        raise RuntimeError("second apply failed atomically")

    trace = transaction_loop(
        workspace,
        apply=apply,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.applied_commits == ("c1",) and trace.rolled_back == ("c1",)
    assert trace.baseline_restored is True and workspace.state == {}


def test_verify_exception_restores_actual_state() -> None:
    workspace = TransactionWorkspace()

    def verify(_receipt: ApplyReceipt) -> VerificationReceipt:
        raise RuntimeError("verification crashed")

    trace = transaction_loop(workspace, verify=verify).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )
    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.baseline_digest == trace.final_digest and workspace.state == {}


def test_verify_exception_after_mutation_records_digest_evidence() -> None:
    """A crashing pure callback must leave evidence when it changes managed state."""
    workspace = TransactionWorkspace()

    def verify(_receipt: ApplyReceipt) -> VerificationReceipt:
        workspace.state["verify-orphan"] = True
        raise RuntimeError("verify exploded")

    trace = transaction_loop(workspace, verify=verify).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )

    before = hashlib.sha256(json.dumps({"RED": True}, sort_keys=True).encode()).hexdigest()
    after = hashlib.sha256(
        json.dumps({"RED": True, "verify-orphan": True}, sort_keys=True).encode()
    ).hexdigest()
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:verify"
    assert trace.applied_commits == ("c1",) and trace.rolled_back == ("c1",)
    assert trace.baseline_digest == trace.final_digest and workspace.state == {}
    assert trace.baseline_restored is False
    assert [(error.stage, error.round_no, error.message) for error in trace.stage_errors] == [
        (HealStage.VERIFY, 1, "verify exploded"),
        (HealStage.VERIFY, 1, "callback mutated managed state"),
    ]
    assert trace.stage_errors[-1].evidence == (
        f"before_digest={before!r}",
        f"after_digest={after!r}",
    )


def test_apply_exception_after_mutation_records_digest_evidence() -> None:
    """A failed apply must explain an unaddressable state mutation before rollback."""
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "second", ("app.py",), "SECOND")
    apply_calls = 0

    def apply(candidate: Patch) -> ApplyReceipt:
        nonlocal apply_calls
        apply_calls += 1
        if apply_calls == 1:
            return workspace.apply(candidate)
        workspace.state["orphan"] = True
        raise RuntimeError("apply exploded")

    trace = transaction_loop(
        workspace,
        apply=apply,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    ).heal(FailureSignal("test", "first", ("app.py",), "FIRST"))

    before = hashlib.sha256(json.dumps({"FIRST": True}, sort_keys=True).encode()).hexdigest()
    after = hashlib.sha256(
        json.dumps({"FIRST": True, "orphan": True}, sort_keys=True).encode()
    ).hexdigest()
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:apply"
    assert trace.applied_commits == ("c1",) and trace.rolled_back == ("c1",)
    assert trace.baseline_digest == trace.final_digest and workspace.state == {}
    assert trace.baseline_restored is False
    assert [(error.stage, error.round_no, error.message) for error in trace.stage_errors] == [
        (HealStage.APPLY, 2, "apply exploded"),
        (HealStage.APPLY, 2, "callback mutated managed state"),
    ]
    assert trace.stage_errors[-1].evidence == (
        f"before_digest={before!r}",
        f"after_digest={after!r}",
    )


@pytest.mark.parametrize("kind", ["failed", "wrong_id", "wrong_digest", "blank_detail"])
def test_failed_or_mismatched_rollback_receipt_is_not_proof(kind: str) -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "next", ("app.py",), "NEXT")

    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        workspace.state = dict(workspace.snapshots[receipt.commit_id])
        if kind == "failed":
            return RollbackReceipt(receipt.commit_id, receipt.patch_digest, False, "failed")
        if kind == "wrong_id":
            return RollbackReceipt("other", receipt.patch_digest, True, "restored")
        if kind == "wrong_digest":
            return RollbackReceipt(receipt.commit_id, "other", True, "restored")
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "")

    trace = transaction_loop(
        workspace,
        rollback=rollback,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    )
    trace.stability = StabilityPolicy(max_rounds=1)
    result = trace.heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert result.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert result.baseline_restored is False
    assert result.stop_reason == "round_budget_exhausted"
    assert workspace.state == {} and result.final_digest == result.baseline_digest
    assert len(result.rollback_receipts) == 1
    assert result.rollback_receipts[0].commit_id == (
        "other" if kind == "wrong_id" else "c1"
    )
    assert result.stage_errors[-1].stage is HealStage.ROLLBACK
    returned = result.rollback_receipts[0]
    assert result.stage_errors[-1].evidence == (
        f"commit_id={returned.commit_id!r}",
        f"patch_digest={returned.patch_digest!r}",
        f"succeeded={returned.succeeded!r}",
        f"detail={returned.detail!r}",
    )


def test_invalid_newest_rollback_receipt_retains_identity_and_order() -> None:
    workspace = TransactionWorkspace()
    failures = iter(
        [
            FailureSignal("test", "second", ("app.py",), "SECOND"),
            FailureSignal("test", "third", ("app.py",), "THIRD"),
        ]
    )
    returned: list[RollbackReceipt] = []

    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        workspace.state = dict(workspace.snapshots[receipt.commit_id])
        item = RollbackReceipt(
            receipt.commit_id,
            "wrong-digest" if receipt.commit_id == "c2" else receipt.patch_digest,
            True,
            "restored",
        )
        returned.append(item)
        return item

    loop = transaction_loop(
        workspace,
        rollback=rollback,
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, next(failures), "ci", "red"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    )
    loop.stability = StabilityPolicy(max_rounds=2, max_radius_multiplier=4)
    trace = loop.heal(FailureSignal("test", "first", ("app.py",), "FIRST"))

    assert trace.rollback_receipts[0] is returned[0]
    assert trace.rollback_receipts[1] is returned[1]
    assert trace.rolled_back == ("c2", "c1")
    assert trace.stage_errors[-1].stage is HealStage.ROLLBACK
    assert trace.stage_errors[-1].evidence == (
        "commit_id='c2'", "patch_digest='wrong-digest'", "succeeded=True", "detail='restored'"
    )
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stop_reason == "round_budget_exhausted"
    assert workspace.state == {} and trace.final_digest == trace.baseline_digest
    assert trace.baseline_restored is False


def test_noop_rollback_cannot_claim_restoration() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "next", ("app.py",), "NEXT")
    loop = transaction_loop(
        workspace,
        rollback=lambda receipt: RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "claimed restore"),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
    )
    loop.stability = StabilityPolicy(max_rounds=1)
    trace = loop.heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.baseline_restored is False and trace.final_digest != trace.baseline_digest


def test_description_and_path_order_cannot_evade_no_progress() -> None:
    workspace = TransactionWorkspace()
    same = FailureSignal("test", "red", ("a.py", "b.py"), "SAME")
    descriptions = iter(["first label", "second label"])
    loop = transaction_loop(
        workspace,
        fix=lambda _code: Patch(next(descriptions), payload("same"), ("b.py", "a.py")),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, same, "ci", "red"
        ),
    )
    trace = loop.heal(same)
    assert trace.status is HealStatus.ROLLED_BACK_NO_PROGRESS
    assert trace.applied_commits == ("c1",) and trace.baseline_restored is True


def test_rollback_failure_preserves_original_stop_reason() -> None:
    workspace = TransactionWorkspace()
    red = FailureSignal("test", "next", ("app.py",), "NEXT")
    loop = transaction_loop(
        workspace,
        review=lambda patch, failure: PatchReview(
            patch.digest, failure.code != "NEXT", "blocked", ("policy",)
        ),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, red, "ci", "red"
        ),
        rollback=lambda receipt: RollbackReceipt(
            receipt.commit_id, receipt.patch_digest, False, "rollback failed"
        ),
        fix=lambda code: Patch("repair", payload(code), ("app.py",)),
    )
    trace = loop.heal(FailureSignal("test", "first", ("app.py",), "FIRST"))
    assert trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert trace.stop_reason == "review_rejected"


def test_same_signature_radius_expansion_still_stops() -> None:
    workspace = TransactionWorkspace()
    same_but_wide = FailureSignal("test", "same class", ("a.py", "b.py", "c.py"), "SAME")
    loop = transaction_loop(
        workspace,
        fix=lambda code: Patch("repair", payload(code), ("a.py",)),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, same_but_wide, "ci", "red"
        ),
    )
    trace = loop.heal(FailureSignal("test", "same class", ("a.py",), "SAME"))
    assert trace.status is HealStatus.ROLLED_BACK_REGRESSION
    assert trace.stop_reason == "blast_radius_exceeded"


def test_equal_size_disjoint_failures_accumulate_radius() -> None:
    workspace = TransactionWorkspace()
    failures = iter(
        [
            FailureSignal("test", "second", ("b.py",), "SECOND"),
            FailureSignal("test", "third", ("c.py", "d.py"), "THIRD"),
        ]
    )
    loop = transaction_loop(
        workspace,
        fix=lambda code: Patch("repair", payload(code), ("a.py",)),
        verify=lambda receipt: VerificationReceipt(
            receipt.commit_id, receipt.patch_digest, next(failures), "ci", "red"
        ),
    )
    trace = loop.heal(FailureSignal("test", "first", ("a.py",), "FIRST"))
    assert trace.status is HealStatus.ROLLED_BACK_REGRESSION
    assert trace.rolled_back == ("c2", "c1")
    assert trace.baseline_restored is True and workspace.state == {}


def test_invalid_apply_and_post_digest_failure_retain_both_errors() -> None:
    """A state-check failure cannot erase semantic receipt evidence."""
    workspace = TransactionWorkspace()
    returned = ApplyReceipt("c2", "wrong-digest", ("wrong.py",))
    seen: list[ApplyReceipt] = []
    fail_next_digest = False

    def digest() -> str:
        nonlocal fail_next_digest
        if fail_next_digest:
            fail_next_digest = False
            raise RuntimeError("post-apply digest unavailable")
        return workspace.digest()

    def apply(_patch: Patch) -> ApplyReceipt:
        nonlocal fail_next_digest
        workspace.snapshots["c2"] = dict(workspace.state)
        workspace.state["changed"] = True
        fail_next_digest = True
        return returned

    def rollback(receipt: ApplyReceipt) -> RollbackReceipt:
        seen.append(receipt)
        workspace.state = dict(workspace.snapshots[receipt.commit_id])
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "restored")

    trace = transaction_loop(workspace, digest=digest, apply=apply, rollback=rollback).heal(
        FailureSignal("test", "red", ("app.py",), "RED")
    )

    assert [error.stage for error in trace.stage_errors] == [
        HealStage.APPLY,
        HealStage.STATE_CHECK,
    ]
    assert trace.stage_errors[0].evidence == (
        "commit_id='c2'", "patch_digest='wrong-digest'", "changed_files=('wrong.py',)"
    )
    assert trace.apply_receipts == (returned,) and trace.apply_receipts[0] is returned
    assert seen[0] is returned and trace.rolled_back == ("c2",)
    assert trace.stop_reason == "stage_error:state_check"
    assert trace.baseline_digest == trace.final_digest
    assert trace.baseline_restored is True and workspace.state == {}
