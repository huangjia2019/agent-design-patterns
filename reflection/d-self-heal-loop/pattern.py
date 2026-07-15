"""Self-Heal Loop pattern.

Reference implementation from column lecture 06-05 (30). The claim:
**a self-heal loop is only as safe as its stopping machinery.** The
loop itself is trivial — red signal, diagnose, patch, re-run. What
separates a production healer from a main-branch incident is the
triple stop: a hard round budget (Aider hardcodes 3), an independent
critic that reviews each patch before it is applied (and specifically
blocks patches that weaken the tests instead of fixing the code), and
a regression check on failure signatures + blast radius that rolls
everything back when "fixing" makes things worse.

Loop topology — the module's only structurally mandatory loop. The
trigger is a deterministic failure signal (test, lint, build, CI), not
the model's opinion of its own output; that external signal is why
this pattern escapes the self-correction trap (LLMs cannot reliably
self-correct by introspection). Exhausted rounds hand off to a human
with the full trace; a healer that cannot fix must never quietly ship
or quietly crash.

Three roles:

* `FailureSignal` — one deterministic red light, with a stable
  signature (same signature = still the same problem) and an
  affected-files list (the blast-radius measure).
* `SelfHealLoop.heal` — the bounded loop: diagnose -> patch -> critic
  gate -> atomic apply -> verify. Every apply is a single revertible
  commit; a regression rolls the whole stack back in reverse order.
* `propose_guard` — the graduation edge: a failure class healed
  repeatedly should stop being healed at runtime and become a
  pre-action guard / regression test (compiled, human-reviewed),
  so next month the same red light never turns on.

Named failure modes:

* **Test cheating** — the patch weakens the test until it passes.
  Closed by the critic checkpoint on what the patch touches.
* **Patch thrashing** — each round changes the error without fixing
  the cause. Surfaced by failure signatures.
* **Blast-radius sprawl** — every round touches more files; the
  original bug is now a mess. Closed by the regression check +
  full rollback.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class FailureSignal:
    kind: str                    # test | lint | build | ci
    error_text: str
    affected_files: list[str] = field(default_factory=list)

    @property
    def signature(self) -> str:
        key = f"{self.kind}|{self.error_text[:200]}"
        return hashlib.sha256(key.encode()).hexdigest()[:10]


@dataclass
class Patch:
    description: str
    touches: list[str]           # files the patch modifies

    @property
    def touches_tests(self) -> bool:
        return any("test" in f for f in self.touches)


@dataclass
class HealRound:
    round_no: int
    failure: FailureSignal
    diagnosis: str
    patch: Patch | None
    commit_id: str | None
    critic_verdict: str          # approved | blocked:<reason> | (none)


@dataclass
class HealTrace:
    rounds: list[HealRound] = field(default_factory=list)
    applied_commits: list[str] = field(default_factory=list)
    rolled_back: list[str] = field(default_factory=list)
    status: str = "pending"
    # fixed | blocked_by_critic | rolled_back_regression | max_rounds_human_handoff


DiagnoseFn = Callable[[FailureSignal], str]
FixFn = Callable[[str], Patch]
# The critic reviews the patch against the failure BEFORE it is applied.
# Returns "" to approve or a reason to block. Production: a different
# model family than the generator (shared blind spots defeat same-family
# review); here deterministic rules stand in.
CriticFn = Callable[[Patch, FailureSignal], str]
ApplyFn = Callable[[Patch], str]                       # -> commit id
VerifyFn = Callable[[], FailureSignal | None]          # None = green
RollbackFn = Callable[[str], None]


class SelfHealLoop:
    def __init__(self, diagnose: DiagnoseFn, fix: FixFn, critic: CriticFn,
                 apply: ApplyFn, verify: VerifyFn, rollback: RollbackFn,
                 max_rounds: int = 3) -> None:
        self.diagnose = diagnose
        self.fix = fix
        self.critic = critic
        self.apply = apply
        self.verify = verify
        self.rollback = rollback
        self.max_rounds = max_rounds

    def heal(self, failure: FailureSignal) -> HealTrace:
        trace = HealTrace()
        baseline_radius = max(len(failure.affected_files), 1)
        for round_no in range(1, self.max_rounds + 1):
            diagnosis = self.diagnose(failure)
            patch = self.fix(diagnosis)

            verdict = self.critic(patch, failure)
            if verdict:
                trace.rounds.append(HealRound(
                    round_no, failure, diagnosis, patch, None,
                    f"blocked:{verdict}"))
                trace.status = "blocked_by_critic"
                return trace                # not applied; a human decides

            commit = self.apply(patch)
            trace.applied_commits.append(commit)
            new_failure = self.verify()
            trace.rounds.append(HealRound(
                round_no, failure, diagnosis, patch, commit, "approved"))

            if new_failure is None:
                trace.status = "fixed"
                return trace

            # Regression check: a DIFFERENT failure with a bigger blast
            # radius means the healer is making things worse. Roll back
            # the entire commit stack, newest first.
            if (new_failure.signature != failure.signature
                    and len(new_failure.affected_files) > 2 * baseline_radius):
                for cid in reversed(trace.applied_commits):
                    self.rollback(cid)
                    trace.rolled_back.append(cid)
                trace.status = "rolled_back_regression"
                return trace

            failure = new_failure

        trace.status = "max_rounds_human_handoff"      # never quietly ship
        return trace


def propose_guard(signature: str, months_seen: list[str],
                  min_recurrence: int = 2) -> dict | None:
    """The graduation edge (lectures 15/25): a failure class healed in
    `min_recurrence`+ separate runs should be compiled into a pre-action
    guard / regression test instead of being re-healed every month.
    Returned as `proposed` — a human review promotes it to enforced.
    One-off flukes stay un-promoted: hardening every heal just piles up
    front-layer checks that misfire."""
    if len(months_seen) < min_recurrence:
        return None
    return {"kind": "regression_test", "trigger_signature": signature,
            "seen_in": months_seen, "status": "proposed"}
