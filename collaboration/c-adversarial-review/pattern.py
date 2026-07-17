"""Adversarial Review pattern.

A candidate artifact crosses a release boundary only after independent reviewers
return machine-readable objections against a versioned rubric. Reviewers must
return objections, never endorsement. A deterministic gate combines declared
rule coverage, reviewer health, and open blockers.

The shared collaboration chain remains:

``TaskContract -> ArtifactEnvelope -> ReviewReceipt -> AcceptanceReceipt``

This module owns the loop topology: review the current artifact, revise only
when blockers exist, then review the new artifact. Every receipt stays bound to
one contract digest, artifact id, content fingerprint, revision, and rubric
version. The final round never creates an unreviewed replacement artifact.
"""
from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Awaitable, Generic, Protocol, TypeVar


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from collaboration.boundary_contract import (  # noqa: E402
    AcceptanceDecision,
    AcceptanceReceipt,
    ArtifactEnvelope,
    Finding,
    FindingSeverity,
    TaskContract,
)


PayloadT = TypeVar("PayloadT")
Severity = FindingSeverity


class Outcome(str, Enum):
    CONFIRMED = "confirmed"
    HELD_FOR_HUMAN = "held_for_human"
    NO_REVIEWER = "no_reviewer"
    INVALID_ARTIFACT = "invalid_artifact"


@dataclass(frozen=True)
class Objection:
    """A reviewer's only business output: one evidenced fault."""

    code: str
    rule_id: str
    severity: Severity
    field: str
    claim: str
    evidence_refs: tuple[str, ...]
    reviewer_id: str = ""

    def __post_init__(self) -> None:
        required = (self.code, self.rule_id, self.field, self.claim)
        if not all(value.strip() for value in required):
            raise ValueError("objection identity and claim fields must not be empty")
        if not self.evidence_refs:
            raise ValueError("an objection must carry evidence")


@dataclass(frozen=True)
class ReviewPolicy:
    """Versioned release rubric and loop budget."""

    rubric_version: str
    required_rule_ids: tuple[str, ...]
    max_rounds: int = 3

    def __post_init__(self) -> None:
        if not self.rubric_version.strip():
            raise ValueError("rubric_version must not be empty")
        if not self.required_rule_ids:
            raise ValueError("at least one required review rule is needed")
        if len(self.required_rule_ids) != len(set(self.required_rule_ids)):
            raise ValueError("required_rule_ids must not contain duplicates")
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")


@dataclass(frozen=True)
class ReviewRequest(Generic[PayloadT]):
    """The context-isolated package one reviewer receives."""

    contract: TaskContract
    artifact: ArtifactEnvelope[PayloadT]
    artifact_revision: int
    artifact_fingerprint: str
    rubric_version: str

    def __post_init__(self) -> None:
        if self.artifact_revision < 0:
            raise ValueError("artifact_revision must not be negative")
        if not self.artifact_fingerprint.strip():
            raise ValueError("artifact_fingerprint must not be empty")
        if not self.rubric_version.strip():
            raise ValueError("rubric_version must not be empty")


class ReviewFn(Protocol[PayloadT]):
    def __call__(
        self,
        request: ReviewRequest[PayloadT],
    ) -> Awaitable[Sequence[Objection]]: ...


class ReviseFn(Protocol[PayloadT]):
    def __call__(
        self,
        request: ReviewRequest[PayloadT],
        blockers: tuple[Objection, ...],
    ) -> Awaitable[ArtifactEnvelope[PayloadT]]: ...


@dataclass(frozen=True)
class ReviewerSpec(Generic[PayloadT]):
    """One reviewer identity and the rules it declares it can check."""

    reviewer_id: str
    actor_id: str
    rule_ids: tuple[str, ...]
    evidence_scope: tuple[str, ...]
    review: ReviewFn[PayloadT]

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.reviewer_id, self.actor_id)):
            raise ValueError("reviewer identity fields must not be empty")
        if not self.rule_ids:
            raise ValueError("a reviewer must declare at least one rule")
        if len(self.rule_ids) != len(set(self.rule_ids)):
            raise ValueError("reviewer rule_ids must not contain duplicates")
        if not callable(self.review):
            raise ValueError("review must be callable")


@dataclass(frozen=True)
class ReviserSpec(Generic[PayloadT]):
    reviser_id: str
    actor_id: str
    revise: ReviseFn[PayloadT]

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.reviser_id, self.actor_id)):
            raise ValueError("reviser identity fields must not be empty")
        if not callable(self.revise):
            raise ValueError("revise must be callable")


@dataclass(frozen=True)
class ReviewerFailure:
    reviewer_id: str
    error: str
    retryable: bool


