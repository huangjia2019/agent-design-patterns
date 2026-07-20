"""Regression tests for the reconciled Generator-Critic contract."""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    AcceptancePolicy,
    Artifact,
    Critique,
    Decision,
    GeneratorCriticChain,
    Issue,
    Severity,
)


def test_issue_needs_named_check_and_evidence_to_be_actionable() -> None:
    opinion = Issue(
        Severity.BLOCKER,
        "ledger count is wrong",
        "paid",
        evidence="paid=798",
    )

    critique = Critique(score=0.95, issues=[opinion], summary="unsupported")

    assert critique.issues == []
    assert critique.dropped_issues == [opinion]
    assert AcceptancePolicy().decide(critique) is Decision.ACCEPTED


def test_low_score_needs_score_evidence_to_trigger_revision() -> None:
    unsupported = Critique(score=0.4, issues=[], summary="feels incomplete")
    grounded = Critique(
        score=0.4,
        issues=[],
        summary="rubric failed",
        score_evidence="completeness rubric=0.4",
    )

    assert AcceptancePolicy().decide(unsupported) is Decision.ACCEPTED
    assert AcceptancePolicy().decide(grounded) is Decision.NEEDS_REVISION


def test_revision_draft_is_separate_from_reviewed_artifact() -> None:
    grounded = Issue(
        Severity.BLOCKER,
        "paid count disagrees with the ledger",
        "paid",
        evidence="ledger paid=798",
        check="reconcile_paid",
    )
    opinion = Issue(Severity.WARNING, "make it longer", "body", check="vibe")
    chain = GeneratorCriticChain(
        generator=lambda _prompt: Artifact("paid=800"),
        critic=lambda _artifact: Critique(
            score=0.4,
            issues=[grounded, opinion],
            summary="one grounded blocker",
            score_evidence="one grounded blocker",
        ),
        reviser=lambda artifact, _critique: artifact.revise("paid=798"),
    )

    result = chain.run("monthly report")

    assert result.decision is Decision.NEEDS_REVISION
    assert result.reviewed_artifact.content == "paid=800"
    assert result.revision_draft.content == "paid=798"
    assert result.artifact is result.revision_draft
    assert result.trace == (
        "generated",
        "critiqued",
        "dropped_opinions:1",
        "needs_revision",
        "revision_drafted",
    )


def test_revision_requires_an_explicit_second_review() -> None:
    def critic(artifact: Artifact) -> Critique:
        if artifact.revision == 1:
            return Critique(score=0.95, issues=[], summary="reconciled")
        return Critique(
            score=0.4,
            issues=[
                Issue(
                    Severity.BLOCKER,
                    "paid count disagrees with the ledger",
                    "paid",
                    evidence="ledger paid=798",
                    check="reconcile_paid",
                )
            ],
            summary="wrong",
            score_evidence="one grounded blocker",
        )

    chain = GeneratorCriticChain(
        generator=lambda _prompt: Artifact("paid=800"),
        critic=critic,
        reviser=lambda artifact, _critique: artifact.revise("paid=798"),
    )

    first = chain.run("monthly report")
    second = chain.review(first.revision_draft)

    assert first.decision is Decision.NEEDS_REVISION
    assert second.decision is Decision.ACCEPTED
    assert second.reviewed_artifact.revision == 1
    assert second.trace == ("artifact_received", "critiqued", "accepted")
