"""End-to-end checks for the lecture 33 fan-out / gather lab."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "fan_out_gather_lab.py", "fanout_lab")
fan = sys.modules["fanout_pattern"]


def test_source_artifacts_are_contract_bound_and_admitted() -> None:
    run = lab.run_competing(lab.month_end())

    assert all(
        artifact.contract_digest == receipt.contract_digest
        for artifact, receipt in zip(
            run.source_artifacts,
            run.source_receipts,
            strict=True,
        )
    )
    assert all(
        receipt.decision is fan.AcceptanceDecision.ACCEPTED
        for receipt in run.source_receipts
    )


def test_finance_divergence_preserves_source_evidence() -> None:
    con = lab.month_end()
    run = lab.run_competing(con)
    report = run.report

    assert report.status is fan.ReconciliationStatus.RECONCILED
    assert report.agreed_items == ("Engineering", "Ops", "Sales", "Support")
    (verdict,) = report.attributable_divergences
    assert verdict.item == "Finance"
    assert verdict.gap == 38_444.0
    assert lab.reversed_by_dept(con)["Finance"] == verdict.gap
    assert verdict.low_sources == ("bank_ledger",)
    assert set(verdict.high_sources) == {"batch_artifacts", "hr_payroll"}


def test_single_source_item_and_seam_finding_reach_root_receipt() -> None:
    run = lab.run_competing(lab.month_end())

    contractor = next(
        verdict
        for verdict in run.report.to_human
        if verdict.item == "Contractors"
    )
    assert contractor.reason == "single-source"
    assert run.report.seam_findings
    assert run.report_receipt.decision is fan.AcceptanceDecision.ESCALATED
    assert {
        finding.code for finding in run.report_receipt.findings
    } == {"unresolved_line_item", "seam_finding"}


def test_required_bank_failure_blocks_reconciliation() -> None:
    run = lab.run_with_dead_bank(lab.month_end())

    assert run.report.status is fan.ReconciliationStatus.INSUFFICIENT_SOURCES
    assert run.report.missing_required_sources == ("bank_ledger",)
    failed = next(
        artifact.payload
        for artifact in run.source_artifacts
        if artifact.payload.source_id == "bank_ledger"
    )
    assert failed.failure_code == "RuntimeError: bank API down"
    assert run.report_receipt.decision is fan.AcceptanceDecision.ESCALATED


def test_additive_contract_swallows_competing_divergence() -> None:
    run = lab.run_additive(lab.month_end())
    report = run.report

    assert report.merged["Finance"] == 2_764_781.0 + 2_764_781.0 + 2_726_337.0
    assert report.verdicts == ()
    assert report.seam_findings == ()
    assert run.report_receipt.decision is fan.AcceptanceDecision.ACCEPTED


def test_three_way_scatter_stays_unresolved() -> None:
    report = fan.Reconciler(tol=1.0).reconcile(
        (
            fan.SourceResult.from_mapping(
                source_id="a",
                snapshot_ref="snapshot://a",
                period="2026-06",
                unit="CNY",
                line_items={"Ops": 100.0},
            ),
            fan.SourceResult.from_mapping(
                source_id="b",
                snapshot_ref="snapshot://b",
                period="2026-06",
                unit="CNY",
                line_items={"Ops": 200.0},
            ),
            fan.SourceResult.from_mapping(
                source_id="c",
                snapshot_ref="snapshot://c",
                period="2026-06",
                unit="CNY",
                line_items={"Ops": 300.0},
            ),
        )
    )

    (verdict,) = report.to_human
    assert verdict.reason == "unexplained-divergence"
