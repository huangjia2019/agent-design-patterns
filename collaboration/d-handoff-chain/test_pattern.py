"""Invariants for the contract-bound Handoff Chain pattern."""
from __future__ import annotations

import asyncio
import os
import sys

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    AcceptanceDecision,
    FactRecord,
    FactRule,
    FactValue,
    HandoffChain,
    SeamError,
    StageBinding,
    StageDelta,
    StageSpec,
    TaskContract,
    new_baton,
)


def contract() -> TaskContract:
    return TaskContract(
        contract_id="book-trip",
        version=1,
        objective="book one reviewed trip",
        output_schema="TravelBaton",
        accountable_owner="travel-controller",
        boundary="each specialist owns declared facts",
    )


def rule(
    key: str,
    producer: str,
    value_type: type = str,
    *,
    validator=None,
    evidence_required: bool = True,
) -> FactRule:
    return FactRule(
        key=key,
        producer_stage=producer,
        value_type=value_type,
        validator=validator,
        evidence_required=evidence_required,
    )


def good_chain(*, route_fn=None, pay_fn=None) -> HandoffChain:
    async def intent(view):
        return StageDelta(
            facts=(
                FactValue("city", "Shanghai", ("request://trip",)),
                FactValue("date", "2026-07-18", ("request://trip",)),
            )
        )

    async def route(view):
        return StageDelta(
            facts=(
                FactValue("depart_by", "18:00", ("map://route-42",)),
            )
        )

    async def pay(view):
        return StageDelta(
            facts=(
                FactValue("booking_id", "trip-42", ("booking://trip-42",)),
            ),
            artifact_refs=("artifact://ticket-42",),
        )

    return HandoffChain(
        contract(),
        (
            StageBinding(
                StageSpec("intent", provides=("city", "date")),
                intent,
            ),
            StageBinding(
                StageSpec(
                    "route",
                    requires=("city", "date"),
                    provides=("depart_by",),
                ),
                route_fn or route,
            ),
            StageBinding(
                StageSpec(
                    "pay",
                    requires=("depart_by",),
                    provides=("booking_id",),
                ),
                pay_fn or pay,
            ),
        ),
        (
            rule("city", "intent"),
            rule("date", "intent"),
            rule("depart_by", "route"),
            rule("booking_id", "pay"),
        ),
        chain_id="travel-handoff",
    )


def initial():
    return new_baton(
        contract(),
        baton_id="travel-42",
        intent="be in Shanghai tomorrow",
    )


def test_full_chain_commits_three_versions_and_an_acceptance_receipt() -> None:
    result = asyncio.run(good_chain().run(initial()))

    assert result.baton.revision == 3
    assert result.baton.trace == ("intent", "route", "pay")
    assert result.baton.facts["city"] == "Shanghai"
    assert result.baton.facts["booking_id"] == "trip-42"
    assert result.baton.artifact_refs == ("artifact://ticket-42",)
    assert len(result.receipts) == 3
    assert result.baton.stage_receipts == result.receipts
    assert result.acceptance_receipt.decision is AcceptanceDecision.ACCEPTED
    assert result.acceptance_receipt.artifact_id == result.baton.snapshot_id
    assert all(
        receipt.contract_digest == contract().digest
        for receipt in result.receipts
    )


def test_stage_receipt_binds_input_and_output_revisions() -> None:
    result = asyncio.run(good_chain().run(initial()))

    assert [
        (receipt.input_revision, receipt.output_revision)
        for receipt in result.receipts
    ] == [(0, 1), (1, 2), (2, 3)]
    assert all(
        receipt.input_fingerprint != receipt.output_fingerprint
        for receipt in result.receipts
    )


def test_stage_must_deliver_its_own_promised_fact() -> None:
    async def empty_route(view):
        return StageDelta()

    with pytest.raises(SeamError) as err:
        asyncio.run(good_chain(route_fn=empty_route).run(initial()))

    assert err.value.stage_name == "route"
    assert err.value.code == "promised_fact_missing"
    assert err.value.checkpoint.revision == 1
    assert err.value.checkpoint.trace == ("intent",)


