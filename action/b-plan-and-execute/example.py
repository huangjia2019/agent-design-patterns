"""Runnable demo for the Plan-and-Execute pattern.

Replays a trimmed version of the HR recruiting agent from the lecture
opening. The original v1 was a ReAct-style free-for-all: 17 tools,
LLM decides each step, average 47 model invocations per candidate,
salary data leaking to hiring managers before interviews, offers
sent before background checks.

The fixed v2 (this example) plans the full pipeline up front:

    1. parse_jd                          ← Phase 1 info gathering
    2. query_team_capacity               ← parallel with 1
    3. query_salary_band                 ← parallel with 1, 2
    4. shortlist_candidates  (deps: 1)
    5. schedule_interview    (deps: 4)
    6. interview_session     (deps: 5)   [HUMAN]
    7. background_check      (deps: 6)
    8. assemble_offer        (deps: 7)
    9. send_offer            (deps: 8)   [HUMAN approval]

The DAG enforces ordering: background_check must DONE before
assemble_offer; assemble_offer must DONE before send_offer.
`interview_session` is `requires_human=True` so the executor
blocks there until a human signs off.

Run:
    python action/b-plan-and-execute/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Executor,
    Plan,
    PlanStep,
    StepStatus,
    approve,
    release_blocked,
)


# --- Handlers — stand-ins for real recruiting tooling -----------------------

def parse_jd(args, prior):
    return {"role": args["role"], "level": "senior", "stack": ["python", "ml"]}


def query_team_capacity(args, prior):
    return {"open_headcount": 1, "team": args["team"]}


def query_salary_band(args, prior):
    return {"min": 280000, "max": 380000, "currency": "CNY"}


def shortlist_candidates(args, prior):
    jd = prior["1"]
    return [
        {"name": "Candidate A", "stack": jd["stack"], "score": 0.92},
        {"name": "Candidate B", "stack": jd["stack"], "score": 0.87},
    ]


def schedule_interview(args, prior):
    short = prior["4"]
    return {"interviews_booked": [c["name"] for c in short[:1]]}


def interview_session(args, prior):
    # Human-in-loop — should not auto-run.
    return None


def background_check(args, prior):
    return {"verified": True, "concerns": []}


def assemble_offer(args, prior):
    band = prior["3"]
    return {
        "candidate": "Candidate A",
        "salary": 340000,
        "salary_within_band": band["min"] <= 340000 <= band["max"],
    }


def send_offer(args, prior):
    offer = prior["8"]
    return {"sent": True, "candidate": offer["candidate"], "amount": offer["salary"]}


HANDLERS = {
    "parse_jd": parse_jd,
    "query_team_capacity": query_team_capacity,
    "query_salary_band": query_salary_band,
    "shortlist_candidates": shortlist_candidates,
    "schedule_interview": schedule_interview,
    "interview_session": interview_session,
    "background_check": background_check,
    "assemble_offer": assemble_offer,
    "send_offer": send_offer,
}


def build_plan() -> Plan:
    plan = Plan(goal="Hire one senior backend engineer for team gravity")
    plan.add(PlanStep("1", "Parse JD", "parse_jd", args={"role": "senior_backend"}))
    plan.add(PlanStep("2", "Query team capacity", "query_team_capacity",
                      args={"team": "gravity"}))
    plan.add(PlanStep("3", "Query salary band", "query_salary_band"))
    plan.add(PlanStep("4", "Shortlist", "shortlist_candidates", deps=["1"]))
    plan.add(PlanStep("5", "Schedule interview", "schedule_interview", deps=["4"]))
    plan.add(PlanStep("6", "Interview (HUMAN)", "interview_session", deps=["5"],
                      requires_human=True))
    plan.add(PlanStep("7", "Background check", "background_check", deps=["6"]))
    plan.add(PlanStep("8", "Assemble offer", "assemble_offer", deps=["3", "7"]))
    plan.add(PlanStep("9", "Send offer", "send_offer", deps=["8"]))
    return plan


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _print_status(plan: Plan) -> None:
    for sid in sorted(plan.steps.keys()):
        s = plan.steps[sid]
        marker = {
            "todo": "·", "doing": ">", "done": "✓",
            "blocked": "⏸", "failed": "✗", "skipped": "—",
        }[s.status.value]
        human = " [HUMAN]" if s.requires_human else ""
        print(f"  {marker} {sid}. {s.description:30s} [{s.status.value}]{human}")


def main() -> None:
    plan = build_plan()
    plan.validate()
    approve(plan, token="hr-approval-2026-05-19")
    executor = Executor(HANDLERS)

    _print_section("Plan (DAG, approved)")
    _print_status(plan)

    _print_section("Phase 1: run until first HUMAN block")
    plan = executor.run(plan)
    _print_status(plan)

    _print_section("Salary band visible at planning, not before offer assembly")
    band = plan.steps["3"].output
    print(f"  step 3 output: salary band {band['min']}–{band['max']} CNY")
    print("  step 8 (assemble offer) consumes it via its `prior` map.")
    print("  No leak path to step 5 (schedule_interview) or step 6 (interview).")

    _print_section("Human signs off on the interview")
    release_blocked(plan, "6")
    print("  step 6 → TODO")

    _print_section("Phase 2: run to completion")
    plan = executor.run(plan)
    _print_status(plan)

    _print_section("Summary")
    done = sum(1 for s in plan.steps.values() if s.status == StepStatus.DONE)
    print(f"  steps completed   : {done}/{len(plan.steps)}")
    final_offer = plan.steps["9"].output
    if final_offer:
        print(f"  offer sent        : {final_offer['candidate']} @ ¥{final_offer['amount']:,}")
    print("  background check before offer: enforced by the DAG (8.deps = [3, 7])")


if __name__ == "__main__":
    main()
