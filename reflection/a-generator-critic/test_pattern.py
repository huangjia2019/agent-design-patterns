"""Invariant tests for the Generator-Critic reference interface."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))
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


def grounded_blocker(message: str = "missing evidence") -> Issue:
    return Issue(
        Severity.BLOCKER,
        message,
        "report",
        evidence="ledger query returned a conflicting count",
        check="ledger_reconciliation",
    )


def test_policy_accepts_clean_high_score_artifact() -> None:
    critique = Critique(score=0.92, issues=[], summary="clear")

    assert AcceptancePolicy().decide(critique) is Decision.ACCEPTED


def test_policy_requires_evidence_for_low_score() -> None:
    unsupported = Critique(score=0.71, issues=[], summary="thin")
    grounded = Critique(
        score=0.71,
        issues=[],
        summary="thin",
        score_evidence="rubric completeness=0.71",
    )

    assert AcceptancePolicy().decide(unsupported) is Decision.ACCEPTED
    assert AcceptancePolicy().decide(grounded) is Decision.NEEDS_REVISION


def test_policy_requires_revision_for_grounded_blocker() -> None:
    critique = Critique(score=0.95, issues=[grounded_blocker()], summary="unsafe")

    assert AcceptancePolicy().decide(critique) is Decision.NEEDS_REVISION


def test_policy_can_hold_grounded_warnings() -> None:
    critique = Critique(
        score=0.9,
        issues=[
            Issue(
                Severity.WARNING,
                "tone is too broad",
                "headline",
                evidence="style guide R-7 rejects broad headlines",
                check="style_guide",
            )
        ],
        summary="minor issue",
    )

    policy = AcceptancePolicy(min_score=0.8, allow_warnings=False)

    assert policy.decide(critique) is Decision.NEEDS_REVISION


def test_ungrounded_opinion_is_dropped_and_cannot_trigger_revision() -> None:
    opinion = Issue(Severity.BLOCKER, "the report feels thin", "body", check="vibe")
    critique = Critique(score=0.92, issues=[opinion], summary="one opinion")

    assert critique.issues == ()
    assert critique.dropped_issues == (opinion,)
    assert AcceptancePolicy(require_evidence=True).decide(critique) is Decision.ACCEPTED
    assert (
        AcceptancePolicy(require_evidence=False).decide(critique)
        is Decision.NEEDS_REVISION
    )


def test_critique_issue_buckets_are_immutable_after_classification() -> None:
    opinion = Issue(Severity.BLOCKER, "the report feels thin", "body", check="vibe")
    critique = Critique(score=0.92, issues=[opinion], summary="one opinion")

    assert isinstance(critique.issues, tuple)
    assert isinstance(critique.dropped_issues, tuple)
    with pytest.raises(AttributeError):
        critique.issues.append(opinion)
    with pytest.raises(AttributeError):
        critique.dropped_issues.append(grounded_blocker())
    assert AcceptancePolicy().decide(critique) is Decision.ACCEPTED


def test_critique_reclassifies_grounded_items_from_dropped_input() -> None:
    blocker = grounded_blocker("paid count mismatch")

    critique = Critique(
        score=0.92,
        issues=[],
        dropped_issues=[blocker],
        summary="misbucketed input",
    )

    assert critique.issues == (blocker,)
    assert critique.dropped_issues == ()
    assert AcceptancePolicy().decide(critique) is Decision.NEEDS_REVISION


def test_critique_score_must_be_unit_interval() -> None:
    with pytest.raises(ValueError, match="score"):
        Critique(score=1.2, issues=[], summary="invalid")


def test_chain_calls_critic_once_and_accepts_reviewed_artifact() -> None:
    calls: list[str] = []

    def generator(prompt: str) -> Artifact:
        calls.append(f"generate:{prompt}")
        return Artifact("sourced report")

    def critic(artifact: Artifact) -> Critique:
        calls.append(f"critic:{artifact.content}")
        return Critique(0.92, [], "ready")

    result = GeneratorCriticChain(generator, critic).run("monthly report")

    assert result.decision is Decision.ACCEPTED
    assert result.reviewed_artifact.content == "sourced report"
    assert result.revision_draft is None
    assert result.artifact is result.reviewed_artifact
    assert calls == ["generate:monthly report", "critic:sourced report"]
    assert result.trace == ("generated", "critiqued", "accepted")


def test_revision_draft_is_separate_and_never_auto_accepted() -> None:
    critic_calls = 0

    def critic(_artifact: Artifact) -> Critique:
        nonlocal critic_calls
        critic_calls += 1
        return Critique(0.4, [grounded_blocker("paid count mismatch")], "wrong")

    chain = GeneratorCriticChain(
        generator=lambda _prompt: Artifact("paid=800"),
        critic=critic,
        reviser=lambda artifact, _critique: artifact.revise(
            "paid=798", note="reconciled with ledger"
        ),
    )

    result = chain.run("report")

    assert result.decision is Decision.NEEDS_REVISION
    assert result.reviewed_artifact.content == "paid=800"
    assert result.revision_draft.content == "paid=798"
    assert result.requires_re_review is True
    assert critic_calls == 1
    assert result.trace[-1] == "revision_drafted"


def test_revision_is_accepted_only_by_explicit_second_pass() -> None:
    def critic(artifact: Artifact) -> Critique:
        if artifact.revision == 1:
            return Critique(0.95, [], "reconciled")
        return Critique(0.4, [grounded_blocker()], "wrong")

    chain = GeneratorCriticChain(
        generator=lambda _prompt: Artifact("paid=800"),
        critic=critic,
        reviser=lambda artifact, _critique: artifact.revise("paid=798"),
    )

    first = chain.run("report")
    second = chain.review(first.revision_draft)

    assert first.decision is Decision.NEEDS_REVISION
    assert second.decision is Decision.ACCEPTED
    assert second.reviewed_artifact.revision == 1
    assert second.trace == ("artifact_received", "critiqued", "accepted")


def test_example_drafts_then_explicitly_reviews_revision() -> None:
    chain = GeneratorCriticChain(
        generator=example.generate_update,
        critic=example.critique_update,
        reviser=example.revise_update,
        policy=AcceptancePolicy(min_score=0.8),
    )

    first = chain.run("draft checkout incident update")
    second = chain.review(first.revision_draft)

    assert first.decision is Decision.NEEDS_REVISION
    assert first.reviewed_artifact.revision == 0
    assert "INC-42" in first.revision_draft.content
    assert second.decision is Decision.ACCEPTED
    assert second.reviewed_artifact.revision == 1


def test_shared_low_score_fixture_has_grounded_score_evidence() -> None:
    critique = shared.parse_critique_json(shared.LOW_SCORE_CRITIQUE_JSON)
    original = Artifact(shared.INITIAL_DRAFT)
    revision = shared.revise_with_evidence(original, critique)

    assert not critique.blockers()
    assert critique.score_evidence
    assert "incident ID" in critique.score_evidence
    assert "incident ID" in critique.warnings()[0].message
    assert "INC-42" not in original.content
    assert "INC-42" in revision.content
    assert shared.default_policy().decide(critique) is Decision.NEEDS_REVISION


@pytest.mark.parametrize(
    "raw_json",
    [
        '{"score": 0.95}',
        '{"score": 0.95, "summary": "ready"}',
        '{"score": 0.95, "issues": []}',
        '{"score": 0.95, "summary": "ready", "issues": [{}]}',
        '{"score": 0.95, "summary": "ready", "issues": [{"severity": "warning"}]}',
    ],
)
def test_shared_parser_fails_closed_for_incomplete_schema(raw_json: str) -> None:
    critique = shared.parse_critique_json(raw_json)

    assert critique.score == 0.0
    assert critique.blockers()
    assert shared.default_policy().decide(critique) is Decision.NEEDS_REVISION


@pytest.mark.parametrize(
    "raw_json",
    [
        "",
        "  \n\t",
        '{"score": true, "summary": "ready", "issues": []}',
        '{"score": "0.95", "summary": "ready", "issues": []}',
    ],
)
def test_shared_parser_failures_cannot_pass_at_zero_score_threshold(
    raw_json: str,
) -> None:
    critique = shared.parse_critique_json(raw_json)

    assert critique.score == 0.0
    assert critique.blockers()
    assert critique.dropped_issues == ()
    assert critique.blockers()[0].evidence.strip()
    assert (
        AcceptancePolicy(min_score=0.0).decide(critique)
        is Decision.NEEDS_REVISION
    )


@pytest.mark.parametrize(
    "raw_json",
    [
        (
            '{"score": 0.95, "summary": "ready", "issues": ['
            '{"severity": "warning", "message": "thin", "location": "body"}]}'
        ),
        (
            '{"score": 0.95, "summary": "ready", "issues": ['
            '{"severity": "warning", "message": "thin", "location": "body", '
            '"source": null, "evidence": null}]}'
        ),
        (
            '{"score": 0.95, "summary": "ready", "issues": ['
            '{"severity": "warning", "message": "thin", "location": "body", '
            '"source": "", "evidence": "   "}]}'
        ),
    ],
)
def test_shared_parser_drops_unsupported_opinions(raw_json: str) -> None:
    critique = shared.parse_critique_json(raw_json)

    assert critique.score == 0.95
    assert critique.issues == ()
    assert len(critique.dropped_issues) == 1
    assert shared.default_policy().decide(critique) is Decision.ACCEPTED


def test_model_loader_can_be_forced_off_for_deterministic_notebook_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text(
        "MODEL_PROVIDER=ernie\nOPENAI_API_KEY=real-key-in-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert model_config.get_model() is None


def test_model_config_imports_without_optional_notebook_dependencies() -> None:
    code = """
import importlib.abc
import sys

class BlockOptionalNotebookDeps(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        blocked = ("dotenv", "langchain_dev_utils")
        if fullname in blocked or fullname.startswith(tuple(f"{name}." for name in blocked)):
            raise ModuleNotFoundError(f"No module named {fullname!r}")
        return None

sys.meta_path.insert(0, BlockOptionalNotebookDeps())

import model_config

assert model_config.get_model() is None
"""
    env = os.environ.copy()
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ERNIE_API_KEY"):
        env.pop(key, None)

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