@dataclass(frozen=True)
class ReviewReceipt:
    """Coverage, objections, and reviewer health for one exact artifact."""

    review_id: str
    contract_digest: str
    artifact_id: str
    artifact_revision: int
    artifact_fingerprint: str
    rubric_version: str
    reviewer_ids: tuple[str, ...]
    checked_rule_ids: tuple[str, ...]
    missing_rule_ids: tuple[str, ...]
    objections: tuple[Objection, ...]
    reviewer_failures: tuple[ReviewerFailure, ...] = ()

    def __post_init__(self) -> None:
        required = (
            self.review_id,
            self.contract_digest,
            self.artifact_id,
            self.artifact_fingerprint,
            self.rubric_version,
        )
        if not all(value.strip() for value in required):
            raise ValueError("review receipt binding fields must not be empty")
        if self.artifact_revision < 0:
            raise ValueError("artifact_revision must not be negative")
        checked = set(self.checked_rule_ids)
        if checked.intersection(self.missing_rule_ids):
            raise ValueError("a rule cannot be both checked and missing")
        for objection in self.objections:
            if objection.rule_id not in checked:
                raise ValueError("an objection must belong to a checked rule")
            if objection.reviewer_id not in self.reviewer_ids:
                raise ValueError("an objection must name a receipt reviewer")

    @property
    def blockers(self) -> tuple[Objection, ...]:
        return tuple(
            objection
            for objection in self.objections
            if objection.severity is Severity.BLOCKER
        )

    @property
    def complete(self) -> bool:
        return not self.missing_rule_ids and not self.reviewer_failures


@dataclass(frozen=True)
class ReviewPanel(Generic[PayloadT]):
    panel_id: str
    reviewers: tuple[ReviewerSpec[PayloadT], ...]

    def __post_init__(self) -> None:
        if not self.panel_id.strip():
            raise ValueError("panel_id must not be empty")
        if not self.reviewers:
            raise ValueError("a review panel needs at least one reviewer")
        reviewer_ids = [reviewer.reviewer_id for reviewer in self.reviewers]
        if len(reviewer_ids) != len(set(reviewer_ids)):
            raise ValueError("reviewer ids must be unique")

    async def review(
        self,
        request: ReviewRequest[PayloadT],
        policy: ReviewPolicy,
    ) -> ReviewReceipt:
        async def run_one(reviewer: ReviewerSpec[PayloadT]):
            try:
                raw = tuple(await reviewer.review(request))
                for objection in raw:
                    if objection.rule_id not in reviewer.rule_ids:
                        raise ValueError(
                            f"undeclared rule {objection.rule_id}"
                        )
                bound = tuple(
                    replace(objection, reviewer_id=reviewer.reviewer_id)
                    for objection in raw
                )
                return reviewer, bound, None
            except Exception as exc:
                failure = ReviewerFailure(
                    reviewer_id=reviewer.reviewer_id,
                    error=f"{type(exc).__name__}: {exc}",
                    retryable=isinstance(
                        exc,
                        (TimeoutError, asyncio.TimeoutError),
                    ),
                )
                return reviewer, (), failure

        results = await asyncio.gather(
            *(run_one(reviewer) for reviewer in self.reviewers)
        )
        objections: list[Objection] = []
        checked: set[str] = set()
        failures: list[ReviewerFailure] = []
        for reviewer, reviewer_objections, failure in results:
            if failure is not None:
                failures.append(failure)
                continue
            checked.update(reviewer.rule_ids)
            objections.extend(reviewer_objections)

        return ReviewReceipt(
            review_id=(
                f"review::{request.artifact.artifact_id}"
                f"::r{request.artifact_revision}"
            ),
            contract_digest=request.contract.digest,
            artifact_id=request.artifact.artifact_id,
            artifact_revision=request.artifact_revision,
            artifact_fingerprint=request.artifact_fingerprint,
            rubric_version=policy.rubric_version,
            reviewer_ids=tuple(
                reviewer.reviewer_id for reviewer in self.reviewers
            ),
            checked_rule_ids=tuple(sorted(checked)),
            missing_rule_ids=tuple(
                sorted(set(policy.required_rule_ids) - checked)
            ),
            objections=tuple(objections),
            reviewer_failures=tuple(failures),
        )


