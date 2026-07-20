"""Stress · 组合模块工作台：选错拓扑的可测代价。

行动模块压的是「执行时的注入」，协作模块压的是「跨 Agent 边界的泄漏」。组合模块不一样，
它压的是**选型**——同一个模式，用在对的任务上是解药，用在错的任务上是毒药，而且错得
悄无声息。这个台不搞攻击矩阵（那对一个讲选型的模块反而刻意），它用真代码演示一件事：

    同一个「扇出聚合」，在两种总账缺口上，一次对、一次错。

    任务 A（四个数据源口径不一，彼此独立）：扇出聚合对——分歧能归因，缺口被定位。
    任务 B（上月结转错误滚到本月，带时间依赖）：扇出聚合错——四个源都读了同一份被污染的
        结转，于是一致地报出同一个错数，聚合器看到「一致」，判「缺口不在这」，真错被漏掉。

任务 B 违反了 Brooks 的老话：任务的子部分有依赖时，并行扇出不但白花 N 倍 token，还会
制造虚假的一致。选型（六步法第一步认知功能 + 执行拓扑）本该在这里就把扇出聚合拦下，
改用迭代假设验证（循环）顺时间线回溯。

框架不动：直接用 collaboration/b-fan-out-gather 的真 Reconciler。

    python3 composition/stress_compose.py
"""
from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(__file__)


