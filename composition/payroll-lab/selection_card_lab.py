"""Payroll lab for the Pattern Selection Card.

The lab compares two tasks that sound nearly identical:

* independent snapshots: compare four ledgers and locate a disagreement;
* shared-state history: explain why four ledgers agree on the same wrong value.

The first task suits Fan-out and Gather. The second needs Iterative Hypothesis
Testing. Both runs use the repository's real pattern implementations. The card
does not choose by name. It binds each choice to a dependency claim and then
lets a baseline comparison accept or reject the added architecture.
"""
from __future__ import annotations

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


CARD = _load(
    "composition/a-pattern-selection-card/pattern.py",
    "composition_selection_card_pattern",
)
FANOUT = _load(
    "collaboration/b-fan-out-gather/pattern.py",
    "composition_fanout_pattern",
)
HYPOTHESIS = _load(
    "reasoning/d-iterative-hypothesis/pattern.py",
    "composition_iterative_hypothesis_pattern",
)


WORKLOAD_INDEPENDENT = "fixture://payroll/2026-06/independent-v1"
WORKLOAD_SHARED = "fixture://payroll/2026-06/shared-carryover-v1"
EXPECTED_SOCIAL_SECURITY = 120_000.0
CORRUPTED_CARRYOVER = 108_000.0


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _reading(source_id: str, amount: float):
    return FANOUT.SourceResult.from_mapping(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06",
        unit="CNY",
        line_items={"social_security": amount},
    )


def run_fanout(*, shared_carryover: bool) -> dict[str, Any]:
    """Run the real Reconciler and expose the evidence that matters."""

    if shared_carryover:
        amounts = {
            "payroll": CORRUPTED_CARRYOVER,
            "general_ledger": CORRUPTED_CARRYOVER,
            "social_security": CORRUPTED_CARRYOVER,
            "attendance": CORRUPTED_CARRYOVER,
        }
    else:
        amounts = {
            "payroll": EXPECTED_SOCIAL_SECURITY,
            "general_ledger": EXPECTED_SOCIAL_SECURITY,
            "social_security": CORRUPTED_CARRYOVER,
            "attendance": EXPECTED_SOCIAL_SECURITY,
        }

    report = FANOUT.Reconciler(tol=1.0).reconcile(
        tuple(_reading(source_id, amount) for source_id, amount in amounts.items())
    )
    divergences = [
        {
            "item": verdict.item,
            "gap": verdict.gap,
            "low_sources": list(verdict.low_sources),
            "high_sources": list(verdict.high_sources),
        }
        for verdict in report.attributable_divergences
    ]
    agreed = list(report.agreed_items)
    defect_recall = float(any(item["item"] == "social_security" for item in divergences))
    false_consensus = float(
        shared_carryover
        and "social_security" in agreed
        and not divergences
    )

    return {
        "pattern": "扇出聚合（Fan-out and Gather）",
        "source_values": amounts,
        "agreed_items": agreed,
        "divergences": divergences,
        "metrics": {
            "defect_recall": defect_recall,
            "false_consensus": false_consensus,
            "source_reads": 4.0,
        },
        "evidence_refs": [
            f"snapshot://{source_id}/2026-06"
            for source_id in amounts
        ],
    }