def test_stage_cannot_return_an_undeclared_fact() -> None:
    async def noisy_route(view):
        return StageDelta(
            facts=(
                FactValue("depart_by", "18:00", ("map://route-42",)),
                FactValue("secret", "leaked", ("memory://private",)),
            )
        )

    with pytest.raises(SeamError) as err:
        asyncio.run(good_chain(route_fn=noisy_route).run(initial()))

    assert err.value.code == "undeclared_fact"
    assert "secret" in err.value.detail


def test_stage_receives_a_detached_read_only_snapshot() -> None:
    observed: dict[str, object] = {}

    async def mutating_route(view):
        observed["intent"] = view.intent
        with pytest.raises(TypeError):
            view.facts["city"] = "Beijing"
        nested = view.facts["profile"]
        nested["vip"] = False
        return StageDelta(
            facts=(
                FactValue("depart_by", "18:00", ("map://route-42",)),
            )
        )

    c = TaskContract(
        contract_id="nested",
        version=1,
        objective="prove detached views",
        output_schema="Baton",
        accountable_owner="controller",
    )

    async def input_stage(view):
        return StageDelta(
            facts=(
                FactValue(
                    "profile",
                    {"vip": True},
                    ("request://profile",),
                ),
            )
        )

    chain = HandoffChain(
        c,
        (
            StageBinding(
                StageSpec("input", provides=("profile",)),
                input_stage,
            ),
            StageBinding(
                StageSpec(
                    "route",
                    requires=("profile",),
                    provides=("depart_by",),
                ),
                mutating_route,
            ),
        ),
        (
            rule("profile", "input", dict),
            rule("depart_by", "route"),
        ),
    )
    result = asyncio.run(
        chain.run(new_baton(c, baton_id="nested-1", intent="keep me"))
    )

    assert observed["intent"] == "keep me"
    assert result.baton.facts["profile"] == {"vip": True}


def test_committed_record_values_are_exposed_as_detached_copies() -> None:
    result = asyncio.run(good_chain().run(initial()))

    exposed = result.baton.fact_record("city").value
    assert exposed == "Shanghai"

    nested = FactRecord(
        key="profile",
        value={"roles": ["traveler"]},
        producer_stage="intent",
        stage_run_id="run-1",
        evidence_refs=("request://profile",),
    )
    exposed_nested = nested.value
    exposed_nested["roles"].append("admin")

    assert nested.value == {"roles": ["traveler"]}


def test_stage_cannot_tamper_with_the_snapshot_used_by_a_validator() -> None:
    async def mutating_route(view):
        view.facts["policy"]["latest_departure"] = "23:59"
        return StageDelta(
            facts=(
                FactValue("depart_by", "22:00", ("map://route-42",)),
            )
        )

    async def policy_stage(view):
        return StageDelta(
            facts=(
                FactValue(
                    "policy",
                    {"latest_departure": "20:00"},
                    ("policy://travel",),
                ),
            )
        )

    c = contract()
    chain = HandoffChain(
        c,
        (
            StageBinding(
                StageSpec("policy", provides=("policy",)),
                policy_stage,
            ),
            StageBinding(
                StageSpec(
                    "route",
                    requires=("policy",),
                    provides=("depart_by",),
                ),
                mutating_route,
            ),
        ),
        (
            rule("policy", "policy", dict),
            rule(
                "depart_by",
                "route",
                validator=lambda value, view: (
                    None
                    if value <= view.facts["policy"]["latest_departure"]
                    else f"too late: {value}"
                ),
            ),
        ),
    )

    with pytest.raises(SeamError) as err:
        asyncio.run(
            chain.run(
                new_baton(c, baton_id="validator-1", intent="keep policy")
            )
        )

    assert err.value.code == "fact_semantic_violation"
    assert err.value.checkpoint.facts["policy"] == {
        "latest_departure": "20:00"
    }


@pytest.mark.parametrize(
    ("fact", "code"),
    [
        (
            FactValue("depart_by", 1800, ("map://route-42",)),
            "fact_type_mismatch",
        ),
        (
            FactValue("depart_by", "18:00"),
            "fact_evidence_missing",
        ),
    ],
)
def test_type_and_evidence_are_checked_at_the_producing_seam(
    fact: FactValue,
    code: str,
) -> None:
    async def bad_route(view):
        return StageDelta(facts=(fact,))

    with pytest.raises(SeamError) as err:
        asyncio.run(good_chain(route_fn=bad_route).run(initial()))

    assert err.value.stage_name == "route"
    assert err.value.code == code


