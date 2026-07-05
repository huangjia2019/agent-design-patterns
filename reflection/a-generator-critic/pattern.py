"""Generator-Critic pattern.

Minimal, framework-agnostic reference implementation of the Reflect x Chain
pattern. One role generates an artifact. A separate role critiques it. A
deterministic gate decides whether the artifact is accepted or needs revision.

The topology is intentionally a chain:

    generate -> critique -> gate -> optional revision draft

There is no re-critique loop here. If a revision draft is produced, it is still
marked ``NEEDS_REVISION`` until another pass critiques it. That boundary keeps
Generator-Critic distinct from the sibling Self-Heal Loop pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Severity(str, Enum):
    """How strongly a critic issue should affect the gate."""

    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class Decision(str, Enum):
    """Deterministic gate result."""

    ACCEPTED = "accepted"
    NEEDS_REVISION = "needs_revision"


@dataclass(frozen=True)
class Issue:
    """One concrete fault or note from the critic."""

    severity: Severity
    message: str
    location: str = ""


@dataclass(frozen=True)
class Artifact:
    """The generated object under critique."""

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
    issues: list[Issue]
    summary: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")

    def blockers(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity is Severity.BLOCKER]

    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity is Severity.WARNING]


@dataclass(frozen=True)
class AcceptancePolicy:
    """Deterministic gate between critic evidence and shipping decision."""

    min_score: float = 0.8
    allow_warnings: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")

    def decide(self, critique: Critique) -> Decision:
        if critique.blockers():
            return Decision.NEEDS_REVISION
        if not self.allow_warnings and critique.warnings():
            return Decision.NEEDS_REVISION
        if critique.score < self.min_score:
            return Decision.NEEDS_REVISION
        return Decision.ACCEPTED


Generator = Callable[[str], Artifact]
Critic = Callable[[Artifact], Critique]
Reviser = Callable[[Artifact, Critique], Artifact]


@dataclass(frozen=True)
class ChainResult:
    """Auditable output of one Generator-Critic pass."""

    decision: Decision
    artifact: Artifact
    critique: Critique
    trace: list[str]


class GeneratorCriticChain:
    """Run one generate -> critique -> gate pass.

    The critic's job is to produce evidence. The policy owns acceptance. This
    split prevents the common failure mode where a critic is prompted into
    saying "looks good" and the harness treats that as approval.
    """

    def __init__(
        self,
        generator: Generator,
        critic: Critic,
        reviser: Reviser | None = None,
        policy: AcceptancePolicy | None = None,
    ) -> None:
        self.generator = generator
        self.critic = critic
        self.reviser = reviser
        self.policy = policy or AcceptancePolicy()

    def run(self, prompt: str) -> ChainResult:
        trace = ["generated"]
        artifact = self.generator(prompt)

        critique = self.critic(artifact)
        trace.append("critiqued")

        decision = self.policy.decide(critique)
        trace.append(decision.value)

        if decision is Decision.NEEDS_REVISION and self.reviser is not None:
            artifact = self.reviser(artifact, critique)
            trace.append("revision_drafted")

        return ChainResult(
            decision=decision,
            artifact=artifact,
            critique=critique,
            trace=trace,
        )
