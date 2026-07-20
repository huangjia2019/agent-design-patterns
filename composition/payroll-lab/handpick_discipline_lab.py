"""Composition capstone: is hand-picking a few patterns actually useful?

An independent teaching lab for the composition module's honest-reckoning
lecture. It does not select patterns for you. It runs three scenes that
answer the skeptic's charge -- "picking 3 patterns off a 33-pattern matrix
is astrology with a grid" -- with committed code, on the payroll world the
course has used throughout.

    scene 1  the loudest output is STOP. Two payroll asks that sound like
             agent work. A capability vector (seven cognitive functions,
             none/light/heavy) is written down for each. The payslip
             lookup scores zero Heavy -- the framework's answer is "do
             not build an agent, build a lookup". Only the reconciliation
             diagnosis clears the bar. The matrix earns its keep by what
             it makes you refuse.
    scene 2  the product is the rejected alternative, not the pattern.
             Two reconciliation tasks that read identically by their
             label. Hand-picking by label gives both the SAME pattern
             (Fan-out and Gather). On the shared-carryover twin the real
             committed Reconciler returns defect_recall=0 and a false
             consensus; the real committed Iterative Hypothesis loop
             recovers the root cause. The discriminator that separates
             the twins -- "does discovering A reshape the search for B"
             -- is the whole selection, and the card records Fan-out as a
             rejected alternative bound to evidence.
    scene 3  selection is necessary, not sufficient. The RIGHT pattern
             (Iterative Hypothesis) is kept fixed and one number is
             changed: max_iterations 1 vs 2. At 1 the loop cannot confirm
             and stalls (converged=False); at 2 it confirms the carryover
             root cause. The error was never in the pattern choice.

Every import here is committed code: the real Fan-out and Iterative
Hypothesis patterns. The capability vector and the thin selection card are
a teaching minimum, deliberately not Codex's composition/ pattern.py --
the two schemes are kept independent on purpose.

Run `python3 handpick_discipline_lab.py` from the repo root.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def _load(rel: str, name: str):
    """Load a committed pattern under a lab-unique module name so this lab
    never collides with Codex's composition labs in sys.modules."""
    path = REPO / rel
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_FANOUT = _load("collaboration/b-fan-out-gather/pattern.py",
                "_handpick_fanout")
_HYP = _load("reasoning/d-iterative-hypothesis/pattern.py",
             "_handpick_hypothesis")

# The payroll carry-over facts (domain data, not another lab's code).
EXPECTED_SOCIAL_SECURITY = 120_000.0
CORRUPTED_CARRYOVER = 108_000.0
GAP = EXPECTED_SOCIAL_SECURITY - CORRUPTED_CARRYOVER  # 12,000


# ---- scene 1: the capability vector and the STOP signal -------------------------

class Need(Enum):
    NONE = "none"
    LIGHT = "light"
    HEAVY = "heavy"


FUNCTIONS = ("perception", "memory", "reasoning",
             "action", "reflection", "collaboration", "governance")


@dataclass(frozen=True)
class CapabilityVector:
    """What a task actually demands of an agent, written down before any
    pattern is named. Zero Heavy dimensions is the STOP signal."""

    ask: str
    perception: Need
    memory: Need
    reasoning: Need
    action: Need
    reflection: Need
    collaboration: Need
    governance: Need

    def heavy_functions(self) -> tuple[str, ...]:
        return tuple(f for f in FUNCTIONS
                     if getattr(self, f) is Need.HEAVY)

    def verdict(self) -> str:
        heavy = self.heavy_functions()
        if not heavy:
            return "STOP: no heavy dimension -- build a lookup or a RAG, not an agent"
        return "PROCEED: heavy on " + ", ".join(heavy)


def payslip_lookup_vector() -> CapabilityVector:
    return CapabilityVector(
        ask="查询某员工本月工资条明细",
        perception=Need.LIGHT,   # one employee id in
        memory=Need.NONE,        # no state carried across turns
        reasoning=Need.NONE,     # no diagnosis, just retrieval
        action=Need.NONE,        # read-only, no external effect
        reflection=Need.NONE,
        collaboration=Need.NONE,
        governance=Need.LIGHT,   # read authorization only
    )


def reconciliation_vector() -> CapabilityVector:
    return CapabilityVector(
        ask="解释四套本月账为什么一致地少了 12000 元",
        perception=Need.LIGHT,
        memory=Need.LIGHT,       # last month's checkpoint
        reasoning=Need.HEAVY,    # propose, falsify, revise root causes
        action=Need.NONE,        # read-only investigation
        reflection=Need.LIGHT,
        collaboration=Need.NONE,
        governance=Need.LIGHT,
    )


# ---- scene 2: the twin tasks and the discriminator ------------------------------

def _reading(source_id: str, amount: float):
    return _FANOUT.SourceResult.from_mapping(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06",
        unit="CNY",
        line_items={"social_security": amount},
    )


