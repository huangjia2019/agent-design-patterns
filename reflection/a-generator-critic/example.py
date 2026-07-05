"""Runnable example for the Generator-Critic pattern.

Scenario: a support agent drafts a customer-facing incident update. The critic
checks whether the draft has evidence and a useful next step. A deterministic
policy decides whether the draft can ship.
"""
from __future__ import annotations

from pattern import (
    AcceptancePolicy,
    Artifact,
    Critique,
    GeneratorCriticChain,
    Issue,
    Severity,
)


def draft_incident_update(prompt: str) -> Artifact:
    return Artifact(
        content=(
            "We identified elevated checkout errors. "
            "Impact is limited to card payments. "
            "Next update in 30 minutes."
        ),
        metadata={"prompt": prompt},
    )


def critique_update(artifact: Artifact) -> Critique:
    issues: list[Issue] = []
    if "Impact" not in artifact.content:
        issues.append(Issue(Severity.BLOCKER, "missing customer impact", "body"))
    if "Next update" not in artifact.content:
        issues.append(Issue(Severity.WARNING, "missing next-update promise", "body"))
    if "dashboard" not in artifact.content:
        issues.append(Issue(Severity.BLOCKER, "no evidence link", "body"))

    score = 0.86 if not any(issue.severity is Severity.BLOCKER for issue in issues) else 0.62
    return Critique(score=score, issues=issues, summary=f"{len(issues)} issue(s) found")


def revise_update(artifact: Artifact, critique: Critique) -> Artifact:
    issue_text = "; ".join(issue.message for issue in critique.issues)
    revised = (
        f"{artifact.content} Evidence: status dashboard incident INC-42. "
        f"Revision addressed: {issue_text}."
    )
    return artifact.revise(revised, note="added evidence from critic feedback")


if __name__ == "__main__":
    chain = GeneratorCriticChain(
        generator=draft_incident_update,
        critic=critique_update,
        reviser=revise_update,
        policy=AcceptancePolicy(min_score=0.8),
    )

    result = chain.run("draft checkout incident update")
    print("Decision:", result.decision.value)
    print("Trace:", " -> ".join(result.trace))
    print("Critique:", result.critique.summary)
    print("Artifact:", result.artifact.content)
