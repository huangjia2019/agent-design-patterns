"""Lecture 29 hands-on: June's fall becomes July's background.

Uses the pattern from ../c-experience-replay/pattern.py on the payroll
bench. June's settlement ended with a saga rollback (E0007/E0012
REVERSED, lecture 22); the L1 lesson distilled from that trace says:
verify an employee's CURRENT department against the HR record before
binding them into a department batch. Three scenes:

    scene 1  recall changes the decision: July's batch build runs twice,
             once bare (a transferred employee lands in the old
             department's batch, totals balance, nobody notices) and
             once inside the recalled context layer (membership check
             applied, the employee is re-routed)
    scene 2  the external signal at work: six months of reuse outcomes
             flow back; the superstitious lesson ("June worked because
             we exported the report twice first") sinks below the
             health line and is archived, while the membership lesson
             builds the track record that qualifies it to graduate
             into a pre-action guard
    scene 3  run with --no-feedback: nobody writes reuse outcomes back;
             in month 7 the superstitious lesson is still being
             injected, and the real lesson still has no track record

Run `python3 experience_replay_lab.py` (add --no-feedback for scene 3).
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "c-experience-replay"))
from pattern import Experience, ExperienceStore  # noqa: E402
import bench  # noqa: E402

NO_FEEDBACK = "--no-feedback" in sys.argv

con = bench.month_end_state()

# The HR record: E0012 transferred at the end of June. The employees
# table still carries the stale department -- exactly the mismatch that
# broke June's batch.
TRANSFERS = {"E0012": ("Finance", "Engineering")}


def current_dept(emp_id: str, stale_dept: str) -> str:
    return TRANSFERS.get(emp_id, (None, stale_dept))[1]


# ---- seed the store: June's L1 entries ---------------------------------------

store = ExperienceStore(top_k=3)

june_lesson = store.record(Experience(
    exp_id="2026-06-batch-fail",
    task_kind="cross-dept-batch",
    outcome="failure",
    lesson="before binding an employee into a department batch, verify "
           "current membership against the HR record (June: stale dept "
           "broke the batch, saga rollback, E0007/E0012 reversed)",
    keywords=["batch", "department", "payment", "membership", "build"],
    steps=["build_payment_batch:Finance", "transfer_salary:E0012 -> TIMEOUT",
           "rollback_session:2026-06"]))

for month in ("2026-04", "2026-05"):
    store.record(Experience(
        exp_id=f"{month}-batch-ok", task_kind="cross-dept-batch",
        outcome="success",
        lesson="department batches built after a membership pass ran clean",
        keywords=["batch", "department", "payment", "build", "monthly"]))

# Enough similar L1 entries: distill the L2 heuristic.
heuristic = store.distill("cross-dept-batch")

superstition = store.record(Experience(
    exp_id="2026-06-report-ritual",
    task_kind="monthly-report",
    outcome="success",
    lesson="June closed clean because the report was exported twice "
           "before paying (mis-attributed cause)",
    keywords=["report", "monthly", "export", "settlement"]))


# ---- the July task, run bare and run inside the recalled layer --------------

def build_batches(apply_membership_check: bool):
    batches: dict[str, list[str]] = {}
    rerouted = []
    for emp_id, stale in con.execute("SELECT emp_id, dept FROM employees"):
        dept = stale
        if apply_membership_check:
            dept = current_dept(emp_id, stale)
            if dept != stale:
                rerouted.append((emp_id, stale, dept))
        batches.setdefault(dept, []).append(emp_id)
    return batches, rerouted


def misbound(batches) -> list[str]:
    return [e for e, (_, new) in TRANSFERS.items()
            if e in batches.get(TRANSFERS[e][0], [])]


if not NO_FEEDBACK:
    print("== scene 1: recall changes the decision ==")
    task = "2026-07 build department payment batch"

    batches, _ = build_batches(apply_membership_check=False)
    print(f"   bare run: {sum(len(v) for v in batches.values())} employees "
          f"bound into {len(batches)} batches")
    print(f"   mis-bound (stale department, totals still balance): {misbound(batches)}")

    hits = store.retrieve(task)
    print("\n   with replay -- the context layer this run executes under:")
    for line in store.render(hits).splitlines():
        print(f"      {line}")
    batches, rerouted = build_batches(apply_membership_check=True)
    for emp, old, new in rerouted:
        print(f"   membership check: {emp} re-routed {old} -> {new}")
    print(f"   mis-bound: {misbound(batches)}")

    print("\n== scene 2: reuse outcomes write back, six months ==")
    # Deterministic monthly reconciliation signals. Batch months succeed
    # whenever the membership lesson is in context (it is, all six).
    # Report months succeed or fail on data issues the export ritual
    # has nothing to do with.
    batch_outcomes = [True, True, True, True, True, True]
    report_outcomes = [True, False, True, False, False, True]
    for m, (b_ok, r_ok) in enumerate(zip(batch_outcomes, report_outcomes), 1):
        gone = store.feedback([june_lesson], b_ok)
        gone += store.feedback([superstition], r_ok)
        line = (f"   month {m}: membership eff={june_lesson.effectiveness:.2f}"
                f"   ritual eff={superstition.effectiveness:.2f}")
        if gone:
            line += f"   -> archived: {gone}"
        print(line)

    print(f"\n   ritual lesson archived={superstition.archived} "
          f"after {superstition.reuses} reuses below the health line")
    grads = store.graduation_candidates()
    print(f"   graduation candidates: {[e.exp_id for e in grads]}")
    print("   -> membership consistency is deterministically checkable and has")
    print("      a proven track record: compile it into a pre-action guard")
    print("      (lecture 25's GuardRegistry) and retire the soft lesson.")
    print("   Same signal, both directions: reuse outcomes archived the")
    print("   superstition and qualified the real lesson to graduate.")

else:
    print("== scene 3 (--no-feedback): nobody writes outcomes back ==")
    for month in range(1, 7):
        store.retrieve("2026-07 monthly report export settlement")
    print(f"   six months later: ritual eff={superstition.effectiveness:.2f} "
          f"(still neutral), archived={superstition.archived}")
    hits = store.retrieve("2026-07 monthly report export settlement")
    print("   month 7 context still contains:")
    for line in store.render(hits).splitlines():
        print(f"      {line}")
    print(f"   membership lesson: reuses={june_lesson.reuses}, "
          f"eff={june_lesson.effectiveness:.2f} -- no track record,")
    print("   so it can never qualify to graduate into a guard either.")
    print("   Without reuse outcomes the store cannot tell a mis-attributed")
    print("   cause from a real one; both just sit there, occupying context.")
