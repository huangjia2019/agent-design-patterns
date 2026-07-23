"""Course finale: why eight seats and not one god-prompt?

The honest-reckoning lecture (handpick_discipline_lab.py) answered the
skeptic's charge about *picking* patterns. This capstone answers the
charge about *composing* them: once you have selected seven cognitive
seats, what does wiring them into one system actually buy you that a
single well-written prompt does not?

The answer is measured, not asserted. One month-end payroll day carries
the defect this course has tracked since lecture 33: two payslips were
reversed with the wrong sign -- E0007 (+30,000 instead of -30,000) and
E0012 (+8,444 instead of -8,444) -- so the gross-to-net delta is inflated
by exactly 38,444. The composed system routes that day through seven
independent detection-and-containment layers, each backed by committed
code, each emitting one receipt into a hash-linked evidence chain:

    perception    ContextTriage surfaces the reversal audit trace even
                  when it is short and over budget (it is an error trace).
    memory        last month's approved delta (0) is the baseline that
                  makes this month's 38,444 an anomaly rather than noise.
    reasoning     IterativeHypothesisLoop confirms the root cause is a
                  reversed sign, not rounding or new hires.
    collaboration Reconciler cross-checks four ledgers and localizes the
                  divergence to those two employees.
    action        the write gate blocks a reversal line that is positive.
    reflection    GeneratorCriticChain raises a grounded BLOCKER before
                  the month report is committed.
    governance    an approval bound to the settlement fingerprint plus an
                  intact trace chain make the night reconstructable.

Then the lab runs leave-one-out: knock out one layer and the completeness
check names the link that went dark. Two seats (action, governance) let
the defect reach the payslip or make the night unauditable; the five
detection seats each remove one independent chance to catch the defect.
Seven verified links vs. six-plus-a-hole is the whole argument for
composition: the deliverable is the evidence chain, and it is only as
complete as its sparsest link.

Four seats wrap a real committed pattern engine (ContextTriage,
IterativeHypothesisLoop, Reconciler, GeneratorCriticChain). Memory,
action and governance are thin in-lab checkpoints -- each the module's
job reduced to its one load-bearing assertion -- with the hash chain
standing in for the observability-harness pattern. This is a teaching
minimum kept independent of Codex's capstone_lab.py on purpose; the two
integration schemes are not merged.

Run `python3 composition/payroll-lab/closing_ablation_lab.py` from the repo root.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def _load(rel: str, name: str):
    """Load a committed engine under a lab-unique module name so this lab
    never collides with the other composition labs in sys.modules."""
    path = REPO / rel
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_TRIAGE = _load("perception/a-context-triage/pattern.py", "_closing_triage")
_HYP = _load("reasoning/d-iterative-hypothesis/pattern.py", "_closing_hyp")
_FANOUT = _load("collaboration/b-fan-out-gather/pattern.py", "_closing_fanout")
_CRITIC = _load("reflection/a-generator-critic/pattern.py", "_closing_critic")

# The defect this course has tracked since lecture 33.
REVERSALS = {"E0007": 30_000.0, "E0012": 8_444.0}
GROSS_TO_NET_GAP = sum(REVERSALS.values())  # 38,444
EXPECTED_SOCIAL_SECURITY = 120_000.0

SEATS = ("perception", "memory", "reasoning",
         "collaboration", "action", "reflection", "governance")


# ---- the evidence chain ---------------------------------------------------------

def _digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class Receipt:
    seq: int
    seat: str
    claim: str
    ok: bool
    evidence_digest: str
    prev_hash: str
    entry_hash: str


class EvidenceChain:
    """Append-only, hash-linked. A receipt goes THROUGH it, so a seat can
    go dark only visibly."""

    def __init__(self) -> None:
        self._entries: list[Receipt] = []

    def append(self, seat: str, claim: str, ok: bool, evidence: str) -> Receipt:
        seq = len(self._entries)
        prev = self._entries[-1].entry_hash if self._entries else "genesis"
        ed = _digest(evidence)
        entry = _digest(f"{seq}|{seat}|{ok}|{ed}|{prev}")
        receipt = Receipt(seq, seat, claim, ok, ed, prev, entry)
        self._entries.append(receipt)
        return receipt

    @property
    def receipts(self) -> tuple[Receipt, ...]:
        return tuple(self._entries)

    def verify(self) -> bool:
        prev = "genesis"
        for r in self._entries:
            recomputed = _digest(f"{r.seq}|{r.seat}|{r.ok}|{r.evidence_digest}|{prev}")
            if recomputed != r.entry_hash or r.prev_hash != prev:
                return False
            prev = r.entry_hash
        return True


# ---- seat 1: perception (real ContextTriage) ------------------------------------

def _perception_ok(drop: bool) -> tuple[bool, str]:
    """Four equal-size items, budget fits three. ContextTriage boosts the
    reversal audit trace (an IMPORTANT error trace) above the routine bulk
    and keeps it; a naive length-first cut ignores priority, fills on the
    routine docs, and drops the reversal."""
    Priority = _TRIAGE.Priority
    items = [
        _TRIAGE.ContextItem("routine_payslips", "x", Priority.SUPPORTING, 400),
        _TRIAGE.ContextItem("policy_manual", "y", Priority.SUPPORTING, 400),
        _TRIAGE.ContextItem("headcount_report", "z", Priority.SUPPORTING, 400),
        _TRIAGE.ContextItem("reversal_audit", "两笔工资条冲正，符号可能写反",
                            Priority.IMPORTANT, 400, is_error=True),
    ]
    if drop:
        # naive cut: input order until budget, no priority, no error protection.
        budget = 1200
        used = 0
        selected = []
        for it in items:
            if used + it.token_estimate <= budget:
                selected.append(it.name)
                used += it.token_estimate
        surfaced = "reversal_audit" in selected
    else:
        sel, _deferred, _decision = _TRIAGE.ContextTriage(budget=1200).triage(items)
        surfaced = "reversal_audit" in [i.name for i in sel]
    claim = "感知层把冲正审计线索送进了工作上下文" if surfaced \
        else "冲正线索被预算截断，下游根本没看见"
    return surfaced, claim


# ---- seat 2: memory (thin committed checkpoint) ---------------------------------

def _memory_ok(drop: bool) -> tuple[bool, str]:
    """Last month's approved gross-to-net delta was 0. That baseline is what
    turns this month's 38,444 into an anomaly instead of variation."""
    last_month_delta = 0.0
    if drop:
        return False, "没有上月基线，38,444 的差额无从判断是否异常"
    flagged = abs(GROSS_TO_NET_GAP - last_month_delta) > 1.0
    claim = "记忆层用上月基线把 38,444 标成异常" if flagged \
        else "差额与上月一致，视为正常"
    return flagged, claim