def _load(rel, name):
    path = os.path.join(ROOT, "..", "collaboration", rel, "pattern.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FAN = _load("b-fan-out-gather", "compose_b")
Reconciler = FAN.Reconciler
SourceResult = FAN.SourceResult

HANDOFF = _load("d-handoff-chain", "compose_d")


def _source_result(source_id: str, amount: float):
    return SourceResult.from_mapping(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06",
        unit="CNY",
        line_items={"社保代扣": amount},
    )


def task_a_independent() -> dict:
    """四个独立数据源，各自口径算同一笔总额。社保代扣三个 12万、一个 10.8万 → 分歧可归因。"""
    results = [
        _source_result("payroll", 120_000.0),
        _source_result("gl", 120_000.0),
        _source_result("social_security", 108_000.0),
        _source_result("attendance", 120_000.0),
    ]
    report = Reconciler(tol=1.0).reconcile(results)
    located = sorted(
        {
            source
            for verdict in report.attributable_divergences
            for source in verdict.low_sources
        }
    )
    return {"located": located, "agreed": list(report.agreed_items)}


def task_b_dependent() -> dict:
    """带时间依赖：真错是上月结转把社保基数写错了。四个源本月都从这份被污染的结转起算，
    于是全都算出同一个错数（10.8万），彼此『一致』。扇出聚合看到一致 → 判缺口不在这。"""
    corrupted = 108_000.0                         # 被上月结转污染的错数
    results = [
        _source_result("payroll", corrupted),
        _source_result("gl", corrupted),
        _source_result("social_security", corrupted),
        _source_result("attendance", corrupted),
    ]
    report = Reconciler(tol=1.0).reconcile(results)
    located = sorted(
        {
            source
            for verdict in report.attributable_divergences
            for source in verdict.low_sources
        }
    )
    return {"located": located, "agreed": list(report.agreed_items)}


# ── 六步法：给整个发薪系统落坐标（每个子任务选对那一个模式）──────────────────
# 每一行 = 一个子任务的六步法产出：认知功能（Step 2）× 执行拓扑（Step 3）→ 模式（Step 4）。
# has_dep = 这个子任务的内部步骤之间有没有先后依赖，是 Step 4 交互校验的输入。
# 坐标全部照 canonical 双轴表（一模式一格）。

PAYROLL_SUBTASKS = [
    #  子任务,            认知功能, 执行拓扑, 模式,            has_dep
    ("入口分诊",          "感知",   "路由",   "上下文分诊",      False),
    ("花名册语义压缩",    "感知",   "链式",   "语义压缩",        False),
    ("发薪工具准入",      "行动",   "路由",   "工具调度",        False),
    ("批量发薪计划",      "行动",   "编排",   "规划执行",        True),   # 计划内步骤有序
    ("段间挂闸",          "行动",   "链式",   "提示链",          True),   # 段与段有序
    ("高危动作前中后",    "行动",   "层级",   "护栏三明治",      False),
    ("主管拆批",          "协作",   "层级",   "层级委派",        False),  # 批间独立
    ("多源对账",          "协作",   "并行",   "扇出聚合",        False),  # 源彼此独立
    ("放行评审",          "协作",   "循环",   "对抗评审",        False),
    ("流水线交接",        "协作",   "链式",   "交接链",          True),   # 棒有先后
    ("分歧时间回溯",      "推理",   "循环",   "迭代假设验证",    True),   # 沿时间线依赖
    ("打款审批门",        "治理",   "路由",   "审批门",          False),
    ("全程留痕",          "治理",   "编排",   "可观测性",        False),
]

PARALLEL_TOPOLOGIES = {"并行", "扇出"}


def interaction_check(subtasks) -> list[dict]:
    """Step 4 的交互校验之一：带步间依赖的子任务不许落在并行拓扑上（Brooks）。
    返回违规清单，空 = 这套选型内部自洽。"""
    violations = []
    for name, func, topo, pattern, has_dep in subtasks:
        if has_dep and topo in PARALLEL_TOPOLOGIES:
            violations.append({"subtask": name, "topo": topo, "pattern": pattern,
                               "rule": "带步间依赖的子任务不能用并行拓扑（Brooks）"})
    return violations


def select_payroll_system() -> dict:
    """走完六步法，给发薪系统的每个子任务落坐标，再跑 Step 4 交互校验。"""
    good = interaction_check(PAYROLL_SUBTASKS)
    # 反例：把「分歧时间回溯」错选成并行的扇出聚合（本该是循环的迭代假设验证）
    wrong = [(n, f, ("并行" if n == "分歧时间回溯" else t),
              ("C2 扇出聚合" if n == "分歧时间回溯" else p), d)
             for n, f, t, p, d in PAYROLL_SUBTASKS]
    bad = interaction_check(wrong)
    return {"good_violations": good, "bad_violations": bad}


# ── 后半场：Step 4 教学版只查一条规则，查不出跨模式的接缝冲突 ─────────────────
# 两个模式各自都选对了：A2 规划执行（失败就局部改写重排）+ C4 交接链（棒 append-only）。
# 单独看都对。可把它们组合在一条流水线上，A2 想改写一个已经交接committed 的值，
# 就撞上 C4 的 append-only。dependency×parallel 那条交互校验查不出这类冲突。

def compose_seam_conflict() -> dict:
    FactRule = HANDOFF.FactRule
    FactValue = HANDOFF.FactValue
    HandoffChain = HANDOFF.HandoffChain
    StageBinding = HANDOFF.StageBinding
    StageDelta = HANDOFF.StageDelta
    StageSpec = HANDOFF.StageSpec
    TaskContract = HANDOFF.TaskContract

    async def settle(b):
        return StageDelta(
            facts=(
                FactValue(
                    "net_amount",
                    9600.0,
                    evidence_refs=("artifact://settlement/v1",),
                ),
            )
        )

    async def replan(b):
        return StageDelta(
            facts=(
                FactValue(
                    "net_amount",
                    9900.0,
                    evidence_refs=("plan://revised/v2",),
                ),
            )
        )

    # 交互校验（只查依赖×并行）看这套选型：两个都不是并行 → 判『无违规』
    fake_subtasks = [
        ("settle", "协作", "链式", "交接链", True),
        ("replan", "行动", "编排", "规划执行", True),
    ]
    check_passed = len(interaction_check(fake_subtasks)) == 0

    caught = None
    try:
        HandoffChain(
            contract=TaskContract(
                contract_id="compose-seam-conflict",
                version=1,
                objective="settle and release one payroll result",
                output_schema="Baton",
                accountable_owner="payroll-controller",
            ),
            stages=(
                StageBinding(
                    StageSpec("settle", provides=("net_amount",)),
                    settle,
                ),
                StageBinding(
                    StageSpec("replan", provides=("net_amount",)),
                    replan,
                ),
            ),
            fact_rules=(
                FactRule("net_amount", "settle", float),
            ),
        )
    except ValueError as e:
        caught = str(e)

    return {"check_passed": check_passed, "seam_conflict": caught is not None,
            "detail": caught or "（无冲突）"}


def report_selection() -> None:
    sel = select_payroll_system()
    print("=" * 74)
    print("Stress 组合 · 六步法给发薪系统落坐标（每个子任务选对那一个模式）")
    print("=" * 74)
    print(f"{'子任务':<16}{'认知功能':<8}{'执行拓扑':<8}{'模式':<16}{'步间依赖'}")
    print("-" * 74)
    for name, func, topo, pattern, has_dep in PAYROLL_SUBTASKS:
        print(f"{name:<15}{func:<8}{topo:<8}{pattern:<15}{'有' if has_dep else '—'}")
    print("-" * 74)
    print(f"Step 4 交互校验（带依赖的不许并行）：正确选型违规 {len(sel['good_violations'])} 条")
    assert not sel["good_violations"], "正确选型不该有违规"
    print("反例：把「分歧时间回溯」从循环的迭代假设验证错选成并行的扇出聚合：")
    for v in sel["bad_violations"]:
        print(f"  ✗ {v['subtask']}（{v['topo']}）违反：{v['rule']}")
    assert sel["bad_violations"], "反例应被交互校验抓到"
    print("同一套子任务，选对拓扑内部自洽；错一个坐标，Step 4 当场拦下。")
    print("这一步拦不住，错的代价就从设计期滑到运行期，掉进下面那个『虚假一致』。")

    print("\n后半场 · 单条交互校验的盲区（跨模式接缝冲突）")
    sc = compose_seam_conflict()
    print(f"  规划执行 + 交接链，两个都选对了。依赖×并行校验："
          f"{'通过(判无违规)' if sc['check_passed'] else '拦下'}")
    print("  可组合到一条流水线上，规划执行想改写已 committed 的值 → 撞交接链 append-only：")
    print(f"  ✗ {sc['detail']}")
    assert sc["check_passed"] and sc["seam_conflict"], "接缝冲突演示未如期成立"
    print("  教学版 Step 4 只查一条规则，查不出这类接缝冲突。坐标对 ≠ 组合对。")


def report() -> None:
    a = task_a_independent()
    b = task_b_dependent()
    print("=" * 74)
    print("Stress 组合 · 同一个「扇出聚合」，两种任务，一对一错")
    print("=" * 74)
    print("\n【任务 A · 四源独立】扇出聚合是对的选型")
    print(f"  定位到根因：{a['located'] or '（无）'}     一致项：{a['agreed'] or '（无）'}")
    print("  → 分歧可归因，缺口被定位到 social_security。选对了。")
    print("\n【任务 B · 带时间依赖（上月结转错误）】扇出聚合是错的选型")
    print(f"  定位到根因：{b['located'] or '（无）'}     一致项：{b['agreed']}")
    print("  → 四个源一致报同一个错数，聚合器判『一致·缺口不在这』，真错被漏。")
    print("  → 违反 Brooks：子任务有依赖时并行给不出独立探针，只买来虚假一致。")

    a_ok = "social_security" in a["located"]
    b_trap = "社保代扣" in b["agreed"] and not b["located"]   # 错被当成一致
    print("\n" + "-" * 74)
    print(f"任务A 扇出聚合定位成功 = {a_ok}")
    print(f"任务B 扇出聚合掉进虚假一致陷阱 = {b_trap}")
    print("同一份真 Reconciler 代码，选型对错的代价是可测的：A 定位根因，B 把真错藏进『一致』。")
    print("组合的第一课不是把模式堆起来，是先按认知功能 + 执行拓扑选对那一个。")
    print("=" * 74)
    assert a_ok and b_trap, "组合演示未如期成立"


if __name__ == "__main__":
    report_selection()
    print()
    report()
