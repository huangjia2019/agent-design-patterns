"""Tests for the Generator-Critic pattern.

Run: pytest reflection/a-generator-critic/test_pattern.py -v

No API key needed. Deterministic generator, critic, and reviser callables stand
in for model roles so the pattern invariants are visible and repeatable.
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

import example  # noqa: E402
import model_config  # noqa: E402
import shared  # noqa: E402
from pattern import (  # noqa: E402
    AcceptancePolicy,
    Artifact,
    Critique,
    Decision,
    GeneratorCriticChain,
    Issue,
    Severity,
)


def test_policy_accepts_clean_high_score_artifact() -> None:
    policy = AcceptancePolicy(min_score=0.8)
    critique = Critique(score=0.92, issues=[], summary="clear")

    assert policy.decide(critique) is Decision.ACCEPTED


def test_policy_requires_revision_when_score_is_too_low() -> None:
    policy = AcceptancePolicy(min_score=0.8)
    critique = Critique(score=0.71, issues=[], summary="thin evidence")

    assert policy.decide(critique) is Decision.NEEDS_REVISION


def test_policy_requires_revision_when_any_blocker_exists() -> None:
    policy = AcceptancePolicy(min_score=0.8)
    critique = Critique(
        score=0.95,
        issues=[
            Issue(
                severity=Severity.BLOCKER,
                message="claim lacks a cited source",
                location="paragraph 2",
            )
        ],
        summary="good prose, unsafe evidence",
    )

    assert policy.decide(critique) is Decision.NEEDS_REVISION


def test_policy_can_be_configured_to_hold_warnings() -> None:
    policy = AcceptancePolicy(min_score=0.8, allow_warnings=False)
    critique = Critique(
        score=0.9,
        issues=[Issue(Severity.WARNING, "tone is too broad", "headline")],
        summary="minor issue",
    )

    assert policy.decide(critique) is Decision.NEEDS_REVISION


def test_critique_score_must_be_unit_interval() -> None:
    with pytest.raises(ValueError, match="score"):
        Critique(score=1.2, issues=[], summary="impossible")


def test_chain_runs_generator_then_critic_and_accepts_clean_artifact() -> None:
    calls: list[str] = []

    def generator(prompt: str) -> Artifact:
        calls.append(f"generate:{prompt}")
        return Artifact(content="three sourced bullets")

    def critic(artifact: Artifact) -> Critique:
        calls.append(f"critic:{artifact.content}")
        return Critique(score=0.91, issues=[], summary="ready")

    chain = GeneratorCriticChain(generator=generator, critic=critic)

    result = chain.run("summarize the incident")

    assert result.decision is Decision.ACCEPTED
    assert result.artifact.content == "three sourced bullets"
    assert calls == [
        "generate:summarize the incident",
        "critic:three sourced bullets",
    ]
    assert result.trace == ["generated", "critiqued", "accepted"]


def test_chain_with_reviser_drafts_revision_but_does_not_auto_accept_it() -> None:
    def generator(_prompt: str) -> Artifact:
        return Artifact(content="uncited claim")

    def critic(_artifact: Artifact) -> Critique:
        return Critique(
            score=0.6,
            issues=[Issue(Severity.BLOCKER, "missing citation", "sentence 1")],
            summary="needs evidence",
        )

    def reviser(artifact: Artifact, critique: Critique) -> Artifact:
        assert critique.blockers()[0].message == "missing citation"
        return artifact.revise("cited claim [source]", note="added source")

    chain = GeneratorCriticChain(generator=generator, critic=critic, reviser=reviser)

    result = chain.run("draft a claim")

    assert result.decision is Decision.NEEDS_REVISION
    assert result.artifact.content == "cited claim [source]"
    assert result.artifact.revision == 1
    assert result.trace == ["generated", "critiqued", "needs_revision", "revision_drafted"]


def test_chain_without_reviser_returns_original_artifact_for_revision() -> None:
    def generator(_prompt: str) -> Artifact:
        return Artifact(content="underspecified plan")

    def critic(_artifact: Artifact) -> Critique:
        return Critique(score=0.5, issues=[], summary="too vague")

    chain = GeneratorCriticChain(generator=generator, critic=critic)

    result = chain.run("make a plan")

    assert result.decision is Decision.NEEDS_REVISION
    assert result.artifact.content == "underspecified plan"
    assert result.trace == ["generated", "critiqued", "needs_revision"]


def test_example_missing_evidence_drafts_revision_instead_of_accepting() -> None:
    chain = GeneratorCriticChain(
        generator=example.draft_incident_update,
        critic=example.critique_update,
        reviser=example.revise_update,
        policy=AcceptancePolicy(min_score=0.8),
    )

    result = chain.run("draft checkout incident update")

    assert result.decision is Decision.NEEDS_REVISION
    assert result.trace == ["generated", "critiqued", "needs_revision", "revision_drafted"]
    assert "Evidence: status dashboard incident INC-42." in result.artifact.content


def test_shared_low_score_fixture_stays_below_default_policy_threshold() -> None:
    critique = shared.parse_critique_json(shared.LOW_SCORE_CRITIQUE_JSON)

    assert shared.default_policy().decide(critique) is Decision.NEEDS_REVISION


def test_model_loader_can_be_forced_off_for_deterministic_notebook_runs(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text(
        "MODEL_PROVIDER=ernie\nOPENAI_API_KEY=real-key-in-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert model_config.get_model() is None
