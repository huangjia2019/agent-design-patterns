"""Invariant tests for the lightweight handoff-chain lab."""

from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_handoff_lab as lab  # noqa: E402


def test_text_relay_can_publish_a_stale_claim() -> None:
    weak = lab.weak_text_relay()

    assert weak["source_checked"] is True
    assert weak["published"] is True
    assert weak["draft"] == "All dsh subagents are fully isolated by default."


def test_binding_rule_rejects_a_draft_built_from_the_old_claim() -> None:
    _, receipts = lab.run_contract_chain()
    rejected = receipts[2]

    assert rejected.stage_id == "edit"
    assert rejected.accepted is False
    assert rejected.reason == "stale_claim_binding"
    assert rejected.input_version == rejected.output_version == 2


def test_repair_resumes_from_the_last_accepted_version() -> None:
    baton, receipts = lab.run_contract_chain()

    repaired = receipts[3]
    published = receipts[4]
    assert repaired.accepted is True
    assert repaired.input_version == 2
    assert repaired.output_version == 3
    assert published.accepted is True
    assert baton.version == 4


def test_stage_cannot_write_a_fact_it_does_not_own() -> None:
    baton = lab.Baton("ownership-test", 0)
    _, receipt = lab.apply_stage(
        baton,
        lab.RESEARCH,
        {
            "raw_claim": ("claim", "source"),
            "unexpected": ("value", "source"),
        },
    )

    assert receipt.accepted is False
    assert receipt.reason == "wrong_delta_shape"
