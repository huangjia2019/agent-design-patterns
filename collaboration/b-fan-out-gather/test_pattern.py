"""Invariants for the Fan-out / Gather pattern."""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import replace

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    AcceptanceDecision,
    AggregationBoundary,
    AggregatorPolicy,
    ConflictResolution,
    ContributionRule,
    FanOutGather,
    Layer,
    Reconciler,
    ReconciliationStatus,
    SourceAdmissionPolicy,
    SourceResult,
    SourceSpec,
    Strategy,
    TaskContract,
    Tolerance,
    bind_source_result,
)


ROWS = [{"id": "e1"}, {"id": "e2"}]


def root_contract() -> TaskContract:
    return TaskContract(
        contract_id="payroll-reconciliation",
        version=1,
        objective="reconcile June payroll by department",
        output_schema="ReconciliationReport",
        accountable_owner="payroll-controller",
        input_refs=("sqlite://payroll.db?month=2026-06",),
    )


def spec(
    source_id: str,
    *,
    required: bool = True,
    expected_items: tuple[str, ...] = ("base",),
) -> SourceSpec:
    return SourceSpec(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06",
        unit="CNY",
        boundary=f"read only from {source_id}",
        required=required,
        expected_items=expected_items,
        allowed_tools=(f"read_{source_id}",),
        authority_scope=(f"read:{source_id}",),
    )


def reading(
    source_id: str,
    items: dict[str, float],
    *,
    confidence: float = 1.0,
) -> SourceResult:
    source = spec(source_id, expected_items=())
    return SourceResult.from_mapping(
        source_id=source_id,
        snapshot_ref=source.snapshot_ref,
        period=source.period,
        unit=source.unit,
        line_items=items,
        confidence=confidence,
    )


def worker(
    source: SourceSpec,
    items: dict[str, float],
    *,
    confidence: float = 1.0,
):
    async def run(handoff, rows):
        result = SourceResult.from_mapping(
            source_id=source.source_id,
            snapshot_ref=source.snapshot_ref,
            period=source.period,
            unit=source.unit,
            line_items=items,
            confidence=confidence,
        )
        return bind_source_result(
            handoff,
            result,
            evidence_refs=(source.snapshot_ref,),
        )

    return run


def test_source_contracts_bind_identity_snapshot_and_scope() -> None:
    source = spec("gl")
    fanout = FanOutGather(((source, worker(source, {"base": 100.0})),))

    handoff = fanout.handoff_for(root_contract(), source)

    assert handoff.contract.contract_id == "source::gl"
    assert handoff.contract.input_refs == (source.snapshot_ref,)
    assert handoff.contract.allowed_tools == ("read_gl",)
    assert handoff.contract.authority_scope == ("read:gl",)


def test_source_admission_consumes_binding_evidence_and_confidence() -> None:
    source = spec("gl")
    fanout = FanOutGather(
        ((source, worker(source, {"base": 100.0}, confidence=0.4)),),
        source_policy=SourceAdmissionPolicy(min_confidence=0.8),
    )

    run = asyncio.run(fanout.run(root_contract(), ROWS))
    codes = {finding.code for finding in run.source_receipts[0].findings}

    assert "confidence_below_floor" in codes
    assert run.report.status is ReconciliationStatus.INSUFFICIENT_SOURCES


@pytest.mark.parametrize(
    ("mutate", "finding_code"),
    [
        (
            lambda artifact: replace(artifact, contract_digest="wrong"),
            "contract_digest_mismatch",
        ),
        (
            lambda artifact: replace(artifact, schema="WrongSchema"),
            "schema_mismatch",
        ),
        (
            lambda artifact: replace(artifact, evidence_refs=()),
            "missing_evidence",
        ),
    ],
)
def test_source_admission_rejects_unbound_or_unevidenced_artifacts(
    mutate,
    finding_code: str,
) -> None:
    source = spec("gl")
    fanout = FanOutGather(((source, worker(source, {"base": 100.0})),))
    handoff = fanout.handoff_for(root_contract(), source)
    artifact = asyncio.run(worker(source, {"base": 100.0})(handoff, tuple(ROWS)))

    receipt = fanout.source_policy.evaluate(source, handoff, mutate(artifact))

    assert receipt.decision is AcceptanceDecision.ESCALATED
    assert finding_code in {finding.code for finding in receipt.findings}


