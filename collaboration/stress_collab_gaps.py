"""Stress · 协作模块后半场：教学版四个模式，各放到一种真实压力下逼出缺口。

和行动模块的 stress_gaps 同一个思路。stress_collab 证明的是「装上模式关掉一列」，
那是教学版在自己承诺的范围内成立。这个文件不植入任何 bug，把 collaboration/{a,b,c,d}
四个教学版模式一行不改，各放到一种真实压力下，让「从教学到生产」之间的缺口自己冒出来。

    G1 层级委派 · 聚合级越限   逐批都不越单批阈值，合起来几百万照样自动放行（主管只逐批把关）
    G2 扇出聚合 · 加和吞冲突   additive 把两个『分歧』求成一个更大的和，冲突信息被抹平
    G3 对抗评审 · 评审者盲区   独立评审只查它知道的那条规则，另一类阻断级从眼皮底下过
    G4 交接链   · 查存在不查值 接缝校验只保证 net_amount『交付了』，不保证它『交付对了』

四条都是教学契约本身的边界，不是错误。它们标出从教学版到生产之间真正要补的那段路。
框架四个 pattern.py 一行没改。

    python3 collaboration/stress_collab_gaps.py
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


DELEG = _load("a-hierarchical-delegation", "gaps_a")
FANOUT = _load("b-fan-out-gather", "gaps_b")
REVIEW = _load("c-adversarial-review", "gaps_c")
HANDOFF = _load("d-handoff-chain", "gaps_d")


# ── G1 · 层级委派 · 聚合级越限 ──────────────────────────────────────────────
# 教学版 SafetyBoundary.must_escalate 逐个 artifact 判 total_amount > 阈值。
# 压力：把发薪拆成很多小批，每批总额都卡在阈值下一点点。逐批都合规，合起来几百万，
# 全部自动放行，人工队列空。主管守住了每一批的边界，守不住『所有批加起来』这条边界。

def gap_aggregate_blindness() -> dict:
    SettlementSupervisor = DELEG.SettlementSupervisor
    SafetyBoundary = DELEG.SafetyBoundary
    SalaryBatchArtifact = DELEG.SalaryBatchArtifact
    Verdict = DELEG.Verdict

    threshold = 100_000.0
    per_batch = 99_000.0                       # 每批卡在阈值下一点点
    n_batches = 60
    roster = [{"id": f"e{i}", "client": f"c{i}", "base": 8000} for i in range(n_batches)]

    async def dispatch(spec, rows):
        return SalaryBatchArtifact(spec.batch_id, Verdict.SUCCESS, len(rows),
                                   total_amount=per_batch, confidence=0.99)
    sup = SettlementSupervisor(dispatch=dispatch,
                               boundary=SafetyBoundary(amount_threshold=threshold))
    result = asyncio.run(sup.run(roster))
    aggregate = round(per_batch * n_batches, 2)
    to_human = result["human_review"]
    return {"gap": "聚合级越限", "pattern": "C1 层级委派",
            "leaked": len(to_human) == 0 and aggregate > threshold * 10,
            "evidence": f"{n_batches}批×{per_batch:.0f}=合计{aggregate:.0f}，"
                        f"逐批都<{threshold:.0f}阈值 → 人工队列{len(to_human)}条，全自动放行"}


# ── G2 · 扇出聚合 · 加和吞冲突 ──────────────────────────────────────────────
# 教学版 additive 策略按 dedup_key 求和，去重是它的本分。可 additive 分不清『重复』
# 和『冲突』。压力：两个源对同一笔社保代扣报了不同的数（12万 vs 10.8万，真冲突），
# additive 把它们求成 22.8万。分歧信息被抹平，聚合器给出一个既非 12万也非 10.8万的和。
# 该用的是 competing 策略（会聚成两簇、定位分歧），选错策略 = 冲突被静默求和。

def gap_additive_masks_conflict() -> dict:
    Reconciler = FANOUT.Reconciler
    AggregatorPolicy = FANOUT.AggregatorPolicy
    Strategy = FANOUT.Strategy
    SourceResult = FANOUT.SourceResult

    sources = [
        SourceResult("payroll", {"社保代扣": 120_000.0}),
        SourceResult("social_security", {"社保代扣": 108_000.0}),   # 真冲突，不是措辞重复
    ]
    add = Reconciler(AggregatorPolicy(strategy=Strategy.ADDITIVE)).reconcile(sources)
    summed = add["merged"]["社保代扣"]
    # 对照：competing 策略能把这对冲突聚成两簇、定位到分歧
    comp = Reconciler(tol=1.0).reconcile(sources)
    located = [rc["item"] for rc in comp["root_causes"]]
    return {"gap": "加和吞冲突", "pattern": "C2 扇出聚合",
            "leaked": summed == 228_000.0 and "社保代扣" in located,
            "evidence": f"两源冲突(12万/10.8万)：additive求和={summed:.0f}(分歧被抹平)  "
                        f"competing定位到分歧={located}"}


# ── G3 · 对抗评审 · 评审者盲区 ──────────────────────────────────────────────
# 教学版独立评审真的独立，可它只查它知道的那条规则（车比登机晚）。压力：换一份产出，
# 这次赶得上车，但埋的是另一类阻断级（护照 6 个月内过期，出不了境）。评审者不查护照，
# 于是一份该拦的产出被 CONFIRMED 放行。独立 ≠ 全知，评审只挡它会查的那类问题。

def gap_reviewer_blind_spot() -> dict:
    AdversarialReview = REVIEW.AdversarialReview
    Itinerary = REVIEW.Itinerary
    Objection = REVIEW.Objection
    Severity = REVIEW.Severity
    Outcome = REVIEW.Outcome

    # 车赶得上，但护照快过期——另一类阻断级
    plan = Itinerary(legs=[{"type": "flight", "boarding": "19:30", "intl": True},
                           {"type": "taxi", "airport_eta": "18:10"},
                           {"type": "doc", "passport_expiry_days": 90}])

    async def reviewer_taxi_only(plan):        # 只会查『车 vs 登机』这一条
        taxi = next((l for l in plan.legs if l["type"] == "taxi"), None)
        flight = next((l for l in plan.legs if l["type"] == "flight"), None)
        if taxi and flight and taxi["airport_eta"] > flight["boarding"]:
            return [Objection(Severity.BLOCKER, "taxi", "车比登机晚")]
        return []

    out = asyncio.run(AdversarialReview(reviewer=reviewer_taxi_only).run(plan))
    doc = next(l for l in plan.legs if l["type"] == "doc")
    real_blocker = doc["passport_expiry_days"] < 180        # 出境要求护照有效期>6个月
    return {"gap": "评审者盲区", "pattern": "C3 对抗评审",
            "leaked": out["outcome"] is Outcome.CONFIRMED and real_blocker,
            "evidence": f"埋的是护照过期(有效期{doc['passport_expiry_days']}天<180)，"
                        f"评审只查车/登机 → 结论={out['outcome'].value}(放行)"}


# ── G4 · 交接链 · 查存在不查值 ──────────────────────────────────────────────
# 教学版接缝校验查 provides/requires 的 key 在不在 baton 上。压力：核算这棒确实交付了
# net_amount 这个 key，但值是错的（-500，一个负的发薪额）。key 在，接缝校验全过，
# 打款那棒拿到 -500 照付。接缝保证了『交付了』，没保证『交付对了』。

def gap_present_but_wrong() -> dict:
    Baton = HANDOFF.Baton
    StageSpec = HANDOFF.StageSpec
    HandoffChain = HANDOFF.HandoffChain

    paid_amount = {}

    async def intent(b):   return {"facts": {"emp": "E0007", "month": "2026-06"}}
    async def settle(b):   return {"facts": {"net_amount": -500.0}}   # key 在，值是错的
    async def pay(b):
        paid_amount["v"] = b.facts["net_amount"]
        return {"facts": {"paid": True}}

    specs = [
        (StageSpec("intent", provides=("emp", "month")), intent),
        (StageSpec("settle", requires=("emp", "month"), provides=("net_amount",)), settle),
        (StageSpec("pay", requires=("net_amount",), provides=("paid",)), pay),
    ]
    baton = asyncio.run(HandoffChain(specs).run(Baton(intent="发薪")))
    return {"gap": "查存在不查值", "pattern": "C4 交接链",
            "leaked": baton.facts.get("paid") is True and paid_amount["v"] < 0,
            "evidence": f"核算交付 net_amount={paid_amount['v']:.0f}(负数)，key在→接缝全过 → "
                        f"打款照付(paid={baton.facts.get('paid')})"}


GAPS = [gap_aggregate_blindness, gap_additive_masks_conflict,
        gap_reviewer_blind_spot, gap_present_but_wrong]


def report() -> None:
    print("=" * 78)
    print("Stress 协作后半场 · 教学版四模式 × 一种真实压力，缺口全靠压出来（零植入）")
    print("=" * 78)
    for fn in GAPS:
        r = fn()
        mark = "❌ 漏" if r["leaked"] else "✓ 挡"
        print(f"\n【{r['pattern']} · {r['gap']}】 {mark}")
        print(f"  {r['evidence']}")
        assert r["leaked"], f"{r['gap']} 未如期暴露"
    print("\n" + "-" * 78)
    print("四条都是教学契约的边界，不是 bug：主管逐批不看总量 / additive 分不清冲突与重复 /")
    print("评审只挡它会查的那类 / 接缝查 key 不查值。这就是教学版到生产之间要补的那段路。")
    print("=" * 78)


if __name__ == "__main__":
    report()
