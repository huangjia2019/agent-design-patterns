"""Service layer for the Payroll Reflection Lab teaching UI."""
from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


HERE = Path(__file__).parent
ACTION_LAB = HERE.parent.parent / "action" / "payroll-lab"
DB = ACTION_LAB / "payroll.db"
BASELINE = ACTION_LAB / "payroll.baseline.db"
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
    "26": {
        "number": "26",
        "title": "反思模块导论",
        "pattern": "外部信号契约",
        "coordinate": "Reflection baseline",
        "question": "同一份月报，Agent 自评和账本对账为什么会得出相反结论？",
        "summary": "对照纯内省与两条 SQL，让事实源成为反思回路之外的镜子。",
        "stages": ["待审月报", "纯内省", "SQL 对账", "强制修订"],
        "variant_label": "更严格自评",
        "available": True,
    },
    "27": {
        "number": "27",
        "title": "生成批评",
        "pattern": "Generator-Critic",
        "coordinate": "Reflection x Chain",
        "question": "为什么修改稿必须重新送审，不能在同一遍里自动通过？",
        "summary": "运行一次生成、批评、策略闸和修改稿，再显式送入第二遍复审。",
        "stages": ["Generate", "Critique", "Policy Gate", "Revision Draft"],
        "variant_label": "橡皮图章",
        "available": True,
    },
    "28": {
        "number": "28",
        "title": "技能包",
        "pattern": "Skill Package",
        "coordinate": "Reflection x Router",
        "question": "一次跑通的流程，凭什么进入复用路由？",
        "summary": "对照验证后入库与跳过验证，让路由只看 VERIFIED。",
        "stages": ["Distill", "Verify", "Promote", "Route"],
        "variant_label": "跳过验证",
        "available": True,
    },
    "29": {
        "number": "29",
        "title": "经验回放",
        "pattern": "Experience Replay",
        "coordinate": "Reflection x Hierarchy",
        "question": "一条教训怎样靠复用战绩留下或出池？",
        "summary": "召回历史经验，回写下游成败，归档伪经验并毕业硬规则。",
        "stages": ["Recall", "Inject", "Feedback", "Graduate"],
        "variant_label": "断开反馈",
        "available": True,
    },
    "30": {
        "number": "30",
        "title": "自愈循环",
        "pattern": "Self-Heal Loop",
        "coordinate": "Reflection x Loop",
        "question": "修复怎样在确定性信号和熔断线之间收敛？",
        "summary": "用确定性红灯驱动修复，失败路径统一回滚到基线后交人工。",
        "stages": ["Diagnose", "Review Patch", "Atomic Apply", "Verify / Stop"],
        "variant_label": "失控循环",
        "available": True,
    },
}


class LabError(RuntimeError):
    """Raised when a controlled lab command cannot complete."""


class LabBusy(LabError):
    """Raised when another local lab run owns the shared SQLite bench."""


class LabUnavailable(LabError):
    """Raised when a lecture is designed but not connected to the Repo yet."""


@dataclass(frozen=True)
class LabCommand:
    label: str
    argv: tuple[str, ...]
    cwd: Path = HERE


@contextmanager
def exclusive_run() -> Iterator[None]:
    if not LAB_LOCK.acquire(blocking=False):
        raise LabBusy("已有反思实验正在运行，请等待当前实验完成。")
    try:
        yield
    finally:
        LAB_LOCK.release()


def _run(command: LabCommand, timeout: int = 90) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, *command.argv],
        cwd=command.cwd,
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


def _reset_action_database() -> dict[str, Any]:
    result = _run(LabCommand("Reset action baseline", ("db.py",), ACTION_LAB))
    if result["return_code"] != 0:
        raise LabError(result["output"])
    return result


def ensure_database() -> None:
    if not DB.exists() or not BASELINE.exists():
        _reset_action_database()


def _prepare_month_end() -> None:
    _reset_action_database()
    with sqlite3.connect(DB) as con:
        con.execute("UPDATE payroll SET status='PAID' WHERE month=?", (MONTH,))
        con.execute(
            "UPDATE payroll SET status='REVERSED' "
            "WHERE month=? AND emp_id IN ('E0007','E0012')",
            (MONTH,),
        )
        con.commit()


def prepare_month_end_state() -> dict[str, Any]:
    with exclusive_run():
        started = time.monotonic()
        _prepare_month_end()
        operation = {
            "label": "Rebuild month-end reflection state",
            "command": "month_end_state()",
            "return_code": 0,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "output": "月末场景已重建：PAID 798，REVERSED 2。",
        }
        return {"operation": operation, "state": database_state()}


def reset_database() -> dict[str, Any]:
    with exclusive_run():
        operation = _reset_action_database()
        return {"operation": operation, "state": database_state()}