def run_iterative_hypothesis() -> dict[str, Any]:
    """Run the real hypothesis loop against the shared carryover timeline."""

    hypotheses = {
        "current_formula": "本月计算公式发生错误",
        "prior_carryover": "上月结转写入了错误的社保基数",
        "ledger_posting": "总账过账独立篡改了社保金额",
    }

    def planner(problem, existing, iteration):
        if existing or iteration > 1:
            return []
        return [
            (hypotheses["current_formula"], 0.40),
            (hypotheses["prior_carryover"], 0.55),
            (hypotheses["ledger_posting"], 0.35),
        ]

    def generator(hypothesis):
        if hypothesis.description == hypotheses["current_formula"]:
            return [
                (
                    "本月公式版本 payroll-2026.06 与审批版本一致",
                    "config://payroll/formula/2026.06",
                )
            ]
        if hypothesis.description == hypotheses["prior_carryover"]:
            return [
                (
                    "上月检查点 social_security=108000，政策基线=120000",
                    "checkpoint://payroll/2026-05",
                )
            ]
        return [
            (
                "总账记录的 source_ref 指向同一份上月检查点",
                "lineage://general-ledger/2026-06",
            )
        ]

    def evaluator(hypothesis, evidence, source):
        del evidence, source
        if hypothesis.description == hypotheses["prior_carryover"]:
            return "supports", 0.45
        return "refutes", -0.60

    tree, outcome = HYPOTHESIS.IterativeHypothesisLoop(
        planner=planner,
        generator=generator,
        evaluator=evaluator,
        max_iterations=2,
    ).run("解释四套本月账为什么一致地少了 12000 元")

    confirmed = tree.by_id(outcome.confirmed_id) if outcome.confirmed_id else None
    evidence = [
        {
            "hypothesis": item.description,
            "status": item.status.value,
            "evidence": [
                {
                    "description": record.description,
                    "source": record.source,
                    "effect": record.effect,
                }
                for record in item.evidence
            ],
        }
        for item in tree.hypotheses.values()
    ]
    found_carryover = (
        confirmed is not None
        and confirmed.description == hypotheses["prior_carryover"]
    )

    return {
        "pattern": "迭代假设验证（Iterative Hypothesis）",
        "confirmed": confirmed.description if confirmed else None,
        "converged": outcome.converged,
        "iterations_used": outcome.iterations_used,
        "hypotheses": evidence,
        "metrics": {
            "defect_recall": float(found_carryover),
            "false_consensus": 0.0,
            "source_reads": 3.0,
        },
        "evidence_refs": [
            "config://payroll/formula/2026.06",
            "checkpoint://payroll/2026-05",
            "lineage://general-ledger/2026-06",
        ],
    }


def _gates():
    return (
        CARD.MetricGate(
            "defect_recall",
            CARD.Comparison.AT_LEAST,
            1.0,
        ),
        CARD.MetricGate(
            "false_consensus",
            CARD.Comparison.AT_MOST,
            0.0,
        ),
    )


def _trial(candidate_id: str, workload_ref: str, run: dict[str, Any]):
    return CARD.TrialResult(
        candidate_id=candidate_id,
        workload_ref=workload_ref,
        metrics=tuple(run["metrics"].items()),
        evidence_refs=tuple(run["evidence_refs"]),
    )


def independent_card():
    problem = CARD.ProblemContract(
        problem_id="payroll-independent-reconciliation",
        objective="定位四份独立账本之间的社保差异",
        workload_ref=WORKLOAD_INDEPENDENT,
        input_refs=(
            "snapshot://payroll/2026-06",
            "snapshot://general-ledger/2026-06",
            "snapshot://social-security/2026-06",
            "snapshot://attendance/2026-06",
        ),
        output_contract="带来源证据的差异报告",
        dependency_shape=CARD.DependencyShape.INDEPENDENT,
        constraints=("只读", "不得自动改账", "四个来源必须使用独立快照"),
        observed_baseline_failure="只读薪酬库时，12000 元差异不可见",
    )
    baseline = CARD.ArchitectureCandidate(
        candidate_id="single-source-check",
        patterns=(),
        rationale="最小基线只读取薪酬库",
    )
    proposal = CARD.ArchitectureCandidate(
        candidate_id="fanout-gather",
        patterns=(
            CARD.PatternSpec(
                name="Fan-out and Gather",
                cognitive_function="collaborate",
                topology=CARD.Topology.PARALLEL,
                solves="并行读取独立来源并显式比较",
                preconditions=("independent_sources",),
                produces=("reconciliation_report",),
            ),
        ),
        rationale="四个来源分别拥有快照，读取顺序不改变下一次查询",
        assumptions=(
            CARD.Assumption(
                key="independent_sources",
                claim="四个来源分别生成快照，没有共享上游计算值",
                evidence_ref="lineage://payroll/independent-snapshots/v1",
            ),
        ),
    )
    return CARD.PatternSelectionCard(
        card_id="psc-payroll-independent",
        version=1,
        problem=problem,
        baseline=baseline,
        proposal=proposal,
        rejected_alternatives=(
            CARD.RejectedAlternative(
                candidate_id="iterative-hypothesis",
                reason="一个来源的结果不会改变下一个来源的读取目标",
                evidence_ref="lineage://payroll/independent-snapshots/v1",
            ),
        ),
        experiment=CARD.ExperimentPlan(
            workload_ref=problem.workload_ref,
            gates=_gates(),
            disconfirming_signals=("发现多个来源共享同一上游结转值",),
            rollback_plan="保留单源检查，不放行任何改账动作",
        ),
    )


