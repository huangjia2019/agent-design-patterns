"""Full System Assembly pattern.

The pattern does not replace the eight course modules. It gives their local
receipts one end-to-end identity and verifies that the business endpoint
consumed the exact artifact that governance approved.

The reference contract is deliberately small:

* one immutable run contract names the workload and selected patterns;
* every module receipt binds to that contract and the previous receipt;
* input and output digests make transformations explicit;
* endpoint evidence must bind the terminal receipt, artifact, authorization,
  and independently checked business facts.

Local module success is necessary, but it cannot prove system success.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ModuleName(str, Enum):
    COMPOSITION = "composition"
    PERCEPTION = "perception"
    COLLABORATION = "collaboration"
    REASONING = "reasoning"
    ACTION = "action"
    REFLECTION = "reflection"
    GOVERNANCE = "governance"
    MEMORY = "memory"


MODULE_ORDER = (
    ModuleName.COMPOSITION,
    ModuleName.PERCEPTION,
    ModuleName.COLLABORATION,
    ModuleName.REASONING,
    ModuleName.ACTION,
    ModuleName.REFLECTION,
    ModuleName.GOVERNANCE,
    ModuleName.MEMORY,
)


class ReceiptStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FindingSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"


def stable_digest(payload: Mapping[str, Any] | str) -> str:
    """Return a short deterministic digest for a contract or artifact."""

    if isinstance(payload, str):
        canonical = payload
    else:
        canonical = json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class PatternBinding:
    module: ModuleName
    pattern: str
    purpose: str

    def __post_init__(self) -> None:
        if not self.pattern.strip() or not self.purpose.strip():
            raise ValueError("a pattern binding needs a pattern and purpose")


@dataclass(frozen=True)
class SystemRunContract:
    run_id: str
    version: int
    goal: str
    workload_ref: str
    workload_digest: str
    selection_receipt_digest: str
    pattern_bindings: tuple[PatternBinding, ...]

    def __post_init__(self) -> None:
        required = (
            self.run_id,
            self.goal,
            self.workload_ref,
            self.workload_digest,
            self.selection_receipt_digest,
        )
        if not all(value.strip() for value in required):
            raise ValueError("system run contract fields must not be empty")
        if self.version < 1:
            raise ValueError("contract version must be at least one")
        modules = [binding.module for binding in self.pattern_bindings]
        if len(modules) != len(set(modules)):
            raise ValueError("one module cannot bind more than one primary pattern")
        if set(modules) != set(MODULE_ORDER):
            missing = sorted(module.value for module in set(MODULE_ORDER) - set(modules))
            extra = sorted(module.value for module in set(modules) - set(MODULE_ORDER))
            raise ValueError(
                f"pattern bindings must cover the eight modules: missing={missing} extra={extra}"
            )

    @property
    def digest(self) -> str:
        return stable_digest(
            {
                "run_id": self.run_id,
                "version": self.version,
                "goal": self.goal,
                "workload_ref": self.workload_ref,
                "workload_digest": self.workload_digest,
                "selection_receipt_digest": self.selection_receipt_digest,
                "pattern_bindings": tuple(
                    (binding.module.value, binding.pattern, binding.purpose)
                    for binding in self.pattern_bindings
                ),
            }
        )

    def pattern_for(self, module: ModuleName) -> str:
        for binding in self.pattern_bindings:
            if binding.module is module:
                return binding.pattern
        raise KeyError(module)


@dataclass(frozen=True)
class ModuleReceipt:
    receipt_id: str
    module: ModuleName
    pattern: str
    run_id: str
    contract_digest: str
    workload_digest: str
    input_digest: str
    output_digest: str
    parent_receipts: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    status: ReceiptStatus = ReceiptStatus.ACCEPTED

    def __post_init__(self) -> None:
        required = (
            self.receipt_id,
            self.pattern,
            self.run_id,
            self.contract_digest,
            self.workload_digest,
            self.input_digest,
            self.output_digest,
        )
        if not all(value.strip() for value in required):
            raise ValueError("module receipt identity and digests must not be empty")
        if len(self.parent_receipts) != len(set(self.parent_receipts)):
            raise ValueError("parent receipt digests must be unique")
        if not self.evidence_refs:
            raise ValueError("a module receipt must carry durable evidence")

    @property
    def digest(self) -> str:
        return stable_digest(
            {
                "receipt_id": self.receipt_id,
                "module": self.module.value,
                "pattern": self.pattern,
                "run_id": self.run_id,
                "contract_digest": self.contract_digest,
                "workload_digest": self.workload_digest,
                "input_digest": self.input_digest,
                "output_digest": self.output_digest,
                "parent_receipts": self.parent_receipts,
                "evidence_refs": self.evidence_refs,
                "status": self.status.value,
            }
        )


@dataclass(frozen=True)
class BusinessCheck:
    name: str
    passed: bool
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.evidence_ref.strip():
            raise ValueError("a business check needs a name and evidence")


@dataclass(frozen=True)
class EndpointEvidence:
    contract_digest: str
    terminal_receipt_digest: str
    artifact_digest: str
    authorization_ref: str
    external_refs: tuple[str, ...]
    checks: tuple[BusinessCheck, ...]

    def __post_init__(self) -> None:
        required = (
            self.contract_digest,
            self.terminal_receipt_digest,
            self.artifact_digest,
            self.authorization_ref,
        )
        if not all(value.strip() for value in required):
            raise ValueError("endpoint identity fields must not be empty")
        if not self.external_refs:
            raise ValueError("endpoint evidence needs at least one external reference")
        if not self.checks:
            raise ValueError("endpoint evidence needs at least one business check")


@dataclass(frozen=True)
class AssemblyFinding:
    code: str
    detail: str
    evidence_ref: str
    severity: FindingSeverity = FindingSeverity.BLOCKER


@dataclass(frozen=True)
class SystemAcceptanceReport:
    accepted: bool
    local_acceptance_count: int
    required_module_count: int
    findings: tuple[AssemblyFinding, ...]
    receipt_digests: tuple[str, ...]
    endpoint_evidence: EndpointEvidence


class AssemblyError(RuntimeError):
    """Raised when the strict assembly path would break the evidence spine."""


def audit_system(
    contract: SystemRunContract,
    receipts: tuple[ModuleReceipt, ...],
    endpoint: EndpointEvidence,
) -> SystemAcceptanceReport:
    """Audit local receipts, cross-module lineage, and endpoint truth."""

    findings: list[AssemblyFinding] = []
    by_module: dict[ModuleName, ModuleReceipt] = {}
    for receipt in receipts:
        if receipt.module in by_module:
            findings.append(
                AssemblyFinding(
                    "duplicate_module_receipt",
                    f"module {receipt.module.value} produced more than one receipt",
                    f"receipt://{receipt.digest}",
                )
            )
            continue
        by_module[receipt.module] = receipt

    previous: ModuleReceipt | None = None
    for module in MODULE_ORDER:
        receipt = by_module.get(module)
        if receipt is None:
            findings.append(
                AssemblyFinding(
                    "missing_module_receipt",
                    f"module {module.value} has no receipt",
                    f"contract://{contract.digest}",
                )
            )
            previous = None
            continue
        if receipt.run_id != contract.run_id:
            findings.append(
                AssemblyFinding(
                    "run_identity_drift",
                    f"module {module.value} belongs to another run",
                    f"receipt://{receipt.digest}",
                )
            )
        if receipt.contract_digest != contract.digest:
            findings.append(
                AssemblyFinding(
                    "contract_drift",
                    f"module {module.value} binds another system contract",
                    f"receipt://{receipt.digest}",
                )
            )
        if receipt.workload_digest != contract.workload_digest:
            findings.append(
                AssemblyFinding(
                    "workload_drift",
                    f"module {module.value} evaluated another workload",
                    f"receipt://{receipt.digest}",
                )
            )
        if receipt.pattern != contract.pattern_for(module):
            findings.append(
                AssemblyFinding(
                    "unselected_pattern",
                    f"module {module.value} ran {receipt.pattern!r}",
                    f"selection://{contract.selection_receipt_digest}",
                )
            )
        if receipt.status is not ReceiptStatus.ACCEPTED:
            findings.append(
                AssemblyFinding(
                    "module_rejected",
                    f"module {module.value} rejected its local artifact",
                    f"receipt://{receipt.digest}",
                )
            )
        if previous is None:
            if module is ModuleName.COMPOSITION and receipt.parent_receipts:
                findings.append(
                    AssemblyFinding(
                        "unexpected_root_parent",
                        "the composition receipt must start the evidence spine",
                        f"receipt://{receipt.digest}",
                    )
                )
        else:
            expected_parent = (previous.digest,)
            if receipt.parent_receipts != expected_parent:
                findings.append(
                    AssemblyFinding(
                        "lineage_break",
                        (
                            f"{module.value} does not descend from "
                            f"{previous.module.value}"
                        ),
                        f"receipt://{receipt.digest}",
                    )
                )
            if receipt.input_digest != previous.output_digest:
                findings.append(
                    AssemblyFinding(
                        "artifact_handoff_mismatch",
                        (
                            f"{module.value} consumed {receipt.input_digest}, "
                            f"but {previous.module.value} produced "
                            f"{previous.output_digest}"
                        ),
                        f"receipt://{receipt.digest}",
                    )
                )
        previous = receipt

    if endpoint.contract_digest != contract.digest:
        findings.append(
            AssemblyFinding(
                "endpoint_contract_mismatch",
                "the business endpoint belongs to another contract version",
                endpoint.external_refs[0],
            )
        )
    terminal = by_module.get(MODULE_ORDER[-1])
    if terminal is None or endpoint.terminal_receipt_digest != terminal.digest:
        findings.append(
            AssemblyFinding(
                "endpoint_receipt_mismatch",
                "the endpoint does not bind the terminal module receipt",
                endpoint.external_refs[0],
            )
        )
    if terminal is None or endpoint.artifact_digest != terminal.output_digest:
        findings.append(
            AssemblyFinding(
                "endpoint_artifact_mismatch",
                "the endpoint artifact differs from the assembled artifact",
                endpoint.external_refs[0],
            )
        )
    governance = by_module.get(ModuleName.GOVERNANCE)
    if governance is None or endpoint.authorization_ref not in governance.evidence_refs:
        findings.append(
            AssemblyFinding(
                "authorization_not_bound",
                "the endpoint authorization is absent from governance evidence",
                endpoint.authorization_ref,
            )
        )
    for check in endpoint.checks:
        if not check.passed:
            findings.append(
                AssemblyFinding(
                    "business_check_failed",
                    f"endpoint check {check.name!r} failed",
                    check.evidence_ref,
                )
            )

    return SystemAcceptanceReport(
        accepted=not any(
            finding.severity is FindingSeverity.BLOCKER for finding in findings
        ),
        local_acceptance_count=sum(
            receipt.status is ReceiptStatus.ACCEPTED for receipt in receipts
        ),
        required_module_count=len(MODULE_ORDER),
        findings=tuple(findings),
        receipt_digests=tuple(receipt.digest for receipt in receipts),
        endpoint_evidence=endpoint,
    )


class SystemAssembly:
    """Strict builder that refuses a broken cross-module lineage."""

    def __init__(self, contract: SystemRunContract) -> None:
        self.contract = contract
        self._receipts: list[ModuleReceipt] = []

    @property
    def receipts(self) -> tuple[ModuleReceipt, ...]:
        return tuple(self._receipts)

    def record(self, receipt: ModuleReceipt) -> ModuleReceipt:
        position = len(self._receipts)
        if position >= len(MODULE_ORDER):
            raise AssemblyError("the eight-module assembly is already complete")
        expected_module = MODULE_ORDER[position]
        if receipt.module is not expected_module:
            raise AssemblyError(
                f"expected module {expected_module.value}, got {receipt.module.value}"
            )
        if receipt.run_id != self.contract.run_id:
            raise AssemblyError("module receipt belongs to another run")
        if receipt.contract_digest != self.contract.digest:
            raise AssemblyError("module receipt belongs to another contract")
        if receipt.workload_digest != self.contract.workload_digest:
            raise AssemblyError("module receipt belongs to another workload")
        if receipt.pattern != self.contract.pattern_for(receipt.module):
            raise AssemblyError("module receipt uses an unselected pattern")
        if receipt.status is not ReceiptStatus.ACCEPTED:
            raise AssemblyError("a rejected module cannot enter the accepted spine")
        if position == 0:
            if receipt.parent_receipts:
                raise AssemblyError("the composition root cannot have a parent")
        else:
            previous = self._receipts[-1]
            if receipt.parent_receipts != (previous.digest,):
                raise AssemblyError("module receipt does not bind the previous receipt")
            if receipt.input_digest != previous.output_digest:
                raise AssemblyError("module input does not match the previous output")
        self._receipts.append(receipt)
        return receipt

    def seal(self, endpoint: EndpointEvidence) -> SystemAcceptanceReport:
        report = audit_system(self.contract, self.receipts, endpoint)
        if not report.accepted:
            codes = ", ".join(finding.code for finding in report.findings)
            raise AssemblyError(f"system acceptance failed: {codes}")
        return report