def test_run_dispatches_sources_concurrently() -> None:
    started: list[str] = []
    release = asyncio.Event()

    def tracking_worker(source: SourceSpec):
        async def run(handoff, rows):
            started.append(source.source_id)
            if len(started) == 3:
                release.set()
            await asyncio.wait_for(release.wait(), timeout=1)
            return await worker(source, {"base": 100.0})(handoff, rows)

        return run

    sources = tuple(
        (source, tracking_worker(source))
        for source in (spec("a"), spec("b"), spec("c"))
    )

    asyncio.run(FanOutGather(sources).run(root_contract(), ROWS))

    assert sorted(started) == ["a", "b", "c"]


def test_worker_failure_is_evidenced_and_required_source_blocks_report() -> None:
    live = spec("live")
    dead = spec("dead")

    async def boom(handoff, rows):
        raise RuntimeError("source crashed")

    run = asyncio.run(
        FanOutGather(
            (
                (live, worker(live, {"base": 100.0})),
                (dead, boom),
            ),
            min_success_rate=0.5,
        ).run(root_contract(), ROWS)
    )
    failed = next(
        artifact.payload
        for artifact in run.source_artifacts
        if artifact.payload.source_id == "dead"
    )

    assert failed.failure_code == "RuntimeError: source crashed"
    assert run.report.status is ReconciliationStatus.INSUFFICIENT_SOURCES
    assert run.report.missing_required_sources == ("dead",)


def test_optional_source_can_fail_when_success_floor_still_holds() -> None:
    live = spec("live")
    optional = spec("optional", required=False)

    async def boom(handoff, rows):
        raise RuntimeError("optional source crashed")

    run = asyncio.run(
        FanOutGather(
            (
                (live, worker(live, {"base": 100.0})),
                (optional, boom),
            ),
            min_success_rate=0.5,
        ).run(root_contract(), ROWS)
    )

    assert run.report.status is ReconciliationStatus.RECONCILED


def test_empty_or_duplicate_source_sets_are_rejected() -> None:
    with pytest.raises(ValueError, match="at least one source"):
        FanOutGather(())

    duplicate = spec("same")
    with pytest.raises(ValueError, match="unique"):
        FanOutGather(
            (
                (duplicate, worker(duplicate, {"base": 1.0})),
                (duplicate, worker(duplicate, {"base": 1.0})),
            )
        )


def test_competing_agreement_and_two_cluster_divergence_are_typed() -> None:
    report = Reconciler(tol=1.0).reconcile(
        (
            reading("payroll", {"base": 100.0, "tax": 120.0}),
            reading("gl", {"base": 100.5, "tax": 120.0}),
            reading("bank", {"base": 100.0, "tax": 108.0}),
        )
    )

    assert report.agreed_items == ("base",)
    (tax,) = report.attributable_divergences
    assert tax.item == "tax"
    assert tax.layer is Layer.ATTRIBUTABLE
    assert tax.gap == 12.0
    assert tax.low_sources == ("bank",)
    assert set(tax.high_sources) == {"payroll", "gl"}


def test_conflict_resolver_is_executable_policy() -> None:
    def prefer_gl(verdict):
        return ConflictResolution(
            selected_value=verdict.values["gl"],
            rule="source-priority",
            evidence="policy://payroll/gl-is-book-of-record",
        )

    report = Reconciler(
        AggregatorPolicy(conflict_resolver=prefer_gl),
        tol=1.0,
    ).reconcile(
        (
            reading("payroll", {"tax": 120.0}),
            reading("gl", {"tax": 120.0}),
            reading("bank", {"tax": 108.0}),
        )
    )

    (verdict,) = report.attributable_divergences
    assert verdict.resolution is not None
    assert verdict.resolution.selected_value == 120.0
    assert report.to_human == ()


