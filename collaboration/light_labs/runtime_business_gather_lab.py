"""Bonus lab: the Harness runs workers; business code earns the conclusion.

The lab deliberately keeps the execution plane and the evidence plane separate.
`AsyncFanOutHarness` knows concurrency, timeouts, and worker settlement. It does
not know payroll. `PayrollEvidenceGatherer` knows source coverage, comparable
units, lineage, and reconciliation invariants. It does not start workers.

Run from the repository root:
    python3 collaboration/light_labs/runtime_business_gather_lab.py
    python3 collaboration/light_labs/runtime_business_gather_lab.py --scenario unexplained-gap
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Protocol


MONTH = "2026-06"
UNIT = "CNY"


class WorkerStatus(str, Enum):
    SUCCEEDED = "succeeded"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class RuntimeStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"


class BusinessStatus(str, Enum):
    READY = "ready"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICT = "business_conflict"


@dataclass(frozen=True)
class EvidenceCard:
    """One source reading with identity, lineage, scope, and typed facts."""

    source_id: str
    lineage_id: str
    period: str
    unit: str
    evidence_ref: str
    facts: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        required = (
            self.source_id,
            self.lineage_id,
            self.period,
            self.unit,
            self.evidence_ref,
        )
        if not all(value.strip() for value in required):
            raise ValueError("evidence identity fields must not be empty")
        keys = [name for name, _ in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("facts must not contain duplicate keys")

    @property
    def values(self) -> dict[str, int]:
        return dict(self.facts)


@dataclass(frozen=True)
class WorkOrder:
    """A provider-neutral request that a Harness can schedule."""

    job_id: str
    source_id: str
    delay_ms: int


class EvidenceProvider(Protocol):
    async def collect(self, order: WorkOrder) -> EvidenceCard:
        """Return one structured card or raise a provider/runtime error."""


@dataclass(frozen=True)
class WorkerOutcome:
    job_id: str
    source_id: str
    status: WorkerStatus
    duration_ms: int
    card: EvidenceCard | None = None
    error: str | None = None


@dataclass(frozen=True)
class RuntimeBatch:
    """What the execution plane can honestly say after the workers settle."""

    status: RuntimeStatus
    outcomes: tuple[WorkerOutcome, ...]
    elapsed_ms: int
    peak_concurrency: int

    @property
    def successful_cards(self) -> tuple[EvidenceCard, ...]:
        return tuple(
            outcome.card
            for outcome in self.outcomes
            if outcome.status is WorkerStatus.SUCCEEDED and outcome.card is not None
        )


class ScriptedProvider:
    """Deterministic stand-in for OpenAI, Anthropic, dsh, or another provider."""

    def __init__(
        self,
        cards: Mapping[str, EvidenceCard],
        failures: Mapping[str, Exception] | None = None,
    ) -> None:
        self.cards = dict(cards)
        self.failures = dict(failures or {})

    async def collect(self, order: WorkOrder) -> EvidenceCard:
        await asyncio.sleep(order.delay_ms / 1000)
        if order.job_id in self.failures:
            raise self.failures[order.job_id]
        return self.cards[order.job_id]


class AsyncFanOutHarness:
    """Run provider-neutral work concurrently and report settlement facts."""

    def __init__(self, *, max_concurrent: int = 4, timeout_ms: int = 80) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if timeout_ms < 1:
            raise ValueError("timeout_ms must be positive")
        self.max_concurrent = max_concurrent
        self.timeout_ms = timeout_ms

    async def run(
        self,
        orders: Sequence[WorkOrder],
        provider: EvidenceProvider,
    ) -> RuntimeBatch:
        semaphore = asyncio.Semaphore(self.max_concurrent)
        activity_lock = asyncio.Lock()
        active = 0
        peak = 0

        async def run_one(order: WorkOrder) -> WorkerOutcome:
            nonlocal active, peak
            started = perf_counter()
            async with semaphore:
                async with activity_lock:
                    active += 1
                    peak = max(peak, active)
                try:
                    card = await asyncio.wait_for(
                        provider.collect(order),
                        timeout=self.timeout_ms / 1000,
                    )
                    if card.source_id != order.source_id:
                        raise ValueError(
                            f"source mismatch: expected {order.source_id}, got {card.source_id}"
                        )
                    return WorkerOutcome(
                        job_id=order.job_id,
                        source_id=order.source_id,
                        status=WorkerStatus.SUCCEEDED,
                        duration_ms=_elapsed_ms(started),
                        card=card,
                    )
                except asyncio.TimeoutError:
                    return WorkerOutcome(
                        job_id=order.job_id,
                        source_id=order.source_id,
                        status=WorkerStatus.TIMED_OUT,
                        duration_ms=_elapsed_ms(started),
                        error=f"timeout>{self.timeout_ms}ms",
                    )
                except Exception as exc:
                    return WorkerOutcome(
                        job_id=order.job_id,
                        source_id=order.source_id,
                        status=WorkerStatus.FAILED,
                        duration_ms=_elapsed_ms(started),
                        error=f"{type(exc).__name__}: {exc}",
                    )
                finally:
                    async with activity_lock:
                        active -= 1

        batch_started = perf_counter()
        outcomes = tuple(await asyncio.gather(*(run_one(order) for order in orders)))
        status = (
            RuntimeStatus.COMPLETE
            if all(outcome.status is WorkerStatus.SUCCEEDED for outcome in outcomes)
            else RuntimeStatus.PARTIAL
        )
        return RuntimeBatch(
            status=status,
            outcomes=outcomes,
            elapsed_ms=_elapsed_ms(batch_started),
            peak_concurrency=peak,
        )


@dataclass(frozen=True)
class BusinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class GatherDecision:
    """A business verdict that remains distinct from runtime completion."""

    status: BusinessStatus
    release_allowed: bool
    admitted_sources: tuple[str, ...]
    missing_sources: tuple[str, ...]
    duplicate_lineages: tuple[str, ...]
    quarantined: tuple[str, ...]
    checks: tuple[BusinessCheck, ...]


class PayrollEvidenceGatherer:
    """Turn comparable payroll evidence into a deterministic release decision."""

    required_facts = {
        "hr_roster": frozenset({"eligible_count", "obligation_total"}),
        "payroll_batch": frozenset({"batch_count", "instructed_total"}),
        "bank_ledger": frozenset(
            {"settled_count", "settled_total", "reversed_count", "reversed_total"}
        ),
    }

    def __init__(self, *, period: str = MONTH, unit: str = UNIT) -> None:
        self.period = period
        self.unit = unit

    def gather(self, cards: Sequence[EvidenceCard]) -> GatherDecision:
        admitted: dict[str, EvidenceCard] = {}
        seen_lineages: set[str] = set()
        duplicates: list[str] = []
        quarantined: list[str] = []

        for card in cards:
            if card.period != self.period:
                quarantined.append(f"{card.source_id}:period={card.period}")
                continue
            if card.unit != self.unit:
                quarantined.append(f"{card.source_id}:unit={card.unit}")
                continue
            if card.lineage_id in seen_lineages:
                duplicates.append(card.source_id)
                continue
            expected = self.required_facts.get(card.source_id)
            if expected is None:
                quarantined.append(f"{card.source_id}:unexpected_source")
                continue
            missing_facts = sorted(expected - card.values.keys())
            if missing_facts:
                quarantined.append(
                    f"{card.source_id}:missing={','.join(missing_facts)}"
                )
                continue
            if card.source_id in admitted:
                quarantined.append(f"{card.source_id}:duplicate_source_id")
                continue
            seen_lineages.add(card.lineage_id)
            admitted[card.source_id] = card

        missing_sources = tuple(sorted(self.required_facts.keys() - admitted.keys()))
        if missing_sources:
            return GatherDecision(
                status=BusinessStatus.INSUFFICIENT_EVIDENCE,
                release_allowed=False,
                admitted_sources=tuple(sorted(admitted)),
                missing_sources=missing_sources,
                duplicate_lineages=tuple(duplicates),
                quarantined=tuple(quarantined),
                checks=(),
            )

        hr = admitted["hr_roster"].values
        batch = admitted["payroll_batch"].values
        bank = admitted["bank_ledger"].values
        checks = (
            BusinessCheck(
                name="instruction_matches_obligation",
                passed=batch["instructed_total"] == hr["obligation_total"],
                detail=(
                    f"instructed={batch['instructed_total']} "
                    f"obligation={hr['obligation_total']}"
                ),
            ),
            BusinessCheck(
                name="instruction_covers_people",
                passed=batch["batch_count"] == hr["eligible_count"],
                detail=f"batch={batch['batch_count']} eligible={hr['eligible_count']}",
            ),
            BusinessCheck(
                name="ledger_explains_amount",
                passed=(
                    bank["settled_total"] + bank["reversed_total"]
                    == batch["instructed_total"]
                ),
                detail=(
                    f"settled={bank['settled_total']} + reversed={bank['reversed_total']} "
                    f"vs instructed={batch['instructed_total']}"
                ),
            ),
            BusinessCheck(
                name="ledger_explains_people",
                passed=(
                    bank["settled_count"] + bank["reversed_count"]
                    == batch["batch_count"]
                ),
                detail=(
                    f"settled={bank['settled_count']} + reversed={bank['reversed_count']} "
                    f"vs batch={batch['batch_count']}"
                ),
            ),
        )
        release_allowed = all(check.passed for check in checks)
        return GatherDecision(
            status=BusinessStatus.READY if release_allowed else BusinessStatus.CONFLICT,
            release_allowed=release_allowed,
            admitted_sources=tuple(sorted(admitted)),
            missing_sources=(),
            duplicate_lineages=tuple(duplicates),
            quarantined=tuple(quarantined),
            checks=checks,
        )


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    runtime: RuntimeBatch
    business: GatherDecision


def _card(
    source_id: str,
    lineage_id: str,
    facts: Mapping[str, int],
    *,
    period: str = MONTH,
    unit: str = UNIT,
) -> EvidenceCard:
    return EvidenceCard(
        source_id=source_id,
        lineage_id=lineage_id,
        period=period,
        unit=unit,
        evidence_ref=f"sqlite://payroll/{source_id}?period={period}",
        facts=tuple(sorted(facts.items())),
    )


def scenario_fixture(
    name: str,
) -> tuple[tuple[WorkOrder, ...], ScriptedProvider, int]:
    cards = {
        "hr": _card(
            "hr_roster",
            "lineage://hr/roster-v7",
            {"eligible_count": 800, "obligation_total": 13_744_541},
        ),
        "batch": _card(
            "payroll_batch",
            "lineage://payroll/batch-v3",
            {"batch_count": 800, "instructed_total": 13_744_541},
        ),
        "bank": _card(
            "bank_ledger",
            "lineage://bank/export-42",
            {
                "settled_count": 798,
                "settled_total": 13_706_097,
                "reversed_count": 2,
                "reversed_total": 38_444,
            },
        ),
    }
    orders = [
        WorkOrder("hr", "hr_roster", 30),
        WorkOrder("batch", "payroll_batch", 45),
        WorkOrder("bank", "bank_ledger", 20),
    ]
    timeout_ms = 80

    if name == "bank-timeout":
        orders[2] = WorkOrder("bank", "bank_ledger", 140)
    elif name == "duplicate-lineage":
        cards["hr-copy"] = _card(
            "hr_roster_copy",
            "lineage://hr/roster-v7",
            {"eligible_count": 800, "obligation_total": 13_744_541},
        )
        orders.append(WorkOrder("hr-copy", "hr_roster_copy", 25))
    elif name == "unit-mismatch":
        cards["bank"] = _card(
            "bank_ledger",
            "lineage://bank/export-42",
            {
                "settled_count": 798,
                "settled_total": 1_370_609_700,
                "reversed_count": 2,
                "reversed_total": 3_844_400,
            },
            unit="CNY_CENTS",
        )
    elif name == "unexplained-gap":
        cards["bank"] = _card(
            "bank_ledger",
            "lineage://bank/export-42",
            {
                "settled_count": 798,
                "settled_total": 13_706_097,
                "reversed_count": 2,
                "reversed_total": 30_000,
            },
        )
    elif name != "healthy":
        raise ValueError(f"unknown scenario: {name}")

    return tuple(orders), ScriptedProvider(cards), timeout_ms


async def run_scenario(name: str) -> ScenarioResult:
    orders, provider, timeout_ms = scenario_fixture(name)
    runtime = await AsyncFanOutHarness(timeout_ms=timeout_ms).run(orders, provider)
    business = PayrollEvidenceGatherer().gather(runtime.successful_cards)
    return ScenarioResult(name=name, runtime=runtime, business=business)


def run_scenario_sync(name: str) -> ScenarioResult:
    return asyncio.run(run_scenario(name))


def _elapsed_ms(started: float) -> int:
    return max(1, round((perf_counter() - started) * 1000))


def print_result(result: ScenarioResult) -> None:
    runtime = result.runtime
    business = result.business
    print(f"== {result.name} ==")
    print(
        f"runtime: status={runtime.status.value} returned={len(runtime.outcomes)} "
        f"peak={runtime.peak_concurrency} elapsed~{runtime.elapsed_ms}ms"
    )
    for outcome in runtime.outcomes:
        suffix = outcome.error or (outcome.card.evidence_ref if outcome.card else "")
        print(f"  {outcome.source_id:<15} {outcome.status.value:<9} {suffix}")
    print(
        f"business: status={business.status.value} "
        f"release_allowed={str(business.release_allowed).lower()}"
    )
    if business.missing_sources:
        print(f"  missing={','.join(business.missing_sources)}")
    if business.duplicate_lineages:
        print(f"  duplicate_lineage={','.join(business.duplicate_lineages)}")
    if business.quarantined:
        print(f"  quarantined={';'.join(business.quarantined)}")
    for check in business.checks:
        print(f"  check {check.name:<31} {str(check.passed).lower():<5} {check.detail}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Harness settlement with payroll evidence semantics."
    )
    parser.add_argument(
        "--scenario",
        choices=(
            "all",
            "healthy",
            "bank-timeout",
            "duplicate-lineage",
            "unit-mismatch",
            "unexplained-gap",
        ),
        default="all",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    names = (
        "healthy",
        "bank-timeout",
        "duplicate-lineage",
        "unit-mismatch",
        "unexplained-gap",
    )
    selected = names if args.scenario == "all" else (args.scenario,)
    for index, name in enumerate(selected):
        if index:
            print()
        print_result(run_scenario_sync(name))


if __name__ == "__main__":
    main()