def run_lecture(lecture: str, *, variant: bool = False) -> dict[str, Any]:
    if lecture == "all":
        selected = [number for number, meta in LECTURES.items() if meta["available"]]
    elif lecture not in LECTURES:
        raise KeyError(lecture)
    elif not LECTURES[lecture]["available"]:
        raise LabUnavailable(f"第 {lecture} 讲尚未接入可运行 Repo。")
    else:
        selected = [lecture]

    with exclusive_run():
        before = database_state()
        argv = ["run_reflection_module.py", "--lecture", lecture]
        if variant and lecture != "all":
            argv.append("--variant")
        result = _run(LabCommand(f"Lecture {lecture}", tuple(argv)))
        after = database_state()
        payload = {
            "lecture": lecture,
            "variant": variant,
            "meta": (
                {
                    "title": "已接入的反思模块",
                    "pattern": "26 -> 30",
                    "coordinate": "Reflection module",
                }
                if lecture == "all"
                else LECTURES[lecture]
            ),
            "lectures_run": selected,
            "before": before,
            "after": after,
            "events": parse_output(result["output"]),
            "analysis": analyze_output(lecture, result["output"]),
            **result,
        }
        if result["return_code"] != 0:
            raise LabError(result["output"] or "lab command failed")
        return payload


def parse_output(output: str) -> list[dict[str, str]]:
    """Turn CLI output into evidence-oriented events."""
    events: list[dict[str, str]] = []
    for raw in output.splitlines():
        text = raw.strip()
        if not text or set(text) == {"="}:
            continue

        lowered = text.lower()
        kind = "detail"
        if text.startswith("==") or text.startswith("Lecture "):
            kind = "phase"
        elif text.startswith("[VERDICT]") or "ledger truth" in lowered:
            kind = "evidence"
        elif (
            text.startswith("REJECTED:")
            or "[FAIL]" in text
            or "ISSUE BLOCKER" in text
            or "BLOCKED_BY_CRITIC" in text
        ):
            kind = "blocked"
        elif "APPROVED, score" in text:
            kind = "introspection"
        elif text.startswith("[REVISION_DRAFT]") or (
            text.startswith("MONTHLY-REPORT") and "exceptions=E" in text
        ):
            kind = "revised"
        elif (
            text.startswith("[PASS")
            or "PROMOTED" in text
            or "status: CLEAN" in text
            or "status: FIXED" in text
        ):
            kind = "success"
        elif text.startswith("status:"):
            kind = "blocked"
        elif text.startswith("baseline_restored:"):
            kind = "evidence"
        elif text.startswith("[BOUNDARY]") or "rolled back" in lowered:
            kind = "evidence"
        elif "external" in lowered or "two sql" in lowered or "ledger" in lowered:
            kind = "evidence"
        elif "archived" in lowered or "graduation candidates" in lowered:
            kind = "evidence"
        elif text.startswith("[runner]") or text.startswith("created payroll.db"):
            kind = "system"

        events.append({"kind": kind, "text": text})
    return events


