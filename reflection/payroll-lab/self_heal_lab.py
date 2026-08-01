"""Lecture 30: state-digest-proven bounded payroll repair scenarios."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "d-self-heal-loop"))
from pattern import (  # noqa: E402
    ApplyReceipt, FailureSignal, HealStatus, HealTrace, Patch, PatchReview,
    RollbackReceipt, SelfHealLoop, StabilityPolicy, VerificationReceipt, propose_guard,
)


@dataclass
class PayrollWorkspace:
    files: dict[str, dict[str, object]] = field(default_factory=lambda: {
        "payout.py": {"exclude_reversed": False},
        "batch.py": {"membership_check": False},
    })
    snapshots: dict[str, dict[str, dict[str, object]]] = field(default_factory=dict)
    next_commit: int = 0
    rollback_succeeds: bool = True
    fail_rollback_ids: set[str] = field(default_factory=set)
    rollback_attempts: list[str] = field(default_factory=list)

    def state_digest(self) -> str:
        body = json.dumps(self.files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def apply(self, patch: Patch) -> ApplyReceipt:
        document = json.loads(patch.payload)
        edits = document.get("edits")
        if not isinstance(edits, dict):
            raise ValueError("payload must contain an edits object")
        changed_files = tuple(sorted(edits))
        if changed_files != patch.touches:
            raise ValueError("payload edits must exactly match patch touches")
        candidate = copy.deepcopy(self.files)
        for path, assignments in edits.items():
            if not isinstance(assignments, dict):
                raise ValueError("each edit must be an object")
            candidate.setdefault(path, {}).update(assignments)
        self.next_commit += 1
        commit_id = f"c{self.next_commit}"
        self.snapshots[commit_id] = copy.deepcopy(self.files)
        self.files = candidate
        return ApplyReceipt(commit_id, patch.digest, changed_files)

    def rollback(self, receipt: ApplyReceipt) -> RollbackReceipt:
        self.rollback_attempts.append(receipt.commit_id)
        if not self.rollback_succeeds or receipt.commit_id in self.fail_rollback_ids:
            return RollbackReceipt(receipt.commit_id, receipt.patch_digest, False, "configured rollback failure")
        snapshot = self.snapshots.get(receipt.commit_id)
        if snapshot is None:
            return RollbackReceipt(receipt.commit_id, receipt.patch_digest, False, "snapshot not found")
        self.files = copy.deepcopy(snapshot)
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "restored exact pre-apply snapshot")


@dataclass
class ScenarioResult:
    name: str
    workspace: PayrollWorkspace
    baseline_state: dict[str, dict[str, object]]
    trace: HealTrace

    def to_record(self) -> dict[str, object]:
        return {
            "scenario": self.name,
            "status": self.trace.status.name,
            "stop_reason": self.trace.stop_reason,
            "baseline_digest": self.trace.baseline_digest,
            "final_digest": self.trace.final_digest,
            "baseline_restored": self.trace.baseline_restored,
            "apply_receipts": [asdict(item) for item in self.trace.apply_receipts],
            "rollback_receipts": [asdict(item) for item in self.trace.rollback_receipts],
        }


def make_patch(description: str, edits: dict[str, dict[str, object]]) -> Patch:
    return Patch(description, json.dumps({"edits": edits}, ensure_ascii=False, sort_keys=True, separators=(",", ":")), tuple(edits))


def diagnose(failure: FailureSignal) -> str:
    return failure.code or failure.signature


def fix(diagnosis: str) -> Patch:
    if diagnosis == "PAYROLL_REVERSED_IN_PAYOUT":
        return make_patch("exclude REVERSED payslips in payout builder", {"payout.py": {"exclude_reversed": True}})
    return make_patch("verify membership against HR record before binding", {"batch.py": {"membership_check": True}})


def cheat_fix(_diagnosis: str) -> Patch:
    return make_patch("raise expected total in reconcile test to match actual", {"tests/test_reconcile.py": {"expected_total": "weakened"}})


def review(patch: Patch, _failure: FailureSignal) -> PatchReview:
    if patch.touches_tests:
        return PatchReview(patch.digest, False, "patch weakens the test; the code it guards is unchanged", ("policy=test-files-blocked",))
    if len(patch.touches) > 2:
        return PatchReview(patch.digest, False, "patch touches more files than the diagnosis names", ("policy=blast-radius",))
    return PatchReview(patch.digest, True, "", ("policy=source-only",))


def ci_failure(workspace: PayrollWorkspace) -> FailureSignal | None:
    if not workspace.files["payout.py"]["exclude_reversed"]:
        return FailureSignal("test", "reconcile_payout includes REVERSED payslips", ("payout.py",), "PAYROLL_REVERSED_IN_PAYOUT")
    if not workspace.files["batch.py"]["membership_check"]:
        return FailureSignal("test", "batch_membership uses stale department", ("batch.py",), "PAYROLL_STALE_DEPARTMENT_BINDING")
    return None


def verification_receipt(receipt: ApplyReceipt, failure: FailureSignal | None) -> VerificationReceipt:
    return VerificationReceipt(receipt.commit_id, receipt.patch_digest, failure, "payroll-reconciliation", "green" if failure is None else f"red:{failure.code or failure.signature}")


def _result(name: str, workspace: PayrollWorkspace, loop: SelfHealLoop, failure: FailureSignal) -> ScenarioResult:
    baseline = copy.deepcopy(workspace.files)
    return ScenarioResult(name, workspace, baseline, loop.heal(failure))


def run_convergence_scene() -> ScenarioResult:
    workspace = PayrollWorkspace()
    loop = SelfHealLoop(diagnose=diagnose, fix=fix, review=review, apply=workspace.apply, verify=lambda receipt: verification_receipt(receipt, ci_failure(workspace)), rollback=workspace.rollback, state_digest=workspace.state_digest)
    return _result("convergence", workspace, loop, ci_failure(workspace) or FailureSignal("test", "unexpected"))


def run_critic_block_scene() -> ScenarioResult:
    workspace = PayrollWorkspace()
    def staged_fix(diagnosis: str) -> Patch:
        return fix(diagnosis) if diagnosis == "PAYROLL_REVERSED_IN_PAYOUT" else cheat_fix(diagnosis)
    def staged_verify(receipt: ApplyReceipt) -> VerificationReceipt:
        return verification_receipt(receipt, FailureSignal("test", "stale department", ("batch.py",), "PAYROLL_STALE_DEPARTMENT_BINDING"))
    loop = SelfHealLoop(diagnose=diagnose, fix=staged_fix, review=review, apply=workspace.apply, verify=staged_verify, rollback=workspace.rollback, state_digest=workspace.state_digest)
    return _result("critic-block", workspace, loop, ci_failure(workspace) or FailureSignal("test", "unexpected"))


def run_meltdown_scene(*, rollback_succeeds: bool = True, fail_rollback_ids: set[str] | None = None) -> ScenarioResult:
    workspace = PayrollWorkspace(rollback_succeeds=rollback_succeeds, fail_rollback_ids=fail_rollback_ids or set())
    def staged_fix(diagnosis: str) -> Patch:
        attempt = 1 if diagnosis == "PAYROLL_REVERSED_IN_PAYOUT" else 2
        return make_patch(f"controlled symptom repair {attempt}", {"payout.py": {f"attempt_{attempt}": True}})
    def staged_verify(receipt: ApplyReceipt) -> VerificationReceipt:
        failure = (
            FailureSignal("test", "batch binding red", ("payout.py", "batch.py"), "NEXT")
            if receipt.commit_id == "c1"
            else FailureSignal("test", "payslip regression", ("payout.py", "batch.py", "payslip_gen.py"), "REGRESSION")
        )
        return verification_receipt(receipt, failure)
    loop = SelfHealLoop(diagnose=diagnose, fix=staged_fix, review=review, apply=workspace.apply, verify=staged_verify, rollback=workspace.rollback, state_digest=workspace.state_digest)
    return _result("meltdown", workspace, loop, FailureSignal("test", "payout red", ("payout.py",), "PAYROLL_REVERSED_IN_PAYOUT"))


def run_no_progress_scene() -> ScenarioResult:
    workspace = PayrollWorkspace()
    same = FailureSignal("test", "payout red", ("payout.py",), "SAME")
    loop = SelfHealLoop(diagnose=diagnose, fix=lambda _: make_patch("same repair", {"payout.py": {"attempt": True}}), review=review, apply=workspace.apply, verify=lambda receipt: verification_receipt(receipt, same), rollback=workspace.rollback, state_digest=workspace.state_digest)
    return _result("no-progress", workspace, loop, same)


def run_round_budget_scene() -> ScenarioResult:
    workspace = PayrollWorkspace()
    def bounded_fix(diagnosis: str) -> Patch:
        attempt = 1 if diagnosis == "FIRST" else 2
        return make_patch(f"attempt {attempt}", {"payout.py": {f"attempt_{attempt}": True}})
    def bounded_verify(receipt: ApplyReceipt) -> VerificationReceipt:
        failure = (
            FailureSignal("test", "second", ("payout.py",), "SECOND")
            if receipt.commit_id == "c1"
            else FailureSignal("test", "third", ("payout.py",), "THIRD")
        )
        return verification_receipt(receipt, failure)
    loop = SelfHealLoop(diagnose=diagnose, fix=bounded_fix, review=review, apply=workspace.apply, verify=bounded_verify, rollback=workspace.rollback, state_digest=workspace.state_digest, stability=StabilityPolicy(max_rounds=2, max_radius_multiplier=4))
    return _result("round-budget", workspace, loop, FailureSignal("test", "first", ("payout.py",), "FIRST"))


def _show(result: ScenarioResult) -> None:
    for round_ in result.trace.rounds:
        print(f"   round {round_.round_no}: RED  [{round_.failure.code or round_.failure.signature}] {round_.failure.error_text}")
    print(f"   status: {result.trace.status.name}")
    if result.trace.status is not HealStatus.FIXED:
        print(f"   baseline_restored: {str(result.trace.baseline_restored).lower()}")
    print("SELF_HEAL_RESULT " + json.dumps(result.to_record(), sort_keys=True, separators=(",", ":")))


def _render_meltdown() -> None:
    print("== scene 3 (--meltdown): the incident, then bounded repair ==")
    print("   naive loop (no critic, no signature check, no atomic commits):")
    for number in range(1, 10):
        print(f"      round {number}: RED  [naive-{number}] simulated payroll symptom")
    print("   distinct failure classes: 7")
    print("\n   same fixer under the bounded stop policy:")
    result = run_meltdown_scene()
    _show(result)
    print(f"      rolled back, newest first: {[item.commit_id for item in result.trace.rollback_receipts]}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meltdown", action="store_true")
    args = parser.parse_args(argv)
    if args.meltdown:
        _render_meltdown()
        return 0
    print("== scene 1: two red lights, two rounds, green ==")
    convergence = run_convergence_scene()
    _show(convergence)
    guard = propose_guard(convergence.trace.rounds[0].failure.signature, ["teaching-run-2026-06", "teaching-run-2026-07"])
    print(f"   propose guard: {guard}")
    print("\n== scene 2: the cheating patch ==")
    _show(run_critic_block_scene())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
