"""Service layer for the Payroll Action Lab teaching UI.

The CLI scripts remain the source of truth. This module gives the web layer a
small, structured API for running those scripts and inspecting SQLite state.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HERE = Path(__file__).parent
DB = HERE / "payroll.db"
BASELINE = HERE / "payroll.baseline.db"
MONTH = "2026-06"
TABLES = ("employees", "payroll", "approvals", "policies")
PRIMARY_KEYS = {
    "employees": "emp_id",
    "payroll": "id",
    "approvals": "id",
    "policies": "key",
}
LAB_LOCK = threading.Lock()


LECTURES: dict[str, dict[str, Any]] = {
    "21": {
        "number": "21",
        "title": "行动模块导论",
        "pattern": "裸 PRA 循环",
        "coordinate": "Action baseline",
        "question": "没有执行边界时，Agent 到底会多做多少事？",
        "summary": "观察范围漂移、批量副作用，以及已批准的 999999 如何穿透裸循环。",
        "stages": ["感知", "推理", "行动", "DB Diff"],
    },
    "22": {
        "number": "22",
        "title": "工具调度",
        "pattern": "Tool Dispatch",
        "coordinate": "Action x Router",
        "question": "这个工具此刻能不能执行？",
        "summary": "查看工具存在性、状态新鲜度、配额、审批和 Saga 补偿。",
        "stages": ["候选工具", "执行准入", "Handler", "执行账本"],
    },
    "23": {
        "number": "23",
        "title": "规划执行",
        "pattern": "Plan-and-Execute",
        "coordinate": "Action x Orchestration",
        "question": "长任务怎样在局部失败后不丢掉全局目标？",
        "summary": "运行 800 人发薪 DAG，让 b3 失败，再观察局部重排和人工对账门。",
        "stages": ["Goal", "Plan DAG", "Executor", "Checkpoint"],
    },
    "24": {
        "number": "24",
        "title": "提示链",
        "pattern": "Prompt Chaining",
        "coordinate": "Action x Chain",
        "question": "一步的错误怎样避免污染下一步？",
        "summary": "对照 checksum gate 与非空 gate，观察 27 万差额能否继续传播。",
        "stages": ["结算", "对账", "生成指令", "申请书"],
    },
    "25": {
        "number": "25",
        "title": "守卫三明治",
        "pattern": "Guardrail Sandwich",
        "coordinate": "Action x Hierarchy",
        "question": "高风险动作发生前后，分别要留下什么控制？",
        "summary": "读取 E0099 审批证据，运行 PRE、工具、POST 与策略版本 Trace。",
        "stages": ["PRE Hooks", "Tool", "POST Hooks", "Evidence"],
    },
}


class LabError(RuntimeError):
    """Raised when a controlled lab command cannot complete."""


@dataclass(frozen=True)
class LabCommand:
    label: str
    argv: tuple[str, ...]


def _run(command: LabCommand, timeout: int = 90) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, *command.argv],
        cwd=HERE,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    output = completed.stdout
    if completed.stderr:
        output += ("\n" if output else "") + completed.stderr
    return {
        "label": command.label,
        "command": "python3 " + " ".join(command.argv),
        "return_code": completed.returncode,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "output": output.strip(),
    }


def ensure_database() -> None:
    if not DB.exists() or not BASELINE.exists():
        result = _run(LabCommand("Reset database", ("db.py",)))
        if result["return_code"] != 0:
            raise LabError(result["output"])


def reset_database() -> dict[str, Any]:
    with LAB_LOCK:
        result = _run(LabCommand("Reset database", ("db.py",)))
        if result["return_code"] != 0:
            raise LabError(result["output"])
        return {"operation": result, "state": database_state()}


def inject_typo() -> dict[str, Any]:
    ensure_database()
    with LAB_LOCK:
        result = _run(LabCommand("Inject E0099 typo", ("db.py", "--inject-typo")))
        if result["return_code"] != 0:
            raise LabError(result["output"])
        return {"operation": result, "state": database_state()}


def run_lecture(lecture: str) -> dict[str, Any]:
    if lecture not in {*LECTURES, "all"}:
        raise KeyError(lecture)

    with LAB_LOCK:
        before = database_state()
        argv = ("run_action_module.py", "--lecture", lecture, "--keep-state")
        result = _run(LabCommand(f"Lecture {lecture}", argv))
        after = database_state()
        payload = {
            "lecture": lecture,
            "meta": (
                {"title": "完整行动模块", "pattern": "21 -> 25", "coordinate": "Action module"}
                if lecture == "all"
                else LECTURES[lecture]
            ),
            "before": before,
            "after": after,
            "events": parse_output(result["output"]),
            **result,
        }
        if result["return_code"] != 0:
            raise LabError(result["output"] or "lab command failed")
        return payload


def parse_output(output: str) -> list[dict[str, str]]:
    """Turn CLI output into display events without changing its meaning."""
    events: list[dict[str, str]] = []
    for raw in output.splitlines():
        text = raw.strip()
        if not text or set(text) == {"="}:
            continue

        lowered = text.lower()
        kind = "detail"
        if text.startswith("==") or text.startswith("--"):
            kind = "phase"
        elif "approval evidence" in lowered or "ledger check" in lowered:
            kind = "evidence"
        elif text.startswith("[LEDGER]") or text.startswith("[AUDIT]"):
            kind = "evidence"
        elif "pre-hook" in lowered or "post-hook" in lowered:
            kind = "control"
        elif any(token in text for token in ("BLOCKED", "REJECTED", "GATE!", "FAIL ")):
            kind = "blocked"
        elif any(token in text for token in ("PASSED", "SUCCESS", "[PASS", "[DONE")):
            kind = "success"
        elif text.startswith("[PERCEIVE]"):
            kind = "perception"
        elif text.startswith("[REASON]"):
            kind = "reasoning"
        elif text.startswith("[ACT]"):
            kind = "action"
        elif text.startswith("[runner]"):
            kind = "system"

        events.append({"kind": kind, "text": text})
    return events


def database_state() -> dict[str, Any]:
    ensure_database()
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        employee_count = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        payroll_status = dict(con.execute(
            "SELECT status, COUNT(*) FROM payroll WHERE month=? GROUP BY status",
            (MONTH,),
        ))
        approval_status = dict(con.execute(
            "SELECT status, COUNT(*) FROM approvals GROUP BY status"
        ))
        payroll_total = con.execute(
            "SELECT SUM(base + bonus + adjustment) FROM payroll WHERE month=?",
            (MONTH,),
        ).fetchone()[0]
        e0099 = con.execute(
            "SELECT id, emp_id, amount, status FROM approvals "
            "WHERE emp_id='E0099' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    changes = database_changes(limit=12)
    return {
        "database": str(DB),
        "month": MONTH,
        "employees": employee_count,
        "payroll_total": payroll_total,
        "payroll_status": payroll_status,
        "approval_status": approval_status,
        "e0099": dict(e0099) if e0099 else None,
        "change_count": changes["total"],
        "changes": changes["rows"],
        "tables": schema_overview(),
    }


def schema_overview() -> list[dict[str, Any]]:
    ensure_database()
    result: list[dict[str, Any]] = []
    with sqlite3.connect(DB) as con:
        for table in TABLES:
            columns = [
                {
                    "name": row[1],
                    "type": row[2] or "TEXT",
                    "primary_key": bool(row[5]),
                }
                for row in con.execute(f"PRAGMA table_info({table})")
            ]
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            result.append({"name": table, "count": count, "columns": columns})
    return result


def database_changes(limit: int = 20) -> dict[str, Any]:
    if not DB.exists() or not BASELINE.exists():
        return {"total": 0, "rows": []}

    rows: list[dict[str, Any]] = []
    current = sqlite3.connect(DB)
    baseline = sqlite3.connect(BASELINE)
    try:
        for table in TABLES:
            key = PRIMARY_KEYS[table]
            columns = [row[1] for row in current.execute(f"PRAGMA table_info({table})")]
            key_index = columns.index(key)
            before = {
                row[key_index]: row
                for row in baseline.execute(f"SELECT * FROM {table}")
            }
            for row in current.execute(f"SELECT * FROM {table}"):
                identifier = row[key_index]
                old = before.get(identifier)
                if old is None:
                    rows.append({
                        "table": table,
                        "key": str(identifier),
                        "kind": "new",
                        "fields": "new row",
                    })
                elif old != row:
                    changed = [
                        columns[index]
                        for index, value in enumerate(row)
                        if value != old[index]
                    ]
                    rows.append({
                        "table": table,
                        "key": str(identifier),
                        "kind": "changed",
                        "fields": ", ".join(changed),
                    })
    finally:
        current.close()
        baseline.close()

    return {"total": len(rows), "rows": rows[:limit]}


def table_rows(
    table: str,
    *,
    page: int = 1,
    page_size: int = 25,
    search: str = "",
) -> dict[str, Any]:
    if table not in TABLES:
        raise KeyError(table)
    page = max(1, page)
    page_size = min(100, max(5, page_size))
    offset = (page - 1) * page_size

    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        columns = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
        params: list[Any] = []
        where = ""
        if search:
            where = " WHERE " + " OR ".join(
                f"CAST({column} AS TEXT) LIKE ?" for column in columns
            )
            params.extend([f"%{search}%"] * len(columns))

        total = con.execute(
            f"SELECT COUNT(*) FROM {table}{where}",
            params,
        ).fetchone()[0]
        key = PRIMARY_KEYS[table]
        records = [
            dict(row)
            for row in con.execute(
                f"SELECT * FROM {table}{where} ORDER BY {key} LIMIT ? OFFSET ?",
                [*params, page_size, offset],
            )
        ]

    return {
        "table": table,
        "columns": columns,
        "rows": records,
        "page": page,
        "page_size": page_size,
        "total": total,
    }
