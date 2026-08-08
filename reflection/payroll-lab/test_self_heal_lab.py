"""Stateful payroll scenarios exercise the shared transaction contract."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("self_heal_lab", None)
from self_heal_lab import (  # noqa: E402
    ScenarioResult,
    PayrollWorkspace,
    diagnose,
    fix,
    review,
    run_convergence_scene,
    run_critic_block_scene,
    run_meltdown_scene,
    run_no_progress_scene,
    run_round_budget_scene,
)

sys.path.insert(0, str(HERE.parent / "d-self-heal-loop"))
from pattern import FailureSignal, HealStatus, SelfHealLoop  # noqa: E402


def test_convergence_retains_verified_workspace() -> None:
    result = run_convergence_scene()
    assert result.trace.status is HealStatus.FIXED
    assert result.workspace.files["payout.py"]["exclude_reversed"] is True
    assert result.workspace.files["batch.py"]["membership_check"] is True
    assert result.trace.final_digest != result.trace.baseline_digest
    assert result.trace.baseline_restored is None
    assert result.trace.rollback_receipts == ()
    assert result.trace.stop_reason == "verification_passed"
    assert len(result.trace.apply_receipts) == 2


def test_critic_block_leaves_exact_baseline() -> None:
    result = run_critic_block_scene()
    assert result.trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert result.workspace.files == result.baseline_state
    assert result.trace.final_digest == result.trace.baseline_digest
    assert result.trace.baseline_restored is True
    assert result.trace.stop_reason == "review_rejected"
    assert [item.commit_id for item in result.trace.rollback_receipts] == ["c1"]


@pytest.mark.parametrize(
    ("run_scene", "expected_status"),
    [(run_meltdown_scene, HealStatus.ROLLED_BACK_REGRESSION), (run_no_progress_scene, HealStatus.ROLLED_BACK_NO_PROGRESS), (run_round_budget_scene, HealStatus.MAX_ROUNDS_HUMAN_HANDOFF)],
)
def test_compensable_stops_restore_exact_payroll_state(run_scene: Callable[[], ScenarioResult], expected_status: HealStatus) -> None:
    result = run_scene()
    assert result.trace.status is expected_status
    assert result.workspace.files == result.baseline_state
    assert result.trace.final_digest == result.trace.baseline_digest
    assert result.trace.baseline_restored is True
    assert result.trace.stop_reason in {"blast_radius_exceeded", "no_progress_same_failure_and_patch", "round_budget_exhausted"}


def test_import_is_side_effect_free() -> None:
    result = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import self_heal_lab", str(HERE)], capture_output=True, text=True, check=True)
    assert result.stdout == "" and result.stderr == ""


def test_regression_restores_real_state_newest_first() -> None:
    result = run_meltdown_scene()
    assert [item.commit_id for item in result.trace.rollback_receipts] == ["c2", "c1"]
    assert result.workspace.files == result.baseline_state


def test_noop_rollback_cannot_claim_restoration() -> None:
    result = run_meltdown_scene(rollback_succeeds=False)
    assert result.trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert result.trace.stop_reason == "blast_radius_exceeded"
    assert result.trace.final_digest != result.trace.baseline_digest
    assert result.trace.baseline_restored is False
    assert result.workspace.files != result.baseline_state


def test_failed_newest_rollback_still_attempts_older_receipt() -> None:
    result = run_meltdown_scene(fail_rollback_ids={"c2"})
    assert result.workspace.rollback_attempts == ["c2", "c1"]
    assert result.trace.status is HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF
    assert result.trace.stop_reason == "blast_radius_exceeded"


def test_receipts_bind_exact_patch_and_commit() -> None:
    result = run_meltdown_scene()
    assert all(
        round_.verification_receipt.commit_id == round_.apply_receipt.commit_id
        and round_.verification_receipt.patch_digest == round_.apply_receipt.patch_digest
        for round_ in result.trace.rounds
        if round_.verification_receipt
    )
    assert [(item.commit_id, item.patch_digest) for item in result.trace.rollback_receipts] == [(item.commit_id, item.patch_digest) for item in reversed(result.trace.apply_receipts)]


def test_machine_record_contains_structured_restoration_proof() -> None:
    record = run_meltdown_scene().to_record()
    assert {"scenario", "status", "stop_reason", "baseline_digest", "final_digest", "baseline_restored", "apply_receipts", "rollback_receipts"} <= set(record)
    json.dumps(record)


def test_verify_exception_restores_real_state() -> None:
    workspace = PayrollWorkspace()
    baseline = copy.deepcopy(workspace.files)

    def verify(_receipt):
        raise RuntimeError("payroll verification crashed")

    loop = SelfHealLoop(
        diagnose=diagnose,
        fix=fix,
        review=review,
        apply=workspace.apply,
        verify=verify,
        rollback=workspace.rollback,
        state_digest=workspace.state_digest,
    )
    trace = loop.heal(
        FailureSignal(
            "test",
            "reconcile_payout includes REVERSED payslips",
            ("payout.py",),
            "PAYROLL_REVERSED_IN_PAYOUT",
        )
    )

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert workspace.files == baseline
    assert trace.final_digest == trace.baseline_digest
    assert trace.baseline_restored is True
    assert trace.stop_reason == "stage_error:verify"
    assert [item.commit_id for item in trace.rollback_receipts] == ["c1"]