def test_single_source_and_three_way_scatter_go_to_human() -> None:
    report = Reconciler(tol=1.0).reconcile(
        (
            reading("a", {"single": 5.0, "scatter": 100.0}),
            reading("b", {"scatter": 200.0}),
            reading("c", {"scatter": 300.0}),
        )
    )

    assert {verdict.reason for verdict in report.to_human} == {
        "single-source",
        "unexplained-divergence",
    }


def test_clustering_uses_full_range_not_single_link_chaining() -> None:
    report = Reconciler(tol=1.0).reconcile(
        (
            reading("a", {"x": 0.0}),
            reading("b", {"x": 0.9}),
            reading("c", {"x": 1.8}),
        )
    )

    assert report.agreed_items == ()
    assert report.attributable_divergences[0].gap == 1.8


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        (ContributionRule.SUM, 6.0),
        (ContributionRule.MAX, 3.0),
        (ContributionRule.COUNT_SOURCES, 3.0),
    ],
)
def test_additive_contribution_rule_is_explicit(
    rule: ContributionRule,
    expected: float,
) -> None:
    report = Reconciler(
        AggregatorPolicy(
            strategy=Strategy.ADDITIVE,
            identity_key=lambda key: "risk" if key.startswith("risk") else key,
            contribution_rule=rule,
        )
    ).reconcile(
        (
            reading("a", {"risk-a": 1.0}),
            reading("b", {"risk-b": 2.0}),
            reading("c", {"risk-c": 3.0}),
        )
    )

    assert report.merged == {"risk": expected}
    assert report.merged_items[0].raw_keys == ("risk-a", "risk-b", "risk-c")


def test_seam_reviewer_reads_the_assembled_typed_report() -> None:
    def reviewer(report):
        if len(report.attributable_divergences) >= 2:
            return ("linked systems require joint sign-off",)
        return ()

    report = Reconciler(
        AggregatorPolicy(seam_reviewer=reviewer),
        tol=1.0,
    ).reconcile(
        (
            reading("a", {"tax": 100.0, "overtime": 50.0}),
            reading("b", {"tax": 100.0, "overtime": 50.0}),
            reading("c", {"tax": 90.0, "overtime": 70.0}),
        )
    )

    assert report.seam_findings == ("linked systems require joint sign-off",)


def test_root_receipt_escalates_unresolved_divergence() -> None:
    a = spec("a")
    b = spec("b")
    run = asyncio.run(
        FanOutGather(
            (
                (a, worker(a, {"base": 100.0})),
                (b, worker(b, {"base": 90.0})),
            ),
            min_success_rate=1.0,
        ).run(root_contract(), ROWS)
    )

    assert run.report_receipt.decision is AcceptanceDecision.ESCALATED
    assert {
        finding.code for finding in run.report_receipt.findings
    } == {"unresolved_line_item"}


@pytest.mark.parametrize(
    ("mutate", "finding_code"),
    [
        (
            lambda artifact: replace(artifact, produced_by="unknown-controller"),
            "report_producer_mismatch",
        ),
        (
            lambda artifact: replace(artifact, evidence_refs=()),
            "report_evidence_missing",
        ),
    ],
)
def test_root_receipt_checks_producer_and_evidence(
    mutate,
    finding_code: str,
) -> None:
    source = spec("gl")
    run = asyncio.run(
        FanOutGather(((source, worker(source, {"base": 100.0})),)).run(
            root_contract(),
            ROWS,
        )
    )

    receipt = AggregationBoundary().evaluate(
        run.root_contract,
        mutate(run.report_artifact),
    )

    assert receipt.decision is AcceptanceDecision.ESCALATED
    assert finding_code in {finding.code for finding in receipt.findings}


def test_source_configuration_is_validated() -> None:
    with pytest.raises(ValueError, match="identity"):
        SourceSpec(
            source_id="",
            snapshot_ref="snapshot://x",
            period="2026-06",
            unit="CNY",
            boundary="read only",
        )
    with pytest.raises(ValueError, match="tolerances"):
        Tolerance(absolute=-1)
