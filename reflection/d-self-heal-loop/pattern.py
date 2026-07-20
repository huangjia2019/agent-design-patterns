"""Self-Heal Loop reference implementation.

Self-Heal Loop is the Reflect x Loop pattern. A deterministic failure signal
drives a bounded repair transaction:

    diagnose -> draft patch -> review -> atomic apply -> verify -> repeat/stop

Unlike Generator-Critic, repetition is structural here. The output is already
broken, and the loop keeps working until an external signal turns green or a
stop policy takes control. Every non-success terminal path restores the baseline
before handing the trace to a human.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath
from typing import Callable


class HealStatus(str, Enum):
    FIXED = "fixed"
    BLOCKED_BY_CRITIC = "blocked_by_critic"
    ROLLED_BACK_REGRESSION = "rolled_back_regression"
    ROLLED_BACK_NO_PROGRESS = "rolled_back_no_progress"
    MAX_ROUNDS_HUMAN_HANDOFF = "max_rounds_human_handoff"


@dataclass(frozen=True)
class FailureSignal:
    """One deterministic red light from test, lint, build, or CI."""

    kind: str
    error_text: str
    affected_files: list[str] = field(default_factory=list)
    code: str = ""

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


@dataclass(frozen=True)
class Patch:
    """A proposed atomic change."""

    description: str
    touches: list[str]

    @property
    def fingerprint(self) -> str:
        key = f"{self.description}|{'|'.join(sorted(self.touches))}"
        return hashlib.sha256(key.encode()).hexdigest()[:12]

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
    commit_id: str | None
    critic_verdict: str
    verification: FailureSignal | None = None


@dataclass
class HealTrace:
    rounds: list[HealRound] = field(default_factory=list)
    applied_commits: list[str] = field(default_factory=list)
    rolled_back: list[str] = field(default_factory=list)
    status: HealStatus | None = None

    @property
    def baseline_restored(self) -> bool:
        return self.rolled_back == list(reversed(self.applied_commits))


DiagnoseFn = Callable[[FailureSignal], str]
FixFn = Callable[[str], Patch]
# Empty string approves. Any non-empty reason blocks the patch before apply.
CriticFn = Callable[[Patch, FailureSignal], str]
ApplyFn = Callable[[Patch], str]
VerifyFn = Callable[[], FailureSignal | None]
RollbackFn = Callable[[str], None]


class SelfHealLoop:
    """Run a bounded, rollback-safe repair loop."""

    def __init__(
        self,
        diagnose: DiagnoseFn,
        fix: FixFn,
        critic: CriticFn,
        apply: ApplyFn,
        verify: VerifyFn,
        rollback: RollbackFn,
        max_rounds: int = 3,
        stability: StabilityPolicy | None = None,
    ) -> None:
        self.diagnose = diagnose
        self.fix = fix
        self.critic = critic
        self.apply = apply
        self.verify = verify
        self.rollback = rollback
        self.stability = stability or StabilityPolicy(max_rounds=max_rounds)

    def _rollback_all(self, trace: HealTrace) -> None:
        rolled_back = set(trace.rolled_back)
        for commit_id in reversed(trace.applied_commits):
            if commit_id in rolled_back:
                continue
            self.rollback(commit_id)
            trace.rolled_back.append(commit_id)

    def heal(self, failure: FailureSignal) -> HealTrace:
        trace = HealTrace()
        baseline_radius = max(len(failure.affected_files), 1)
        attempts: set[tuple[str, str]] = set()

        for round_no in range(1, self.stability.max_rounds + 1):
            diagnosis = self.diagnose(failure)
            patch = self.fix(diagnosis)
            attempt = (failure.signature, patch.fingerprint)

            if attempt in attempts:
                trace.rounds.append(
                    HealRound(
                        round_no,
                        failure,
                        diagnosis,
                        patch,
                        None,
                        "blocked:no_progress_same_failure_and_patch",
                    )
                )
                self._rollback_all(trace)
                trace.status = HealStatus.ROLLED_BACK_NO_PROGRESS
                return trace
            attempts.add(attempt)

            verdict = self.critic(patch, failure)
            if verdict:
                trace.rounds.append(
                    HealRound(
                        round_no,
                        failure,
                        diagnosis,
                        patch,
                        None,
                        f"blocked:{verdict}",
                    )
                )
                self._rollback_all(trace)
                trace.status = HealStatus.BLOCKED_BY_CRITIC
                return trace

            commit_id = self.apply(patch)
            trace.applied_commits.append(commit_id)
            new_failure = self.verify()
            trace.rounds.append(
                HealRound(
                    round_no,
                    failure,
                    diagnosis,
                    patch,
                    commit_id,
                    "approved",
                    new_failure,
                )
            )

            if new_failure is None:
                trace.status = HealStatus.FIXED
                return trace

            radius_limit = baseline_radius * self.stability.max_radius_multiplier
            changed_failure = new_failure.signature != failure.signature
            if changed_failure and len(new_failure.affected_files) > radius_limit:
                self._rollback_all(trace)
                trace.status = HealStatus.ROLLED_BACK_REGRESSION
                return trace

            failure = new_failure

        self._rollback_all(trace)
        trace.status = HealStatus.MAX_ROUNDS_HUMAN_HANDOFF
        return trace


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
