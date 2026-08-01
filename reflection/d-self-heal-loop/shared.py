"""Deterministic fixtures shared by the Self-Heal reference notebooks.

The transaction authority remains in :mod:`pattern`; this module supplies only
strict model parsing, an in-memory workspace, and scenario callbacks.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

from pattern import (
    ApplyReceipt,
    FailureSignal,
    HealStage,
    HealStatus,
    HealTrace,
    Patch,
    PatchReview,
    RollbackReceipt,
    SelfHealLoop,
    StabilityPolicy,
    VerificationReceipt,
)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(raw: str) -> object:
    if not isinstance(raw, str):
        raise TypeError("JSON input must be a string")
    return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)


def _decode_payload(payload: str) -> dict[str, str]:
    decoded = _load_json(payload)
    if not isinstance(decoded, dict) or set(decoded) != {"set"}:
        raise ValueError("payload must contain only a set object")
    replacements = decoded["set"]
    if not isinstance(replacements, dict) or not replacements:
        raise ValueError("set must be a nonempty object")
    if any(
        not isinstance(path, str) or not isinstance(text, str)
        for path, text in replacements.items()
    ):
        raise TypeError("set paths and replacement texts must be strings")
    return replacements


def _canonical_payload(replacements: Mapping[str, str]) -> str:
    return json.dumps(
        {"set": dict(replacements)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def parse_diagnosis_json(raw: str) -> str:
    """Accept exactly one nonblank diagnosis string from a model response."""
    decoded = _load_json(raw)
    if not isinstance(decoded, dict) or set(decoded) != {"diagnosis"}:
        raise ValueError("diagnosis response must contain only diagnosis")
    diagnosis = decoded["diagnosis"]
    if not isinstance(diagnosis, str):
        raise TypeError("diagnosis must be a string")
    if not diagnosis.strip():
        raise ValueError("diagnosis must be nonblank")
    return diagnosis


def parse_patch_json(raw: str) -> Patch:
    """Parse a canonical patch model response without changing its identity."""
    decoded = _load_json(raw)
    if not isinstance(decoded, dict) or set(decoded) != {
        "description",
        "payload",
        "touches",
    }:
        raise ValueError("patch response must contain description, payload, and touches")
    description = decoded["description"]
    payload = decoded["payload"]
    touches = decoded["touches"]
    if not isinstance(description, str) or not description.strip():
        raise ValueError("description must be a nonblank string")
    if not isinstance(payload, str):
        raise TypeError("payload must be a string")
    if not isinstance(touches, list) or any(not isinstance(path, str) for path in touches):
        raise TypeError("touches must be a list of strings")
    replacements = _decode_payload(payload)
    if payload != _canonical_payload(replacements):
        raise ValueError("payload must use canonical JSON")
    patch = Patch(description, payload, tuple(touches))
    if tuple(sorted(replacements)) != patch.touches:
        raise ValueError("payload paths must exactly match canonical touches")
    return patch


@dataclass
class MemoryWorkspace:
    """A snapshotting workspace that produces receipt-bound mutations."""

    files: dict[str, str]
    snapshots: dict[str, dict[str, str]] = field(default_factory=dict)
    rollback_attempts: list[str] = field(default_factory=list)
    next_commit: int = 0
    failed_rollbacks: set[str] = field(default_factory=set)

    def state_digest(self) -> str:
        body = json.dumps(self.files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def apply(self, patch: Patch) -> ApplyReceipt:
        replacements = _decode_payload(patch.payload)
        if tuple(sorted(replacements)) != patch.touches:
            raise ValueError("patch payload paths must equal touches")
        self.next_commit += 1
        commit_id = f"c{self.next_commit}"
        self.snapshots[commit_id] = dict(self.files)
        self.files.update(replacements)
        return ApplyReceipt(commit_id, patch.digest, patch.touches)

    def rollback(self, receipt: ApplyReceipt) -> RollbackReceipt:
        self.rollback_attempts.append(receipt.commit_id)
        if receipt.commit_id in self.failed_rollbacks:
            return RollbackReceipt(
                receipt.commit_id,
                receipt.patch_digest,
                False,
                "configured rollback failure retained the applied workspace",
            )
        try:
            snapshot = self.snapshots[receipt.commit_id]
        except KeyError as exc:
            raise ValueError(f"unknown commit for rollback: {receipt.commit_id}") from exc
        self.files = dict(snapshot)
        return RollbackReceipt(
            receipt.commit_id,
            receipt.patch_digest,
            True,
            "restored exact pre-apply snapshot",
        )


@dataclass(frozen=True)
class _PatchPlan:
    description: str
    replacements: tuple[tuple[str, str], ...]

    def patch(self) -> Patch:
        replacements = dict(self.replacements)
        return Patch(
            self.description,
            _canonical_payload(replacements),
            tuple(sorted(replacements)),
        )


@dataclass(frozen=True)
class _ReviewPlan:
    approved: bool
    reason: str = ""


@dataclass(frozen=True)
class _VerificationPlan:
    failure: FailureSignal | None = None
    exception: str | None = None


@dataclass(frozen=True)
class _Scenario:
    name: str
    initial_state: tuple[tuple[str, str], ...]
    initial_failure: FailureSignal
    diagnoses: tuple[str, ...]
    patches: tuple[_PatchPlan, ...]
    reviews: tuple[_ReviewPlan, ...]
    verifications: tuple[_VerificationPlan, ...]
    stability: StabilityPolicy
    failed_rollbacks: frozenset[str] = frozenset()


def _failure(code: str, files: tuple[str, ...] = ("app.py",)) -> FailureSignal:
    return FailureSignal("deterministic-ci", f"scenario failure: {code}", files, code)


SCENARIO_ORDER = (
    "convergence",
    "critic_block",
    "no_progress",
    "regression",
    "round_budget",
    "stage_error",
    "rollback_failure",
)


_SCENARIOS: Mapping[str, _Scenario] = MappingProxyType(
    {
        "convergence": _Scenario(
            "convergence",
            (("app.py", "broken-v1"),),
            _failure("CONVERGENCE_1"),
            ("repair first failing branch", "repair second failing branch"),
            (
                _PatchPlan("repair first branch", (("app.py", "partial-fix"),)),
                _PatchPlan("repair second branch", (("app.py", "fixed"),)),
            ),
            (_ReviewPlan(True), _ReviewPlan(True)),
            (_VerificationPlan(_failure("CONVERGENCE_2")), _VerificationPlan()),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
        ),
        "critic_block": _Scenario(
            "critic_block",
            (("app.py", "broken-v1"),),
            _failure("CRITIC_BLOCK_1"),
            ("repair the first failing branch", "propose a prohibited second repair"),
            (
                _PatchPlan("repair first branch", (("app.py", "partial-fix"),)),
                _PatchPlan(
                    "add prohibited dependency",
                    (("app.py", "dependency-added"),),
                ),
            ),
            (
                _ReviewPlan(True),
                _ReviewPlan(False, "policy rejects the proposed dependency"),
            ),
            (_VerificationPlan(_failure("CRITIC_BLOCK_2")),),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
        ),
        "no_progress": _Scenario(
            "no_progress",
            (("app.py", "broken-v1"),),
            _failure("NO_PROGRESS"),
            ("repeat the same repair", "repeat the same repair"),
            (
                _PatchPlan("repeat repair", (("app.py", "still-broken"),)),
                _PatchPlan("repeat repair", (("app.py", "still-broken"),)),
            ),
            (_ReviewPlan(True),),
            (_VerificationPlan(_failure("NO_PROGRESS")),),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
        ),
        "regression": _Scenario(
            "regression",
            (("app.py", "broken-v1"),),
            _failure("REGRESSION_1"),
            ("repair focused branch", "repair expanded branch"),
            (
                _PatchPlan("repair focused branch", (("app.py", "partial-fix"),)),
                _PatchPlan(
                    "repair expanded branch",
                    (("tests/regression.py", "new regression coverage"),),
                ),
            ),
            (_ReviewPlan(True), _ReviewPlan(True)),
            (
                _VerificationPlan(
                    _failure("REGRESSION_2", ("app.py", "tests/regression.py"))
                ),
                _VerificationPlan(
                    _failure(
                        "REGRESSION_3",
                        ("app.py", "tests/regression.py", "docs/impact.md"),
                    )
                ),
            ),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
        ),
        "round_budget": _Scenario(
            "round_budget",
            (("app.py", "broken-v1"),),
            _failure("BUDGET_1"),
            ("first bounded repair", "second bounded repair"),
            (
                _PatchPlan("first bounded repair", (("app.py", "attempt-one"),)),
                _PatchPlan("second bounded repair", (("app.py", "attempt-two"),)),
            ),
            (_ReviewPlan(True), _ReviewPlan(True)),
            (
                _VerificationPlan(_failure("BUDGET_2")),
                _VerificationPlan(_failure("BUDGET_3")),
            ),
            StabilityPolicy(max_rounds=2, max_radius_multiplier=2.0),
        ),
        "stage_error": _Scenario(
            "stage_error",
            (("app.py", "broken-v1"),),
            _failure("STAGE_ERROR"),
            ("repair before verifier outage",),
            (_PatchPlan("repair before verifier outage", (("app.py", "attempted-fix"),)),),
            (_ReviewPlan(True),),
            (_VerificationPlan(exception="configured verifier outage"),),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
        ),
        "rollback_failure": _Scenario(
            "rollback_failure",
            (("app.py", "broken-v1"),),
            _failure("ROLLBACK_FAILURE_1"),
            ("repair that later needs rollback", "second repair is rejected"),
            (
                _PatchPlan("first repair", (("app.py", "applied-but-unrestored"),)),
                _PatchPlan("rejected second repair", (("app.py", "not-applied"),)),
            ),
            (_ReviewPlan(True), _ReviewPlan(False, "review rejects second patch")),
            (_VerificationPlan(_failure("ROLLBACK_FAILURE_2")),),
            StabilityPolicy(max_rounds=3, max_radius_multiplier=2.0),
            frozenset({"c1"}),
        ),
    }
)

if tuple(_SCENARIOS) != SCENARIO_ORDER:
    raise RuntimeError("Self-Heal scenarios must match the locked order")


@dataclass
class ScenarioRuntime:
    """Fresh callback state for exactly one scenario execution."""

    scenario: _Scenario
    workspace: MemoryWorkspace
    role_indices: dict[str, int] = field(default_factory=dict)

    def _next(self, role: str, values: tuple[object, ...]) -> object:
        index = self.role_indices.get(role, 0)
        if index >= len(values):
            raise RuntimeError(f"scenario callback {role!r} exhausted at call {index + 1}")
        self.role_indices[role] = index + 1
        return values[index]

    def diagnose(self, _failure_signal: FailureSignal) -> str:
        value = self._next("diagnose", self.scenario.diagnoses)
        assert isinstance(value, str)
        return value

    def fix(self, _diagnosis: str) -> Patch:
        value = self._next("fix", self.scenario.patches)
        assert isinstance(value, _PatchPlan)
        return value.patch()

    def review(self, patch: Patch, _failure_signal: FailureSignal) -> PatchReview:
        index = self.role_indices.get("review", 0)
        value = self._next("review", self.scenario.reviews)
        assert isinstance(value, _ReviewPlan)
        expected_patch = self.scenario.patches[index].patch()
        matches_scope = patch.touches == expected_patch.touches
        matches_semantics = patch.digest == expected_patch.digest
        approved = value.approved and matches_semantics
        if not matches_scope:
            reason = "patch touches files outside the current repair scope"
        elif not matches_semantics:
            reason = "patch content does not satisfy the current failure"
        else:
            reason = "" if approved else value.reason
        return PatchReview(
            patch.digest,
            approved,
            reason,
            (
                "policy=scenario-repair-contract",
                f"expected_patch_digest={expected_patch.digest}",
                f"patch_digest={patch.digest}",
            ),
        )

    def verify(self, receipt: ApplyReceipt) -> VerificationReceipt:
        index = self.role_indices.get("verify", 0)
        value = self._next("verify", self.scenario.verifications)
        assert isinstance(value, _VerificationPlan)
        if value.exception is not None:
            raise RuntimeError(value.exception)
        expected_patch = self.scenario.patches[index].patch()
        replacements = dict(self.scenario.patches[index].replacements)
        mismatches = tuple(
            path
            for path, expected_text in replacements.items()
            if self.workspace.files.get(path) != expected_text
        )
        if receipt.patch_digest != expected_patch.digest:
            mismatches = tuple(sorted(set((*mismatches, *expected_patch.touches))))
        failure = value.failure
        if mismatches:
            failure = _failure(
                f"STATE_MISMATCH_{self.scenario.name.upper()}_{index + 1}",
                mismatches,
            )
        return VerificationReceipt(
            receipt.commit_id,
            receipt.patch_digest,
            failure,
            "deterministic-workspace-check",
            "workspace matches reviewed patch"
            if failure is None
            else f"failure={failure.code}",
        )


def new_runtime(name: str) -> ScenarioRuntime:
    """Build a fresh mutable workspace and callback counters for one scenario."""
    try:
        scenario = _SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"unknown Self-Heal scenario: {name}") from exc
    return ScenarioRuntime(
        scenario,
        MemoryWorkspace(dict(scenario.initial_state), failed_rollbacks=set(scenario.failed_rollbacks)),
    )


def run_core_reference(name: str) -> tuple[HealTrace, ScenarioRuntime]:
    """Run the sealed core against one deterministic fixture runtime."""
    runtime = new_runtime(name)
    loop = SelfHealLoop(
        diagnose=runtime.diagnose,
        fix=runtime.fix,
        review=runtime.review,
        apply=runtime.workspace.apply,
        verify=runtime.verify,
        rollback=runtime.workspace.rollback,
        state_digest=runtime.workspace.state_digest,
        stability=runtime.scenario.stability,
    )
    return loop.heal(runtime.scenario.initial_failure), runtime


RECORD_FIELDS = (
    "scenario",
    "status",
    "stop_reason",
    "baseline_digest",
    "final_digest",
    "baseline_restored",
    "apply_receipts",
    "verification_receipts",
    "rollback_receipts",
    "stage_errors",
)


def trace_record(name: str, trace: HealTrace) -> dict[str, object]:
    """Serialize a trace with stable JSON-safe shapes for notebook comparison."""
    apply_receipts = [
        {
            "commit_id": receipt.commit_id,
            "patch_digest": receipt.patch_digest,
            "changed_files": list(receipt.changed_files),
        }
        for receipt in trace.apply_receipts
    ]
    verification_receipts = [
        {
            "commit_id": receipt.commit_id,
            "patch_digest": receipt.patch_digest,
            "failure_signature": (
                receipt.failure.signature if receipt.failure is not None else None
            ),
            "check": receipt.check,
            "evidence": receipt.evidence,
        }
        for round_ in trace.rounds
        if (receipt := round_.verification_receipt) is not None
    ]
    return {
        "scenario": name,
        "status": trace.status.value,
        "stop_reason": trace.stop_reason,
        "baseline_digest": trace.baseline_digest,
        "final_digest": trace.final_digest,
        "baseline_restored": trace.baseline_restored,
        "apply_receipts": apply_receipts,
        "verification_receipts": verification_receipts,
        "rollback_receipts": [
            {
                "commit_id": receipt.commit_id,
                "patch_digest": receipt.patch_digest,
                "succeeded": receipt.succeeded,
                "detail": receipt.detail,
            }
            for receipt in trace.rollback_receipts
        ],
        "stage_errors": [
            {
                "stage": error.stage.value,
                "round_no": error.round_no,
                "exception_type": error.exception_type,
                "message": error.message,
                "evidence": list(error.evidence),
            }
            for error in trace.stage_errors
        ],
    }


def _record_items_for_display(
    record: Mapping[str, object],
    field: str,
) -> list[Mapping[str, object]]:
    value = record[field]
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise ValueError(f"{field} must be a list of mappings")
    return list(value)


def _restoration_label(value: object) -> str:
    if value is None:
        return "-"
    return "yes" if value is True else "no"


def format_scenario_matrix(
    records: Sequence[Mapping[str, object]],
) -> str:
    """Render public outcomes without dumping receipt bodies or full digests."""
    headers = (
        "scenario",
        "status",
        "apply",
        "verify",
        "rollback",
        "restored",
        "reason",
    )
    rows: list[tuple[str, ...]] = []
    for record in records:
        if tuple(record) != RECORD_FIELDS:
            raise ValueError("record fields differ from the public contract")
        applies = _record_items_for_display(record, "apply_receipts")
        verifies = _record_items_for_display(record, "verification_receipts")
        rollbacks = _record_items_for_display(record, "rollback_receipts")
        rollback_order = " -> ".join(
            f"{item['commit_id']}{'' if item['succeeded'] is True else ' (failed)'}"
            for item in rollbacks
        ) or "-"
        rows.append(
            (
                str(record["scenario"]),
                str(record["status"]),
                str(len(applies)),
                str(len(verifies)),
                rollback_order,
                _restoration_label(record["baseline_restored"]),
                str(record["stop_reason"]),
            )
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def line(values: tuple[str, ...]) -> str:
        return "  ".join(
            value.ljust(widths[index]) for index, value in enumerate(values)
        ).rstrip()

    return "\n".join(
        (
            line(headers),
            line(tuple("-" * width for width in widths)),
            *(line(row) for row in rows),
        )
    )


def _short_digest(value: object) -> str:
    return value[:8] if isinstance(value, str) and value else "-"


def format_scenario_walkthrough(record: Mapping[str, object]) -> str:
    """Show the receipt chain for one scenario in at most a few short lines."""
    if tuple(record) != RECORD_FIELDS:
        raise ValueError("record fields differ from the public contract")
    applies = _record_items_for_display(record, "apply_receipts")
    verifies = {
        item["commit_id"]: item
        for item in _record_items_for_display(record, "verification_receipts")
    }
    rollbacks = _record_items_for_display(record, "rollback_receipts")

    lines = [
        f"scenario: {record['scenario']}",
        f"outcome: {record['status']} ({record['stop_reason']})",
    ]
    for number, receipt in enumerate(applies, start=1):
        commit_id = receipt["commit_id"]
        verification = verifies.get(commit_id)
        if verification is None:
            result = "verification produced no receipt"
        elif verification["failure_signature"] is None:
            result = "verification passed"
        else:
            result = (
                "verification failed "
                f"{_short_digest(verification['failure_signature'])}"
            )
        lines.append(
            f"round {number}: apply {commit_id} "
            f"patch {_short_digest(receipt['patch_digest'])}; {result}"
        )
    for receipt in rollbacks:
        result = "succeeded" if receipt["succeeded"] is True else "failed"
        lines.append(f"rollback {receipt['commit_id']}: {result}")
    lines.append(f"baseline restored: {_restoration_label(record['baseline_restored'])}")
    return "\n".join(lines)


@dataclass(frozen=True)
class _ExpectedRecord:
    status: HealStatus
    stop_reason: str
    applies: tuple[str, ...]
    verifications: tuple[str, ...]
    verification_has_failure: tuple[bool, ...]
    rollbacks: tuple[str, ...]
    rollback_succeeded: tuple[bool, ...]
    baseline_restored: bool | None
    stage_errors: tuple[tuple[HealStage, int | None, str], ...] = ()


_EXPECTED_RECORDS: Mapping[str, _ExpectedRecord] = MappingProxyType(
    {
        "convergence": _ExpectedRecord(
            HealStatus.FIXED,
            "verification_passed",
            ("c1", "c2"),
            ("c1", "c2"),
            (True, False),
            (),
            (),
            None,
        ),
        "critic_block": _ExpectedRecord(
            HealStatus.BLOCKED_BY_CRITIC,
            "review_rejected",
            ("c1",),
            ("c1",),
            (True,),
            ("c1",),
            (True,),
            True,
        ),
        "no_progress": _ExpectedRecord(
            HealStatus.ROLLED_BACK_NO_PROGRESS,
            "no_progress_same_failure_and_patch",
            ("c1",),
            ("c1",),
            (True,),
            ("c1",),
            (True,),
            True,
        ),
        "regression": _ExpectedRecord(
            HealStatus.ROLLED_BACK_REGRESSION,
            "blast_radius_exceeded",
            ("c1", "c2"),
            ("c1", "c2"),
            (True, True),
            ("c2", "c1"),
            (True, True),
            True,
        ),
        "round_budget": _ExpectedRecord(
            HealStatus.MAX_ROUNDS_HUMAN_HANDOFF,
            "round_budget_exhausted",
            ("c1", "c2"),
            ("c1", "c2"),
            (True, True),
            ("c2", "c1"),
            (True, True),
            True,
        ),
        "stage_error": _ExpectedRecord(
            HealStatus.STAGE_ERROR_HUMAN_HANDOFF,
            "stage_error:verify",
            ("c1",),
            (),
            (),
            ("c1",),
            (True,),
            True,
            ((HealStage.VERIFY, 1, "RuntimeError"),),
        ),
        "rollback_failure": _ExpectedRecord(
            HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF,
            "review_rejected",
            ("c1",),
            ("c1",),
            (True,),
            ("c1",),
            (False,),
            False,
            ((HealStage.ROLLBACK, None, "ValueError"),),
        ),
    }
)


def _record_items(
    value: object,
    fields: tuple[str, ...],
    label: str,
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise AssertionError(f"{label} must be a list")
    items: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping) or tuple(item) != fields:
            raise AssertionError(f"{label} fields differ from contract")
        items.append(item)
    return items


def _is_hex_digest(value: object, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def assert_expected_record(record: Mapping[str, object]) -> None:
    """Validate the complete normalized transaction and receipt-binding chain."""
    if tuple(record) != RECORD_FIELDS:
        raise AssertionError(f"record keys differ from contract: {tuple(record)}")
    name = record["scenario"]
    if not isinstance(name, str) or name not in _EXPECTED_RECORDS:
        raise AssertionError(f"unknown scenario record: {name!r}")
    expected = _EXPECTED_RECORDS[name]
    if record["status"] != expected.status.value:
        raise AssertionError(f"unexpected status for {name}")
    if record["stop_reason"] != expected.stop_reason:
        raise AssertionError(f"unexpected stop reason for {name}")

    applies = _record_items(
        record["apply_receipts"],
        ("commit_id", "patch_digest", "changed_files"),
        "apply_receipts",
    )
    verifications = _record_items(
        record["verification_receipts"],
        ("commit_id", "patch_digest", "failure_signature", "check", "evidence"),
        "verification_receipts",
    )
    rollbacks = _record_items(
        record["rollback_receipts"],
        ("commit_id", "patch_digest", "succeeded", "detail"),
        "rollback_receipts",
    )
    stage_errors = _record_items(
        record["stage_errors"],
        ("stage", "round_no", "exception_type", "message", "evidence"),
        "stage_errors",
    )

    if [item["commit_id"] for item in applies] != list(expected.applies):
        raise AssertionError(f"unexpected apply receipt order for {name}")
    apply_by_commit: dict[str, Mapping[str, object]] = {}
    for receipt in applies:
        commit_id = receipt["commit_id"]
        patch_digest = receipt["patch_digest"]
        changed_files = receipt["changed_files"]
        if not isinstance(commit_id, str) or not commit_id.strip():
            raise AssertionError(f"invalid apply commit ID for {name}")
        if commit_id in apply_by_commit or not _is_hex_digest(patch_digest, 64):
            raise AssertionError(f"invalid apply identity for {name}")
        if (
            not isinstance(changed_files, list)
            or not changed_files
            or any(
                not isinstance(path, str) or not path.strip()
                for path in changed_files
            )
        ):
            raise AssertionError(f"invalid changed files for {name}")
        try:
            canonical_files = Patch(
                "validate receipt paths",
                "{}",
                tuple(changed_files),
            ).touches
        except (TypeError, ValueError) as exc:
            raise AssertionError(f"invalid changed files for {name}") from exc
        if list(canonical_files) != changed_files:
            raise AssertionError(f"noncanonical changed files for {name}")
        apply_by_commit[commit_id] = receipt

    if [item["commit_id"] for item in verifications] != list(
        expected.verifications
    ):
        raise AssertionError(f"unexpected verification receipt order for {name}")
    for index, receipt in enumerate(verifications):
        commit_id = receipt["commit_id"]
        applied = apply_by_commit.get(commit_id) if isinstance(commit_id, str) else None
        if applied is None or receipt["patch_digest"] != applied["patch_digest"]:
            raise AssertionError(f"misbound verification receipt for {name}")
        failure_signature = receipt["failure_signature"]
        has_failure = failure_signature is not None
        if has_failure != expected.verification_has_failure[index]:
            raise AssertionError(f"unexpected verification result for {name}")
        if has_failure and not _is_hex_digest(failure_signature, 12):
            raise AssertionError(f"invalid failure signature for {name}")
        if not isinstance(receipt["check"], str) or not receipt["check"].strip():
            raise AssertionError(f"invalid verification check for {name}")
        if not isinstance(receipt["evidence"], str) or not receipt["evidence"].strip():
            raise AssertionError(f"invalid verification evidence for {name}")

    if [item["commit_id"] for item in rollbacks] != list(expected.rollbacks):
        raise AssertionError(f"unexpected rollback receipt order for {name}")
    for index, receipt in enumerate(rollbacks):
        commit_id = receipt["commit_id"]
        applied = apply_by_commit.get(commit_id) if isinstance(commit_id, str) else None
        if applied is None or receipt["patch_digest"] != applied["patch_digest"]:
            raise AssertionError(f"misbound rollback receipt for {name}")
        if receipt["succeeded"] is not expected.rollback_succeeded[index]:
            raise AssertionError(f"unexpected rollback result for {name}")
        if not isinstance(receipt["detail"], str) or not receipt["detail"].strip():
            raise AssertionError(f"invalid rollback detail for {name}")

    actual_stage_errors: list[tuple[str, int | None, str]] = []
    for error in stage_errors:
        round_no = error["round_no"]
        if round_no is not None and type(round_no) is not int:
            raise AssertionError(f"invalid stage-error round for {name}")
        exception_type = error["exception_type"]
        message = error["message"]
        evidence = error["evidence"]
        if not isinstance(exception_type, str) or not exception_type.strip():
            raise AssertionError(f"invalid stage-error type for {name}")
        if not isinstance(message, str) or not message.strip():
            raise AssertionError(f"invalid stage-error message for {name}")
        if (
            not isinstance(evidence, list)
            or len(evidence) > 8
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
        ):
            raise AssertionError(f"invalid stage-error evidence for {name}")
        stage = error["stage"]
        if not isinstance(stage, str):
            raise AssertionError(f"invalid stage-error stage for {name}")
        actual_stage_errors.append((stage, round_no, exception_type))
    expected_stage_errors = [
        (stage.value, round_no, exception_type)
        for stage, round_no, exception_type in expected.stage_errors
    ]
    if actual_stage_errors != expected_stage_errors:
        raise AssertionError(f"unexpected stage errors for {name}")

    if record["baseline_restored"] is not expected.baseline_restored:
        raise AssertionError(f"unexpected restoration result for {name}")
    baseline = record["baseline_digest"]
    final = record["final_digest"]
    if not _is_hex_digest(baseline, 64) or not _is_hex_digest(final, 64):
        raise AssertionError(f"scenario {name} must provide baseline and final digests")
    if expected.baseline_restored is True and baseline != final:
        raise AssertionError(f"restored scenario {name} changed its baseline digest")
    if expected.baseline_restored is False and baseline == final:
        raise AssertionError(f"failed rollback scenario {name} claims restoration")
    if expected.baseline_restored is None and baseline == final:
        raise AssertionError(f"fixed scenario {name} did not retain its repair")
