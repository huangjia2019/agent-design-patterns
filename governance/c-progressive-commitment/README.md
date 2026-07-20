# c · Progressive Commitment

> Pattern · Govern × Chain
>
> [中文 README](README.zh-CN.md)

## The problem

A new agent should not receive full production authority on day one. Runtime age
does not prove trust, and model, policy, or authority changes can invalidate old
evidence.

## The pattern

Authority advances through an ordered chain:

```text
OBSERVE -> RECOMMEND -> SHADOW -> LIMITED -> AUTONOMOUS
```

Each promotion moves exactly one level and requires a fresh evidence window plus
independent administrator approval. Outcomes carry unique run identities,
provenance, evaluation slices, and timestamps. Duplicate, stale, or incomplete
evidence cannot support promotion. A `PromotionRequest` binds the digest of the
complete window, so any change after review makes the request stale. Promotion
clears the window. An `AuthorityCredential` binds agent, level, authority
version, and policy digest.

The credential is only a capability ceiling. Live effects still need Approval
Gate and Blast Radius receipts. A critical incident immediately demotes to
`OBSERVE` and invalidates the old credential. Trusted role resolution governs
both promotion and demotion. Every change becomes an `AuthorityTransition`.

Policy construction also checks that the chain is genuinely progressive:
higher levels retain lower-level actions, live authority limits cannot shrink,
and `AUTONOMOUS` cannot silently remove controls already required by `LIMITED`.
Promotion approval and demotion timestamps must follow the current credential
and request timeline.

## Public interface

| Object | Responsibility |
|---|---|
| `CapabilityProfile` | Actions and limits available at one level |
| `RunOutcome` | One evaluation with identity, provenance, slice, and time |
| `EvidenceWindow` | Outcomes under the current authority version |
| `PromotionRequest` | One-level request bound to an exact evidence window |
| `AuthorityCredential` | Versioned authority evidence |
| `AuthorityTransition` | Versioned promotion or demotion record |
| `ProgressiveCommitment` | Enroll, record, promote, authorize, and demote |

## Run

```bash
python3 governance/c-progressive-commitment/example.py
pytest governance/c-progressive-commitment/test_pattern.py -q
python3 governance/payroll-lab/progressive_commitment_lab.py
python3 governance/payroll-lab/progressive_commitment_lab.py --variant
```

## Where this pattern sits

Govern × Chain. Evidence at the current level is the prerequisite for the next;
levels cannot be skipped and old-version evidence cannot be inherited.
