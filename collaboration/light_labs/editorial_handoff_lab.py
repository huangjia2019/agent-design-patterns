"""A no-key lab for contract-checked handoff chains.

Run from the repository root:
    python3 collaboration/light_labs/editorial_handoff_lab.py
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class FactRecord:
    """One fact together with its owner and evidence reference."""

    key: str
    value: str
    producer_stage: str
    evidence_ref: str


@dataclass(frozen=True)
class BindingRule:
    """Require two fact values to refer to the same content version."""

    left_key: str
    right_key: str
    error_code: str


@dataclass(frozen=True)
class StageSpec:
    """The fields a stage consumes, owns, and must keep bound together."""

    stage_id: str
    requires: tuple[str, ...]
    provides: tuple[str, ...]
    bindings: tuple[BindingRule, ...] = ()


@dataclass(frozen=True)
class Baton:
    """An immutable, versioned handoff packet."""

    run_id: str
    version: int
    facts: tuple[FactRecord, ...] = ()

    def as_dict(self) -> dict[str, FactRecord]:
        return {fact.key: fact for fact in self.facts}


@dataclass(frozen=True)
class StageReceipt:
    """The result of checking one stage against one baton version."""

    stage_id: str
    input_version: int
    output_version: int
    accepted: bool
    reason: str


RESEARCH = StageSpec("research", (), ("raw_claim", "source_url"))
FACT_CHECK = StageSpec(
    "fact_check",
    ("raw_claim", "source_url"),
    ("verified_claim", "verified_claim_digest"),
)
EDIT = StageSpec(
    "edit",
    ("verified_claim", "verified_claim_digest"),
    ("draft", "draft_claim_digest"),
    (BindingRule("draft_claim_digest", "verified_claim_digest", "stale_claim_binding"),),
)
PUBLISH = StageSpec(
    "publish",
    ("draft", "draft_claim_digest", "verified_claim_digest"),
    ("publication_id",),
    (BindingRule("draft_claim_digest", "verified_claim_digest", "stale_claim_binding"),),
)


def apply_stage(
    baton: Baton,
    spec: StageSpec,
    updates: dict[str, tuple[str, str]],
) -> tuple[Baton, StageReceipt]:
    """Validate one delta, then commit it as the next immutable baton version."""

    current = baton.as_dict()
    missing = tuple(key for key in spec.requires if key not in current)
    if missing:
        return baton, StageReceipt(
            spec.stage_id,
            baton.version,
            baton.version,
            False,
            f"missing:{','.join(missing)}",
        )

    if set(updates) != set(spec.provides):
        return baton, StageReceipt(
            spec.stage_id,
            baton.version,
            baton.version,
            False,
            "wrong_delta_shape",
        )

    if any(key in current for key in updates):
        return baton, StageReceipt(
            spec.stage_id,
            baton.version,
            baton.version,
            False,
            "fact_owner_violation",
        )

    proposed = {
        **current,
        **{
            key: FactRecord(key, value, spec.stage_id, evidence_ref)
            for key, (value, evidence_ref) in updates.items()
        },
    }
    if any(not record.evidence_ref for record in proposed.values()):
        return baton, StageReceipt(
            spec.stage_id,
            baton.version,
            baton.version,
            False,
            "missing_evidence",
        )

    for binding in spec.bindings:
        if proposed[binding.left_key].value != proposed[binding.right_key].value:
            return baton, StageReceipt(
                spec.stage_id,
                baton.version,
                baton.version,
                False,
                binding.error_code,
            )

    next_baton = Baton(baton.run_id, baton.version + 1, tuple(proposed.values()))
    return next_baton, StageReceipt(
        spec.stage_id,
        baton.version,
        next_baton.version,
        True,
        "accepted",
    )


def weak_text_relay() -> dict[str, str | bool]:
    """A cold relay that checks only whether each text field is non-empty."""

    raw_claim = "All dsh subagents are fully isolated by default."
    verified_claim = (
        "In-process spawn subagents use separate sessions. "
        "Filesystem isolation depends on runtime policy."
    )
    draft = raw_claim
    return {
        "source_checked": bool(verified_claim),
        "published": bool(draft),
        "draft": draft,
    }


def run_contract_chain() -> tuple[Baton, tuple[StageReceipt, ...]]:
    baton = Baton("editorial-run-0815", 0)
    receipts: list[StageReceipt] = []

    baton, receipt = apply_stage(
        baton,
        RESEARCH,
        {
            "raw_claim": (
                "All dsh subagents are fully isolated by default.",
                "research-card:atlas",
            ),
            "source_url": (
                "https://github.com/deepseek-ai/deepseek-harness/",
                "research-card:atlas",
            ),
        },
    )
    receipts.append(receipt)

    verified_claim = (
        "In-process spawn subagents use separate sessions. "
        "Filesystem isolation depends on runtime policy."
    )
    baton, receipt = apply_stage(
        baton,
        FACT_CHECK,
        {
            "verified_claim": (verified_claim, "fact-check:birch"),
            "verified_claim_digest": (digest(verified_claim), "fact-check:birch"),
        },
    )
    receipts.append(receipt)

    stale_claim = baton.as_dict()["raw_claim"].value
    _, rejected = apply_stage(
        baton,
        EDIT,
        {
            "draft": (stale_claim, "draft:comet"),
            "draft_claim_digest": (digest(stale_claim), "draft:comet"),
        },
    )
    receipts.append(rejected)

    baton, receipt = apply_stage(
        baton,
        EDIT,
        {
            "draft": (verified_claim, "draft:comet-repaired"),
            "draft_claim_digest": (digest(verified_claim), "draft:comet-repaired"),
        },
    )
    receipts.append(receipt)

    baton, receipt = apply_stage(
        baton,
        PUBLISH,
        {"publication_id": ("brief-2026-08-15", "publisher:delta")},
    )
    receipts.append(receipt)
    return baton, tuple(receipts)


def main() -> None:
    weak = weak_text_relay()
    print("== text relay ==")
    print(
        f"source_checked={str(weak['source_checked']).lower()} "
        f"published={str(weak['published']).lower()}"
    )
    print(f"draft={weak['draft']}")
    print("problem=stale_claim_survived")

    baton, receipts = run_contract_chain()
    print("\n== contract handoff ==")
    for receipt in receipts:
        print(
            f"{receipt.stage_id:<10} "
            f"v{receipt.input_version}->v{receipt.output_version} "
            f"accepted={str(receipt.accepted).lower()} reason={receipt.reason}"
        )
    print(f"final_version={baton.version} publication=brief-2026-08-15")


if __name__ == "__main__":
    main()
