"""Lecture 43: assemble eight real pattern modules around one payroll run.

The lab compares two integration styles:

``local-only``
    Every module reports local acceptance, but adapters do not carry parent
    receipt identities and governance remains bound to a stale report.

``bound``
    The same module outputs are connected by one immutable run contract,
    artifact digests, parent receipts, approval identity, and SQLite endpoint
    checks.

The local-only variant is a wiring ablation. It does not ask a model to make a
mistake and it does not weaken the individual pattern implementations.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import sqlite3
import sys
from dataclasses import asdict, replace
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load(relative_path: str, module_name: str) -> ModuleType:
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ASSEMBLY = _load(
    "composition/c-argus-full-case/pattern.py",
    "composition_capstone_assembly",
)
TRIAGE = _load(
    "perception/a-context-triage/pattern.py",
    "composition_capstone_triage",
)
HYPOTHESIS = _load(
    "reasoning/d-iterative-hypothesis/pattern.py",
    "composition_capstone_hypothesis",
)
PLAN = _load(
    "action/b-plan-and-execute/pattern.py",
    "composition_capstone_plan",
)
REFLECTION = _load(
    "reflection/a-generator-critic/pattern.py",
    "composition_capstone_reflection",
)
HANDOFF = _load(
    "collaboration/d-handoff-chain/pattern.py",
    "composition_capstone_handoff",
)
APPROVAL = _load(
    "governance/a-approval-gate/pattern.py",
    "composition_capstone_approval",
)
MEMORY = _load(
    "memory/c-progress-tracking/pattern.py",
    "composition_capstone_memory",
)


MONTH = "2026-06"
RUN_ID = f"payroll-close-{MONTH}"
WORKLOAD_REF = f"sqlite://payroll/{MONTH}/month-end-v1"
BASELINE_DB = REPO_ROOT / "action" / "payroll-lab" / "payroll.baseline.db"
STALE_REPORT = (
    f"MONTHLY-REPORT month={MONTH} paid=800 reversed=0 "
    "exceptions=none conclusion=all-clear"
)
PATTERNS = {
    ASSEMBLY.ModuleName.COMPOSITION: "Full System Assembly",
    ASSEMBLY.ModuleName.PERCEPTION: "Context Triage",
    ASSEMBLY.ModuleName.COLLABORATION: "Handoff Chain",
    ASSEMBLY.ModuleName.REASONING: "Iterative Hypothesis",
    ASSEMBLY.ModuleName.ACTION: "Plan and Execute",
    ASSEMBLY.ModuleName.REFLECTION: "Generator-Critic",
    ASSEMBLY.ModuleName.GOVERNANCE: "Approval Gate",
    ASSEMBLY.ModuleName.MEMORY: "Progress Tracking",
}
PURPOSES = {
    ASSEMBLY.ModuleName.COMPOSITION: "bind one system decision and evidence spine",
    ASSEMBLY.ModuleName.PERCEPTION: "keep current ledger facts in context",
    ASSEMBLY.ModuleName.COLLABORATION: "move typed facts across specialist seams",
    ASSEMBLY.ModuleName.REASONING: "diagnose the stale month-end report",
    ASSEMBLY.ModuleName.ACTION: "build a versioned release artifact",
    ASSEMBLY.ModuleName.REFLECTION: "review the artifact against ledger evidence",
    ASSEMBLY.ModuleName.GOVERNANCE: "approve the exact reviewed artifact",
    ASSEMBLY.ModuleName.MEMORY: "persist the accepted run checkpoint",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _fixture() -> sqlite3.Connection:
    """Copy the tracked payroll fixture into an isolated in-memory database."""

    source = sqlite3.connect(f"file:{BASELINE_DB}?mode=ro", uri=True)
    connection = sqlite3.connect(":memory:")
    source.backup(connection)
    source.close()
    connection.execute(
        "UPDATE payroll SET status='PAID', note='' WHERE month=?",
        (MONTH,),
    )
    connection.execute(
        "UPDATE payroll SET status='REVERSED' "
        "WHERE month=? AND emp_id IN ('E0007', 'E0012')",
        (MONTH,),
    )
    connection.execute(
        """
        CREATE TABLE releases (
            run_id TEXT PRIMARY KEY,
            report_digest TEXT NOT NULL,
            approval_ref TEXT NOT NULL,
            paid_count INTEGER NOT NULL,
            reversed_count INTEGER NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def _truth(connection: sqlite3.Connection) -> dict[str, Any]:
    paid_count = int(
        connection.execute(
            "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
            (MONTH,),
        ).fetchone()[0]
    )
    reversed_ids = tuple(
        row[0]
        for row in connection.execute(
            "SELECT emp_id FROM payroll "
            "WHERE month=? AND status='REVERSED' ORDER BY emp_id",
            (MONTH,),
        )
    )
    paid_total = float(
        connection.execute(
            "SELECT SUM(e.base_salary) FROM payroll p "
            "JOIN employees e ON e.emp_id=p.emp_id "
            "WHERE p.month=? AND p.status='PAID'",
            (MONTH,),
        ).fetchone()[0]
    )
    return {
        "paid_count": paid_count,
        "reversed_count": len(reversed_ids),
        "reversed_ids": reversed_ids,
        "paid_total": paid_total,
    }


def _contract() -> Any:
    selection_payload = {
        "workload": WORKLOAD_REF,
        "patterns": tuple(
            (module.value, PATTERNS[module]) for module in ASSEMBLY.MODULE_ORDER
        ),
        "decision": "adopt evidence-bound payroll close",
    }
    selection_digest = ASSEMBLY.stable_digest(selection_payload)
    return ASSEMBLY.SystemRunContract(
        run_id=RUN_ID,
        version=1,
        goal="release one reconciled month-end payroll report",
        workload_ref=WORKLOAD_REF,
        workload_digest=ASSEMBLY.stable_digest(WORKLOAD_REF),
        selection_receipt_digest=selection_digest,
        pattern_bindings=tuple(
            ASSEMBLY.PatternBinding(module, PATTERNS[module], PURPOSES[module])
            for module in ASSEMBLY.MODULE_ORDER
        ),
    )


def _context_triage() -> dict[str, Any]:
    items = [
        TRIAGE.ContextItem(
            "goal-contract",
            "Release the reconciled June payroll report.",
            TRIAGE.Priority.CRITICAL,
            token_estimate=20,
        ),
        TRIAGE.ContextItem(
            "current-ledger",
            "SQLite payroll status for June.",
            TRIAGE.Priority.IMPORTANT,
            token_estimate=30,
        ),
        TRIAGE.ContextItem(
            "stale-report",
            STALE_REPORT,
            TRIAGE.Priority.IMPORTANT,
            token_estimate=35,
        ),
        TRIAGE.ContextItem(
            "release-policy",
            "High-value payroll release needs independent approval.",
            TRIAGE.Priority.SUPPORTING,
            token_estimate=30,
        ),
        TRIAGE.ContextItem(
            "generic-agent-background",
            "General background that can be retrieved later.",
            TRIAGE.Priority.DEFERRABLE,
            token_estimate=50,
        ),
    ]
    selected, deferred, decision = TRIAGE.ContextTriage(budget=120).triage(items)
    return {
        "selected": tuple(item.name for item in selected),
        "deferred": tuple(item.name for item in deferred),
        "tokens_used": decision.tokens_used,
        "decision_ref": f"triage://{RUN_ID}/v1",
    }


def _handoff(
    connection: sqlite3.Connection,
    context_digest: str,
) -> dict[str, Any]:
    task = HANDOFF.TaskContract(
        contract_id=f"payroll-evidence-{MONTH}",
        version=1,
        objective="produce typed month-end facts for report diagnosis",
        output_schema="PayrollEvidenceBundle",
        accountable_owner="payroll-controller",
        input_refs=(f"context://{context_digest}", WORKLOAD_REF),
        constraints=(
            "ledger facts have one owner",
            "every fact carries source evidence",
        ),
    )

    async def ledger_reader(_view):
        truth = _truth(connection)
        ledger_ref = f"sqlite://payroll.db/payroll?month={MONTH}"
        return HANDOFF.StageDelta(
            facts=(
                HANDOFF.FactValue(
                    "paid_count",
                    truth["paid_count"],
                    (ledger_ref,),
                ),
                HANDOFF.FactValue(
                    "reversed_ids",
                    truth["reversed_ids"],
                    (ledger_ref,),
                ),
                HANDOFF.FactValue(
                    "paid_total",
                    truth["paid_total"],
                    (ledger_ref,),
                ),
            )
        )

    async def evidence_packager(view):
        bundle = {
            "paid_count": view.facts["paid_count"],
            "reversed_count": len(view.facts["reversed_ids"]),
            "reversed_ids": view.facts["reversed_ids"],
            "paid_total": view.facts["paid_total"],
            "stale_report": STALE_REPORT,
        }
        return HANDOFF.StageDelta(
            facts=(
                HANDOFF.FactValue(
                    "evidence_bundle",
                    bundle,
                    (
                        f"sqlite://payroll.db/payroll?month={MONTH}",
                        f"artifact://monthly-report/{MONTH}/stale",
                    ),
                ),
            ),
            artifact_refs=(f"artifact://payroll-evidence/{MONTH}/v1",),
        )

    chain = HANDOFF.HandoffChain(
        contract=task,
        stages=(
            HANDOFF.StageBinding(
                HANDOFF.StageSpec(
                    "ledger_reader",
                    requires=("context_digest",),
                    provides=("paid_count", "reversed_ids", "paid_total"),
                ),
                ledger_reader,
            ),
            HANDOFF.StageBinding(
                HANDOFF.StageSpec(
                    "evidence_packager",
                    requires=("paid_count", "reversed_ids", "paid_total"),
                    provides=("evidence_bundle",),
                ),
                evidence_packager,
            ),
        ),
        fact_rules=(
            HANDOFF.FactRule("context_digest", "__input__", str),
            HANDOFF.FactRule("paid_count", "ledger_reader", int),
            HANDOFF.FactRule("reversed_ids", "ledger_reader", tuple),
            HANDOFF.FactRule("paid_total", "ledger_reader", float),
            HANDOFF.FactRule("evidence_bundle", "evidence_packager", dict),
        ),
        initial_fact_keys=("context_digest",),
        chain_id="capstone-payroll-evidence",
    )
    baton = HANDOFF.new_baton(
        task,
        baton_id=f"payroll-evidence-{MONTH}",
        intent=task.objective,
        initial_facts=(
            HANDOFF.FactValue(
                "context_digest",
                context_digest,
                (f"context://{context_digest}",),
            ),
        ),
    )
    run = asyncio.run(chain.run(baton))
    return {
        "bundle": dict(run.baton.facts["evidence_bundle"]),
        "snapshot_id": run.baton.snapshot_id,
        "stage_receipts": tuple(receipt.receipt_id for receipt in run.receipts),
        "acceptance_receipt": run.acceptance_receipt.receipt_id,
    }


def _diagnose(evidence_bundle: dict[str, Any]) -> dict[str, Any]:
    stale = "report reads the pre-reversal payroll snapshot"
    current = "current ledger still contains 800 paid rows"

    def planner(_problem, existing, iteration):
        if iteration > 1 or existing:
            return []
        return [(stale, 0.65), (current, 0.50)]

    def generator(hypothesis):
        if hypothesis.description == stale:
            return [
                (
                    (
                        f"report says paid=800/reversed=0 while ledger says "
                        f"paid={evidence_bundle['paid_count']}/"
                        f"reversed={evidence_bundle['reversed_count']}"
                    ),
                    f"evidence://payroll/{MONTH}/report-ledger-diff",
                )
            ]
        return [
            (
                (
                    f"SQLite returns paid={evidence_bundle['paid_count']} "
                    f"and reversed={evidence_bundle['reversed_ids']}"
                ),
                f"sqlite://payroll.db/payroll?month={MONTH}",
            )
        ]

    def evaluator(hypothesis, _description, _source):
        if hypothesis.description == stale:
            return "supports", 0.35
        return "refutes", -0.50

    tree, outcome = HYPOTHESIS.IterativeHypothesisLoop(
        planner,
        generator,
        evaluator,
        max_iterations=2,
    ).run("Why does the month-end report disagree with the payroll ledger?")
    confirmed = tree.by_id(outcome.confirmed_id)
    if confirmed is None:
        raise AssertionError("the deterministic diagnosis did not converge")
    return {
        "confirmed": confirmed.description,
        "confirmed_id": confirmed.h_id,
        "iterations": outcome.iterations_used,
        "evidence": tuple(
            item.description for item in confirmed.evidence
        ),
    }


def _build_report(
    evidence_bundle: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    def draft(_args, _prior):
        exceptions = ",".join(evidence_bundle["reversed_ids"])
        return (
            f"MONTHLY-REPORT month={MONTH} "
            f"paid={evidence_bundle['paid_count']} "
            f"reversed={evidence_bundle['reversed_count']} "
            f"exceptions={exceptions} conclusion=exceptions-held"
        )

    def bind(_args, prior):
        return {
            "content": prior["draft"],
            "diagnosis_id": diagnosis["confirmed_id"],
            "source_snapshot": f"sqlite://payroll.db/payroll?month={MONTH}",
        }

    plan = PLAN.Plan(goal="build a reconciled and source-bound payroll report")
    plan.add(
        PLAN.PlanStep(
            step_id="draft",
            description="write the reconciled report",
            handler="draft",
        )
    )
    plan.add(
        PLAN.PlanStep(
            step_id="bind",
            description="bind diagnosis and source snapshot",
            handler="bind",
            deps=["draft"],
        )
    )
    PLAN.approve(plan, f"plan-approval://{RUN_ID}/v1")
    PLAN.Executor({"draft": draft, "bind": bind}).run(plan)
    if not plan.is_complete():
        raise AssertionError("the report plan did not complete")
    return {
        **plan.steps["bind"].output,
        "steps": tuple(
            (step.step_id, step.status.value) for step in plan.steps.values()
        ),
    }


def _review_report(report: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    artifact = REFLECTION.Artifact(
        content=report["content"],
        metadata={"month": MONTH, "source": report["source_snapshot"]},
    )

    def critic(candidate):
        expected = (
            f"paid={truth['paid_count']}",
            f"reversed={truth['reversed_count']}",
            f"exceptions={','.join(truth['reversed_ids'])}",
        )
        missing = [token for token in expected if token not in candidate.content]
        issues = [
            REFLECTION.Issue(
                REFLECTION.Severity.BLOCKER,
                f"report is missing {token}",
                "monthly report",
                f"ledger requires {token}",
                "ledger_reconciliation",
            )
            for token in missing
        ]
        return REFLECTION.Critique(
            score=0.42 if missing else 0.96,
            issues=issues,
            summary="ledger-bound report check",
            score_evidence=(
                f"missing ledger tokens: {', '.join(missing)}"
                if missing
                else "all required ledger tokens are present"
            ),
        )

    chain = REFLECTION.GeneratorCriticChain(
        generator=lambda _prompt: artifact,
        critic=critic,
        policy=REFLECTION.AcceptancePolicy(
            min_score=0.8,
            require_evidence=True,
        ),
    )
    result = chain.run("review the month-end payroll report")
    if result.decision is not REFLECTION.Decision.ACCEPTED:
        raise AssertionError("the reconciled report did not pass reflection")
    return {
        "content": result.reviewed_artifact.content,
        "revision": result.reviewed_artifact.revision,
        "decision": result.decision.value,
        "score": result.critique.score,
        "score_evidence": result.critique.score_evidence,
        "trace": result.trace,
    }


def _approve_report(
    contract: Any,
    artifact_digest: str,
    truth: dict[str, Any],
) -> dict[str, Any]:
    roles = {
        "alice": ("payroll-controller",),
        "bob": ("treasury-controller",),
    }
    gate = APPROVAL.ApprovalGate(
        role_resolver=lambda identity: roles.get(identity, ())
    )
    proposal = APPROVAL.ActionProposal(
        proposal_id=f"monthly-report-release-{MONTH}",
        version=1,
        contract_digest=contract.digest,
        artifact_id=f"monthly-report-{MONTH}-v1",
        artifact_digest=artifact_digest,
        requested_by="payroll-report-agent",
        action="payroll.monthly-report.release",
        resource_scope=(f"payroll:{MONTH}",),
        idempotency_key=f"release::{MONTH}::v1",
        risk=APPROVAL.RiskLevel.HIGH,
        reversibility=APPROVAL.Reversibility.REVERSIBLE,
        amount=truth["paid_total"],
        subject_count=truth["paid_count"],
        evidence_refs=(
            f"artifact://monthly-report/{MONTH}/v1#{artifact_digest}",
            f"sqlite://payroll.db/payroll?month={MONTH}",
        ),
    )
    routed = gate.evaluate(proposal, now="2026-07-20T10:00:00+00:00")
    if routed.ticket is None:
        raise AssertionError("the high-value report did not enter human review")
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at="2026-07-20T10:02:00+00:00",
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at="2026-07-20T10:03:00+00:00",
    )
    if not gate.authorize(
        proposal,
        final.receipt,
        at="2026-07-20T10:04:00+00:00",
    ):
        raise AssertionError("the final governance receipt did not authorize release")
    return {
        "proposal_digest": proposal.digest,
        "artifact_digest": proposal.artifact_digest,
        "route": routed.route.value,
        "required_roles": routed.ticket.required_roles,
        "first_decision": first.receipt.decision.value,
        "final_decision": final.receipt.decision.value,
        "receipt_digest": final.receipt.digest,
        "authorization_ref": f"governance-receipt://{final.receipt.digest}",
    }


def _receipt(
    contract: Any,
    module: Any,
    *,
    input_digest: str,
    output_digest: str,
    parent: Any | None,
    evidence_refs: tuple[str, ...],
) -> Any:
    return ASSEMBLY.ModuleReceipt(
        receipt_id=f"{RUN_ID}::{module.value}",
        module=module,
        pattern=PATTERNS[module],
        run_id=contract.run_id,
        contract_digest=contract.digest,
        workload_digest=contract.workload_digest,
        input_digest=input_digest,
        output_digest=output_digest,
        parent_receipts=(parent.digest,) if parent is not None else (),
        evidence_refs=evidence_refs,
    )


def _run_modules() -> dict[str, Any]:
    connection = _fixture()
    truth = _truth(connection)
    contract = _contract()
    assembly = ASSEMBLY.SystemAssembly(contract)
    tracker = MEMORY.ProgressTracker()
    todos = tracker.get_list(RUN_ID)
    todo_by_module = {}
    for module in ASSEMBLY.MODULE_ORDER:
        item = todos.add(
            f"complete {module.value} evidence",
            f"completing {module.value} evidence",
            tags=["capstone", module.value],
        )
        todo_by_module[module] = item

    module_details: dict[str, Any] = {}
    previous = None

    composition_output = contract.digest
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.COMPOSITION,
        input_digest=contract.selection_receipt_digest,
        output_digest=composition_output,
        parent=None,
        evidence_refs=(
            f"selection://{contract.selection_receipt_digest}",
            f"contract://{contract.digest}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.COMPOSITION].todo_id)
    module_details["composition"] = {
        "contract_digest": contract.digest,
        "selection_receipt": contract.selection_receipt_digest,
    }
    previous = receipt

    context = _context_triage()
    context_digest = ASSEMBLY.stable_digest(context)
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.PERCEPTION,
        input_digest=previous.output_digest,
        output_digest=context_digest,
        parent=previous,
        evidence_refs=(
            f"triage://{RUN_ID}/v1",
            f"context://{context_digest}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.PERCEPTION].todo_id)
    module_details["perception"] = context
    previous = receipt

    handoff = _handoff(connection, context_digest)
    evidence_digest = ASSEMBLY.stable_digest(handoff["bundle"])
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.COLLABORATION,
        input_digest=previous.output_digest,
        output_digest=evidence_digest,
        parent=previous,
        evidence_refs=(
            *(f"handoff-receipt://{item}" for item in handoff["stage_receipts"]),
            f"acceptance://{handoff['acceptance_receipt']}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.COLLABORATION].todo_id)
    module_details["collaboration"] = handoff
    previous = receipt

    diagnosis = _diagnose(handoff["bundle"])
    diagnosis_digest = ASSEMBLY.stable_digest(diagnosis)
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.REASONING,
        input_digest=previous.output_digest,
        output_digest=diagnosis_digest,
        parent=previous,
        evidence_refs=(
            f"hypothesis://{diagnosis['confirmed_id']}",
            f"sqlite://payroll.db/payroll?month={MONTH}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.REASONING].todo_id)
    module_details["reasoning"] = diagnosis
    previous = receipt

    report = _build_report(handoff["bundle"], diagnosis)
    draft_digest = ASSEMBLY.stable_digest(report["content"])
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.ACTION,
        input_digest=previous.output_digest,
        output_digest=draft_digest,
        parent=previous,
        evidence_refs=(
            f"plan://{RUN_ID}/v1",
            f"artifact://monthly-report/{MONTH}/v1#{draft_digest}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.ACTION].todo_id)
    module_details["action"] = report
    previous = receipt

    review = _review_report(report, truth)
    reviewed_digest = ASSEMBLY.stable_digest(review["content"])
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.REFLECTION,
        input_digest=previous.output_digest,
        output_digest=reviewed_digest,
        parent=previous,
        evidence_refs=(
            f"review://{RUN_ID}/revision-{review['revision']}",
            f"sqlite://payroll.db/payroll?month={MONTH}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.REFLECTION].todo_id)
    module_details["reflection"] = review
    previous = receipt

    governance = _approve_report(contract, reviewed_digest, truth)
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.GOVERNANCE,
        input_digest=previous.output_digest,
        output_digest=reviewed_digest,
        parent=previous,
        evidence_refs=(
            governance["authorization_ref"],
            f"proposal://{governance['proposal_digest']}",
        ),
    )
    assembly.record(receipt)
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.GOVERNANCE].todo_id)
    module_details["governance"] = governance
    previous = receipt

    connection.execute(
        "INSERT INTO releases VALUES (?, ?, ?, ?, ?)",
        (
            RUN_ID,
            reviewed_digest,
            governance["authorization_ref"],
            truth["paid_count"],
            truth["reversed_count"],
        ),
    )
    connection.commit()
    release_row = connection.execute(
        "SELECT run_id, report_digest, approval_ref, paid_count, reversed_count "
        "FROM releases WHERE run_id=?",
        (RUN_ID,),
    ).fetchone()
    todos.complete(todo_by_module[ASSEMBLY.ModuleName.MEMORY].todo_id)
    checkpoint = todos.render()
    memory_ref = f"checkpoint://{RUN_ID}/{ASSEMBLY.stable_digest(checkpoint)}"
    receipt = _receipt(
        contract,
        ASSEMBLY.ModuleName.MEMORY,
        input_digest=previous.output_digest,
        output_digest=reviewed_digest,
        parent=previous,
        evidence_refs=(
            memory_ref,
            f"sqlite://releases/{RUN_ID}",
        ),
    )
    assembly.record(receipt)
    module_details["memory"] = {
        "all_done": todos.all_done(),
        "checkpoint": checkpoint,
        "checkpoint_ref": memory_ref,
    }
    previous = receipt

    endpoint = ASSEMBLY.EndpointEvidence(
        contract_digest=contract.digest,
        terminal_receipt_digest=previous.digest,
        artifact_digest=release_row[1],
        authorization_ref=release_row[2],
        external_refs=(f"sqlite://releases/{RUN_ID}",),
        checks=(
            ASSEMBLY.BusinessCheck(
                "report artifact persisted",
                release_row[1] == reviewed_digest,
                f"sqlite://releases/{RUN_ID}#report_digest",
            ),
            ASSEMBLY.BusinessCheck(
                "approval persisted with the report",
                release_row[2] == governance["authorization_ref"],
                f"sqlite://releases/{RUN_ID}#approval_ref",
            ),
            ASSEMBLY.BusinessCheck(
                "ledger counts survived release",
                release_row[3:] == (
                    truth["paid_count"],
                    truth["reversed_count"],
                ),
                f"sqlite://releases/{RUN_ID}#counts",
            ),
        ),
    )
    accepted_report = assembly.seal(endpoint)
    connection.close()
    return {
        "contract": contract,
        "truth": truth,
        "module_details": module_details,
        "receipts": assembly.receipts,
        "endpoint": endpoint,
        "report": accepted_report,
        "release_row": {
            "run_id": release_row[0],
            "report_digest": release_row[1],
            "approval_ref": release_row[2],
            "paid_count": release_row[3],
            "reversed_count": release_row[4],
        },
        "stale_report_digest": ASSEMBLY.stable_digest(STALE_REPORT),
    }


def run_capstone(mode: str = "bound") -> dict[str, Any]:
    if mode not in {"bound", "local-only"}:
        raise KeyError(mode)
    executed = _run_modules()
    contract = executed["contract"]
    receipts = executed["receipts"]
    endpoint = executed["endpoint"]

    if mode == "local-only":
        stale = executed["stale_report_digest"]
        local_receipts = []
        for receipt in receipts:
            changed = replace(receipt, parent_receipts=())
            if receipt.module in {
                ASSEMBLY.ModuleName.GOVERNANCE,
                ASSEMBLY.ModuleName.MEMORY,
            }:
                changed = replace(
                    changed,
                    input_digest=stale,
                    output_digest=stale,
                )
            local_receipts.append(changed)
        report = ASSEMBLY.audit_system(
            contract,
            tuple(local_receipts),
            endpoint,
        )
        receipts = tuple(local_receipts)
    else:
        report = executed["report"]

    return _jsonable(
        {
            "mode": mode,
            "mode_label": "端到端绑定" if mode == "bound" else "仅看局部成功",
            "run_id": contract.run_id,
            "contract_digest": contract.digest,
            "selection_receipt_digest": contract.selection_receipt_digest,
            "workload_ref": contract.workload_ref,
            "goal": contract.goal,
            "patterns": [
                {
                    "module": binding.module.value,
                    "pattern": binding.pattern,
                    "purpose": binding.purpose,
                }
                for binding in contract.pattern_bindings
            ],
            "receipts": receipts,
            "module_details": executed["module_details"],
            "truth": executed["truth"],
            "release_row": executed["release_row"],
            "endpoint": endpoint,
            "acceptance": report,
            "explanation": (
                "eight local receipts are accepted, but lineage and artifact "
                "identity are not continuous"
                if mode == "local-only"
                else
                "the endpoint binds the terminal receipt, approved artifact, "
                "and independently queried SQLite facts"
            ),
            "boundaries": (
                "SQLite release row is a teaching endpoint, not a bank receipt.",
                "Short digests demonstrate identity checks, not digital signatures.",
                "All model roles use deterministic fixtures so the system test is reproducible.",
                "The full system assembles selected patterns; it does not require every catalog pattern.",
            ),
        }
    )


def _print(result: dict[str, Any]) -> None:
    acceptance = result["acceptance"]
    print(f"== lecture 43 capstone: {result['mode_label']} ==")
    print(f"run={result['run_id']} contract={result['contract_digest']}")
    print(
        f"local={acceptance['local_acceptance_count']}/"
        f"{acceptance['required_module_count']} "
        f"system={'ACCEPTED' if acceptance['accepted'] else 'REJECTED'}"
    )
    for receipt in result["receipts"]:
        print(
            f"[{receipt['module']:<13}] {receipt['status']:<8} "
            f"in={receipt['input_digest']} out={receipt['output_digest']} "
            f"parents={len(receipt['parent_receipts'])}"
        )
    if acceptance["findings"]:
        print("findings:")
        for finding in acceptance["findings"]:
            print(f"  - {finding['code']}: {finding['detail']}")
    else:
        row = result["release_row"]
        print(
            f"endpoint paid={row['paid_count']} reversed={row['reversed_count']} "
            f"artifact={row['report_digest']}"
        )
        print(f"authorization={row['approval_ref']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the lecture 43 capstone.")
    parser.add_argument(
        "--mode",
        choices=("bound", "local-only"),
        default="bound",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_capstone(args.mode)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print(result)


if __name__ == "__main__":
    main()