def shared_state_card():
    problem = CARD.ProblemContract(
        problem_id="payroll-shared-carryover-diagnosis",
        objective="解释四份本月账为什么一致地少了 12000 元",
        workload_ref=WORKLOAD_SHARED,
        input_refs=(
            "snapshot://payroll/2026-06",
            "snapshot://general-ledger/2026-06",
            "checkpoint://payroll/2026-05",
            "policy://social-security/2026",
        ),
        output_contract="带反证路径的根因报告",
        dependency_shape=CARD.DependencyShape.SHARED_STATE,
        constraints=("只读", "沿时间线验证", "每个结论必须绑定来源"),
        observed_baseline_failure="四源并行比较把共同错数判成一致",
    )
    baseline = CARD.ArchitectureCandidate(
        candidate_id="fanout-gather",
        patterns=(
            CARD.PatternSpec(
                name="Fan-out and Gather",
                cognitive_function="collaborate",
                topology=CARD.Topology.PARALLEL,
                solves="比较多个来源",
                preconditions=("independent_sources",),
            ),
        ),
        rationale="按任务名称手工选择的原始方案",
        assumptions=(
            CARD.Assumption(
                key="independent_sources",
                claim="四个本月来源看起来彼此独立",
                evidence_ref=None,
            ),
        ),
    )
    proposal = CARD.ArchitectureCandidate(
        candidate_id="iterative-hypothesis",
        patterns=(
            CARD.PatternSpec(
                name="Iterative Hypothesis",
                cognitive_function="reason",
                topology=CARD.Topology.LOOP,
                solves="沿共享状态的时间线提出、证伪并修正根因假设",
                preconditions=("ordered_evidence",),
                produces=("root_cause_report",),
            ),
        ),
        rationale="本月四个结果共享上月结转，前一步发现会改变下一步查询",
        assumptions=(
            CARD.Assumption(
                key="ordered_evidence",
                claim="本月金额依赖上月检查点，证据存在先后关系",
                evidence_ref="lineage://payroll/carryover-dag/v1",
            ),
        ),
    )
    return CARD.PatternSelectionCard(
        card_id="psc-payroll-shared-state",
        version=1,
        problem=problem,
        baseline=baseline,
        proposal=proposal,
        rejected_alternatives=(
            CARD.RejectedAlternative(
                candidate_id="fanout-gather",
                reason="四个来源共享上月结转，来源一致不等于数值正确",
                evidence_ref="lineage://payroll/carryover-dag/v1",
            ),
        ),
        experiment=CARD.ExperimentPlan(
            workload_ref=problem.workload_ref,
            gates=_gates(),
            disconfirming_signals=("循环无法排除两个以上强假设",),
            rollback_plan="停在只读调查，不自动修改上月检查点",
        ),
    )