@dataclass(frozen=True)
class IndependenceGuard:
    """Check actor and callable separation before the review loop starts."""

    def evaluate(
        self,
        panel: ReviewPanel[PayloadT],
        *,
        author_actor_id: str,
        reviser: ReviserSpec[PayloadT] | None,
    ) -> tuple[Finding, ...]:
        findings: list[Finding] = []

        def add(code: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field="reviewer_identity",
                    message=code.replace("_", " "),
                    evidence=evidence,
                )
            )

        actor_ids = [reviewer.actor_id for reviewer in panel.reviewers]
        if len(actor_ids) != len(set(actor_ids)):
            add("duplicate_reviewer_actor", f"actors={actor_ids}")
        for reviewer in panel.reviewers:
            if reviewer.actor_id == author_actor_id:
                add(
                    "author_is_reviewer",
                    f"actor={reviewer.actor_id}",
                )
            if reviser is not None and reviewer.actor_id == reviser.actor_id:
                add(
                    "reviser_is_reviewer",
                    f"actor={reviewer.actor_id}",
                )
            if reviser is not None and reviewer.review is reviser.revise:
                add(
                    "reviewer_callable_is_reviser",
                    f"reviewer={reviewer.reviewer_id}",
                )
        return tuple(findings)


@dataclass(frozen=True)
class ReviewGate:
    """A complete receipt with zero blockers may cross the release boundary."""

    def may_confirm(self, receipt: ReviewReceipt) -> bool:
        return receipt.complete and not receipt.blockers


@dataclass(frozen=True)
class ReviewRound(Generic[PayloadT]):
    round_number: int
    request: ReviewRequest[PayloadT]
    receipt: ReviewReceipt


@dataclass(frozen=True)
class ReviewRun(Generic[PayloadT]):
    outcome: Outcome
    contract: TaskContract
    artifact: ArtifactEnvelope[PayloadT]
    artifact_revision: int
    rounds: tuple[ReviewRound[PayloadT], ...]
    acceptance_receipt: AcceptanceReceipt
    run_findings: tuple[Finding, ...] = ()

    @property
    def latest_review(self) -> ReviewReceipt | None:
        return self.rounds[-1].receipt if self.rounds else None


FingerprintFn = Callable[[PayloadT], str]


