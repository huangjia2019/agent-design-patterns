"""Zero-dependency Web workbench for the four lightweight collaboration labs.

Run from the repository root:
    python3 collaboration/light_labs/web_app.py
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import editorial_delegation_lab as delegation
import editorial_gather_lab as gather
import editorial_handoff_lab as handoff
import editorial_review_lab as review
import runtime_business_gather_lab as runtime_gather


ROOT = Path(__file__).resolve().parent
UI_ROOT = ROOT / "ui"

LESSONS: dict[str, dict[str, str]] = {
    "32": {
        "pattern": "层级委派",
        "question": "三位研究员怎样覆盖完整任务，而不是重复同一方向？",
        "benefit": "扩大覆盖面，同时让主管保留总目标与验收责任。",
    },
    "33": {
        "pattern": "扇出聚合",
        "question": "三句都正确的话，为什么会被多数票合成一句错话？",
        "benefit": "缩短墙钟时间，并保留多路证据里的差异、冲突和来源。",
    },
    "34": {
        "pattern": "对抗评审",
        "question": "两条阻断意见已经写下，为什么文章仍然发布？",
        "benefit": "用独立异议发现盲区，并让高风险问题真实影响放行。",
    },
    "35": {
        "pattern": "交接链",
        "question": "上游已经纠正事实，旧说法为什么还能在下一棒复活？",
        "benefit": "让专业角色顺序接力，同时保住状态、版本、证据和责任。",
    },
    "B1": {
        "pattern": "并发与业务聚合",
        "question": "三路 Agent 都成功返回，为什么薪酬结算仍然不能放行？",
        "benefit": "把运行成功与业务结论分账，避免用调用状态冒充证据结论。",
    },
}


def _result(
    *,
    label: str,
    tone: str,
    headline: str,
    summary: str,
    metrics: list[dict[str, str]],
    evidence: list[dict[str, str]],
    trace: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "label": label,
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "metrics": metrics,
        "evidence": evidence,
        "trace": trace,
    }


def _lesson_32() -> dict[str, Any]:
    vague = delegation.run(delegation.vague_assignments())
    scoped = delegation.run(delegation.scoped_assignments())
    return {
        "baseline": _result(
            label="模糊委派",
            tone="danger",
            headline="三个人，只覆盖一个方向",
            summary="每张资料卡单独都合格，整份简报仍缺少状态与交接。",
            metrics=[
                {"label": "覆盖", "value": f"{vague.coverage}/3"},
                {"label": "重复", "value": str(vague.duplicate_lanes)},
                {"label": "准入", "value": "拒绝"},
            ],
            evidence=[
                {"label": card.worker_id, "value": f"{card.lane} · {card.source_id}"}
                for card in vague.cards
            ],
            trace=[
                {"step": "1", "state": "派工", "detail": "三人收到同一句宽泛任务"},
                {"step": "2", "state": "执行", "detail": "三人都选择最显眼的拓扑方向"},
                {"step": "3", "state": "组合闸", "detail": "发现两块缺席，拒绝接收"},
            ],
        ),
        "pattern": _result(
            label="责任委派",
            tone="success",
            headline="三个责任面，各有主人",
            summary="模型没有变化。Assignment 与组合闸让局部努力形成完整覆盖。",
            metrics=[
                {"label": "覆盖", "value": f"{scoped.coverage}/3"},
                {"label": "重复", "value": str(scoped.duplicate_lanes)},
                {"label": "准入", "value": "通过"},
            ],
            evidence=[
                {"label": card.worker_id, "value": f"{card.lane} · {card.source_id}"}
                for card in scoped.cards
            ],
            trace=[
                {"step": "1", "state": "拆责任", "detail": "拓扑、状态、交接各自命名"},
                {"step": "2", "state": "隔离执行", "detail": "每人只处理自己的责任面"},
                {"step": "3", "state": "组合闸", "detail": "覆盖 3/3、无重复，允许接收"},
            ],
        ),
    }


def _lesson_33() -> dict[str, Any]:
    answer, support = gather.flatten_and_vote(gather.CARDS)
    report = gather.gather(gather.CARDS)
    return {
        "baseline": _result(
            label="扁平投票",
            tone="danger",
            headline="2 比 1，却得出过度结论",
            summary="会话、工作区和工具三个维度被压成一个是非题。",
            metrics=[
                {"label": "投票答案", "value": answer},
                {"label": "支持", "value": f"{support}/3"},
                {"label": "丢失", "value": "工作区共享"},
            ],
            evidence=[
                {"label": card.dimension, "value": card.boundary}
                for card in gather.CARDS
            ],
            trace=[
                {"step": "1", "state": "压平", "detail": "三个不同维度变成隔离或共享票"},
                {"step": "2", "state": "计票", "detail": "受限工具被误算成隔离票"},
                {"step": "3", "state": "结论", "detail": "工作区风险从摘要中消失"},
            ],
        ),
        "pattern": _result(
            label="证据聚合",
            tone="success",
            headline="保留差异，再形成限定结论",
            summary="聚合报告完整保留每个边界、来源和工作区风险。",
            metrics=[
                {"label": "结论", "value": report.verdict},
                {"label": "覆盖", "value": "3/3"},
                {"label": "准入", "value": "通过"},
            ],
            evidence=[
                {"label": card.dimension, "value": f"{card.boundary} · {card.source_id}"}
                for card in report.cards
            ],
            trace=[
                {"step": "1", "state": "盘点", "detail": "三个必需维度全部到齐"},
                {"step": "2", "state": "对齐", "detail": "每张卡保留自己的边界语义"},
                {"step": "3", "state": "收口", "detail": "形成 qualified，并披露共享风险"},
            ],
        ),
    }


def _lesson_34() -> dict[str, Any]:
    first = review.risky_proposal()
    first_receipt = review.review(first)
    second = review.revised_proposal()
    second_receipt = review.review(second)
    blockers = sum(item.severity == "blocker" for item in first_receipt.objections)
    return {
        "baseline": _result(
            label="评审只留评论",
            tone="danger",
            headline="两条 blocker，文章仍然发布",
            summary="发布函数只检查正文非空，评审意见没有控制效果。",
            metrics=[
                {"label": "阻断异议", "value": str(blockers)},
                {"label": "版本", "value": "v1"},
                {"label": "发布", "value": "是"},
            ],
            evidence=[
                {"label": item.rule_id, "value": item.message}
                for item in first_receipt.objections
            ],
            trace=[
                {"step": "1", "state": "提案", "detail": "完全隔离的过度结论进入候选"},
                {"step": "2", "state": "评审", "detail": "两位评审者分别提出 blocker"},
                {"step": "3", "state": "发布", "detail": "入口忽略 blocker，照常发布"},
            ],
        ),
        "pattern": _result(
            label="评审进入放行",
            tone="success",
            headline="第一版扣住，第二版重审后发布",
            summary="异议进入确定性闸，回执绑定提案版本、正文与来源。",
            metrics=[
                {"label": "v1", "value": "拒绝"},
                {"label": "v2 blocker", "value": str(len(second_receipt.objections))},
                {"label": "v2 发布", "value": "是"},
            ],
            evidence=[
                {"label": "回执摘要", "value": second_receipt.proposal_digest},
                {"label": "修订结论", "value": second.text},
            ],
            trace=[
                {"step": "1", "state": "拒绝 v1", "detail": "任一 blocker 都不能被高分抵消"},
                {"step": "2", "state": "形成 v2", "detail": "修订者收窄结论并保留边界"},
                {"step": "3", "state": "重新评审", "detail": "零 blocker 后签发本版回执"},
            ],
        ),
    }


def _lesson_35() -> dict[str, Any]:
    weak = handoff.weak_text_relay()
    baton, receipts = handoff.run_contract_chain()
    return {
        "baseline": _result(
            label="文本接力",
            tone="danger",
            headline="核查做过，旧结论仍被发布",
            summary="系统只知道来源查过、正文非空，没有检查正文消费了哪版事实。",
            metrics=[
                {"label": "来源核查", "value": "完成"},
                {"label": "正文", "value": "非空"},
                {"label": "发布", "value": "错误版本"},
            ],
            evidence=[
                {"label": "最终正文", "value": str(weak["draft"])},
                {"label": "问题", "value": "stale_claim_survived"},
            ],
            trace=[
                {"step": "1", "state": "研究", "detail": "形成完全隔离的旧结论"},
                {"step": "2", "state": "核查", "detail": "已经形成带条件的新结论"},
                {"step": "3", "state": "编辑发布", "detail": "误取旧结论，非空检查仍通过"},
            ],
        ),
        "pattern": _result(
            label="契约交接",
            tone="success",
            headline="错误稿件停在原接缝",
            summary="内容摘要不匹配时版本不前进，修复后从最后检查点继续。",
            metrics=[
                {"label": "错误编辑", "value": "v2→v2"},
                {"label": "修复编辑", "value": "v2→v3"},
                {"label": "最终版本", "value": f"v{baton.version}"},
            ],
            evidence=[
                {
                    "label": item.stage_id,
                    "value": f"v{item.input_version}→v{item.output_version} · {item.reason}",
                }
                for item in receipts
            ],
            trace=[
                {"step": "1", "state": "研究与核查", "detail": "已确认事实进入版本 2"},
                {"step": "2", "state": "拒绝旧稿", "detail": "稿件摘要没有绑定核查结论"},
                {"step": "3", "state": "修复并签收", "detail": "版本 3 编辑稿进入版本 4 发布物"},
            ],
        ),
    }


def _lesson_bonus_runtime_gather() -> dict[str, Any]:
    result = runtime_gather.run_scenario_sync("unexplained-gap")
    runtime = result.runtime
    business = result.business
    succeeded = sum(
        outcome.status is runtime_gather.WorkerStatus.SUCCEEDED
        for outcome in runtime.outcomes
    )
    passed = sum(check.passed for check in business.checks)
    return {
        "baseline": _result(
            label="只看 Harness",
            tone="danger",
            headline="3 路全部成功，业务差额仍被漏掉",
            summary="Harness 完成了并发、等待与异常收集。它没有资格替薪酬系统宣布账已对平。",
            metrics=[
                {"label": "调用成功", "value": f"{succeeded}/{len(runtime.outcomes)}"},
                {"label": "并发峰值", "value": str(runtime.peak_concurrency)},
                {"label": "运行状态", "value": runtime.status.value},
            ],
            evidence=[
                {"label": outcome.source_id, "value": outcome.status.value}
                for outcome in runtime.outcomes
            ],
            trace=[
                {"step": "1", "state": "并发启动", "detail": "员工、批次、银行三路同时运行"},
                {"step": "2", "state": "等待收齐", "detail": "三路均在超时线内返回"},
                {"step": "3", "state": "运行完成", "detail": "Harness 到这里已经履约"},
            ],
        ),
        "pattern": _result(
            label="业务证据聚合",
            tone="success",
            headline="三路都成功，放行仍被正确扣住",
            summary="聚合器对齐月份、币种和来源，再用人数与金额恒等式检查接缝。",
            metrics=[
                {"label": "业务检查", "value": f"{passed}/{len(business.checks)}"},
                {"label": "业务状态", "value": business.status.value},
                {"label": "允许放行", "value": "否"},
            ],
            evidence=[
                {
                    "label": check.name,
                    "value": f"{'通过' if check.passed else '失败'} · {check.detail}",
                }
                for check in business.checks
            ],
            trace=[
                {"step": "1", "state": "验覆盖", "detail": "三项必需来源全部到齐"},
                {"step": "2", "state": "对口径", "detail": "月份、币种与证据血缘可比较"},
                {"step": "3", "state": "查接缝", "detail": "银行金额无法解释批次总额，拒绝放行"},
            ],
        ),
    }


BUILDERS = {
    "32": _lesson_32,
    "33": _lesson_33,
    "34": _lesson_34,
    "35": _lesson_35,
    "B1": _lesson_bonus_runtime_gather,
}


def build_comparison(lesson_id: str) -> dict[str, Any]:
    if lesson_id not in BUILDERS:
        raise KeyError(lesson_id)
    return {"lesson": lesson_id, **LESSONS[lesson_id], **BUILDERS[lesson_id]()}


class LabHandler(BaseHTTPRequestHandler):
    """Serve the static UI and deterministic experiment API."""

    server_version = "CollaborationMiniLab/1.0"

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/lessons":
            self._send_json(LESSONS)
            return
        static = {
            "/": (UI_ROOT / "index.html", "text/html; charset=utf-8"),
            "/app.js": (UI_ROOT / "app.js", "text/javascript; charset=utf-8"),
            "/styles.css": (UI_ROOT / "styles.css", "text/css; charset=utf-8"),
        }
        if path in static:
            self._send_file(*static[path])
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        prefix = "/api/compare/"
        if not path.startswith(prefix):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        lesson_id = path.removeprefix(prefix)
        try:
            payload = build_comparison(lesson_id)
        except KeyError:
            self._send_json({"error": "unknown_lesson"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json(payload)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} {format % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the collaboration mini lab UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8098)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LabHandler)
    print(f"Collaboration Mini Lab: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
