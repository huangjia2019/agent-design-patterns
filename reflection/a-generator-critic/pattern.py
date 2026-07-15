"""Generator-Critic pattern.

Framework-agnostic reference implementation of the Reflection x Chain pattern.
One role generates an artifact. A separate role critiques it. A deterministic
gate decides whether the artifact is accepted or needs revision.

The topology is intentionally one pass:

    generate -> critique -> gate -> optional revision draft

There is no re-critique loop here. If a revision draft is produced, it is still
marked ``NEEDS_REVISION`` until another explicit pass critiques it. That keeps
Generator-Critic distinct from the sibling Self-Heal Loop pattern.

The critic's useful power comes from external signals. Every actionable issue
names the check or source that produced it and carries evidence such as a schema
key, policy clause, test failure, ledger count, or database observation. Issues
without evidence are retained as dropped opinions, but they cannot trigger a
revision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Severity(str, Enum):
    """How strongly an evidence-backed critic issue should affect the gate."""

    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class Decision(str, Enum):
    """Deterministic gate result."""

    ACCEPTED = "accepted"
    NEEDS_REVISION = "needs_revision"


@dataclass(frozen=True)
class Issue:
    """One concrete critic finding.

    `source` names the check that produced the finding. `evidence` records what
    the check actually saw. Empty source/evidence means the finding is only an
    opinion; `Critique` keeps it in `dropped_issues` so the trace is auditable,
    but acceptance policy ignores it.
    """

    severity: Severity
    message: str
    location: str = ""
    source: str = ""
    evidence: str = ""

    def is_evidence_backed(self) -> bool:
        return bool(self.source.strip() and self.evidence.strip())


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
    dropped_issues: list[Issue] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")

        evidence_backed: list[Issue] = []
        dropped = list(self.dropped_issues)
        for issue in self.issues:
            if issue.is_evidence_backed():
                evidence_backed.append(issue)
            else:
                dropped.append(issue)

        object.__setattr__(self, "issues", evidence_backed)
        object.__setattr__(self, "dropped_issues", dropped)

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
        if critique.dropped_issues:
            trace.append(f"dropped_opinions:{len(critique.dropped_issues)}")

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
