"""Tests for the Full System Assembly pattern."""
from __future__ import annotations

import os
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    MODULE_ORDER,
    AssemblyError,
    BusinessCheck,
    EndpointEvidence,
    ModuleName,
    ModuleReceipt,
    PatternBinding,
    SystemAssembly,
    SystemRunContract,
    audit_system,
    stable_digest,
)


def contract() -> SystemRunContract:
    return SystemRunContract(
        run_id="run-payroll-2026-06",
        version=1,
        goal="release the reconciled payroll report",
        workload_ref="fixture://payroll/2026-06/month-end-v1",
        workload_digest=stable_digest("fixture://payroll/2026-06/month-end-v1"),
        selection_receipt_digest="selection-1234",
        pattern_bindings=tuple(
            PatternBinding(module, f"pattern-{module.value}", f"purpose-{module.value}")
            for module in MODULE_ORDER
        ),
    )


def receipts(bound_contract: SystemRunContract) -> tuple[ModuleReceipt, ...]:
    result: list[ModuleReceipt] = []
    current = bound_contract.digest
    for index, module in enumerate(MODULE_ORDER, start=1):
        receipt = ModuleReceipt(
            receipt_id=f"receipt-{index}",
            module=module,
            pattern=bound_contract.pattern_for(module),
            run_id=bound_contract.run_id,
            contract_digest=bound_contract.digest,
            workload_digest=bound_contract.workload_digest,
            input_digest=current,
            output_digest=stable_digest(f"artifact-{index}"),
            parent_receipts=(result[-1].digest,) if result else (),
            evidence_refs=(f"evidence://{module.value}/{index}",),
        )
        result.append(receipt)
        current = receipt.output_digest
    return tuple(result)


def endpoint(
    bound_contract: SystemRunContract,
    bound_receipts: tuple[ModuleReceipt, ...],
) -> tuple[EndpointEvidence, tuple[ModuleReceipt, ...]]:
    governance = next(
        receipt
        for receipt in bound_receipts
        if receipt.module is ModuleName.GOVERNANCE
    )
    authorization = "governance-receipt://allowed-1234"
    index = bound_receipts.index(governance)
    bound_receipts = (
        *bound_receipts[:index],
        replace(
            governance,
            evidence_refs=(*governance.evidence_refs, authorization),
        ),
        *bound_receipts[index + 1 :],
    )
    # Replacing governance changes its receipt digest, so rebuild the memory link.
    memory = replace(
        bound_receipts[-1],
        parent_receipts=(bound_receipts[-2].digest,),
    )
    bound_receipts = (*bound_receipts[:-1], memory)
    return EndpointEvidence(
        contract_digest=bound_contract.digest,
        terminal_receipt_digest=memory.digest,
        artifact_digest=memory.output_digest,
        authorization_ref=authorization,
        external_refs=("sqlite://release/run-payroll-2026-06",),
        checks=(
            BusinessCheck(
                "released artifact matches approved artifact",
                True,
                "sqlite://release/run-payroll-2026-06#artifact",
            ),
        ),
    ), bound_receipts


def test_strict_assembly_accepts_one_continuous_evidence_spine() -> None:
    bound_contract = contract()
    bound_receipts = receipts(bound_contract)
    bound_endpoint, bound_receipts = endpoint(bound_contract, bound_receipts)
    assembly = SystemAssembly(bound_contract)

    for receipt in bound_receipts:
        assembly.record(receipt)
    report = assembly.seal(bound_endpoint)

    assert report.accepted is True
    assert report.local_acceptance_count == len(MODULE_ORDER)
    assert report.findings == ()


def test_local_success_without_lineage_does_not_pass_system_acceptance() -> None:
    bound_contract = contract()
    bound_receipts = receipts(bound_contract)
    bound_endpoint, bound_receipts = endpoint(bound_contract, bound_receipts)
    local_only = tuple(
        replace(receipt, parent_receipts=())
        for receipt in bound_receipts
    )

    report = audit_system(bound_contract, local_only, bound_endpoint)

    assert report.local_acceptance_count == len(MODULE_ORDER)
    assert report.accepted is False
    assert "lineage_break" in {finding.code for finding in report.findings}


def test_endpoint_must_bind_the_artifact_governance_approved() -> None:
    bound_contract = contract()
    bound_receipts = receipts(bound_contract)
    bound_endpoint, bound_receipts = endpoint(bound_contract, bound_receipts)
    changed = replace(bound_endpoint, artifact_digest=stable_digest("changed"))

    report = audit_system(bound_contract, bound_receipts, changed)

    assert report.accepted is False
    assert "endpoint_artifact_mismatch" in {
        finding.code for finding in report.findings
    }


def test_strict_builder_rejects_a_cross_run_receipt() -> None:
    bound_contract = contract()
    first = replace(receipts(bound_contract)[0], run_id="run-other")

    with pytest.raises(AssemblyError, match="another run"):
        SystemAssembly(bound_contract).record(first)