def test_value_semantics_are_checked_at_the_producing_seam() -> None:
    async def late_route(view):
        return StageDelta(
            facts=(
                FactValue("depart_by", "22:00", ("map://route-42",)),
            )
        )

    async def intent(view):
        return StageDelta(
            facts=(
                FactValue("city", "Shanghai", ("request://trip",)),
            )
        )

    c = contract()
    chain = HandoffChain(
        c,
        (
            StageBinding(StageSpec("intent", provides=("city",)), intent),
            StageBinding(
                StageSpec(
                    "route",
                    requires=("city",),
                    provides=("depart_by",),
                ),
                late_route,
            ),
        ),
        (
            rule("city", "intent"),
            rule(
                "depart_by",
                "route",
                validator=lambda value, view: (
                    None if value <= "20:00" else f"too late: {value}"
                ),
            ),
        ),
    )

    with pytest.raises(SeamError) as err:
        asyncio.run(chain.run(initial()))

    assert err.value.code == "fact_semantic_violation"
    assert "too late" in err.value.detail


def test_failure_checkpoint_resumes_at_the_failed_stage_with_same_run_id() -> None:
    route_run_ids: list[str] = []
    pay_calls = 0

    async def flaky_route(view):
        route_run_ids.append(view.stage_run_id)
        if len(route_run_ids) == 1:
            raise TimeoutError("map service timed out")
        return StageDelta(
            facts=(
                FactValue("depart_by", "18:00", ("map://route-42",)),
            )
        )

    async def pay(view):
        nonlocal pay_calls
        pay_calls += 1
        return StageDelta(
            facts=(
                FactValue("booking_id", "trip-42", ("booking://trip-42",)),
            )
        )

    chain = good_chain(route_fn=flaky_route, pay_fn=pay)
    with pytest.raises(SeamError) as err:
        asyncio.run(chain.run(initial()))

    checkpoint = err.value.checkpoint
    assert checkpoint.trace == ("intent",)
    assert checkpoint.revision == 1
    result = asyncio.run(chain.run(checkpoint))

    assert route_run_ids[0] == route_run_ids[1]
    assert result.baton.trace == ("intent", "route", "pay")
    assert [receipt.stage_name for receipt in result.receipts] == [
        "intent",
        "route",
        "pay",
    ]
    assert pay_calls == 1


def test_fact_provenance_names_the_unique_producer() -> None:
    result = asyncio.run(good_chain().run(initial()))
    record = result.baton.fact_record("depart_by")

    assert record.producer_stage == "route"
    assert record.stage_run_id == result.receipts[1].stage_run_id
    assert record.evidence_refs == ("map://route-42",)


def test_topology_rejects_missing_or_duplicate_ownership() -> None:
    c = contract()

    async def stage(view):
        return StageDelta()

    with pytest.raises(ValueError, match="no earlier owner"):
        HandoffChain(
            c,
            (
                StageBinding(
                    StageSpec("pay", requires=("amount",)),
                    stage,
                ),
            ),
            (),
        )
    with pytest.raises(ValueError, match="more than one producer"):
        HandoffChain(
            c,
            (
                StageBinding(
                    StageSpec("one", provides=("amount",)),
                    stage,
                ),
                StageBinding(
                    StageSpec("two", provides=("amount",)),
                    stage,
                ),
            ),
            (rule("amount", "one", float),),
        )


def test_initial_fact_must_be_declared_and_contract_bound() -> None:
    c = contract()

    async def stage(view):
        return StageDelta(
            facts=(FactValue("done", True, ("test://done",)),)
        )

    chain = HandoffChain(
        c,
        (
            StageBinding(
                StageSpec(
                    "stage",
                    requires=("request_id",),
                    provides=("done",),
                ),
                stage,
            ),
        ),
        (
            rule("request_id", "__input__"),
            rule("done", "stage", bool),
        ),
        initial_fact_keys=("request_id",),
    )
    baton = new_baton(
        c,
        baton_id="input-1",
        intent="process",
        initial_facts=(
            FactValue("request_id", "req-1", ("request://req-1",)),
        ),
    )
    result = asyncio.run(chain.run(baton))

    assert result.baton.facts["done"] is True
    assert result.baton.fact_record("request_id").producer_stage == "__input__"
