"""Lecture 30 hands-on: the payout script goes red, the agent heals it.

Uses the pattern from ../d-self-heal-loop/pattern.py on the payroll
bench. July's payout script fails its reconciliation tests in CI; the
healer diagnoses, patches, re-runs -- bounded by four non-success
outcomes (critic block, no progress, regression, round budget), all
of which restore the transaction ledger before handoff. Three scenes:

    scene 1  convergence: two real defects surface one after the other
             (REVERSED payslips included in the payout, then a stale
             department binding); two rounds, two atomic commits,
             green. The recurring failure class is then proposed as a
             regression-test guard (lecture 25) so next month the same
             red light never turns on.
    scene 2  test cheating: the patch raises the expected total in the
             test instead of fixing the code; the critic checkpoint
             blocks it before apply and hands the case to a human.
    scene 3  run with --meltdown: the same symptom-chasing fixer, first
             in a controlled incident re-enactment (nine overlapping
             edits, no atomic commits, nothing to roll back to), then
             under the bounded stop policy (regression detected after
             round 2 verification, full rollback, clean).

Run `python3 self_heal_lab.py` (add --meltdown for scene 3).
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "d-self-heal-loop"))
from pattern import (  # noqa: E402
    FailureSignal,
    Patch,
    SelfHealLoop,
    propose_guard,
)
import bench  # noqa: E402

MELTDOWN = "--meltdown" in sys.argv

con = bench.month_end_state()
REVERSED_IDS = list(bench.REVERSED_IDS)

# The July payout script, reduced to the two flags its defects live in.
script = {"exclude_reversed": False, "membership_check": False}
TRANSFERS = {"E0012": ("Finance", "Engineering")}


# ---- the deterministic CI: two reconciliation tests --------------------------

def run_ci() -> FailureSignal | None:
    if not script["exclude_reversed"]:
        return FailureSignal(
            "test",
            f"reconcile_payout: payout list includes REVERSED payslips "
            f"{','.join(REVERSED_IDS)}",
            affected_files=["payout.py"],
            code="PAYROLL_REVERSED_IN_PAYOUT",
        )
    if not script["membership_check"]:
        return FailureSignal(
            "test",
            "batch_membership: E0012 bound to stale department Finance",
            affected_files=["batch.py"],
            code="PAYROLL_STALE_DEPARTMENT_BINDING",
        )
    return None


# ---- healer parts: diagnose -> patch -> critic -> atomic apply ---------------

def diagnose(failure: FailureSignal) -> str:
    if "REVERSED" in failure.error_text:
        return "payout builder does not exclude REVERSED payslips"
    if "stale department" in failure.error_text:
        return "batch builder binds by stale dept, no membership check"
    return "unknown"


def fix(diagnosis: str) -> Patch:
    if "REVERSED" in diagnosis:
        return Patch("exclude REVERSED payslips in payout builder",
                     touches=["payout.py"])
    return Patch("verify membership against HR record before binding",
                 touches=["batch.py"])


def cheat_fix(diagnosis: str) -> Patch:
    return Patch("raise expected total in reconcile test to match actual",
                 touches=["tests/test_reconcile.py"])


def critic(patch: Patch, failure: FailureSignal) -> str:
    """Deterministic stand-in for a cross-family reviewer. The one rule
    that matters most in a money path: a red reconciliation test is
    never fixed by editing the test."""
    if patch.touches_tests:
        return "patch weakens the test; the code it guards is unchanged"
    if len(patch.touches) > 2:
        return "patch touches more files than the diagnosis names"
    return ""


COMMITS = []


def apply(patch: Patch) -> str:
    if "exclude REVERSED" in patch.description:
        script["exclude_reversed"] = True
    if "membership" in patch.description:
        script["membership_check"] = True
    cid = f"c{len(COMMITS) + 1}"
    COMMITS.append((cid, patch.description))
    return cid


def rollback(commit_id: str) -> None:
    print(f"      git revert {commit_id}")


def show(trace):
    for r in trace.rounds:
        signal_id = r.failure.code or r.failure.signature
        print(f"   round {r.round_no}: RED  [{signal_id}] {r.failure.error_text}")
        print(f"      diagnosis: {r.diagnosis}")
        print(
            f"      patch: {r.patch.description} "
            f"(id={r.patch.fingerprint}, touches={r.patch.touches})"
        )
        print(f"      critic: {r.critic_verdict}"
              + (f"   applied as {r.commit_id}" if r.commit_id else ""))
    print(f"   status: {trace.status.upper()}")
    if trace.status.value != "fixed":
        print(f"   baseline_restored: {str(trace.baseline_restored).lower()}")


if not MELTDOWN:
    print("== scene 1: two red lights, two rounds, green ==")
    loop = SelfHealLoop(diagnose, fix, critic, apply, run_ci, rollback)
    trace = loop.heal(run_ci())
    show(trace)
    print(f"   CI after heal: {'green' if run_ci() is None else 'still red'}, "
          f"commits {trace.applied_commits} each independently revertible")

    guard = propose_guard(
        signature=trace.rounds[0].failure.signature,
        runs_seen=["teaching-run-2026-06", "teaching-run-2026-07"])
    print("\n   teaching recurrence fixture: same failure class in two runs ->")
    print(f"   propose guard: {guard}")
    print("   (status=proposed: a human review promotes it to enforced;")
    print("    healing rescues this month, the guard blocks next month.)")

    print("\n== scene 2: the cheating patch ==")
    script.update({"exclude_reversed": False, "membership_check": False})
    COMMITS.clear()
    loop = SelfHealLoop(diagnose, cheat_fix, critic, apply, run_ci, rollback)
    trace = loop.heal(run_ci())
    show(trace)
    print("   -> nothing was applied. The reconcile test still guards the")
    print("      money; the case goes to a human with the blocked patch.")

else:
    print("== scene 3 (--meltdown): the incident, then bounded repair ==")
    # The same symptom-chasing fixer, scripted: every round the error
    # mutates and the patch touches more files.
    SPRAWL = [
        ("reconcile_payout: totals off by 19200", ["payout.py"]),
        ("batch_membership: E0012 stale binding", ["payout.py", "batch.py"]),
        ("payslip_render: missing exceptions field",
         ["payout.py", "batch.py", "payslip_gen.py"]),
        ("approvals_join: unknown column",
         ["payout.py", "batch.py", "approvals.py", "db_helpers.py"]),
        ("tax_calc: negative net pay for 3 employees",
         ["payout.py", "tax_calc.py", "payslip_gen.py"]),
        ("reconcile_payout: totals off by 471833",
         ["payout.py", "batch.py", "tax_calc.py"]),
        ("payslip_render: duplicate rows",
         ["payslip_gen.py", "db_helpers.py", "render_utils.py"]),
        ("batch_membership: 14 employees unassigned",
         ["batch.py", "hr_sync.py"]),
        ("reconcile_payout: totals off by 1088412",
         ["payout.py", "batch.py", "tax_calc.py", "payslip_gen.py"]),
    ]
    print("   naive loop (no critic, no signature check, no atomic commits):")
    touched: set = set()
    failure_classes: dict[str, list[int]] = {}
    for n, (err, files) in enumerate(SPRAWL, 1):
        touched.update(files)
        signature = FailureSignal("test", err).signature
        failure_classes.setdefault(signature, []).append(n)
        print(
            f"      round {n}: RED  [{signature}] {err}  -> edit {files}"
        )
    print(f"   after 9 rounds: {len(touched)} files edited in overlapping,")
    print("   non-atomic changes -- payslip_gen.py and tax_calc.py had")
    print("   nothing wrong. There is no clean state to roll back to.")
    print(f"   distinct failure classes: {len(failure_classes)}")
    repeated = [
        (signature, rounds)
        for signature, rounds in failure_classes.items()
        if len(rounds) > 1
    ]
    for signature, rounds in repeated:
        print(f"      repeated class {signature}: rounds {rounds}")

    print("\n   same fixer under the bounded stop policy:")
    sprawl_iter = iter(SPRAWL[1:])

    def sprawl_verify():
        err, files = next(sprawl_iter)
        return FailureSignal("test", err, affected_files=files)

    def sprawl_fix(diagnosis):
        return Patch("chase the symptom", touches=["payout.py"])

    counter = {"n": 0}

    def sprawl_apply(patch):
        counter["n"] += 1
        return f"c{counter['n']}"

    reverted = []
    loop = SelfHealLoop(diagnose, sprawl_fix, critic, apply=sprawl_apply,
                        verify=sprawl_verify, rollback=reverted.append)
    first = FailureSignal("test", SPRAWL[0][0], affected_files=SPRAWL[0][1])
    trace = loop.heal(first)
    show(trace)
    print(f"      rolled back, newest first: {reverted}")
    print("   -> a different failure with a bigger blast radius is a")
    print("      regression: everything applied is reverted, newest first.")
    print("      Two rounds of damage, fully undone, instead of nine")
    print("      overlapping edits with nothing to revert to.")
