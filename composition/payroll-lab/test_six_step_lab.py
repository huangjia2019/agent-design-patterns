import os
import sys


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("six_step_lab", None)

from six_step_lab import run_methodology  # noqa: E402


def test_six_step_lab_rejects_shared_writer_and_adopts_split_ownership():
    result = run_methodology()
    by_id = {
        candidate["candidate_id"]: candidate
        for candidate in result["candidates"]
    }

    assert by_id["shared-net-amount"]["trial_ready"] is False
    assert any(
        finding["code"] == "multiple_writers"
        for finding in by_id["shared-net-amount"]["findings"]
    )
    assert by_id["split-plan-and-settlement"]["trial_ready"] is True
    assert result["receipt"]["status"] == "adopt_candidate"
    assert result["receipt"]["selected_candidate"] == "split-plan-and-settlement"


def test_full_bundle_passes_and_each_ablation_exposes_a_gap():
    result = run_methodology()
    experiments = {
        item["case_id"]: item
        for item in result["experiments"]
    }

    assert experiments["split-full"]["metrics"] == {
        "recovery_success": 1.0,
        "committed_fact_overwrites": 0.0,
        "settlement_receipts": 1.0,
    }
    assert experiments["split-without-plan"]["metrics"]["recovery_success"] == 0.0
    assert (
        experiments["split-without-handoff"]["metrics"][
            "committed_fact_overwrites"
        ]
        == 1.0
    )
    assert (
        experiments["split-without-handoff"]["metrics"]["settlement_receipts"]
        == 0.0
    )


def test_real_handoff_chain_rejects_two_fact_producers():
    result = run_methodology()
    assert "more than one producer" in result["framework_conflict"]


def test_reopen_binds_the_prior_decision_receipt():
    result = run_methodology()
    assert result["reopened_version"] == 2
    assert result["prior_receipt_digest"] == result["receipt_digest"]
