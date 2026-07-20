"""Service layer for the Composition Selection Workbench."""
from __future__ import annotations

import threading
from typing import Any

from capstone_lab import run_capstone
from selection_card_lab import run_scenario
from six_step_lab import run_methodology


LAB_LOCK = threading.Lock()

LECTURES: dict[str, dict[str, Any]] = {
    "41": {
        "number": "41",
        "title": "模式选型卡",
        "pattern": "Pattern Selection Card",
        "question": "手工挑出几个模式，凭什么相信这套架构真的有用？",
        "summary": "把模式组合写成可证伪假设，再让同负载基线实验裁决。",
        "href": "/",
    },
    "42": {
        "number": "42",
        "title": "六步选型法",
        "pattern": "Six-Step Methodology",
        "question": "怎样从业务边界走到可演进的系统组合？",
        "summary": "用接缝预检、同负载对照与消融收敛多模式架构。",
        "href": "/42",
    },
    "43": {
        "number": "43",
        "title": "完整系统",
        "pattern": "Full System Assembly",
        "question": "八个模块都通过测试，为什么完整系统仍可能失败？",
        "summary": "让版本、回执、权限与业务事实沿同一条证据链闭环。",
        "href": "/43",
    },
}

SCENARIOS = {
    "independent": {
        "id": "independent",
        "label": "四源独立",
        "description": "来源各自拥有快照，一个结果不改变下一次读取。",
    },
    "shared_state": {
        "id": "shared_state",
        "label": "共享结转",
        "description": "四个本月结果依赖同一份上月检查点。",
    },
}

SIX_STEP_VIEWS = {
    "seams": {
        "id": "seams",
        "label": "接缝预检",
        "description": "先查同一工件的写入权与冻结时点，再决定谁能进入实验。",
    },
    "decision": {
        "id": "decision",
        "label": "对照与消融",
        "description": "在同一超时负载上比较基线、候选与两个移除变体。",
    },
}

CAPSTONE_MODES = {
    "local-only": {
        "id": "local-only",
        "label": "局部成功",
        "description": "八个模块各自通过，但父回执与工件版本没有连续传递。",
    },
    "bound": {
        "id": "bound",
        "label": "端到端闭环",
        "description": "同一批模块绑定运行契约、工件摘要、审批回执与 SQLite 端点。",
    },
}


class LabBusy(RuntimeError):
    """Raised when another local workbench run is active."""


def meta(active_lecture: str = "41") -> dict[str, Any]:
    return {
        "title": "Pattern Composition Lab",
        "subtitle": "组合选型与架构证据工作台",
        "lectures": [
            {
                **lecture,
                "active": lecture["number"] == active_lecture,
            }
            for lecture in LECTURES.values()
        ],
        "scenarios": list(SCENARIOS.values()),
    }


def six_step_meta() -> dict[str, Any]:
    return {
        **meta("42"),
        "views": list(SIX_STEP_VIEWS.values()),
    }


def capstone_meta() -> dict[str, Any]:
    return {
        **meta("43"),
        "modes": list(CAPSTONE_MODES.values()),
    }


def run(scenario: str) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise KeyError(scenario)
    if not LAB_LOCK.acquire(blocking=False):
        raise LabBusy("已有选型实验正在运行，请等待当前实验完成。")
    try:
        return {
            "meta": SCENARIOS[scenario],
            "run": run_scenario(scenario),
        }
    finally:
        LAB_LOCK.release()


def run_six_step(view: str) -> dict[str, Any]:
    if view not in SIX_STEP_VIEWS:
        raise KeyError(view)
    if not LAB_LOCK.acquire(blocking=False):
        raise LabBusy("已有选型实验正在运行，请等待当前实验完成。")
    try:
        return {
            "meta": SIX_STEP_VIEWS[view],
            "view": view,
            "run": run_methodology(),
        }
    finally:
        LAB_LOCK.release()


def run_capstone_workbench(mode: str) -> dict[str, Any]:
    if mode not in CAPSTONE_MODES:
        raise KeyError(mode)
    if not LAB_LOCK.acquire(blocking=False):
        raise LabBusy("已有选型实验正在运行，请等待当前实验完成。")
    try:
        return {
            "meta": CAPSTONE_MODES[mode],
            "mode": mode,
            "run": run_capstone(mode),
        }
    finally:
        LAB_LOCK.release()
