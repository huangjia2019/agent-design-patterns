"""Service layer for the Payroll Governance Lab teaching console."""

from __future__ import annotations

import threading
from typing import Any

from governance_payroll_imports import load_local


bench = load_local("bench")
governance_lab = load_local("governance_lab")
observability_lab = load_local("observability_harness_lab")
policy_lab = load_local("ungoverned_policy_lab")
run_changed_after_approval = governance_lab.run_changed_after_approval
run_approval_gate = governance_lab.run_approval_gate
run_blast_radius = governance_lab.run_blast_radius
run_governed = governance_lab.run_governed
run_naive = governance_lab.run_naive
run_progressive_commitment = governance_lab.run_progressive_commitment
run_incomplete_trace = observability_lab.run_incomplete_trace
run_policy_drift = policy_lab.run_policy_drift


LAB_LOCK = threading.Lock()

LECTURES: dict[str, dict[str, Any]] = {
    "36": {
        "number": "36",
        "title": "治理模块导论",
        "pattern": "治理控制面",
        "coordinate": "Governance baseline",
        "question": "一份已经验收通过的工件，凭什么还不能直接改变世界？",
        "summary": "对照无治理桥接与完整治理链，区分工件正确、执行授权和责任回执。",
        "stages": ["已验收工件", "行动提案", "治理回执", "外部效果"],
        "variant_label": "静默放宽策略",
    },
    "37": {
        "number": "37",
        "title": "审批门",
        "pattern": "Approval Gate",
        "coordinate": "Governance x Router",
        "question": "哪类动作自动放行，哪类必须等到明确的人类授权？",
        "summary": "先路由执行路线，再路由签字角色，把审批绑定到工件、提案和策略版本。",
        "stages": ["路线分类", "签字人路由", "签署", "授权"],
        "variant_label": "补回两张工资单",
    },
    "38": {
        "number": "38",
        "title": "爆炸半径控制",
        "pattern": "Blast Radius Control",
        "coordinate": "Governance x Hierarchy",
        "question": "每个子批次都合规时，组合总额为什么仍可能越界？",
        "summary": "先沿父子预算路径预留，再允许真实副作用。",
        "stages": ["Scope Tree", "Reserve", "Effect", "Commit"],
        "variant_label": "追加第三个部门",
    },
    "39": {
        "number": "39",
        "title": "渐进承诺",
        "pattern": "Progressive Commitment",
        "coordinate": "Governance x Chain",
        "question": "Agent 的权限怎样靠证据逐级挣得，并在事故后立即收回？",
        "summary": "用新鲜证据窗口晋升，用版本化凭证授权，用事故触发快速降级。",
        "stages": [
            "入组（Enroll）",
            "评估（Evaluate）",
            "晋升（Promote）",
            "授权或降级",
        ],
        "variant_label": "越界后立即降级",
    },
    "40": {
        "number": "40",
        "title": "可观测性",
        "pattern": "Observability Harness",
        "coordinate": "Governance x Orchestrate",
        "question": "有日志为什么仍然无法证明一次执行经过了完整治理？",
        "summary": "用语义事件、因果父子关系、哈希链和覆盖审计证明发生了什么。",
        "stages": ["Emit", "Link", "Replay", "Audit"],
        "variant_label": "缺失治理控制",
    },
}


class LabBusy(RuntimeError):
    """Raised when another local governance run owns the SQLite bench."""


def reset() -> dict:
    with LAB_LOCK:
        return bench.prepare()


def run_lecture(lecture: str, *, variant: bool = False) -> dict:
    if lecture not in LECTURES:
        raise KeyError(lecture)
    if not LAB_LOCK.acquire(blocking=False):
        raise LabBusy("已有治理实验正在运行，请等待当前实验完成。")
    try:
        if lecture == "36":
            if variant:
                bench.prepare()
                result = run_policy_drift()
            else:
                naive = run_naive()
                governed = run_governed()
                result = {"naive": naive, "governed": governed}
        elif lecture == "37":
            result = run_approval_gate(
                changed_after_approval=variant,
            )
        elif lecture == "38":
            result = run_blast_radius(include_third=variant)
        elif lecture == "39":
            result = run_progressive_commitment(incident=variant)
        else:
            result = run_incomplete_trace() if variant else run_governed()
        return {
            "lecture": lecture,
            "variant": variant,
            "meta": LECTURES[lecture],
            "result": result,
            "state": bench.state(),
        }
    finally:
        LAB_LOCK.release()
