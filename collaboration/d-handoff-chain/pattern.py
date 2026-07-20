"""Handoff Chain pattern.

Work moves through an ordered line of specialist stages. Each stage receives a
read-only snapshot, consumes declared facts, and returns a typed delta. The chain
validates ownership, evidence, type, value semantics, and exact delivery at the
seam before committing the next immutable baton revision.

The shared collaboration boundary remains:

``TaskContract -> Baton revisions -> StageReceipt -> AcceptanceReceipt``

The pattern owns five invariants:

* a stage must receive every fact it declares in ``requires``;
* a stage must itself deliver every fact it declares in ``provides``;
* one fact has one declared producer and committed facts are append-only;
* values cross the seam only after type, evidence, and semantic validation;
* a failed stage leaves the prior baton revision untouched, so a retry starts from
  the same checkpoint and receives the same stage-run id.

This is a static specialist pipeline. Dynamic conversational handoff also needs
route allowlists, context filtering, and authority transfer.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from collaboration.boundary_contract import (  # noqa: E402
    AcceptanceDecision,
    AcceptanceReceipt,
    TaskContract,
)


FactValidator = Callable[[Any, "BatonView"], str | None]


class SeamError(Exception):
    """A failed seam plus the last committed, retryable checkpoint."""

    def __init__(
        self,
        stage_name: str,
        code: str,
        detail: str,
        *,
        checkpoint: "Baton | None" = None,
        receipts: tuple["StageReceipt", ...] = (),
    ):
        self.stage_name = stage_name
        self.code = code
        self.detail = detail
        self.checkpoint = checkpoint
        self.receipts = receipts
        super().__init__(f"stage '{stage_name}' [{code}] {detail}")


@dataclass(frozen=True)
class FactValue:
    """One value proposed by a stage, with the evidence used to derive it."""

    key: str
    value: Any
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("fact key must not be empty")
        object.__setattr__(self, "value", copy.deepcopy(self.value))


@dataclass(frozen=True)
class FactRule:
    """Ownership and admission contract for one fact crossing a seam."""

    key: str
    producer_stage: str
    value_type: type
    validator: FactValidator | None = None
    evidence_required: bool = True

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.key, self.producer_stage)):
            raise ValueError("fact rule identity fields must not be empty")
        if not isinstance(self.value_type, type):
            raise ValueError("value_type must be a runtime type")
        if self.validator is not None and not callable(self.validator):
            raise ValueError("validator must be callable")


@dataclass(frozen=True, init=False)
class FactRecord:
    """A committed fact and its provenance."""

    key: str
    _value: Any = field(repr=False)
    producer_stage: str
    stage_run_id: str
    evidence_refs: tuple[str, ...]

    def __init__(
        self,
        key: str,
        value: Any,
        producer_stage: str,
        stage_run_id: str,
        evidence_refs: tuple[str, ...],
    ) -> None:
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "_value", copy.deepcopy(value))
        object.__setattr__(self, "producer_stage", producer_stage)
        object.__setattr__(self, "stage_run_id", stage_run_id)
        object.__setattr__(self, "evidence_refs", evidence_refs)
        self.__post_init__()

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (self.key, self.producer_stage, self.stage_run_id)
        ):
            raise ValueError("fact provenance fields must not be empty")

    @property
    def value(self) -> Any:
        return copy.deepcopy(self._value)


@dataclass(frozen=True)
class Baton:
    """An immutable committed checkpoint passed between specialist stages."""

    baton_id: str
    contract_digest: str
    intent: str
    revision: int = 0
    records: tuple[FactRecord, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    trace: tuple[str, ...] = ()
    stage_receipts: tuple["StageReceipt", ...] = ()

    def __post_init__(self) -> None:
        required = (self.baton_id, self.contract_digest, self.intent)
        if not all(value.strip() for value in required):
            raise ValueError("baton identity and intent must not be empty")
        if self.revision < 0:
            raise ValueError("baton revision must not be negative")
        if self.revision != len(self.trace):
            raise ValueError("baton revision must match completed stage count")
        if len(self.stage_receipts) != len(self.trace):
            raise ValueError("each completed stage must have one receipt")
        keys = [record.key for record in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError("a baton cannot contain duplicate fact keys")

    @property
    def facts(self) -> Mapping[str, Any]:
        values = {
            record.key: copy.deepcopy(record.value)
            for record in self.records
        }
        return MappingProxyType(values)

    def fact_record(self, key: str) -> FactRecord:
        for record in self.records:
            if record.key == key:
                return record
        raise KeyError(key)

    @property
    def fingerprint(self) -> str:
        payload = {
            "baton_id": self.baton_id,
            "contract_digest": self.contract_digest,
            "intent": self.intent,
            "revision": self.revision,
            "records": [
                {
                    "key": record.key,
                    "value": record.value,
                    "producer_stage": record.producer_stage,
                    "stage_run_id": record.stage_run_id,
                    "evidence_refs": record.evidence_refs,
                }
                for record in self.records
            ],
            "artifact_refs": self.artifact_refs,
            "trace": self.trace,
        }
        canonical = json.dumps(
            payload,
            default=_json_default,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @property
    def snapshot_id(self) -> str:
        return f"{self.baton_id}::r{self.revision}::{self.fingerprint}"


@dataclass(frozen=True)
class BatonView:
    """A stage-scoped, detached view of the latest committed baton."""

    baton_id: str
    contract_digest: str
    intent: str
    revision: int
    stage_name: str
    stage_run_id: str
    facts: Mapping[str, Any]
    artifact_refs: tuple[str, ...]
    trace: tuple[str, ...]


@dataclass(frozen=True)
class StageSpec:
    """One stage's declared entry requirements and owned outputs."""

    name: str
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("stage name must not be empty")
        if len(self.requires) != len(set(self.requires)):
            raise ValueError("stage requires must not contain duplicates")
        if len(self.provides) != len(set(self.provides)):
            raise ValueError("stage provides must not contain duplicates")
        if set(self.requires).intersection(self.provides):
            raise ValueError("a stage cannot require and provide the same fact")