def analyze_output(lecture: str, output: str) -> dict[str, Any]:
    if lecture == "26":
        scores = [
            int(score)
            for score in re.findall(r"attempt \d+ [^\n]*score (\d+)/100", output)
        ]
        rejected = re.findall(r"REJECTED: (.+)", output)
        revisions = re.findall(
            r"MONTHLY-REPORT month=2026-06 paid=(\d+) reversed=(\d+) "
            r"exceptions=([^ ]+) conclusion=([^\n]+)",
            output,
        )
        revision = revisions[-1] if revisions else None
        result = {
            "self_scores": scores,
            "external_findings": len(rejected),
            "findings": rejected,
            "revision": (
                {
                    "paid": int(revision[0]),
                    "reversed": int(revision[1]),
                    "exceptions": revision[2],
                    "conclusion": revision[3],
                }
                if revision
                else None
            ),
        }
        result["metrics"] = [
            {"label": "纯内省", "value": f"{scores[0]} / 100" if scores else "--", "note": "approved twice"},
            {"label": "外部对账", "value": f"{len(rejected)} findings", "note": "ledger findings"},
            {
                "label": "修订结论",
                "value": revision[3] if revision else "--",
                "note": "forced by evidence",
            },
        ]
        return result

    if lecture == "27":
        decisions = re.findall(r"\[PASS \d+\] decision=([a-z_]+)", output)
        blockers = len(re.findall(r"\[ISSUE BLOCKER\]", output))
        wrong_report = "wrong_report=true" in output
        return {
            "decisions": decisions,
            "grounded_blockers": blockers,
            "wrong_report_accepted": wrong_report,
            "metrics": [
                {"label": "首轮裁决", "value": decisions[0].upper() if decisions else "--", "note": "reviewed artifact"},
                {"label": "证据阻断", "value": str(blockers), "note": "grounded blockers"},
                {
                    "label": "复审结果",
                    "value": (
                        "WRONG ACCEPT"
                        if wrong_report
                        else (decisions[-1].upper() if decisions else "--")
                    ),
                    "note": "explicit second pass",
                },
            ],
        }

    if lecture == "28":
        failed = re.findall(
            r"\[FAIL\] ([^:]+): expected (\d+), skill computed (\d+)", output
        )
        passed = re.findall(r"\[PASS\] ([^\n]+)", output)
        promoted = "PROMOTED to VERIFIED" in output
        matched = re.findall(r"(?:matched:|route matched:) ([a-z0-9-]+)", output)
        wrong_match = re.search(r"(\d+) contribution bases computed wrong", output)
        wrong = int(wrong_match.group(1)) if wrong_match else 0
        no_gate = "stored as trusted, never verified" in output

        if no_gate:
            metrics = [
                {"label": "能力准入", "value": "SKIPPED", "note": "never verified"},
                {"label": "错误基数", "value": f"{wrong} / 800", "note": "2025 bounds"},
                {"label": "运行信号", "value": "SILENT", "note": "every step succeeded"},
            ]
        else:
            metrics = [
                {"label": "首次验证", "value": f"{len(failed)} failed", "note": "stays TRIAL"},
                {"label": "修正复验", "value": f"{len(passed) - 1} passed", "note": "promoted"},
                {
                    "label": "能力路由",
                    "value": "VERIFIED ONLY" if promoted else "BLOCKED",
                    "note": matched[-1] if matched else "from_scratch",
                },
            ]

        return {
            "failed_goldens": [item[0] for item in failed],
            "passed_goldens": passed,
            "promoted": promoted,
            "matched": matched[-1] if matched else None,
            "wrong_bases": wrong,
            "gate_skipped": no_gate,
            "metrics": metrics,
        }

    if lecture == "29":
        misbound_groups = re.findall(
            r"mis-bound(?: \([^)]+\))?: \[([^\]]*)\]", output
        )
        misbound_counts = [
            len(re.findall(r"'[^']+'", group)) for group in misbound_groups
        ]
        effectiveness = re.findall(
            r"month \d+: membership eff=([0-9.]+)\s+ritual eff=([0-9.]+)",
            output,
        )
        ritual_state = re.search(
            r"ritual lesson archived=(True|False) after (\d+) reuses", output
        )
        graduation = re.search(r"graduation candidates: \[([^\]]*)\]", output)
        no_feedback = "--no-feedback" in output

        if no_feedback:
            neutral = re.search(
                r"ritual eff=([0-9.]+) \(still neutral\), archived=(True|False)",
                output,
            )
            membership = re.search(
                r"membership lesson: reuses=(\d+), eff=([0-9.]+)", output
            )
            return {
                "feedback_connected": False,
                "ritual_effectiveness": (
                    float(neutral.group(1)) if neutral else None
                ),
                "ritual_archived": (
                    neutral.group(2) == "True" if neutral else None
                ),
                "membership_reuses": (
                    int(membership.group(1)) if membership else None
                ),
                "metrics": [
                    {"label": "反馈回写", "value": "DISCONNECTED", "note": "six months"},
                    {
                        "label": "伪经验",
                        "value": (
                            f"{float(neutral.group(1)):.2f}"
                            if neutral
                            else "--"
                        ),
                        "note": "still in context",
                    },
                    {
                        "label": "真教训战绩",
                        "value": (
                            f"{int(membership.group(1))} reuses"
                            if membership
                            else "--"
                        ),
                        "note": "cannot graduate",
                    },
                ],
            }

        graduates = (
            re.findall(r"'([^']+)'", graduation.group(1)) if graduation else []
        )
        last_effectiveness = effectiveness[-1] if effectiveness else None
        return {
            "feedback_connected": True,
            "misbound_before": misbound_counts[0] if misbound_counts else None,
            "misbound_after": misbound_counts[-1] if misbound_counts else None,
            "membership_effectiveness": (
                float(last_effectiveness[0]) if last_effectiveness else None
            ),
            "ritual_effectiveness": (
                float(last_effectiveness[1]) if last_effectiveness else None
            ),
            "ritual_archived": (
                ritual_state.group(1) == "True" if ritual_state else None
            ),
            "graduation_candidates": graduates,
            "metrics": [
                {
                    "label": "部门错绑",
                    "value": (
                        f"{misbound_counts[0]} -> {misbound_counts[-1]}"
                        if len(misbound_counts) >= 2
                        else "--"
                    ),
                    "note": "bare vs replay",
                },
                {
                    "label": "伪经验",
                    "value": (
                        "ARCHIVED"
                        if ritual_state and ritual_state.group(1) == "True"
                        else "ACTIVE"
                    ),
                    "note": (
                        f"effectiveness {last_effectiveness[1]}"
                        if last_effectiveness
                        else "no signal"
                    ),
                },
                {
                    "label": "守卫候选",
                    "value": str(len(graduates)),
                    "note": graduates[0] if graduates else "none",
                },
            ],
        }

    if lecture == "30":
        statuses = re.findall(r"status: ([A-Z_]+)", output)
        rolled_back = re.findall(r"rolled back, newest first: \[([^\]]*)\]", output)
        is_meltdown = "naive loop (no critic" in output

        if is_meltdown:
            naive_section, controlled_section = output.split(
                "same fixer under the bounded stop policy:", maxsplit=1
            )
            naive_rounds = len(
                re.findall(r"^\s*round \d+: RED", naive_section, flags=re.MULTILINE)
            )
            controlled_rounds = len(
                re.findall(r"^\s*round \d+: RED", controlled_section, flags=re.MULTILINE)
            )
            failure_class_match = re.search(
                r"distinct failure classes: (\d+)", output
            )
            failure_classes = (
                int(failure_class_match.group(1)) if failure_class_match else 0
            )
            metrics = [
                {
                    "label": "裸跑 / 受控",
                    "value": f"{naive_rounds} -> {controlled_rounds}",
                    "note": "rounds before stop",
                },
                {
                    "label": "稳定故障类",
                    "value": str(failure_classes),
                    "note": "9 red signals",
                },
                {
                    "label": "安全出口",
                    "value": statuses[-1] if statuses else "--",
                    "note": "baseline restored",
                },
            ]
        else:
            convergence_section = output.split("== scene 2:", maxsplit=1)[0]
            controlled_rounds = len(
                re.findall(r"^\s*round \d+: RED", convergence_section, flags=re.MULTILINE)
            )
            naive_rounds = 0
            metrics = [
                {"label": "收敛轮次", "value": str(controlled_rounds), "note": "deterministic signals"},
                {
                    "label": "修复终态",
                    "value": statuses[0] if statuses else "--",
                    "note": "verified green",
                },
                {
                    "label": "作弊补丁",
                    "value": statuses[-1] if statuses else "--",
                    "note": "baseline intact",
                },
            ]

        return {
            "statuses": statuses,
            "rounds": naive_rounds + controlled_rounds,
            "naive_rounds": naive_rounds,
            "controlled_rounds": controlled_rounds,
            "failure_classes": failure_classes if is_meltdown else 0,
            "rolled_back": rolled_back[-1] if rolled_back else "",
            "metrics": metrics,
        }

    return {}


