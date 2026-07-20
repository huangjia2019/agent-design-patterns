"""Service tests for the Composition Selection Workbench."""
from __future__ import annotations

import os
import sys

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("ui_service", None)

from ui_service import (  # noqa: E402
    capstone_meta,
    meta,
    run,
    run_capstone_workbench,
    run_six_step,
    six_step_meta,
)


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


def test_six_step_meta_activates_lecture_42() -> None:
    payload = six_step_meta()

    active = [item["number"] for item in payload["lectures"] if item["active"]]
    assert active == ["42"]
    assert [item["id"] for item in payload["views"]] == ["seams", "decision"]


@pytest.mark.parametrize("view", ["seams", "decision"])
def test_six_step_workbench_returns_the_same_bound_decision(view: str) -> None:
    payload = run_six_step(view)

    assert payload["view"] == view
    assert payload["run"]["receipt"]["status"] == "adopt_candidate"
    assert (
        payload["run"]["receipt"]["selected_candidate"]
        == "split-plan-and-settlement"
    )


def test_capstone_meta_activates_lecture_43() -> None:
    payload = capstone_meta()

    active = [item["number"] for item in payload["lectures"] if item["active"]]
    assert active == ["43"]
    assert [item["id"] for item in payload["modes"]] == ["local-only", "bound"]


def test_capstone_workbench_exposes_local_and_system_acceptance() -> None:
    local = run_capstone_workbench("local-only")["run"]
    bound = run_capstone_workbench("bound")["run"]

    assert local["acceptance"]["local_acceptance_count"] == 8
    assert local["acceptance"]["accepted"] is False
    assert bound["acceptance"]["local_acceptance_count"] == 8
    assert bound["acceptance"]["accepted"] is True