def run_fanout(*, shared_carryover: bool) -> dict:
    """The real committed Reconciler on four sources."""
    if shared_carryover:
        amounts = {s: CORRUPTED_CARRYOVER
                   for s in ("payroll", "general_ledger",
                             "social_security", "attendance")}
    else:
        amounts = {"payroll": EXPECTED_SOCIAL_SECURITY,
                   "general_ledger": EXPECTED_SOCIAL_SECURITY,
                   "social_security": CORRUPTED_CARRYOVER,
                   "attendance": EXPECTED_SOCIAL_SECURITY}
    report = _FANOUT.Reconciler(tol=1.0).reconcile(
        tuple(_reading(s, a) for s, a in amounts.items()))
    divergences = [v.item for v in report.attributable_divergences]
    agreed = list(report.agreed_items)
    recall = float("social_security" in divergences)
    false_consensus = float(shared_carryover
                            and "social_security" in agreed
                            and not report.attributable_divergences)
    return {"pattern": "扇出聚合", "recall": recall,
            "false_consensus": false_consensus, "divergences": divergences}


def _hypothesis_roles():
    names = {
        "formula": "本月计算公式发生错误",
        "carryover": "上月结转写入了错误的社保基数",
        "posting": "总账过账独立篡改了社保金额",
    }

    def planner(problem, existing, iteration):
        if existing or iteration > 1:
            return []
        return [(names["formula"], 0.40),
                (names["carryover"], 0.55),
                (names["posting"], 0.35)]

    def generator(h):
        if h.description == names["formula"]:
            return [("本月公式版本与审批版本一致",
                     "config://payroll/formula/2026.06")]
        if h.description == names["carryover"]:
            return [("上月检查点 social_security=108000，政策基线=120000",
                     "checkpoint://payroll/2026-05")]
        return [("总账 source_ref 指向同一份上月检查点",
                 "lineage://general-ledger/2026-06")]

    def evaluator(h, desc, source):
        del desc, source
        if h.description == names["carryover"]:
            # One round of support lifts 0.55 -> 0.80 (still below the 0.9
            # confirmation bar); it takes a second round to confirm. This
            # is what makes max_iterations a load-bearing parameter.
            return "supports", 0.25
        return "refutes", -0.60

    return names, planner, generator, evaluator


def run_hypothesis(max_iterations: int) -> dict:
    """The real committed Iterative Hypothesis loop, parameterized by cap."""
    names, planner, generator, evaluator = _hypothesis_roles()
    tree, outcome = _HYP.IterativeHypothesisLoop(
        planner=planner, generator=generator, evaluator=evaluator,
        max_iterations=max_iterations,
    ).run("解释四套本月账为什么一致地少了 12000 元")
    confirmed = tree.by_id(outcome.confirmed_id) if outcome.confirmed_id else None
    hit = confirmed is not None and confirmed.description == names["carryover"]
    return {"pattern": "迭代假设验证", "max_iterations": max_iterations,
            "converged": outcome.converged, "needs_hitl": outcome.needs_hitl,
            "confirmed": confirmed.description if confirmed else None,
            "recall": float(hit), "reason": outcome.reason}


DISCRIMINATOR = "发现前一个来源的问题，会不会改变下一个来源的查法？"


# ---- scenes ---------------------------------------------------------------------

def main() -> None:
    print("== scene 1: the loudest output is STOP ==")
    for vec in (payslip_lookup_vector(), reconciliation_vector()):
        print(f"   「{vec.ask}」")
        print(f"      heavy={list(vec.heavy_functions()) or '（无）'} -> {vec.verdict()}")
    print("   -> 能力向量最先回答的不是选哪个模式，是要不要建 agent。工资条查询")
    print("      零个 Heavy，正确答案是别建。只有对账诊断越过了这道门槛。")

    print("\n== scene 2: the product is the rejected alternative ==")
    ind = run_fanout(shared_carryover=False)
    print(f"   独立四源：扇出聚合 recall={ind['recall']:.0f} "
          f"（差异定位到 {ind['divergences']}）")
    shared_fo = run_fanout(shared_carryover=True)
    print(f"   共享结转：扇出聚合 recall={shared_fo['recall']:.0f} "
          f"false_consensus={shared_fo['false_consensus']:.0f}（四源一致，误判为无差异）")
    shared_hyp = run_hypothesis(max_iterations=2)
    print(f"   共享结转：迭代假设 recall={shared_hyp['recall']:.0f} "
          f"（根因＝{shared_hyp['confirmed']}）")
    print(f"   判别问句：{DISCRIMINATOR}")
    print("   -> 两个任务按标签看一模一样，手挑给两个都发扇出聚合，第二个 recall=0。")
    print("      选型真正的产物是那张被否掉的扇出聚合卡（附带共享结转的证据），")
    print("      不是最后留下的那个模式名。")

    print("\n== scene 3: selection is necessary, not sufficient ==")
    stalled = run_hypothesis(max_iterations=1)
    solved = run_hypothesis(max_iterations=2)
    print(f"   同一个迭代假设，max_iterations=1 -> converged={stalled['converged']} "
          f"（{stalled['reason']}）")
    print(f"   同一个迭代假设，max_iterations=2 -> converged={solved['converged']} "
          f"（根因＝{solved['confirmed']}）")
    print("   -> 模式没换，只把一个数从 1 改成 2。配 1 时循环找到了唯一线索却")
    print("      来不及确认，停在无法收敛；配 2 才坐实根因。错误几乎从不在选型，")
    print("      在选对之后的参数化，那是另一门靠建了再测的手艺。")


if __name__ == "__main__":
    main()
