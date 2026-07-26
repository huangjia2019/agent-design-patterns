"""Minimal runnable example for the Generator-Critic pattern."""
from __future__ import annotations

from pattern import (
    AcceptancePolicy,
    Artifact,
    Critique,
    GeneratorCriticChain,
    Issue,
    Severity,
)


def generate_update(prompt: str) -> Artifact:
    return Artifact(
        content="Checkout errors affected card payments. Next update in 30 minutes.",
        metadata={"prompt": prompt},
    )


def critique_update(artifact: Artifact) -> Critique:
    issues = []
    if "INC-42" not in artifact.content:
        issues.append(
            Issue(
                severity=Severity.BLOCKER,
                message="impact claim has no incident evidence",
                location="sentence 1",
                evidence="status dashboard incident INC-42",
                check="incident_source",
            )
        )
    return Critique(
        score=0.62 if issues else 0.92,
        issues=issues,
        summary=f"{len(issues)} issue(s)",
        score_evidence="one grounded blocker" if issues else "",
    )


def revise_update(artifact: Artifact, _critique: Critique) -> Artifact:
    return artifact.revise(
        artifact.content + " Evidence: status dashboard incident INC-42.",
        note="attached incident evidence",
    )


if __name__ == "__main__":
    chain = GeneratorCriticChain(
        generator=generate_update,
        critic=critique_update,
        reviser=revise_update,
        policy=AcceptancePolicy(min_score=0.8),
    )

    first_pass = chain.run("draft checkout incident update")
    print("pass 1:", first_pass.decision.value, "->", " -> ".join(first_pass.trace))
    print("revision:", first_pass.revision_draft.content)

    second_pass = chain.review(first_pass.revision_draft)
    print("pass 2:", second_pass.decision.value, "->", " -> ".join(second_pass.trace))