def wrong_handpicked_card():
    """The tempting card that selects by task label and lacks evidence."""

    correct = shared_state_card()
    return CARD.PatternSelectionCard(
        card_id="psc-payroll-handpicked",
        version=1,
        problem=correct.problem,
        baseline=CARD.ArchitectureCandidate(
            candidate_id="single-source-check",
            patterns=(),
            rationale="最小单源检查",
        ),
        proposal=correct.baseline,
        rejected_alternatives=(
            CARD.RejectedAlternative(
                candidate_id="iterative-hypothesis",
                reason="暂时认为四源并行已经足够",
                evidence_ref="meeting-note://architecture/guess",
            ),
        ),
        experiment=correct.experiment,
    )


def _single_source_run(workload_ref: str) -> dict[str, Any]:
    return {
        "pattern": "最小单源检查",
        "metrics": {
            "defect_recall": 0.0,
            "false_consensus": 0.0,
            "source_reads": 1.0,
        },
        "evidence_refs": [f"{workload_ref}#payroll-only"],
    }


def run_independent() -> dict[str, Any]:
    card = independent_card()
    baseline_run = _single_source_run(WORKLOAD_INDEPENDENT)
    proposal_run = run_fanout(shared_carryover=False)
    outcome = card.evaluate(
        (
            _trial(card.baseline.candidate_id, WORKLOAD_INDEPENDENT, baseline_run),
            _trial(card.proposal.candidate_id, WORKLOAD_INDEPENDENT, proposal_run),
        )
    )
    return {
        "scenario": "independent",
        "title": "四源独立：并行比较",
        "question": "哪一个来源与其余三份独立快照不一致？",
        "card": _jsonable(asdict(card)),
        "card_digest": card.digest,
        "baseline": baseline_run,
        "proposal": proposal_run,
        "outcome": _jsonable(asdict(outcome)),
        "preflight_findings": [],
    }


def run_shared_state() -> dict[str, Any]:
    card = shared_state_card()
    wrong_card = wrong_handpicked_card()
    baseline_run = run_fanout(shared_carryover=True)
    proposal_run = run_iterative_hypothesis()
    outcome = card.evaluate(
        (
            _trial(card.baseline.candidate_id, WORKLOAD_SHARED, baseline_run),
            _trial(card.proposal.candidate_id, WORKLOAD_SHARED, proposal_run),
        )
    )
    wrong_findings = [
        _jsonable(asdict(finding))
        for finding in wrong_card.review()
    ]
    return {
        "scenario": "shared_state",
        "title": "共享结转：沿时间线证伪",
        "question": "为什么四个来源一致地少了 12000 元？",
        "card": _jsonable(asdict(card)),
        "card_digest": card.digest,
        "baseline": baseline_run,
        "proposal": proposal_run,
        "outcome": _jsonable(asdict(outcome)),
        "preflight_findings": wrong_findings,
        "handpicked_card_state": wrong_card.evaluate().state.value,
    }


def run_scenario(scenario: str) -> dict[str, Any]:
    if scenario == "independent":
        return run_independent()
    if scenario == "shared_state":
        return run_shared_state()
    raise ValueError(f"unknown scenario: {scenario}")


def print_report(scenario: str) -> None:
    result = run_scenario(scenario)
    print("=" * 72)
    print(f"Pattern Selection Card · {result['title']}")
    print("=" * 72)
    print(f"问题：{result['question']}")
    if result["preflight_findings"]:
        codes = ", ".join(item["code"] for item in result["preflight_findings"])
        print(f"手工选型预检：DRAFT ({codes})")
    print(
        "基线："
        f"{result['baseline']['pattern']} "
        f"recall={result['baseline']['metrics']['defect_recall']:.0f} "
        f"false_consensus={result['baseline']['metrics']['false_consensus']:.0f}"
    )
    print(
        "候选："
        f"{result['proposal']['pattern']} "
        f"recall={result['proposal']['metrics']['defect_recall']:.0f} "
        f"false_consensus={result['proposal']['metrics']['false_consensus']:.0f}"
    )
    print(f"裁决：{result['outcome']['state'].upper()}")
    print(f"证据：{', '.join(result['outcome']['evidence_refs'])}")


if __name__ == "__main__":
    print_report("independent")
    print()
    print_report("shared_state")
