"""Self-Heal Loop reference implementation.

Self-Heal Loop is the Reflect x Loop pattern. A deterministic failure signal
drives a bounded repair transaction:

    diagnose -> draft patch -> review -> atomic apply -> verify -> repeat/stop

Unlike Generator-Critic, repetition is structural here. The output is already
broken, and the loop keeps working until an external signal turns green or a
stop policy takes control. Every non-success terminal path attempts compensation;
the trace claims baseline restoration only when receipts and a final digest prove it.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import PurePosixPath
from typing import Callable, Iterable


class HealStatus(str, Enum):
    FIXED = "fixed"
    BLOCKED_BY_CRITIC = "blocked_by_critic"
    ROLLED_BACK_REGRESSION = "rolled_back_regression"
    ROLLED_BACK_NO_PROGRESS = "rolled_back_no_progress"
    MAX_ROUNDS_HUMAN_HANDOFF = "max_rounds_human_handoff"
    STAGE_ERROR_HUMAN_HANDOFF = "stage_error_human_handoff"
    ROLLBACK_FAILED_HUMAN_HANDOFF = "rollback_failed_human_handoff"


class HealStage(str, Enum):
    STATE_CHECK = "state_check"
    DIAGNOSE = "diagnose"
    FIX = "fix"
    REVIEW = "review"
    APPLY = "apply"
    VERIFY = "verify"
    ROLLBACK = "rollback"


def _canonical_paths(paths: Iterable[str]) -> tuple[str, ...]:
    if isinstance(paths, (str, bytes)):
        raise TypeError("paths must be an iterable of path strings")
    canonical: list[str] = []
    for raw in tuple(paths):
        if not isinstance(raw, str):
            raise TypeError("paths must contain only strings")
        value = raw.strip()
        if not value:
            raise ValueError("paths must be nonblank")
        if "\\" in value or re.match(r"^[A-Za-z]:", value):
            raise ValueError(f"path must use relative POSIX syntax: {raw!r}")
        segments = value.split("/")
        if any(segment in {"", ".", ".."} for segment in segments):
            raise ValueError(f"path must already be canonical: {raw!r}")
        path = PurePosixPath(value)
        if path.is_absolute():
            raise ValueError(f"path must be relative: {raw!r}")
        canonical.append(path.as_posix())
    return tuple(sorted(set(canonical)))


def _snapshot_strings(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) for value in result):
        raise TypeError(f"{field_name} must contain only strings")
    return result


def _require_nonblank(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a nonblank string")
    return value


@dataclass(frozen=True)
class FailureSignal:
    """One deterministic red light from test, lint, build, or CI."""

    kind: str
    error_text: str
    affected_files: tuple[str, ...] = ()
    code: str = ""

    def __post_init__(self) -> None:
        _require_nonblank(self.kind, "kind")
        _require_nonblank(self.error_text, "error_text")
        if not isinstance(self.code, str):
            raise TypeError("code must be a string")
        object.__setattr__(self, "affected_files", _canonical_paths(self.affected_files))

    @property
    def signature(self) -> str:
        # A supplied code is the strongest identity. Otherwise normalize volatile
        # numbers and whitespace so counts and line numbers do not create a new
        # failure class on every run.
        identity = self.code.strip()
        if not identity:
            normalized = re.sub(r"\b\d+\b", "#", self.error_text.lower())
            identity = " ".join(normalized.split())[:240]
        key = f"{self.kind}|{identity}"
        return hashlib.sha256(key.encode()).hexdigest()[:12]


def _valid_failure_signal(value: object) -> bool:
    """Validate a nested signal even if a caller bypassed dataclass construction."""
    if not isinstance(value, FailureSignal):
        return False
    try:
        normalized = FailureSignal(
            value.kind,
            value.error_text,
            value.affected_files,
            value.code,
        )
    except (TypeError, ValueError):
        return False
    return (
        value.kind == normalized.kind
        and value.error_text == normalized.error_text
        and value.affected_files == normalized.affected_files
        and value.code == normalized.code
    )


@dataclass(frozen=True)
class Patch:
    """A proposed atomic change."""

    description: str
    payload: str
    touches: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonblank(self.payload, "payload")
        try:
            self.payload.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("payload must be valid UTF-8") from exc
        object.__setattr__(self, "touches", _canonical_paths(self.touches))

    @property
    def digest(self) -> str:
        frame = json.dumps(
            {"payload": self.payload, "touches": self.touches},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(frame.encode("utf-8")).hexdigest()

    @property
    def fingerprint(self) -> str:
        return self.digest

    @property
    def touches_tests(self) -> bool:
        for raw_path in self.touches:
            path = PurePosixPath(raw_path)
            if (
                "tests" in path.parts
                or path.name.startswith("test_")
                or path.name.endswith("_test.py")
            ):
                return True
        return False


@dataclass(frozen=True)
class PatchReview:
    patch_digest: str
    approved: bool
    reason: str
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", _snapshot_strings(self.evidence, "evidence"))


@dataclass(frozen=True)
class ApplyReceipt:
    commit_id: str
    patch_digest: str
    changed_files: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "changed_files", _canonical_paths(self.changed_files))


@dataclass(frozen=True)
class VerificationReceipt:
    commit_id: str
    patch_digest: str
    failure: FailureSignal | None
    check: str
    evidence: str


@dataclass(frozen=True)
class RollbackReceipt:
    commit_id: str
    patch_digest: str
    succeeded: bool
    detail: str


@dataclass(frozen=True)
class StageError:
    stage: HealStage
    round_no: int | None
    exception_type: str
    message: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        evidence = _snapshot_strings(self.evidence, "evidence")
        if len(evidence) > 8 or any(not value.strip() for value in evidence):
            raise ValueError("evidence must contain zero to eight nonblank strings")
        object.__setattr__(self, "evidence", evidence)


@dataclass(frozen=True)
class StabilityPolicy:
    """Stop conditions that bound the repair transaction."""

    max_rounds: int = 3
    max_radius_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")
        if self.max_radius_multiplier < 1.0:
            raise ValueError("max_radius_multiplier must be at least 1.0")


@dataclass(frozen=True)
class HealRound:
    round_no: int
    failure: FailureSignal
    diagnosis: str
    patch: Patch
    patch_review: PatchReview | None = None
    apply_receipt: ApplyReceipt | None = None
    verification_receipt: VerificationReceipt | None = None


@dataclass(frozen=True)
class HealTrace:
    status: HealStatus
    stop_reason: str
    rounds: tuple[HealRound, ...]
    apply_receipts: tuple[ApplyReceipt, ...]
    rollback_receipts: tuple[RollbackReceipt, ...]
    stage_errors: tuple[StageError, ...]
    baseline_digest: str | None
    final_digest: str | None
    baseline_restored: bool | None

    def __post_init__(self) -> None:
        _require_nonblank(self.stop_reason, "stop_reason")
        for name in ("rounds", "apply_receipts", "rollback_receipts", "stage_errors"):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    @property
    def applied_commits(self) -> tuple[str, ...]:
        return tuple(item.commit_id for item in self.apply_receipts)

    @property
    def rolled_back(self) -> tuple[str, ...]:
        return tuple(item.commit_id for item in self.rollback_receipts)


DiagnoseFn = Callable[[FailureSignal], str]
FixFn = Callable[[str], Patch]
ReviewFn = Callable[[Patch, FailureSignal], PatchReview]
ApplyFn = Callable[[Patch], ApplyReceipt]
VerifyFn = Callable[[ApplyReceipt], VerificationReceipt]
RollbackFn = Callable[[ApplyReceipt], RollbackReceipt]
StateDigestFn = Callable[[], str]


class SelfHealLoop:
    """Run a bounded, rollback-safe repair loop."""

    def __init__(
        self,
        *,
        diagnose: DiagnoseFn,
        fix: FixFn,
        review: ReviewFn,
        apply: ApplyFn,
        verify: VerifyFn,
        rollback: RollbackFn,
        state_digest: StateDigestFn,
        stability: StabilityPolicy | None = None,
    ) -> None:
        self.diagnose = diagnose
        self.fix = fix
        self.review = review
        self.apply = apply
        self.verify = verify
        self.rollback = rollback
        self.state_digest = state_digest
        self.stability = stability or StabilityPolicy()

    def _read_state_digest(self) -> str:
        return _require_nonblank(self.state_digest(), "state_digest")

    def _stage_error(
        self,
        stage: HealStage,
        round_no: int | None,
        exc: BaseException,
        evidence: Iterable[str] = (),
    ) -> StageError:
        values = tuple(value for value in evidence if isinstance(value, str) and value.strip())[:8]
        return StageError(stage, round_no, type(exc).__name__, str(exc) or repr(exc), values)

    def _receipt_evidence(self, receipt: object, fields: Iterable[str]) -> tuple[str, ...]:
        return tuple(f"{name}={getattr(receipt, name, '<missing>')!r}" for name in fields)

    def _check_digest(
        self, errors: list[StageError], round_no: int | None
    ) -> str | None:
        try:
            return self._read_state_digest()
        except Exception as exc:  # the callback owns the digest implementation
            errors.append(self._stage_error(HealStage.STATE_CHECK, round_no, exc))
            return None

    def _error_reason(self, errors: list[StageError], stage: HealStage) -> str:
        last = errors[-1].stage if errors else stage
        return f"stage_error:{last.value}"

    def _mutation_error(
        self, stage: HealStage, round_no: int, before: str, after: str
    ) -> StageError:
        return self._stage_error(
            stage,
            round_no,
            RuntimeError("callback mutated managed state"),
            (f"before_digest={before!r}", f"after_digest={after!r}"),
        )

    def _pure_call(
        self,
        stage: HealStage,
        round_no: int,
        callback: Callable[..., object],
        args: tuple[object, ...],
        errors: list[StageError],
    ) -> tuple[object | None, bool, bool]:
        before = self._check_digest(errors, round_no)
        if before is None:
            return None, False, False
        try:
            result = callback(*args)
        except Exception as exc:
            errors.append(self._stage_error(stage, round_no, exc))
            after = self._check_digest(errors, round_no)
            mutated = after is not None and after != before
            if mutated:
                errors.append(self._mutation_error(stage, round_no, before, after))
            return None, mutated, False
        after = self._check_digest(errors, round_no)
        if after is None:
            return result, False, False
        if after != before:
            errors.append(self._stage_error(stage, round_no, RuntimeError("callback mutated managed state")))
            return result, True, False
        return result, False, True

    def _validate_review(self, receipt: object, patch: Patch) -> tuple[bool, tuple[str, ...]]:
        fields = ("patch_digest", "approved", "reason", "evidence")
        if not isinstance(receipt, PatchReview):
            return False, self._receipt_evidence(receipt, fields)
        valid = (
            receipt.patch_digest == patch.digest
            and type(receipt.approved) is bool
            and isinstance(receipt.evidence, tuple)
            and any(isinstance(item, str) and item.strip() for item in receipt.evidence)
            and (receipt.approved or (isinstance(receipt.reason, str) and receipt.reason.strip()))
        )
        return valid, self._receipt_evidence(receipt, fields)

    def _validate_apply(self, receipt: object, patch: Patch, seen: set[str]) -> tuple[bool, bool, tuple[str, ...]]:
        fields = ("commit_id", "patch_digest", "changed_files")
        if not isinstance(receipt, ApplyReceipt):
            return False, False, self._receipt_evidence(receipt, fields)
        addressable = isinstance(receipt.commit_id, str) and bool(receipt.commit_id.strip()) and receipt.commit_id not in seen
        valid = addressable and receipt.patch_digest == patch.digest and receipt.changed_files == patch.touches
        return valid, addressable, self._receipt_evidence(receipt, fields)

    def _validate_verify(self, receipt: object, apply: ApplyReceipt) -> tuple[bool, tuple[str, ...]]:
        fields = ("commit_id", "patch_digest", "failure", "check", "evidence")
        if not isinstance(receipt, VerificationReceipt):
            return False, self._receipt_evidence(receipt, fields)
        valid = (
            receipt.commit_id == apply.commit_id
            and receipt.patch_digest == apply.patch_digest
            and (receipt.failure is None or _valid_failure_signal(receipt.failure))
            and isinstance(receipt.check, str) and bool(receipt.check.strip())
            and isinstance(receipt.evidence, str) and bool(receipt.evidence.strip())
        )
        return valid, self._receipt_evidence(receipt, fields)

    def _compensate(
        self,
        applies: list[ApplyReceipt],
        errors: list[StageError],
    ) -> tuple[list[RollbackReceipt], bool]:
        receipts: list[RollbackReceipt] = []
        complete = True
        for apply_receipt in reversed(applies):
            try:
                returned = self.rollback(apply_receipt)
            except Exception as exc:
                errors.append(self._stage_error(HealStage.ROLLBACK, None, exc))
                complete = False
                continue
            if not isinstance(returned, RollbackReceipt):
                errors.append(self._stage_error(HealStage.ROLLBACK, None, TypeError("rollback must return RollbackReceipt"), self._receipt_evidence(returned, ("commit_id", "patch_digest", "succeeded", "detail"))))
                complete = False
                continue
            receipts.append(returned)
            valid = (
                returned.commit_id == apply_receipt.commit_id
                and returned.patch_digest == apply_receipt.patch_digest
                and returned.succeeded is True
                and isinstance(returned.detail, str)
                and bool(returned.detail.strip())
            )
            if not valid:
                errors.append(self._stage_error(HealStage.ROLLBACK, None, ValueError("invalid rollback receipt"), self._receipt_evidence(returned, ("commit_id", "patch_digest", "succeeded", "detail"))))
                complete = False
        return receipts, complete and len(receipts) == len(applies)

    def _finish_non_success(
        self,
        status: HealStatus,
        reason: str,
        rounds: list[HealRound],
        applies: list[ApplyReceipt],
        errors: list[StageError],
        baseline: str,
        unaddressable: bool,
    ) -> HealTrace:
        rollbacks, complete = self._compensate(applies, errors)
        final = self._check_digest(errors, None)
        restored = complete and not unaddressable and final == baseline
        terminal = status if restored else HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
        return HealTrace(terminal, reason, tuple(rounds), tuple(applies), tuple(rollbacks), tuple(errors), baseline, final, restored)

    def heal(self, failure: FailureSignal) -> HealTrace:
        errors: list[StageError] = []
        try:
            baseline = self._read_state_digest()
        except Exception as exc:
            errors.append(self._stage_error(HealStage.STATE_CHECK, None, exc))
            return HealTrace(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:state_check", (), (), (), tuple(errors), None, None, None)
        rounds: list[HealRound] = []
        applies: list[ApplyReceipt] = []
        unaddressable = False
        baseline_radius = max(len(failure.affected_files), 1)
        radius_files = set(failure.affected_files)
        attempts: set[tuple[str, str]] = set()
        commit_ids: set[str] = set()
        current_failure = failure

        for round_no in range(1, self.stability.max_rounds + 1):
            diagnosis, mutated, ok = self._pure_call(HealStage.DIAGNOSE, round_no, self.diagnose, (current_failure,), errors)
            unaddressable |= mutated
            if not ok or not isinstance(diagnosis, str):
                if ok:
                    errors.append(self._stage_error(HealStage.DIAGNOSE, round_no, TypeError("diagnose must return str")))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, self._error_reason(errors, HealStage.DIAGNOSE), rounds, applies, errors, baseline, unaddressable)
            patch, mutated, ok = self._pure_call(HealStage.FIX, round_no, self.fix, (diagnosis,), errors)
            unaddressable |= mutated
            if not ok or not isinstance(patch, Patch):
                if ok:
                    errors.append(self._stage_error(HealStage.FIX, round_no, TypeError("fix must return Patch")))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, self._error_reason(errors, HealStage.FIX), rounds, applies, errors, baseline, unaddressable)
            rounds.append(HealRound(round_no, current_failure, diagnosis, patch))
            attempt = (current_failure.signature, patch.digest)

            if attempt in attempts:
                return self._finish_non_success(HealStatus.ROLLED_BACK_NO_PROGRESS, "no_progress_same_failure_and_patch", rounds, applies, errors, baseline, unaddressable)
            attempts.add(attempt)

            review, mutated, ok = self._pure_call(HealStage.REVIEW, round_no, self.review, (patch, current_failure), errors)
            unaddressable |= mutated
            if not ok or not isinstance(review, PatchReview):
                if ok:
                    errors.append(self._stage_error(HealStage.REVIEW, round_no, TypeError("review must return PatchReview"), self._receipt_evidence(review, ("patch_digest", "approved", "reason", "evidence"))))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, self._error_reason(errors, HealStage.REVIEW), rounds, applies, errors, baseline, unaddressable)
            valid, evidence = self._validate_review(review, patch)
            rounds[-1] = replace(rounds[-1], patch_review=review)
            if not valid:
                errors.append(self._stage_error(HealStage.REVIEW, round_no, ValueError("invalid review receipt"), evidence))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:review", rounds, applies, errors, baseline, unaddressable)
            if not review.approved:
                return self._finish_non_success(HealStatus.BLOCKED_BY_CRITIC, "review_rejected", rounds, applies, errors, baseline, unaddressable)

            before = self._check_digest(errors, round_no)
            if before is None:
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:state_check", rounds, applies, errors, baseline, unaddressable)
            try:
                apply_receipt = self.apply(patch)
            except Exception as exc:
                errors.append(self._stage_error(HealStage.APPLY, round_no, exc))
                after = self._check_digest(errors, round_no)
                mutated = after is not None and after != before
                if mutated:
                    errors.append(self._mutation_error(HealStage.APPLY, round_no, before, after))
                unaddressable |= mutated
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:apply", rounds, applies, errors, baseline, unaddressable)
            valid, addressable, evidence = self._validate_apply(apply_receipt, patch, commit_ids)
            if addressable and isinstance(apply_receipt, ApplyReceipt):
                applies.append(apply_receipt)
                commit_ids.add(apply_receipt.commit_id)
                rounds[-1] = replace(rounds[-1], apply_receipt=apply_receipt)
            if not valid:
                errors.append(self._stage_error(HealStage.APPLY, round_no, ValueError("invalid apply receipt"), evidence))
            after = self._check_digest(errors, round_no)
            if not valid:
                if not addressable and after is not None and after != before:
                    unaddressable = True
                if after is None:
                    return self._finish_non_success(
                        HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
                        "stage_error:state_check",
                        rounds,
                        applies,
                        errors,
                        baseline,
                        unaddressable,
                    )
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:apply", rounds, applies, errors, baseline, unaddressable)
            if after is None:
                return self._finish_non_success(
                    HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
                    "stage_error:state_check",
                    rounds,
                    applies,
                    errors,
                    baseline,
                    unaddressable,
                )
            assert isinstance(apply_receipt, ApplyReceipt)
            radius_files.update(patch.touches)
            verified, mutated, ok = self._pure_call(HealStage.VERIFY, round_no, self.verify, (apply_receipt,), errors)
            unaddressable |= mutated
            if not ok or not isinstance(verified, VerificationReceipt):
                if ok:
                    errors.append(self._stage_error(HealStage.VERIFY, round_no, TypeError("verify must return VerificationReceipt"), self._receipt_evidence(verified, ("commit_id", "patch_digest", "failure", "check", "evidence"))))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, self._error_reason(errors, HealStage.VERIFY), rounds, applies, errors, baseline, unaddressable)
            valid, evidence = self._validate_verify(verified, apply_receipt)
            rounds[-1] = replace(rounds[-1], verification_receipt=verified)
            if not valid:
                errors.append(self._stage_error(HealStage.VERIFY, round_no, ValueError("invalid verification receipt"), evidence))
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:verify", rounds, applies, errors, baseline, unaddressable)
            if verified.failure is None:
                final = self._check_digest(errors, round_no)
                if final is not None:
                    return HealTrace(HealStatus.FIXED, "verification_passed", tuple(rounds), tuple(applies), (), tuple(errors), baseline, final, None)
                return self._finish_non_success(HealStatus.STAGE_ERROR_HUMAN_HANDOFF, "stage_error:state_check", rounds, applies, errors, baseline, unaddressable)
            current_failure = verified.failure
            radius_files.update(current_failure.affected_files)
            if len(radius_files) > baseline_radius * self.stability.max_radius_multiplier:
                return self._finish_non_success(HealStatus.ROLLED_BACK_REGRESSION, "blast_radius_exceeded", rounds, applies, errors, baseline, unaddressable)
            if round_no == self.stability.max_rounds:
                return self._finish_non_success(HealStatus.MAX_ROUNDS_HUMAN_HANDOFF, "round_budget_exhausted", rounds, applies, errors, baseline, unaddressable)
        return self._finish_non_success(HealStatus.MAX_ROUNDS_HUMAN_HANDOFF, "round_budget_exhausted", rounds, applies, errors, baseline, unaddressable)


def propose_guard(
    signature: str,
    runs_seen: list[str] | None = None,
    min_recurrence: int = 2,
    *,
    months_seen: list[str] | None = None,
) -> dict | None:
    """Propose a recurring failure class as a regression guard.

    ``months_seen`` remains accepted for compatibility with the first payroll lab.
    The returned guard is only proposed; a human promotes it to enforced.
    """

    observations = runs_seen if runs_seen is not None else (months_seen or [])
    if len(set(observations)) < min_recurrence:
        return None
    return {
        "kind": "regression_test",
        "trigger_signature": signature,
        "seen_in": observations,
        "status": "proposed",
    }