@dataclass(frozen=True)
class StageDelta:
    """The only mutation channel: new facts and immutable artifact references."""

    facts: tuple[FactValue, ...] = ()
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        keys = [fact.key for fact in self.facts]
        if len(keys) != len(set(keys)):
            raise ValueError("a stage delta cannot contain duplicate fact keys")
        if any(not ref.strip() for ref in self.artifact_refs):
            raise ValueError("artifact references must not be empty")


class StageFn(Protocol):
    def __call__(self, baton: BatonView) -> Awaitable[StageDelta]: ...


@dataclass(frozen=True)
class StageBinding:
    spec: StageSpec
    run: StageFn

    def __post_init__(self) -> None:
        if not callable(self.run):
            raise ValueError("stage run must be callable")


@dataclass(frozen=True)
class StageReceipt:
    """Proof that one exact baton revision crossed one stage seam."""

    receipt_id: str
    contract_digest: str
    baton_id: str
    stage_name: str
    stage_run_id: str
    input_revision: int
    output_revision: int
    input_fingerprint: str
    output_fingerprint: str
    consumed_keys: tuple[str, ...]
    produced_keys: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ChainRun:
    contract: TaskContract
    baton: Baton
    receipts: tuple[StageReceipt, ...]
    acceptance_receipt: AcceptanceReceipt


