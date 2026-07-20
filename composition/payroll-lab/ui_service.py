"""Service layer for the Composition Selection Workbench."""
from __future__ import annotations

import threading
from typing import Any

from selection_card_lab import run_scenario


LAB_LOCK = threading.Lock()

LECTURES: dict[str, dict[str, Any]] = {
    "41": {
        "number": "41",
        "title": "模式选型卡",
        "pattern": "Pattern Selection Card",
        "question": "手工挑出几个模式，凭什么相信这套架构真的有用？",
        "summary": "把模式组合写成可证伪假设，再让同负载基线实验裁决。",
        "active": True,
    },
    "42": {
        "number": "42",
        "title": "六步选型法",
        "pattern": "Six-Step Methodology",
        "question": "怎样从业务边界走到可演进的系统组合？",
        "summary": "下一讲将把单张卡扩成完整的架构实验循环。",
        "active": False,
    },
    "43": {
        "number": "43",
        "title": "Argus 收官",
        "pattern": "Argus Full Case",
        "question": "七个认知模块怎样在一个可运行系统中咬合？",
        "summary": "收官讲将用完整 Agent 验证组合与演进。",
        "active": False,
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


class LabBusy(RuntimeError):
    """Raised when another local workbench run is active."""


def meta() -> dict[str, Any]:
    return {
        "title": "Pattern Composition Lab",
        "subtitle": "组合选型与架构证据工作台",
        "lectures": list(LECTURES.values()),
        "scenarios": list(SCENARIOS.values()),
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