# ---- seat 3: reasoning (real IterativeHypothesisLoop) ---------------------------

def _reasoning_ok(drop: bool) -> tuple[bool, str]:
    if drop:
        return False, "跳过诊断，接受表面解释：合计在容差内"
    names = {
        "reversal": "两笔工资条冲正被写成了正数",
        "rounding": "本月出现了大额舍入误差",
        "newhire": "新入职员工抬高了应发合计",
    }

    def planner(problem, existing, iteration):
        del problem
        if existing or iteration > 1:
            return []
        return [(names["reversal"], 0.55),
                (names["rounding"], 0.35),
                (names["newhire"], 0.35)]

    def generator(h):
        if h.description == names["reversal"]:
            return [("E0007、E0012 冲正行符号为正，合计正好 38444",
                     "ledger://payroll/2026-06/reversals")]
        return [("对应科目未见支撑证据", "ledger://payroll/2026-06")]

    def evaluator(h, desc, source):
        del desc, source
        if h.description == names["reversal"]:
            return "supports", 0.25
        return "refutes", -0.60

    tree, outcome = _HYP.IterativeHypothesisLoop(
        planner=planner, generator=generator, evaluator=evaluator,
        max_iterations=2).run("解释 gross-to-net 差额 38444 的根因")
    confirmed = tree.by_id(outcome.confirmed_id) if outcome.confirmed_id else None
    hit = confirmed is not None and confirmed.description == names["reversal"]
    claim = f"推理层坐实根因＝{names['reversal']}" if hit \
        else "推理层未能收敛到根因"
    return hit, claim


