"""Stress · 协作模块后半场：教学版四个模式，各放到一种真实压力下逼出缺口。

和行动模块的 stress_gaps 同一个思路。stress_collab 证明的是「装上模式关掉一列」，
那是教学版在自己承诺的范围内成立。这个文件不植入业务 bug，把 collaboration/{a,b,c,d}
四个教学版模式各放到一种真实压力下，让「接口具备能力」和「生产正确配置」之间的缺口冒出来。

    G1 层级委派 · 聚合级越限   逐批都不越单批阈值，未配置组合上限时整月仍会自动放行
    G2 扇出聚合 · 加和吞冲突   additive 把两个『分歧』求成一个更大的和，冲突信息被抹平
    G3 对抗评审 · 评审者盲区   独立评审只查它知道的那条规则，另一类阻断级从眼皮底下过
    G4 交接链   · 查存在不查值 接缝校验只保证 net_amount『交付了』，不保证它『交付对了』

四条都是教学契约或生产配置的边界，不是业务错误。它们标出从教学版到生产之间真正要补的那段路。

    python3 collaboration/stress_collab_gaps.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from dataclasses import dataclass

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
# SafetyBoundary 逐批验收，PortfolioBoundary 负责组合级约束。
# 压力：把发薪拆成很多小批，每批总额都卡在阈值下一点点。先不配置组合上限，
# 再配置总额上限。接口相同，只改变一项生产策略，观察根回执是否改变。

def gap_aggregate_blindness() -> dict:
    SettlementSupervisor = DELEG.SettlementSupervisor
    SafetyBoundary = DELEG.SafetyBoundary
    PortfolioBoundary = DELEG.PortfolioBoundary
    SalaryBatchResult = DELEG.SalaryBatchResult
    Verdict = DELEG.Verdict
    batch_fingerprint = DELEG.batch_fingerprint
    bind_salary_result = DELEG.bind_salary_result

    threshold = 100_000.0
    per_batch = 99_000.0
    n_batches = 60
    roster = [{"id": f"e{i}", "client": f"c{i}", "base": 8000} for i in range(n_batches)]

    async def dispatch(handoff, rows):
        employee_ids = tuple(str(row["id"]) for row in rows)
        result = SalaryBatchResult(
            batch_id=handoff.contract.contract_id,
            verdict=Verdict.SUCCESS,
            employee_count=len(rows),
            total_amount=per_batch,
            input_fingerprint=batch_fingerprint(employee_ids),
            confidence=0.99,
        )
        return bind_salary_result(
            handoff,
            result,
            evidence_refs=("stress://aggregate-blindness",),
        )

    blind = SettlementSupervisor(
        dispatch=dispatch,
        boundary=SafetyBoundary(amount_threshold=threshold),
        portfolio_boundary=PortfolioBoundary(max_total_amount=None),
    )
    guarded = SettlementSupervisor(
        dispatch=dispatch,
        boundary=SafetyBoundary(amount_threshold=threshold),
        portfolio_boundary=PortfolioBoundary(max_total_amount=threshold * 10),
    )
    blind_result = asyncio.run(blind.run(roster))
    guarded_result = asyncio.run(guarded.run(roster))
    aggregate = round(per_batch * n_batches, 2)
    blind_decision = blind_result.portfolio_receipt.decision.value
    guarded_decision = guarded_result.portfolio_receipt.decision.value
    return {"gap": "聚合级越限", "pattern": "C1 层级委派",
            "leaked": blind_decision == "accepted" and guarded_decision == "escalated",
            "evidence": f"{n_batches}批×{per_batch:.0f}=合计{aggregate:.0f}，"
                        f"未配组合线={blind_decision}，配置组合线={guarded_decision}"}


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
        SourceResult.from_mapping(
            source_id="payroll",
            snapshot_ref="snapshot://payroll",
            period="2026-06",
            unit="CNY",
            line_items={"社保代扣": 120_000.0},
        ),
        SourceResult.from_mapping(
            source_id="social_security",
            snapshot_ref="snapshot://social-security",
            period="2026-06",
            unit="CNY",
            line_items={"社保代扣": 108_000.0},
        ),
    ]
    add = Reconciler(AggregatorPolicy(strategy=Strategy.ADDITIVE)).reconcile(sources)
    summed = add.merged["社保代扣"]
    # 对照：competing 策略能把这对冲突聚成两簇、定位到分歧
    comp = Reconciler(tol=1.0).reconcile(sources)
    located = [verdict.item for verdict in comp.attributable_divergences]
    return {"gap": "加和吞冲突", "pattern": "C2 扇出聚合",
            "leaked": summed == 228_000.0 and "社保代扣" in located,
            "evidence": f"两源冲突(12万/10.8万)：additive求和={summed:.0f}(分歧被抹平)  "
                        f"competing定位到分歧={located}"}


# ── G3 · 对抗评审 · 评审者盲区 ──────────────────────────────────────────────
# 教学版独立评审真的独立，可它只查它知道的那条规则（车比登机晚）。压力：换一份产出，
# 这次赶得上车，但埋的是另一类阻断级（护照 6 个月内过期，出不了境）。评审者不查护照，
# 于是一份该拦的产出被 CONFIRMED 放行。评审闸执行了策略，可策略本身漏了风险目录。


@dataclass(frozen=True)
class TravelCandidate:
    taxi_eta: str
    boarding: str
    passport_expiry_days: int

def gap_reviewer_blind_spot() -> dict:
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
        contract_id="confirm-international-trip",
        version=1,
        objective="confirm one reviewed itinerary",
        output_schema="TravelCandidate",
        accountable_owner="travel-controller",
        boundary="reviewers may object; only the gate may confirm",
    )
    plan = TravelCandidate(
        taxi_eta="18:10",
        boarding="19:30",
        passport_expiry_days=90,
    )
    artifact = ArtifactEnvelope(
        artifact_id="travel-candidate-r0",
        contract_digest=contract.digest,
        schema=contract.output_schema,
        produced_by="travel-author",
        payload=plan,
        evidence_refs=("booking://flight-42", "booking://taxi-7"),
    )

    async def reviewer_taxi_only(request):
        candidate = request.artifact.payload
        if candidate.taxi_eta > candidate.boarding:
            return (
                Objection(
                    code="taxi_after_boarding",
                    rule_id="taxi-before-boarding",
                    severity=Severity.BLOCKER,
                    field="taxi_eta",
                    claim="车比登机晚",
                    evidence_refs=("booking://flight-42", "booking://taxi-7"),
                ),
            )
        return ()

    panel = ReviewPanel(
        "taxi-only-panel",
        (
            ReviewerSpec(
                reviewer_id="taxi-reviewer",
                actor_id="travel-risk-agent",
                rule_ids=("taxi-before-boarding",),
                evidence_scope=("read:flight", "read:taxi"),
                review=reviewer_taxi_only,
            ),
        ),
    )
    system = AdversarialReview(
        panel,
        ReviewPolicy(
            rubric_version="travel-taxi-only-v1",
            required_rule_ids=("taxi-before-boarding",),
            max_rounds=1,
        ),
        author_actor_id="travel-author",
        fingerprint=lambda candidate: (
            f"{candidate.taxi_eta}|{candidate.boarding}|"
            f"{candidate.passport_expiry_days}"
        ),
    )
    out = asyncio.run(system.run(contract, artifact))
    real_blocker = plan.passport_expiry_days < 180
    return {"gap": "评审者盲区", "pattern": "C3 对抗评审",
            "leaked": out.outcome is Outcome.CONFIRMED and real_blocker,
            "evidence": f"护照有效期{plan.passport_expiry_days}天<180，"
                        f"规则目录只声明接送时间 → 结论={out.outcome.value}(放行)"}


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
    print("Stress 协作后半场 · 四个模式 × 一种真实压力")
    print("=" * 78)
    for fn in GAPS:
        r = fn()
        mark = "❌ 漏" if r["leaked"] else "✓ 挡"
        print(f"\n【{r['pattern']} · {r['gap']}】 {mark}")
        print(f"  {r['evidence']}")
        assert r["leaked"], f"{r['gap']} 未如期暴露"
    print("\n" + "-" * 78)
    print("四条都来自接口或配置边界：组合线要显式配置 / additive 不辨冲突与重复 /")
    print("评审闸不能补全残缺规则目录 / 接缝查 key 不查值。这是从教学接口走向生产配置的路。")
    print("=" * 78)


if __name__ == "__main__":
    report()
