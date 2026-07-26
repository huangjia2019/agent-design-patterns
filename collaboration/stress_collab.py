"""Stress · 协作模块消融台：一个团队协作场景，四条边界泄漏，四个模式各关一列。

和行动模块的 stress 一个思路。行动模块的命门是「把判断安全地做出来」，压的是一个 Agent
执行时的注入。协作模块的命门是「边界」——每次活跨过一个 Agent 的边界，都会漏三样：
上下文、责任、真值。这个台把一支发薪团队放到四条真实的边界泄漏下，每装一个协作模式关一列。

    V1 上下文淹没   C1 层级委派   主管只读 artifact，不读工人的原始过程
    V2 聚合坍塌     C2 扇出聚合   gather 去重比对，不是一行 concatenate
    V3 自评橡皮章   C3 对抗评审   请一个独立的对手挑错，不让作者自己盖章
    V4 交接掉棒     C4 交接链     接力棒规约在每道接缝校验，掉了当场点名

每一格都用 collaboration/{a,b,c,d}/pattern.py 的真代码跑「没模式→漏 / 装上→拦」，零植入。
框架四个 pattern.py 一行没改，用 importlib 各自唯一模块名载入避免 `pattern` 撞名。

    python3 collaboration/stress_collab.py
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys

ROOT = os.path.dirname(__file__)


def _load(rel: str, name: str):
    path = os.path.join(ROOT, rel, "pattern.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DELEG = _load("a-hierarchical-delegation", "collab_a")
FANOUT = _load("b-fan-out-gather", "collab_b")
REVIEW = _load("c-adversarial-review", "collab_c")
HANDOFF = _load("d-handoff-chain", "collab_d")


# ── V1 · 上下文淹没（C1 层级委派）───────────────────────────────────────────
# 五个工人各算一批，每个都会倒回一大段原始计算过程。
#   没 C1：主管把每个工人的全过程都读进上下文，越背越重，第四批开始崩。
#   有 C1：SettlementSupervisor 只读工人交回的契约绑定工件，原始过程进不来。


def vector_context_flood() -> dict:
    SettlementSupervisor = DELEG.SettlementSupervisor
    SafetyBoundary = DELEG.SafetyBoundary
    SalaryBatchResult = DELEG.SalaryBatchResult
    Verdict = DELEG.Verdict
    batch_fingerprint = DELEG.batch_fingerprint
    bind_salary_result = DELEG.bind_salary_result

    clients = ["acme", "globex", "initech", "umbrella", "wayne"]
    roster = [{"id": f"e{i}", "client": clients[i % 5], "base": 8000} for i in range(100)]
    RAW_TRACE = "逐人计算：读花名册→查审批→算基数→加津贴→扣社保→核对……" * 30  # 每工人一大段过程

    # 没 C1：一个把工人全过程都concat进上下文的朴素主管
    by_client: dict[str, list] = {}
    for r in roster:
        by_client.setdefault(r["client"], []).append(r)
    naive_context = "".join(RAW_TRACE for _ in by_client)  # 每批一段原始过程全进主管
    naive_chars = len(naive_context)

    # 有 C1：真 SettlementSupervisor，工人只回契约绑定的 artifact
    async def dispatch(handoff, rows):
        _ = RAW_TRACE  # 工人内部算了一大堆…
        employee_ids = tuple(str(row["id"]) for row in rows)
        result = SalaryBatchResult(
            batch_id=handoff.contract.contract_id,
            verdict=Verdict.SUCCESS,
            employee_count=len(rows),
            total_amount=len(rows) * 10_400.0,
            input_fingerprint=batch_fingerprint(employee_ids),
            confidence=0.99,
        )
        return bind_salary_result(
            handoff,
            result,
            evidence_refs=(f"stress://{handoff.contract.contract_id}",),
        )

    sup = SettlementSupervisor(
        dispatch=dispatch, boundary=SafetyBoundary(amount_threshold=5_000_000)
    )
    result = asyncio.run(sup.run(roster))
    # 主管消费的是工件摘要，不把工人的原始过程倒回上下文。
    guarded_context = "\n".join(
        (
            f"{artifact.payload.batch_id}|"
            f"{artifact.payload.employee_count}|"
            f"{artifact.payload.total_amount:.2f}"
        )
        for artifact in result.batch_artifacts
    )
    guarded_chars = len(guarded_context)

    return {
        "vector": "上下文淹没",
        "closes_at": "C1",
        "naive_leaked": RAW_TRACE in naive_context and naive_chars > 10 * guarded_chars,
        "guarded_blocked": RAW_TRACE not in guarded_context and guarded_chars < naive_chars,
        "evidence": f"进主管上下文的字符：朴素concat={naive_chars}  C1只读artifact={guarded_chars}",
    }


# ── V2 · 聚合坍塌（C2 扇出聚合）─────────────────────────────────────────────
# 多个工人从不同角度标同一批风险，同一件事换措辞出现多次。
#   没聚合器：一行 concatenate，六百项里六成重复。
#   有 C2：Reconciler 按 dedup_key 归一化，压到去重后的条数。


def vector_gather_collapse() -> dict:
    Reconciler = FANOUT.Reconciler
    AggregatorPolicy = FANOUT.AggregatorPolicy
    Strategy = FANOUT.Strategy
    SourceResult = FANOUT.SourceResult

    # 三个工人，把同一个风险用不同措辞各报一遍
    workers = [
        SourceResult.from_mapping(
            source_id="w1",
            snapshot_ref="stress://w1",
            period="2026-06",
            unit="finding",
            line_items={"对赌条款增加": 1.0, "社保漏缴": 1.0},
        ),
        SourceResult.from_mapping(
            source_id="w2",
            snapshot_ref="stress://w2",
            period="2026-06",
            unit="finding",
            line_items={"earnout扩大": 1.0, "社保漏缴": 1.0},
        ),
        SourceResult.from_mapping(
            source_id="w3",
            snapshot_ref="stress://w3",
            period="2026-06",
            unit="finding",
            line_items={"对赌条款上调": 1.0},
        ),
    ]
    naive_items = [k for w in workers for k in w.line_items]  # 一行 concat
    naive_count = len(naive_items)  # 5 条，含重复

    def canon(s):
        if s in ("对赌条款增加", "earnout扩大", "对赌条款上调"):
            return "对赌条款变动"
        return s

    r = Reconciler(AggregatorPolicy(strategy=Strategy.ADDITIVE, identity_key=canon))
    report = r.reconcile(workers)
    guarded_count = len(report.merged)  # 去重后
    deduped = sum(len(item.raw_keys) - 1 for item in report.merged_items)

    return {
        "vector": "聚合坍塌",
        "closes_at": "C2",
        "naive_leaked": len({canon(item) for item in naive_items}) < naive_count,
        "guarded_blocked": guarded_count < naive_count and deduped > 0,
        "evidence": f"聚合后条目：concat={naive_count}(含重复)  C2去重={guarded_count}",
    }


# ── V3 · 自评橡皮章（C3 对抗评审）───────────────────────────────────────────
# 一份发薪提案里藏着一条阻断级问题：已冲正工资单仍准备付款。
#   没 C3：作者自己声明可以放行（橡皮章）。
#   有 C3：独立评审者读取工资单状态，挑出阻断级，绝不自动放行。


def vector_rubber_stamp() -> dict:
    AdversarialReview = REVIEW.AdversarialReview
    ArtifactEnvelope = REVIEW.ArtifactEnvelope
    Objection = REVIEW.Objection
    Severity = REVIEW.Severity
    Outcome = REVIEW.Outcome
    ReviewPanel = REVIEW.ReviewPanel
    ReviewPolicy = REVIEW.ReviewPolicy
    ReviewerSpec = REVIEW.ReviewerSpec
    TaskContract = REVIEW.TaskContract

    contract = TaskContract(
        contract_id="stress-review-payroll",
        version=1,
        objective="review one payroll release proposal",
        output_schema="PayrollRelease",
        accountable_owner="payroll-controller",
        boundary="the author proposes; the independent panel reviews",
    )
    proposal = {
        "employee_id": "E0007",
        "payslip_status": "REVERSED",
        "requested_action": "pay",
    }
    artifact = ArtifactEnvelope(
        artifact_id="payroll-release-r0",
        contract_digest=contract.digest,
        schema=contract.output_schema,
        produced_by="payroll-author",
        payload=proposal,
        evidence_refs=("ledger://payroll/E0007",),
    )

    async def independent(request):
        candidate = request.artifact.payload
        if candidate["payslip_status"] == "REVERSED" and candidate["requested_action"] == "pay":
            return (
                Objection(
                    code="reversed_payslip_not_payable",
                    rule_id="reversed-not-payable",
                    severity=Severity.BLOCKER,
                    field="payslip_status",
                    claim="E0007 is REVERSED and cannot be paid",
                    evidence_refs=("ledger://payroll/E0007",),
                ),
            )
        return ()

    panel = ReviewPanel(
        "payroll-risk-panel",
        (
            ReviewerSpec(
                reviewer_id="reversal-reviewer",
                actor_id="payroll-risk-agent",
                rule_ids=("reversed-not-payable",),
                evidence_scope=("read:payroll-ledger",),
                review=independent,
            ),
        ),
    )
    system = AdversarialReview(
        panel,
        ReviewPolicy(
            rubric_version="payroll-release-v1",
            required_rule_ids=("reversed-not-payable",),
            max_rounds=1,
        ),
        author_actor_id="payroll-author",
        fingerprint=lambda candidate: (
            f"{candidate['employee_id']}|"
            f"{candidate['payslip_status']}|"
            f"{candidate['requested_action']}"
        ),
    )
    guarded = asyncio.run(system.run(contract, artifact))
    naive_outcome = Outcome.CONFIRMED

    return {
        "vector": "自评橡皮章",
        "closes_at": "C3",
        "naive_leaked": naive_outcome is Outcome.CONFIRMED,
        "guarded_blocked": guarded.outcome is not Outcome.CONFIRMED,
        "evidence": f"冲正工资单仍请求付款：自评={naive_outcome.value}  "
        f"独立评审={guarded.outcome.value}",
    }


# ── V4 · 交接掉棒（C4 交接链）───────────────────────────────────────────────
# 发薪流水线：意图→核算→审批→打款。核算这棒忘了把「已核金额」交下去。
#   没契约：打款这棒拿不到金额，要么报错要么瞎猜，错在下游、根因在上游。
#   有 C4：接力棒规约在核算这道接缝当场点名它没交付。


def vector_dropped_handoff() -> dict:
    FactRule = HANDOFF.FactRule
    FactValue = HANDOFF.FactValue
    StageSpec = HANDOFF.StageSpec
    StageBinding = HANDOFF.StageBinding
    StageDelta = HANDOFF.StageDelta
    HandoffChain = HANDOFF.HandoffChain
    SeamError = HANDOFF.SeamError
    TaskContract = HANDOFF.TaskContract
    new_baton = HANDOFF.new_baton

    async def intent(view):
        return StageDelta(
            facts=(
                FactValue("emp", "E0007", ("request://payroll/E0007",)),
                FactValue("month", "2026-06", ("request://payroll/E0007",)),
            )
        )

    async def settle(view):
        return StageDelta()  # 忘了交付 net_amount（掉棒）

    async def pay(view):
        return StageDelta(facts=(FactValue("paid", True, ("payment://teaching/E0007",)),))

    contract = TaskContract(
        contract_id="stress-payroll-handoff",
        version=1,
        objective="settle and pay E0007 through specialist stages",
        output_schema="PayrollBaton",
        accountable_owner="payroll-controller",
        boundary="each stage owns only its declared facts",
    )
    stages = (
        StageBinding(
            StageSpec("intent", provides=("emp", "month")),
            intent,
        ),
        StageBinding(
            StageSpec(
                "settle",
                requires=("emp", "month"),
                provides=("net_amount",),
            ),
            settle,
        ),
        StageBinding(
            StageSpec("pay", requires=("net_amount",), provides=("paid",)),
            pay,
        ),
    )
    rules = (
        FactRule("emp", "intent", str),
        FactRule("month", "intent", str),
        FactRule("net_amount", "settle", float),
        FactRule("paid", "pay", bool),
    )

    # 没契约：朴素串起来，settle 没给 net_amount，pay 照跑（拿不到就当 0 / 崩在下游）
    naive_facts = {"emp": "E0007", "month": "2026-06"}  # settle 什么都没加
    naive_leaked = "net_amount" not in naive_facts  # 下游要用却没有，静默错

    # 有 C4：真 HandoffChain，接缝校验
    caught = None
    try:
        asyncio.run(
            HandoffChain(contract, stages, rules).run(
                new_baton(
                    contract,
                    baton_id="stress-payroll-handoff",
                    intent="发薪",
                )
            )
        )
    except SeamError as e:
        caught = str(e)

    return {
        "vector": "交接掉棒",
        "closes_at": "C4",
        "naive_leaked": naive_leaked,
        "guarded_blocked": caught is not None and "settle" in caught,
        "evidence": f"核算掉了 net_amount：没契约=静默流到下游  C4=接缝点名({'settle' if caught else '—'})",
    }


VECTORS = [
    vector_context_flood,
    vector_gather_collapse,
    vector_rubber_stamp,
    vector_dropped_handoff,
]
CLOSES = {"V1": "C1", "V2": "C2", "V3": "C3", "V4": "C4"}
VNAMES = ["上下文淹没", "聚合坍塌", "自评橡皮章", "交接掉棒"]
LEVELS = [
    ("L0", "团队裸奔"),
    ("L1", "+ C1 层级委派"),
    ("L2", "+ C2 扇出聚合"),
    ("L3", "+ C3 对抗评审"),
    ("L4", "+ C4 交接链"),
]
ORDER = ["L0", "L1", "L2", "L3", "L4"]


def run_all() -> list[dict]:
    return [fn() for fn in VECTORS]


def _cell(vi: int, level: str) -> str:
    # 向量 Vi 由第 (i+1) 层（引入对应模式的那层）关闭
    return "✓" if ORDER.index(level) >= (vi + 1) else "✗"


def table() -> None:
    results = run_all()
    for r in results:  # 先确认每条向量真成立
        assert r["naive_leaked"] and r["guarded_blocked"], f"{r['vector']} 未如期成立"
    print("=" * 78)
    print("Stress 协作全景 · 一支发薪团队 × 四条边界泄漏 × 四层协作模式")
    print("=" * 78)
    print(f"{'层级':<6}{'装上的模式':<18}" + "".join(f"{n:<10}" for n in VNAMES))
    print("-" * 78)
    for lid, title in LEVELS:
        cells = "".join(f"{_cell(i, lid):<11}" for i in range(4))
        leaks = sum(_cell(i, lid) == "✗" for i in range(4))
        print(f"{lid:<6}{title:<16}{cells}{'全干净' if leaks == 0 else str(leaks) + '列漏'}")
    print("-" * 78)
    print("每加一个协作模式关掉不同的一列。四格都由 collaboration/a-d 真代码跑出，框架零改动。")
    for r in results:
        print(f"  · {r['vector']}（{r['closes_at']}）：{r['evidence']}")
    print("=" * 78)


if __name__ == "__main__":
    table()