def database_state() -> dict[str, Any]:
    ensure_database()
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        employee_count = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        payroll_status = dict(
            con.execute(
                "SELECT status, COUNT(*) FROM payroll WHERE month=? GROUP BY status",
                (MONTH,),
            )
        )
        payroll_total = con.execute(
            "SELECT SUM(base + bonus + adjustment) FROM payroll WHERE month=?",
            (MONTH,),
        ).fetchone()[0]

    paid = payroll_status.get("PAID", 0)
    reversed_count = payroll_status.get("REVERSED", 0)
    report_claim = {"paid": 800, "reversed": 0, "conclusion": "all-clear"}
    findings = int(paid != report_claim["paid"]) + int(
        reversed_count != report_claim["reversed"]
    )
    changes = database_changes(limit=12)
    return {
        "database": str(DB),
        "month": MONTH,
        "employees": employee_count,
        "payroll_total": payroll_total,
        "payroll_status": payroll_status,
        "change_count": changes["total"],
        "changes": changes["rows"],
        "report_claim": report_claim,
        "ledger_truth": {"paid": paid, "reversed": reversed_count},
        "mismatch_findings": findings,
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
            before = {row[key_index]: row for row in baseline.execute(f"SELECT * FROM {table}")}
            for row in current.execute(f"SELECT * FROM {table}"):
                identifier = row[key_index]
                old = before.get(identifier)
                if old is None:
                    rows.append(
                        {
                            "table": table,
                            "key": str(identifier),
                            "kind": "new",
                            "fields": "new row",
                        }
                    )
                elif old != row:
                    changed = [
                        columns[index]
                        for index, value in enumerate(row)
                        if value != old[index]
                    ]
                    rows.append(
                        {
                            "table": table,
                            "key": str(identifier),
                            "kind": "changed",
                            "fields": ", ".join(changed),
                        }
                    )
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

        total = con.execute(f"SELECT COUNT(*) FROM {table}{where}", params).fetchone()[0]
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
