"""Shared helpers for the Generator-Critic reference implementations.

Both langgraph/ and langchain/ notebooks import from here so the demo artifact,
critique parser, policy, revision rule, and trace rendering stay aligned.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from pattern import AcceptancePolicy, Artifact, ChainResult, Critique, Issue, Severity


DEFAULT_PROMPT = "Draft a customer-facing checkout incident update."
GENERATOR_SYSTEM_PROMPT = "Draft a concise customer-facing incident update."

INITIAL_DRAFT = (
    "We identified elevated checkout errors. Impact is limited to card payments. "
    "Next update in 30 minutes."
)

REVISION_EVIDENCE = "Evidence: status dashboard incident INC-42."

CRITIC_SYSTEM_PROMPT = (
    "Critique the incident update. Return only valid JSON, no markdown. "
    'Use this schema: {"score": number from 0 to 1, "summary": string, '
    '"issues": [{"severity": "blocker" or "warning", "message": string, '
    '"location": string}]}. '
    'Use severity "blocker" only for facts that must be fixed before '
    'publishing; use "warning" for polish issues.'
)

GOOD_CRITIQUE_JSON = json.dumps(
    {
        "score": 0.9,
        "summary": "Ready to ship: impact and next update are clear.",
        "issues": [],
    }
)

NEEDS_REVISION_CRITIQUE_JSON = json.dumps(
    {
        "score": 0.74,
        "summary": "The draft needs one evidence link before it can ship.",
        "issues": [
            {
                "severity": "blocker",
                "message": "impact claim lacks a cited source",
                "location": "sentence 2",
            }
        ],
    }
)

LOW_SCORE_CRITIQUE_JSON = json.dumps(
    {
        "score": 0.62,
        "summary": "Readable, but too vague to publish safely.",
        "issues": [
            {
                "severity": "warning",
                "message": "next update timing is too vague",
                "location": "sentence 3",
            }
        ],
    }
)

BAD_CRITIQUE_JSON = "{not valid json"


def default_policy() -> AcceptancePolicy:
    return AcceptancePolicy(min_score=0.8)


def parse_critique_json(raw: str) -> Critique:
    """Parse the notebook critique JSON format into the core Critique type.

    Fail closed: malformed JSON, unknown severities, missing fields, or invalid
    scores become a blocker critique rather than an accidental pass.
    """
    try:
        payload = json.loads(raw)
        issues = [
            Issue(
                severity=Severity(item["severity"]),
                message=str(item["message"]),
                location=str(item.get("location", "")),
            )
            for item in payload.get("issues", [])
        ]
        return Critique(
            score=float(payload["score"]),
            issues=issues,
            summary=str(payload.get("summary", "")),
        )
    except Exception as exc:  # noqa: BLE001 - parser failure must not become a pass
        return Critique(
            score=0.0,
            issues=[
                Issue(
                    Severity.BLOCKER,
                    f"critic output could not be parsed: {type(exc).__name__}: {exc}",
                    "critic",
                )
            ],
            summary="critic output parse failed",
        )


def critique_to_dict(critique: Critique) -> dict[str, Any]:
    return {
        "score": critique.score,
        "summary": critique.summary,
        "issues": [
            {
                "severity": issue.severity.value,
                "message": issue.message,
                "location": issue.location,
            }
            for issue in critique.issues
        ],
    }


def revise_with_evidence(artifact: Artifact, critique: Critique) -> Artifact:
    issue_text = "; ".join(issue.message for issue in critique.issues) or "critic requested revision"
    return artifact.revise(
        f"{artifact.content} {REVISION_EVIDENCE}",
        note=f"addressed: {issue_text}",
    )


def scripted_generator(_prompt: str) -> Artifact:
    """Framework-agnostic fake generator for notebook mock runs."""
    return Artifact(content=INITIAL_DRAFT, metadata={"source": "scripted"})


def scripted_critic(raw_json: str) -> Callable[[Artifact], Critique]:
    """Return a fake critic that replays one JSON critique through the parser."""
    def critic(_artifact: Artifact) -> Critique:
        return parse_critique_json(raw_json)

    return critic


def print_trace(result: ChainResult) -> None:
    issues = [
        f"{issue.severity.value}:{issue.location}:{issue.message}"
        for issue in result.critique.issues
    ]
    artifact = "\n".join(
        line.rstrip()
        for line in result.artifact.content.splitlines()
        if line.strip()
    )
    print("decision:", result.decision.value)
    print("trace:", " -> ".join(result.trace))
    print("score:", result.critique.score)
    print("issues:", issues or "none")
    print("artifact:", artifact)