# ---- seat 4: collaboration (real Reconciler) ------------------------------------

def _reading(source_id: str, amount: float):
    return _FANOUT.SourceResult.from_mapping(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06", unit="CNY",
        line_items={"reversal_total": amount})


def _collaboration_ok(drop: bool) -> tuple[bool, str]:
    """Payroll booked the reversals as positive; bank/GL/social-security hold
    the correct signed figure. Fan-out localizes the divergence; a single
    source cannot see it."""
    if drop:
        return False, "只查了工资台账这一个来源，冲正差异无从比对"
    report = _FANOUT.Reconciler(tol=1.0).reconcile((
        _reading("payroll", GROSS_TO_NET_GAP),
        _reading("general_ledger", 0.0),
        _reading("bank", 0.0),
        _reading("social_security", 0.0),
    ))
    divergences = [v.item for v in report.attributable_divergences]
    localized = "reversal_total" in divergences
    claim = "协作层把差异定位到冲正合计这一项" if localized \
        else "四源一致，未见差异"
    return localized, claim


# ---- seat 5: action (thin committed checkpoint) ---------------------------------

def _action_ok(drop: bool) -> tuple[bool, str]:
    """The write gate: a reversal line must be non-positive. With the gate off,
    the two positive reversals get written to the payslip."""
    if drop:
        return False, "没有写入闸门，两笔正数冲正被直接写进工资条"
    blocked = all(amount > 0 for amount in REVERSALS.values())
    claim = "行动层拦下符号为正的冲正行，暂缓写入" if blocked \
        else "冲正行符号正常，放行"
    return blocked, claim


# ---- seat 6: reflection (real GeneratorCriticChain) -----------------------------

def _reflection_ok(drop: bool) -> tuple[bool, str]:
    if drop:
        return False, "提交前没有评审，带病月报被直接接受"
    Artifact = _CRITIC.Artifact
    Critique = _CRITIC.Critique
    Issue = _CRITIC.Issue
    Severity = _CRITIC.Severity
    Decision = _CRITIC.Decision
    AcceptancePolicy = _CRITIC.AcceptancePolicy
    GeneratorCriticChain = _CRITIC.GeneratorCriticChain

    def generator(_prompt):
        return Artifact(content="2026-06 月度工资报告：应发合计已结平。")

    def critic(_artifact):
        return Critique(
            score=0.40,
            issues=[Issue(
                severity=Severity.BLOCKER,
                message="gross-to-net 差额 38444 无解释",
                location="summary",
                evidence="E0007、E0012 冲正行符号为正",
                check="reversal_sign")],
            summary="差额未解释，禁止提交",
            score_evidence="两笔冲正合计 38444")

    chain = GeneratorCriticChain(
        generator=generator, critic=critic,
        policy=AcceptancePolicy(min_score=0.8, require_evidence=True))
    result = chain.run("2026-06 月度工资报告")
    caught = result.decision is Decision.NEEDS_REVISION
    claim = "反思层在提交前拦下带病月报（NEEDS_REVISION）" if caught \
        else "反思层放过了月报"
    return caught, claim


# ---- seat 7: governance (thin checkpoint + the chain itself) --------------------

def _governance_ok(drop: bool, chain_intact: bool) -> tuple[bool, str]:
    """An approval bound to the settlement fingerprint plus an intact,
    verifiable trace chain make the night reconstructable."""
    if drop:
        return False, "既没有绑定结算指纹的审批，也没有留痕，当晚无法重建"
    settlement_fingerprint = _digest(f"2026-06|gap={GROSS_TO_NET_GAP}")
    ticket_binds = settlement_fingerprint == _digest(
        f"2026-06|gap={GROSS_TO_NET_GAP}")
    reconstructable = ticket_binds and chain_intact
    claim = "治理层：审批绑定结算指纹、留痕可验证，当晚可重建" if reconstructable \
        else "治理留痕不完整，无法重建当晚"
    return reconstructable, claim


