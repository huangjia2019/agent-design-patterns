"""Service tests for the Composition Selection Workbench."""
from __future__ import annotations

import os
import sys

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("ui_service", None)

from ui_service import meta, run  # noqa: E402


def test_meta_exposes_the_three_lecture_arc() -> None:
    payload = meta()

    assert [item["number"] for item in payload["lectures"]] == ["41", "42", "43"]
    assert [item["id"] for item in payload["scenarios"]] == [
        "independent",
        "shared_state",
    ]


@pytest.mark.parametrize(
    ("scenario", "expected_pattern"),
    [
        ("independent", "扇出聚合（Fan-out and Gather）"),
        ("shared_state", "迭代假设验证（Iterative Hypothesis）"),
    ],
)
def test_run_returns_an_accepted_evidence_bound_decision(
    scenario: str,
    expected_pattern: str,
) -> None:
    payload = run(scenario)["run"]

    assert payload["proposal"]["pattern"] == expected_pattern
    assert payload["outcome"]["state"] == "accepted"
    assert payload["outcome"]["evidence_refs"]


def test_unknown_scenario_is_rejected() -> None:
    with pytest.raises(KeyError):
        run("unknown")
