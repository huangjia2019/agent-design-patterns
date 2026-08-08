"""Small deterministic, framework-neutral Self-Heal Loop demonstration."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from pattern import (  # noqa: E402
    ApplyReceipt, FailureSignal, HealStatus, Patch, PatchReview, RollbackReceipt,
    SelfHealLoop, VerificationReceipt,
)


@dataclass
class Workspace:
    files: dict[str, dict[str, bool]] = field(default_factory=lambda: {"worker.py": {"parse_fixed": False, "validation_fixed": False}})
    snapshots: dict[str, dict[str, dict[str, bool]]] = field(default_factory=dict)
    next_commit: int = 0

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def apply(self, patch: Patch) -> ApplyReceipt:
        edits = json.loads(patch.payload)["edits"]
        candidate = copy.deepcopy(self.files)
        for path, values in edits.items():
            candidate.setdefault(path, {}).update(values)
        self.next_commit += 1
        commit = f"c{self.next_commit}"
        self.snapshots[commit] = copy.deepcopy(self.files)
        self.files = candidate
        return ApplyReceipt(commit, patch.digest, tuple(edits))

    def rollback(self, receipt: ApplyReceipt) -> RollbackReceipt:
        self.files = copy.deepcopy(self.snapshots[receipt.commit_id])
        return RollbackReceipt(receipt.commit_id, receipt.patch_digest, True, "restored exact snapshot")


def patch(description: str, edits: dict[str, dict[str, bool]]) -> Patch:
    return Patch(description, json.dumps({"edits": edits}, sort_keys=True, separators=(",", ":")), tuple(edits))


def review(candidate: Patch, _failure: FailureSignal) -> PatchReview:
    if candidate.touches_tests:
        return PatchReview(candidate.digest, False, "patch weakens the test", ("policy=source-only",))
    return PatchReview(candidate.digest, True, "", ("policy=source-only",))


def run_convergence():
    workspace = Workspace()
    def fix(code: str) -> Patch:
        return patch("repair parser", {"worker.py": {"parse_fixed": True}}) if code == "PARSE_FAILURE" else patch("repair validation", {"worker.py": {"validation_fixed": True}})
    def verify(receipt: ApplyReceipt) -> VerificationReceipt:
        failure = None
        if not workspace.files["worker.py"]["parse_fixed"]:
            failure = FailureSignal("test", "parser red", ("worker.py",), "PARSE_FAILURE")
        elif not workspace.files["worker.py"]["validation_fixed"]:
            failure = FailureSignal("test", "validation red", ("worker.py",), "VALIDATION_FAILURE")
        return VerificationReceipt(receipt.commit_id, receipt.patch_digest, failure, "worker-ci", "green" if failure is None else "red")
    loop = SelfHealLoop(diagnose=lambda failure: failure.code, fix=fix, review=review, apply=workspace.apply, verify=verify, rollback=workspace.rollback, state_digest=workspace.digest)
    trace = loop.heal(FailureSignal("test", "parser red", ("worker.py",), "PARSE_FAILURE"))
    assert trace.status is HealStatus.FIXED and len(trace.apply_receipts) == 2 and not trace.rollback_receipts and trace.baseline_restored is None
    return trace


def run_critic_block_contrast():
    workspace = Workspace()
    def fix(code: str) -> Patch:
        if code == "PARSE_FAILURE":
            return patch("safe parser repair", {"worker.py": {"parse_fixed": True}})
        return patch("weaken test", {"tests/test_worker.py": {"expected": True}})
    def verify(receipt: ApplyReceipt) -> VerificationReceipt:
        return VerificationReceipt(receipt.commit_id, receipt.patch_digest, FailureSignal("test", "validation red", ("worker.py",), "VALIDATION_FAILURE"), "worker-ci", "red")
    loop = SelfHealLoop(diagnose=lambda failure: failure.code, fix=fix, review=review, apply=workspace.apply, verify=verify, rollback=workspace.rollback, state_digest=workspace.digest)
    trace = loop.heal(FailureSignal("test", "parser red", ("worker.py",), "PARSE_FAILURE"))
    assert trace.status is HealStatus.BLOCKED_BY_CRITIC and trace.rolled_back == ("c1",) and trace.baseline_digest == trace.final_digest and trace.baseline_restored is True
    return trace


def main() -> int:
    for label, trace in (
        ("convergence", run_convergence()),
        ("critic_block", run_critic_block_contrast()),
    ):
        print(f"{label}: {trace.status.name} receipts={trace.applied_commits} stop={trace.stop_reason} baseline={trace.baseline_digest} final={trace.final_digest} restored={trace.baseline_restored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