class HandoffChain:
    """Run a statically wired specialist pipeline over immutable checkpoints."""

    def __init__(
        self,
        contract: TaskContract,
        stages: tuple[StageBinding, ...],
        fact_rules: tuple[FactRule, ...],
        *,
        initial_fact_keys: tuple[str, ...] = (),
        chain_id: str = "handoff-chain",
    ):
        if not stages:
            raise ValueError("a handoff chain needs at least one stage")
        if not chain_id.strip():
            raise ValueError("chain_id must not be empty")
        self.contract = contract
        self.stages = stages
        self.fact_rules = fact_rules
        self.initial_fact_keys = initial_fact_keys
        self.chain_id = chain_id
        self._rules = {rule.key: rule for rule in fact_rules}
        self._validate_topology()

    def _validate_topology(self) -> None:
        stage_names = [binding.spec.name for binding in self.stages]
        if len(stage_names) != len(set(stage_names)):
            raise ValueError("stage names must be unique")
        rule_keys = [rule.key for rule in self.fact_rules]
        if len(rule_keys) != len(set(rule_keys)):
            raise ValueError("fact rule keys must be unique")
        if len(self.initial_fact_keys) != len(set(self.initial_fact_keys)):
            raise ValueError("initial_fact_keys must be unique")

        owners: dict[str, str] = {}
        available = set(self.initial_fact_keys)
        for binding in self.stages:
            spec = binding.spec
            missing_wiring = set(spec.requires) - available
            if missing_wiring:
                raise ValueError(
                    f"stage '{spec.name}' requires facts with no earlier owner: "
                    f"{sorted(missing_wiring)}"
                )
            for key in spec.provides:
                if key in owners or key in self.initial_fact_keys:
                    raise ValueError(f"fact '{key}' has more than one producer")
                owners[key] = spec.name
            available.update(spec.provides)

        expected_keys = set(self.initial_fact_keys).union(owners)
        if set(self._rules) != expected_keys:
            missing = sorted(expected_keys - set(self._rules))
            extra = sorted(set(self._rules) - expected_keys)
            raise ValueError(
                f"fact rules do not match chain facts: missing={missing} extra={extra}"
            )
        for key in self.initial_fact_keys:
            if self._rules[key].producer_stage != "__input__":
                raise ValueError(
                    f"initial fact '{key}' must use producer_stage='__input__'"
                )
        for key, owner in owners.items():
            if self._rules[key].producer_stage != owner:
                raise ValueError(
                    f"fact '{key}' owner mismatch: "
                    f"spec={owner} rule={self._rules[key].producer_stage}"
                )

    async def run(self, baton: Baton) -> ChainRun:
        current = baton
        while len(current.trace) < len(self.stages):
            current, _ = await self.advance(current)

        acceptance = AcceptanceReceipt(
            receipt_id=f"accept::{current.snapshot_id}",
            contract_digest=self.contract.digest,
            artifact_id=current.snapshot_id,
            checked_by=self.chain_id,
            decision=AcceptanceDecision.ACCEPTED,
        )
        return ChainRun(
            contract=self.contract,
            baton=current,
            receipts=current.stage_receipts,
            acceptance_receipt=acceptance,
        )

    async def advance(self, baton: Baton) -> tuple[Baton, StageReceipt]:
        """Validate and commit exactly the next stage after this checkpoint."""

        self._validate_checkpoint(baton)
        completed = len(baton.trace)
        if completed == len(self.stages):
            raise ValueError("handoff chain is already complete")
        binding = self.stages[completed]
        spec = binding.spec
        try:
            self._check_requires(spec, baton)
            view = self._view(spec, baton)
            delta = await binding.run(view)
            return self._commit(spec, baton, view, delta)
        except SeamError as exc:
            if exc.checkpoint is not None:
                raise
            raise SeamError(
                spec.name,
                exc.code,
                exc.detail,
                checkpoint=baton,
                receipts=baton.stage_receipts,
            ) from exc
        except Exception as exc:
            raise SeamError(
                spec.name,
                "stage_failed",
                f"{type(exc).__name__}: {exc}",
                checkpoint=baton,
                receipts=baton.stage_receipts,
            ) from exc

    def _validate_checkpoint(self, baton: Baton) -> None:
        if baton.contract_digest != self.contract.digest:
            raise ValueError("baton belongs to another task contract")
        completed = len(baton.trace)
        if completed > len(self.stages):
            raise ValueError("baton has more stages than this chain")
        expected_trace = tuple(
            binding.spec.name for binding in self.stages[:completed]
        )
        if baton.trace != expected_trace:
            raise ValueError("baton trace is not a valid chain prefix")
        expected_keys = set(self.initial_fact_keys)
        for binding in self.stages[:completed]:
            expected_keys.update(binding.spec.provides)
        if set(baton.facts) != expected_keys:
            raise ValueError(
                "baton facts do not match its committed chain prefix"
            )

    @staticmethod
    def _check_requires(spec: StageSpec, baton: Baton) -> None:
        missing = [key for key in spec.requires if key not in baton.facts]
        if missing:
            raise SeamError(
                spec.name,
                "missing_required_fact",
                f"requires {missing}; baton only has {sorted(baton.facts)}",
            )

    @staticmethod
    def _view(spec: StageSpec, baton: Baton) -> BatonView:
        stage_run_id = (
            f"{baton.baton_id}::{spec.name}::"
            f"r{baton.revision}::{baton.fingerprint}"
        )
        detached = copy.deepcopy(dict(baton.facts))
        return BatonView(
            baton_id=baton.baton_id,
            contract_digest=baton.contract_digest,
            intent=baton.intent,
            revision=baton.revision,
            stage_name=spec.name,
            stage_run_id=stage_run_id,
            facts=MappingProxyType(detached),
            artifact_refs=baton.artifact_refs,
            trace=baton.trace,
        )

    def _commit(
        self,
        spec: StageSpec,
        baton: Baton,
        view: BatonView,
        delta: StageDelta,
    ) -> tuple[Baton, StageReceipt]:
        if not isinstance(delta, StageDelta):
            raise SeamError(
                spec.name,
                "invalid_stage_delta",
                "stage must return StageDelta",
            )
        by_key = {fact.key: fact for fact in delta.facts}
        missing = sorted(set(spec.provides) - set(by_key))
        undeclared = sorted(set(by_key) - set(spec.provides))
        if missing:
            raise SeamError(
                spec.name,
                "promised_fact_missing",
                f"promised {list(spec.provides)} but did not provide {missing}",
            )
        if undeclared:
            raise SeamError(
                spec.name,
                "undeclared_fact",
                f"returned facts outside provides: {undeclared}",
            )
        clobbered = sorted(set(by_key).intersection(baton.facts))
        if clobbered:
            raise SeamError(
                spec.name,
                "committed_fact_overwrite",
                f"tried to overwrite committed facts {clobbered}",
            )

        validation_view = self._view(spec, baton)
        new_records: list[FactRecord] = []
        evidence: list[str] = []
        for key in spec.provides:
            fact = by_key[key]
            rule = self._rules[key]
            if not isinstance(fact.value, rule.value_type):
                raise SeamError(
                    spec.name,
                    "fact_type_mismatch",
                    (
                        f"fact '{key}' expected {rule.value_type.__name__}, "
                        f"got {type(fact.value).__name__}"
                    ),
                )
            if rule.evidence_required and not fact.evidence_refs:
                raise SeamError(
                    spec.name,
                    "fact_evidence_missing",
                    f"fact '{key}' requires evidence",
                )
            if rule.validator is not None:
                finding = rule.validator(fact.value, validation_view)
                if finding:
                    raise SeamError(
                        spec.name,
                        "fact_semantic_violation",
                        f"fact '{key}' failed its rule: {finding}",
                    )
            evidence.extend(fact.evidence_refs)
            new_records.append(
                FactRecord(
                    key=key,
                    value=fact.value,
                    producer_stage=spec.name,
                    stage_run_id=view.stage_run_id,
                    evidence_refs=fact.evidence_refs,
                )
            )

        next_baton = Baton(
            baton_id=baton.baton_id,
            contract_digest=baton.contract_digest,
            intent=baton.intent,
            revision=baton.revision + 1,
            records=(*baton.records, *new_records),
            artifact_refs=(*baton.artifact_refs, *delta.artifact_refs),
            trace=(*baton.trace, spec.name),
            stage_receipts=(
                *baton.stage_receipts,
                StageReceipt(
                    receipt_id="pending",
                    contract_digest=baton.contract_digest,
                    baton_id=baton.baton_id,
                    stage_name=spec.name,
                    stage_run_id=view.stage_run_id,
                    input_revision=baton.revision,
                    output_revision=baton.revision + 1,
                    input_fingerprint=baton.fingerprint,
                    output_fingerprint="pending",
                    consumed_keys=spec.requires,
                    produced_keys=spec.provides,
                    evidence_refs=tuple(dict.fromkeys(evidence)),
                ),
            ),
        )
        receipt = StageReceipt(
            receipt_id=f"receipt::{view.stage_run_id}",
            contract_digest=baton.contract_digest,
            baton_id=baton.baton_id,
            stage_name=spec.name,
            stage_run_id=view.stage_run_id,
            input_revision=baton.revision,
            output_revision=next_baton.revision,
            input_fingerprint=baton.fingerprint,
            output_fingerprint=next_baton.fingerprint,
            consumed_keys=spec.requires,
            produced_keys=spec.provides,
            evidence_refs=tuple(dict.fromkeys(evidence)),
        )
        next_baton = Baton(
            baton_id=next_baton.baton_id,
            contract_digest=next_baton.contract_digest,
            intent=next_baton.intent,
            revision=next_baton.revision,
            records=next_baton.records,
            artifact_refs=next_baton.artifact_refs,
            trace=next_baton.trace,
            stage_receipts=(*baton.stage_receipts, receipt),
        )
        return next_baton, receipt


def new_baton(
    contract: TaskContract,
    *,
    baton_id: str,
    intent: str,
    initial_facts: tuple[FactValue, ...] = (),
) -> Baton:
    """Create revision zero bound to a task contract."""

    records = tuple(
        FactRecord(
            key=fact.key,
            value=fact.value,
            producer_stage="__input__",
            stage_run_id=f"{baton_id}::__input__",
            evidence_refs=fact.evidence_refs,
        )
        for fact in initial_facts
    )
    return Baton(
        baton_id=baton_id,
        contract_digest=contract.digest,
        intent=intent,
        records=records,
    )


def _json_default(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    return repr(value)