class AdversarialReview(Generic[PayloadT]):
    """Review, revise, and re-review one contract-bound artifact."""

    def __init__(
        self,
        panel: ReviewPanel[PayloadT],
        policy: ReviewPolicy,
        *,
        author_actor_id: str,
        fingerprint: FingerprintFn[PayloadT],
        reviser: ReviserSpec[PayloadT] | None = None,
        gate: ReviewGate | None = None,
        independence_guard: IndependenceGuard | None = None,
    ):
        if not author_actor_id.strip():
            raise ValueError("author_actor_id must not be empty")
        self.panel = panel
        self.policy = policy
        self.author_actor_id = author_actor_id
        self.fingerprint = fingerprint
        self.reviser = reviser
        self.gate = gate or ReviewGate()
        self.independence_guard = independence_guard or IndependenceGuard()

    def _artifact_findings(
        self,
        contract: TaskContract,
        artifact: ArtifactEnvelope[PayloadT],
        *,
        expected_producer: str,
    ) -> tuple[Finding, ...]:
        findings: list[Finding] = []

        def add(code: str, field: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field=field,
                    message=code.replace("_", " "),
                    evidence=evidence,
                )
            )

        if artifact.contract_digest != contract.digest:
            add(
                "contract_digest_mismatch",
                "contract_digest",
                (
                    f"expected={contract.digest} "
                    f"observed={artifact.contract_digest}"
                ),
            )
        if artifact.schema != contract.output_schema:
            add(
                "schema_mismatch",
                "schema",
                f"expected={contract.output_schema} observed={artifact.schema}",
            )
        if artifact.produced_by != expected_producer:
            add(
                "producer_mismatch",
                "produced_by",
                (
                    f"expected={expected_producer} "
                    f"observed={artifact.produced_by}"
                ),
            )
        if not artifact.evidence_refs:
            add("missing_evidence", "evidence_refs", "evidence_refs=()")
        fingerprint = self.fingerprint(artifact.payload)
        if not fingerprint.strip():
            add(
                "missing_artifact_fingerprint",
                "payload",
                "fingerprint=''",
            )
        return tuple(findings)

    def _request(
        self,
        contract: TaskContract,
        artifact: ArtifactEnvelope[PayloadT],
        revision: int,
    ) -> ReviewRequest[PayloadT]:
        return ReviewRequest(
            contract=contract,
            artifact=artifact,
            artifact_revision=revision,
            artifact_fingerprint=self.fingerprint(artifact.payload),
            rubric_version=self.policy.rubric_version,
        )

    def _acceptance(
        self,
        contract: TaskContract,
        artifact: ArtifactEnvelope[PayloadT],
        outcome: Outcome,
        rounds: Sequence[ReviewRound[PayloadT]],
        run_findings: Sequence[Finding],
    ) -> AcceptanceReceipt:
        findings = list(run_findings)
        if rounds:
            latest = rounds[-1].receipt
            findings.extend(_objection_finding(item) for item in latest.objections)
            for rule_id in latest.missing_rule_ids:
                findings.append(
                    Finding(
                        code="required_rule_missing",
                        field=rule_id,
                        message="required review rule was not checked",
                        evidence=f"rubric={latest.rubric_version}",
                    )
                )
            for failure in latest.reviewer_failures:
                findings.append(
                    Finding(
                        code="reviewer_failed",
                        field=failure.reviewer_id,
                        message=failure.error,
                        evidence=(
                            f"retryable={failure.retryable} "
                            f"artifact={latest.artifact_id}"
                        ),
                    )
                )

        decision = (
            AcceptanceDecision.ACCEPTED
            if outcome is Outcome.CONFIRMED
            else AcceptanceDecision.ESCALATED
        )
        return AcceptanceReceipt(
            receipt_id=f"receipt::{artifact.artifact_id}",
            contract_digest=contract.digest,
            artifact_id=artifact.artifact_id,
            checked_by=self.panel.panel_id,
            decision=decision,
            findings=tuple(findings),
        )

    def _finish(
        self,
        *,
        outcome: Outcome,
        contract: TaskContract,
        artifact: ArtifactEnvelope[PayloadT],
        revision: int,
        rounds: Sequence[ReviewRound[PayloadT]],
        run_findings: Sequence[Finding] = (),
    ) -> ReviewRun[PayloadT]:
        return ReviewRun(
            outcome=outcome,
            contract=contract,
            artifact=artifact,
            artifact_revision=revision,
            rounds=tuple(rounds),
            acceptance_receipt=self._acceptance(
                contract,
                artifact,
                outcome,
                rounds,
                run_findings,
            ),
            run_findings=tuple(run_findings),
        )

    async def run(
        self,
        contract: TaskContract,
        artifact: ArtifactEnvelope[PayloadT],
        *,
        artifact_revision: int = 0,
    ) -> ReviewRun[PayloadT]:
        independence = self.independence_guard.evaluate(
            self.panel,
            author_actor_id=self.author_actor_id,
            reviser=self.reviser,
        )
        if independence:
            return self._finish(
                outcome=Outcome.NO_REVIEWER,
                contract=contract,
                artifact=artifact,
                revision=artifact_revision,
                rounds=(),
                run_findings=independence,
            )

        artifact_findings = self._artifact_findings(
            contract,
            artifact,
            expected_producer=self.author_actor_id,
        )
        if artifact_findings:
            return self._finish(
                outcome=Outcome.INVALID_ARTIFACT,
                contract=contract,
                artifact=artifact,
                revision=artifact_revision,
                rounds=(),
                run_findings=artifact_findings,
            )

        current = artifact
        revision = artifact_revision
        rounds: list[ReviewRound[PayloadT]] = []
        for round_number in range(1, self.policy.max_rounds + 1):
            request = self._request(contract, current, revision)
            receipt = await self.panel.review(request, self.policy)
            rounds.append(
                ReviewRound(
                    round_number=round_number,
                    request=request,
                    receipt=receipt,
                )
            )

            if self.gate.may_confirm(receipt):
                return self._finish(
                    outcome=Outcome.CONFIRMED,
                    contract=contract,
                    artifact=current,
                    revision=revision,
                    rounds=rounds,
                )
            if not receipt.complete:
                break
            if self.reviser is None or round_number == self.policy.max_rounds:
                break

            revised = await self.reviser.revise(request, receipt.blockers)
            revised_findings = self._artifact_findings(
                contract,
                revised,
                expected_producer=self.reviser.actor_id,
            )
            revised_fingerprint = self.fingerprint(revised.payload)
            if revised_fingerprint == request.artifact_fingerprint:
                revised_findings = (
                    *revised_findings,
                    Finding(
                        code="reviser_made_no_progress",
                        field="artifact_fingerprint",
                        message="reviser returned unchanged business content",
                        evidence=f"fingerprint={revised_fingerprint}",
                    ),
                )
            if revised_findings:
                return self._finish(
                    outcome=Outcome.HELD_FOR_HUMAN,
                    contract=contract,
                    artifact=current,
                    revision=revision,
                    rounds=rounds,
                    run_findings=revised_findings,
                )
            current = revised
            revision += 1

        return self._finish(
            outcome=Outcome.HELD_FOR_HUMAN,
            contract=contract,
            artifact=current,
            revision=revision,
            rounds=rounds,
        )


def _objection_finding(objection: Objection) -> Finding:
    return Finding(
        code=objection.code,
        field=objection.field,
        message=objection.claim,
        evidence="; ".join(objection.evidence_refs),
        severity=objection.severity,
    )