# ---- the day --------------------------------------------------------------------

def run_day(drop: str | None = None) -> dict:
    """Route the month-end day through seven layers. `drop` knocks out one
    layer's guard; every other layer still runs and still records."""
    if drop is not None and drop not in SEATS:
        raise ValueError(f"unknown seat: {drop}")
    chain = EvidenceChain()

    p_ok, p_claim = _perception_ok(drop == "perception")
    chain.append("perception", p_claim, p_ok, f"perception|{p_ok}")
    m_ok, m_claim = _memory_ok(drop == "memory")
    chain.append("memory", m_claim, m_ok, f"memory|{m_ok}")
    r_ok, r_claim = _reasoning_ok(drop == "reasoning")
    chain.append("reasoning", r_claim, r_ok, f"reasoning|{r_ok}")
    c_ok, c_claim = _collaboration_ok(drop == "collaboration")
    chain.append("collaboration", c_claim, c_ok, f"collaboration|{c_ok}")
    a_ok, a_claim = _action_ok(drop == "action")
    chain.append("action", a_claim, a_ok, f"action|{a_ok}")
    f_ok, f_claim = _reflection_ok(drop == "reflection")
    chain.append("reflection", f_claim, f_ok, f"reflection|{f_ok}")
    g_ok, g_claim = _governance_ok(drop == "governance", chain.verify())
    chain.append("governance", g_claim, g_ok, f"governance|{g_ok}")

    verified = {r.seat for r in chain.receipts if r.ok}
    missing = set(SEATS) - verified
    return {
        "drop": drop,
        "verified": verified,
        "missing": missing,
        "defect_blocked": a_ok,            # the write gate held
        "reconstructable": g_ok,           # the night can be rebuilt
        "all_verified": verified == set(SEATS),
        "chain": chain,
    }


CONSEQUENCE = {
    "perception": "冲正线索进不了上下文，这一层的探测彻底消失",
    "memory": "没有上月基线，异常判定这一层消失",
    "reasoning": "根因无人坐实，诊断这一层消失",
    "collaboration": "四源不再交叉比对，跨账探测这一层消失",
    "action": "带病冲正被写进工资条（缺口真的落地）",
    "reflection": "提交前的自查这一层消失",
    "governance": "当晚无法重建（审计链断裂）",
}


def main() -> None:
    print("== 全量：七层俱全 ==")
    full = run_day()
    for r in full["chain"].receipts:
        mark = "OK " if r.ok else "!! "
        print(f"   {mark}[{r.seat}] {r.claim}")
    print(f"   -> 七层全部核验={full['all_verified']} "
          f"缺口被拦={full['defect_blocked']} "
          f"当晚可重建={full['reconstructable']} "
          f"链自校验={full['chain'].verify()}")

    print("\n== 逐层拿掉一把椅子（leave-one-out）==")
    for seat in SEATS:
        run = run_day(drop=seat)
        dark = ", ".join(sorted(run["missing"]))
        print(f"   拿掉 {seat:<13} -> 变暗的链节：{dark:<13} "
              f"缺口被拦={run['defect_blocked']} 可重建={run['reconstructable']}")
        print(f"      后果：{CONSEQUENCE[seat]}")

    print("\n== 篡改一条回执，链立刻失配 ==")
    tampered = run_day()["chain"]
    victim = tampered._entries[3]
    tampered._entries[3] = Receipt(
        victim.seq, victim.seat, victim.claim, not victim.ok,
        victim.evidence_digest, victim.prev_hash, victim.entry_hash)
    print(f"   改掉第 4 条回执的结论 -> 链自校验={tampered.verify()}")


if __name__ == "__main__":
    main()
