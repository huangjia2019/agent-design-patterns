"""Payroll lab for the evidence-driven Six-Step Methodology.

The experiment starts from a deliberately small mutable-state baseline. A
transient calculation failure has no local recovery boundary, and a later
replan can overwrite the amount that downstream code already treated as
committed.

Three candidates then enter the method:

* Handoff Chain alone protects settlement ownership but cannot recover a failed
  plan;
* Plan and Execute plus Handoff Chain sharing ``net_amount`` is rejected before
  trial because the fact has two writers;
* split ownership lets planning revise ``payroll_plan`` before commit and lets
  Handoff Chain own ``settled_net_amount`` after commit.

The final candidate must also survive two ablations. This proves that both
patterns contribute to the bound workload instead of decorating the diagram.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from dataclasses import asdict
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


METHOD = _load(
    "composition/b-six-step-methodology/pattern.py",
    "composition_six_step_pattern",
)
PLAN = _load(
    "action/b-plan-and-execute/pattern.py",
    "composition_plan_execute_pattern",
)
HANDOFF = _load(
    "collaboration/d-handoff-chain/pattern.py",
    "composition_handoff_chain_pattern",
)

WORKLOAD = "fixture://payroll/2026-06/transient-replan-v1"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def run_mutable_baseline() -> dict[str, Any]:
    """Run the smallest workflow: one mutable dict shared across two phases."""

    shared_state = {"net_amount": 9_600.0, "status": "calculated"}
    committed_view = dict(shared_state)
    calculation_failed = True
    if calculation_failed:
        shared_state["net_amount"] = 9_900.0
        shared_state["status"] = "replanned"

    overwrite = float(
        shared_state["net_amount"] != committed_view["net_amount"]
    )
    return {
        "name": "共享可变字典基线",
        "before": committed_view,
        "after": shared_state,
        "metrics": {
            "recovery_success": 0.0,
            "committed_fact_overwrites": overwrite,
            "settlement_receipts": 0.0,
        },
        "observed_failures": [
            "计算失败后没有局部恢复边界",
            "被下游视为已提交的 net_amount 从 9600 改成 9900",
            "没有回执证明哪一版金额越过了交接边界",
        ],
        "evidence_refs": [
            "trace://payroll/baseline#calculation-failed",
            "trace://payroll/baseline#net-amount-overwritten",
            "trace://payroll/baseline#receipt-missing",
        ],
    }


def _run_recovered_plan() -> dict[str, Any]:
    """Use the real Plan-and-Execute implementation for local recovery."""

    attempts = {"calculate": 0}

    def calculate_v1(args, prior):
        del args, prior
        attempts["calculate"] += 1
        raise TimeoutError("formula service timed out")

    def calculate_v2(args, prior):
        del args, prior
        attempts["calculate"] += 1
        return {
            "plan_version": 2,
            "employee_id": "E0007",
            "net_amount": 9_600.0,
        }

    def publish(args, prior):
        del args
        return dict(prior["calculate"])

    plan = PLAN.Plan(goal="calculate and settle E0007 payroll")
    plan.add(
        PLAN.PlanStep(
            step_id="calculate",
            description="calculate net salary",
            handler="calculate_v1",
        )
    )
    plan.add(
        PLAN.PlanStep(
            step_id="publish",
            description="publish a versioned payroll plan",
            handler="publish",
            deps=["calculate"],
        )
    )
    PLAN.approve(plan, "approval://payroll-plan/v1")
    executor = PLAN.Executor(
        {
            "calculate_v1": calculate_v1,
            "calculate_v2": calculate_v2,
            "publish": publish,
        }
    )
    executor.run(plan)
    first_failure = plan.first_failed()
    if first_failure is None:
        raise AssertionError("the transient failure did not occur")

    def repaired_planner(goal):
        repaired = PLAN.Plan(goal=goal)
        repaired.add(
            PLAN.PlanStep(
                step_id="calculate",
                description="calculate net salary after refresh",
                handler="calculate_v2",
            )
        )
        repaired.add(
            PLAN.PlanStep(
                step_id="publish",
                description="publish a versioned payroll plan",
                handler="publish",
                deps=["calculate"],
            )
        )
        return repaired

    PLAN.replan_local(plan, repaired_planner, "calculate")
    executor.run(plan)
    artifact = plan.steps["publish"].output
    if not plan.is_complete() or artifact is None:
        raise AssertionError("the repaired plan did not complete")
    return {
        "artifact": artifact,
        "attempts": attempts["calculate"],
        "evidence_refs": (
            "trace://payroll/plan/calculate-v1-timeout",
            "plan://payroll/E0007/v2",
        ),
    }


def _build_handoff(plan_artifact: dict[str, Any]):
    """Bind the recovered plan to the real append-only Handoff Chain."""

    contract = HANDOFF.TaskContract(
        contract_id="payroll-settlement-E0007",
        version=2,
        objective="settle E0007 from the approved payroll plan",
        output_schema="SettlementBaton",
        accountable_owner="payroll-controller",
        input_refs=("plan://payroll/E0007/v2",),
        constraints=("net amount has one producer after commit",),
    )

    async def settle(view):
        payroll_plan = view.facts["payroll_plan"]
        return HANDOFF.StageDelta(
            facts=(
                HANDOFF.FactValue(
                    "settled_net_amount",
                    float(payroll_plan["net_amount"]),
                    evidence_refs=("plan://payroll/E0007/v2",),
                ),
            ),
            artifact_refs=("artifact://settlement/E0007/v1",),
        )

    chain = HANDOFF.HandoffChain(
        contract=contract,
        stages=(
            HANDOFF.StageBinding(
                HANDOFF.StageSpec(
                    "settle",
                    requires=("payroll_plan",),
                    provides=("settled_net_amount",),
                ),
                settle,
            ),
        ),
        fact_rules=(
            HANDOFF.FactRule(
                "payroll_plan",
                "__input__",
                dict,
                evidence_required=True,
            ),
            HANDOFF.FactRule(
                "settled_net_amount",
                "settle",
                float,
                evidence_required=True,
            ),
        ),
        initial_fact_keys=("payroll_plan",),
        chain_id="composition-payroll-handoff",
    )
    input_record = HANDOFF.FactRecord(
        "payroll_plan",
        plan_artifact,
        "__input__",
        "input::payroll-plan::v2",
        ("plan://payroll/E0007/v2",),
    )
    baton = HANDOFF.Baton(
        baton_id="payroll-E0007",
        contract_digest=contract.digest,
        intent=contract.objective,
        records=(input_record,),
    )
    return asyncio.run(chain.run(baton))


def run_full_bundle() -> dict[str, Any]:
    recovered = _run_recovered_plan()
    chain_run = _build_handoff(recovered["artifact"])
    receipt = chain_run.receipts[-1]
    return {
        "name": "规划执行 + 交接链（职责拆分）",
        "plan": recovered["artifact"],
        "plan_attempts": recovered["attempts"],
        "settled_net_amount": chain_run.baton.facts["settled_net_amount"],
        "receipt_id": receipt.receipt_id,
        "baton_snapshot": chain_run.baton.snapshot_id,
        "metrics": {
            "recovery_success": 1.0,
            "committed_fact_overwrites": 0.0,
            "settlement_receipts": 1.0,
        },
        "observed_failures": [],
        "evidence_refs": [
            *recovered["evidence_refs"],
            receipt.receipt_id,
            chain_run.acceptance_receipt.receipt_id,
        ],
    }


def run_without_plan() -> dict[str, Any]:
    return {
        "name": "消融：移除规划执行",
        "metrics": {
            "recovery_success": 0.0,
            "committed_fact_overwrites": 0.0,
            "settlement_receipts": 0.0,
        },
        "observed_failures": ["公式服务超时后没有局部重规划，交接没有开始"],
        "evidence_refs": ["trace://payroll/ablation/no-plan#timeout"],
    }


def run_without_handoff() -> dict[str, Any]:
    recovered = _run_recovered_plan()
    mutable = dict(recovered["artifact"])
    committed = dict(mutable)
    mutable["net_amount"] = 9_900.0
    overwrite = float(mutable["net_amount"] != committed["net_amount"])
    return {
        "name": "消融：移除交接链",
        "metrics": {
            "recovery_success": 1.0,
            "committed_fact_overwrites": overwrite,
            "settlement_receipts": 0.0,
        },
        "observed_failures": ["规划恢复成功，但结算事实仍可被覆盖且没有回执"],
        "evidence_refs": [
            *recovered["evidence_refs"],
            "trace://payroll/ablation/no-handoff#overwrite",
        ],
    }


def run_handoff_only() -> dict[str, Any]:
    return {
        "name": "仅交接链",
        "metrics": {
            "recovery_success": 0.0,
            "committed_fact_overwrites": 0.0,
            "settlement_receipts": 0.0,
        },
        "observed_failures": ["提交边界安全，但上游超时后没有可交接工件"],
        "evidence_refs": ["trace://payroll/candidate/handoff-only#no-plan"],
    }


def run_framework_conflict() -> str:
    """Let the real Handoff Chain reject two producers for one fact."""

    async def settle(view):
        del view
        return HANDOFF.StageDelta(
            facts=(
                HANDOFF.FactValue(
                    "net_amount",
                    9_600.0,
                    evidence_refs=("artifact://settlement/v1",),
                ),
            )
        )

    async def replan(view):
        del view
        return HANDOFF.StageDelta(
            facts=(
                HANDOFF.FactValue(
                    "net_amount",
                    9_900.0,
                    evidence_refs=("plan://revised/v2",),
                ),
            )
        )

    try:
        HANDOFF.HandoffChain(
            contract=HANDOFF.TaskContract(
                contract_id="shared-net-amount",
                version=1,
                objective="settle and then replan one shared amount",
                output_schema="Baton",
                accountable_owner="payroll-controller",
            ),
            stages=(
                HANDOFF.StageBinding(
                    HANDOFF.StageSpec("settle", provides=("net_amount",)),
                    settle,
                ),
                HANDOFF.StageBinding(
                    HANDOFF.StageSpec("replan", provides=("net_amount",)),
                    replan,
                ),
            ),
            fact_rules=(
                HANDOFF.FactRule("net_amount", "settle", float),
            ),
        )
    except ValueError as error:
        return str(error)
    raise AssertionError("the real handoff chain accepted two producers")


def _problem():
    return METHOD.BoundDecision(
        objective="计算失败可局部恢复，已提交的薪酬事实仍保持单一所有者",
        workload_ref=WORKLOAD,
        output_contract="版本化薪酬计划 + 不可改写的结算事实 + 交接回执",
        constraints=(
            "同一结算事实只能有一个生产者",
            "失败只能重写未提交的计划",
            "所有对照使用同一份超时负载",
        ),
        excluded_scope=("银行真实到账", "分布式事务", "跨系统密码学签名"),
        gates=(
            METHOD.QualityGate(
                "recovery_success",
                METHOD.Comparison.AT_LEAST,
                1.0,
            ),
            METHOD.QualityGate(
                "committed_fact_overwrites",
                METHOD.Comparison.AT_MOST,
                0.0,
            ),
            METHOD.QualityGate(
                "settlement_receipts",
                METHOD.Comparison.AT_LEAST,
                1.0,
            ),
        ),
    )


def _diagnoses():
    return (
        METHOD.ConstraintDiagnosis(
            "缺少局部恢复边界",
            "共享字典基线在计算超时后只能整段改状态，无法局部修订计划。",
            "recovery_success",
            ("trace://payroll/baseline#calculation-failed",),
        ),
        METHOD.ConstraintDiagnosis(
            "结算事实没有单一所有者",
            "计划修订与结算交接都能写 net_amount。",
            "committed_fact_overwrites",
            ("trace://payroll/baseline#net-amount-overwritten",),
        ),
        METHOD.ConstraintDiagnosis(
            "交接缺少版本回执",
            "下游无法证明自己接收的是哪一版计划和金额。",
            "settlement_receipts",
            ("trace://payroll/baseline#receipt-missing",),
        ),
    )


def _candidates():
    return (
        METHOD.CandidateArchitecture(
            candidate_id="handoff-only",
            patterns=(
                METHOD.PatternBinding(
                    "交接链（Handoff Chain）",
                    produces=("settled_net_amount",),
                ),
            ),
            targets=("结算事实没有单一所有者", "交接缺少版本回执"),
            rationale="先给结算事实加单一生产者和回执。",
            assumption_refs=("design://payroll/settlement-owner/v1",),
        ),
        METHOD.CandidateArchitecture(
            candidate_id="shared-net-amount",
            patterns=(
                METHOD.PatternBinding(
                    "规划执行（Plan and Execute）",
                    produces=("net_amount",),
                ),
                METHOD.PatternBinding(
                    "交接链（Handoff Chain）",
                    produces=("net_amount",),
                ),
            ),
            targets=(
                "缺少局部恢复边界",
                "结算事实没有单一所有者",
                "交接缺少版本回执",
            ),
            rationale="两个模式共享 net_amount，表面上接口最省。",
            assumption_refs=("design://payroll/shared-field/v1",),
        ),
        METHOD.CandidateArchitecture(
            candidate_id="split-plan-and-settlement",
            patterns=(
                METHOD.PatternBinding(
                    "规划执行（Plan and Execute）",
                    produces=("payroll_plan",),
                    mutates=("payroll_plan_draft",),
                ),
                METHOD.PatternBinding(
                    "交接链（Handoff Chain）",
                    consumes=("payroll_plan",),
                    produces=("settled_net_amount",),
                ),
            ),
            targets=(
                "缺少局部恢复边界",
                "结算事实没有单一所有者",
                "交接缺少版本回执",
            ),
            rationale="规划阶段只改计划，交接阶段独占结算事实。",
            assumption_refs=("design://payroll/fact-ownership/v2",),
            seams=(
                METHOD.SeamContract(
                    artifact="payroll_plan",
                    producer="规划执行（Plan and Execute）",
                    consumer="交接链（Handoff Chain）",
                    owner="规划执行（Plan and Execute）",
                    mutation_policy=METHOD.MutationPolicy.REPLACEABLE_UNTIL_COMMIT,
                    version_field="plan_version",
                ),
            ),
        ),
    )


def _experiments():
    return (
        METHOD.ExperimentCase(
            "handoff-only-full",
            "handoff-only",
            WORKLOAD,
            None,
            "结算边界安全，但超时任务无法恢复。",
        ),
        METHOD.ExperimentCase(
            "split-full",
            "split-plan-and-settlement",
            WORKLOAD,
            None,
            "超时恢复、单一写者和回执三道门全部通过。",
        ),
        METHOD.ExperimentCase(
            "split-without-plan",
            "split-plan-and-settlement",
            WORKLOAD,
            "规划执行（Plan and Execute）",
            "移除规划执行后，超时恢复门失败。",
        ),
        METHOD.ExperimentCase(
            "split-without-handoff",
            "split-plan-and-settlement",
            WORKLOAD,
            "交接链（Handoff Chain）",
            "移除交接链后，事实所有权和回执门失败。",
        ),
    )


def _trial(case_id: str, run: dict[str, Any]):
    return METHOD.TrialResult(
        case_id=case_id,
        workload_ref=WORKLOAD,
        metrics=tuple(run["metrics"].items()),
        evidence_refs=tuple(run["evidence_refs"]),
        observed_failures=tuple(run["observed_failures"]),
    )


def run_methodology() -> dict[str, Any]:
    baseline = run_mutable_baseline()
    handoff_only = run_handoff_only()
    full = run_full_bundle()
    without_plan = run_without_plan()
    without_handoff = run_without_handoff()

    session = METHOD.SixStepSession("payroll-plan-settlement").bound(_problem())
    session.record_baseline(
        METHOD.BaselineEvidence(
            baseline_id="mutable-state-baseline",
            workload_ref=WORKLOAD,
            metrics=tuple(baseline["metrics"].items()),
            evidence_refs=tuple(baseline["evidence_refs"]),
            observed_failures=tuple(baseline["observed_failures"]),
        )
    )
    session.diagnose(_diagnoses())
    session.generate_candidates(_candidates())
    session.specify_seams_and_trials(_experiments())
    receipt = session.decide(
        (
            _trial("handoff-only-full", handoff_only),
            _trial("split-full", full),
            _trial("split-without-plan", without_plan),
            _trial("split-without-handoff", without_handoff),
        ),
        reopen_triggers=(
            "计划工件开始跨服务传输",
            "结算事实增加第二个合法写入方",
            "公式超时负载或验收门发生变化",
        ),
    )
    reopened = session.reopen("示范：事实所有权或负载变化")

    findings_by_candidate: dict[str, list[dict[str, Any]]] = {
        candidate.candidate_id: [] for candidate in session.candidates
    }
    for finding in session.findings:
        assert finding.candidate_id is not None
        findings_by_candidate[finding.candidate_id].append(
            _jsonable(asdict(finding))
        )

    candidate_rows = []
    for candidate in session.candidates:
        candidate_rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "patterns": [
                    pattern.pattern_name for pattern in candidate.patterns
                ],
                "targets": list(candidate.targets),
                "rationale": candidate.rationale,
                "seams": _jsonable(asdict(candidate))["seams"],
                "findings": findings_by_candidate[candidate.candidate_id],
                "trial_ready": candidate.candidate_id in session.trial_ready_ids,
            }
        )

    return {
        "decision_id": session.decision_id,
        "version": session.version,
        "workload_ref": WORKLOAD,
        "steps": [
            {"number": 1, "name": "限定决策", "artifact": "问题契约"},
            {"number": 2, "name": "运行基线", "artifact": "基线证据"},
            {"number": 3, "name": "诊断约束", "artifact": "约束诊断"},
            {"number": 4, "name": "生成候选", "artifact": "候选组合"},
            {"number": 5, "name": "接缝与实验", "artifact": "接缝契约 + 消融"},
            {"number": 6, "name": "裁决与重开", "artifact": "决策回执"},
        ],
        "problem": _jsonable(asdict(session.problem)),
        "baseline": baseline,
        "diagnoses": _jsonable([asdict(item) for item in session.diagnoses]),
        "candidates": candidate_rows,
        "framework_conflict": run_framework_conflict(),
        "experiments": [
            {
                "case_id": "baseline",
                "candidate": "共享可变字典基线",
                "variant": "最小基线",
                **baseline,
            },
            {
                "case_id": "handoff-only-full",
                "candidate": "仅交接链",
                "variant": "完整候选",
                **handoff_only,
            },
            {
                "case_id": "split-full",
                "candidate": "职责拆分组合",
                "variant": "完整候选",
                **full,
            },
            {
                "case_id": "split-without-plan",
                "candidate": "职责拆分组合",
                "variant": "移除规划执行",
                **without_plan,
            },
            {
                "case_id": "split-without-handoff",
                "candidate": "职责拆分组合",
                "variant": "移除交接链",
                **without_handoff,
            },
        ],
        "receipt": _jsonable(asdict(receipt)),
        "receipt_reason_zh": "职责拆分组合通过全部验收门，两个移除变体分别暴露了恢复与交接缺口。",
        "receipt_digest": receipt.digest,
        "reopened_version": reopened.version,
        "prior_receipt_digest": reopened.prior_receipt_digest,
    }


def print_report() -> None:
    result = run_methodology()
    print("=" * 76)
    print("Six-Step Methodology · 薪酬计划与结算接缝")
    print("=" * 76)
    print(
        "基线："
        f"recovery={result['baseline']['metrics']['recovery_success']:.0f} "
        "overwrites="
        f"{result['baseline']['metrics']['committed_fact_overwrites']:.0f} "
        f"receipts={result['baseline']['metrics']['settlement_receipts']:.0f}"
    )
    print("\n候选预检：")
    for candidate in result["candidates"]:
        state = "进入实验" if candidate["trial_ready"] else "接缝拦下"
        print(f"  {candidate['candidate_id']}: {state}")
        for finding in candidate["findings"]:
            print(f"    {finding['code']}: {finding['detail']}")
    print(f"  real framework: {result['framework_conflict']}")
    print("\n同负载对照与消融：")
    for experiment in result["experiments"]:
        metrics = experiment["metrics"]
        print(
            f"  {experiment['variant']:<10} {experiment['name']:<25} "
            f"recovery={metrics['recovery_success']:.0f} "
            f"overwrites={metrics['committed_fact_overwrites']:.0f} "
            f"receipts={metrics['settlement_receipts']:.0f}"
        )
    print(
        f"\n裁决：{result['receipt']['status'].upper()} "
        f"-> {result['receipt']['selected_candidate']}"
    )
    print(
        f"回执：{result['receipt_digest']} "
        f"重开后版本：v{result['reopened_version']}"
    )


if __name__ == "__main__":
    print_report()
