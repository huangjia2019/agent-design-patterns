"""Generator-Critic reference interface.

Generator-Critic is the Reflect x Chain pattern. One pass has a fixed shape:

    generate -> critique -> policy gate -> optional revision draft

The critic reports evidence about the artifact. It does not approve the artifact.
The deterministic policy owns acceptance. A revision produced at the end of the
pass is explicitly unreviewed and therefore cannot be accepted by the same pass.

Repeating review and repair until a deterministic signal turns green belongs to
the sibling Self-Heal Loop pattern. An outer workflow may schedule another
Generator-Critic pass, but the loop is not hidden inside this interface.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Severity(str, Enum):
    """How strongly an issue should affect the policy gate."""

    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class Decision(str, Enum):
    """Deterministic result for the artifact that was actually reviewed."""

    ACCEPTED = "accepted"
    NEEDS_REVISION = "needs_revision"


@dataclass(frozen=True)
class Issue:
    """One concrete issue reported by the critic.

    Evidence records what the check observed, such as a ledger query, schema
    clause, source citation, or quoted span. A policy can require evidence before
    an issue is allowed to trigger an automatic revision.
    """

    severity: Severity
    message: str
    location: str = ""
    evidence: str = ""
    check: str = ""

    @property
    def grounded(self) -> bool:
        return bool(self.check.strip() and self.evidence.strip())

    @property
    def source(self) -> str:
        """Compatibility name used by the notebook JSON schema."""

        return self.check

    def is_evidence_backed(self) -> bool:
        return self.grounded


@dataclass(frozen=True)
class Artifact:
    """The generated object under review."""

    content: str
    revision: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    def revise(self, content: str, *, note: str = "") -> Artifact:
        metadata = dict(self.metadata)
        if note:
            metadata["revision_note"] = note
        return Artifact(content=content, revision=self.revision + 1, metadata=metadata)


@dataclass(frozen=True)
class Critique:
    """The critic's evidence. It can report issues, never approve directly."""

    score: float
    issues: Sequence[Issue]
    summary: str
    score_evidence: str = ""
    dropped_issues: Sequence[Issue] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")

        # Snapshot and reclassify both inputs. Callers cannot mutate the policy
        # boundary after construction or hide grounded findings in the dropped
        # bucket by supplying a pre-classified collection.
        all_issues = (*self.issues, *self.dropped_issues)
        grounded = tuple(issue for issue in all_issues if issue.grounded)
        dropped = tuple(issue for issue in all_issues if not issue.grounded)

        object.__setattr__(self, "issues", grounded)
        object.__setattr__(self, "dropped_issues", dropped)

    def blockers(self, *, include_dropped: bool = False) -> list[Issue]:
        issues = (*self.issues, *self.dropped_issues) if include_dropped else self.issues
        return [issue for issue in issues if issue.severity is Severity.BLOCKER]

    def warnings(self, *, include_dropped: bool = False) -> list[Issue]:
        issues = (*self.issues, *self.dropped_issues) if include_dropped else self.issues
        return [issue for issue in issues if issue.severity is Severity.WARNING]

    def ungrounded(self) -> list[Issue]:
        return list(self.dropped_issues)


@dataclass(frozen=True)
class AcceptancePolicy:
    """Deterministic gate between critic evidence and a shipping decision."""

    min_score: float = 0.8
    allow_warnings: bool = True
    require_evidence: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")

    def _score_is_actionable(self, critique: Critique) -> bool:
        if critique.score >= self.min_score:
            return False
        if not self.require_evidence:
            return True
        return bool(critique.score_evidence.strip())

    def decide(self, critique: Critique) -> Decision:
        include_dropped = not self.require_evidence
        if critique.blockers(include_dropped=include_dropped):
            return Decision.NEEDS_REVISION
        if not self.allow_warnings and critique.warnings(
            include_dropped=include_dropped
        ):
            return Decision.NEEDS_REVISION
        if self._score_is_actionable(critique):
            return Decision.NEEDS_REVISION
        return Decision.ACCEPTED


Generator = Callable[[str], Artifact]
CriticFn = Callable[[Artifact], Critique]
Reviser = Callable[[Artifact, Critique], Artifact]


@dataclass(frozen=True)
class ChainResult:
    """Auditable output of exactly one Generator-Critic pass."""

    decision: Decision
    reviewed_artifact: Artifact
    critique: Critique
    revision_draft: Artifact | None
    trace: tuple[str, ...]

    @property
    def artifact(self) -> Artifact:
        """Compatibility view: the newest artifact produced by this pass."""

        return self.revision_draft or self.reviewed_artifact

    @property
    def requires_re_review(self) -> bool:
        return self.revision_draft is not None


class GeneratorCriticChain:
    """Run one bounded Generator-Critic pass.

    run starts from a prompt and invokes the generator. review starts from an
    existing artifact, which is useful when an outer workflow explicitly submits
    a revision for another pass. Neither method contains a retry loop.
    """

    def __init__(
        self,
        generator: Generator,
        critic: CriticFn,
        reviser: Reviser | None = None,
        policy: AcceptancePolicy | None = None,
    ) -> None:
        self.generator = generator
        self.critic = critic
        self.reviser = reviser
        self.policy = policy or AcceptancePolicy()

    def run(self, prompt: str) -> ChainResult:
        artifact = self.generator(prompt)
        return self._review(artifact, trace=["generated"])

    def review(self, artifact: Artifact) -> ChainResult:
        return self._review(artifact, trace=["artifact_received"])

    def _review(self, artifact: Artifact, *, trace: list[str]) -> ChainResult:
        critique = self.critic(artifact)
        trace.append("critiqued")
        if critique.dropped_issues:
            trace.append(f"dropped_opinions:{len(critique.dropped_issues)}")

        decision = self.policy.decide(critique)
        trace.append(decision.value)

        revision_draft = None
        if decision is Decision.NEEDS_REVISION and self.reviser is not None:
            revision_draft = self.reviser(artifact, critique)
            trace.append("revision_drafted")

        return ChainResult(
            decision=decision,
            reviewed_artifact=artifact,
            critique=critique,
            revision_draft=revision_draft,
            trace=tuple(trace),
        )
