"""Invariants for the Plan-and-Execute pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Executor,
    Plan,
    PlanError,
    PlanStep,
    StepStatus,
    approve,
    release_blocked,
    replan_local,
)


# ---- Plan validation ------------------------------------------------------


def test_unknown_dep_raises() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    plan.add(PlanStep("2", "b", "h", deps=["999"]))
    with pytest.raises(PlanError):
        plan.validate()


def test_cycle_raises() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("a", "A", "h", deps=["b"]))
    plan.add(PlanStep("b", "B", "h", deps=["a"]))
    with pytest.raises(PlanError):
        plan.validate()


def test_valid_dag_does_not_raise() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    plan.add(PlanStep("2", "b", "h", deps=["1"]))
    plan.add(PlanStep("3", "c", "h", deps=["1", "2"]))
    plan.validate()  # no raise


# ---- Ready-step detection ------------------------------------------------


def test_ready_steps_excludes_steps_with_unmet_deps() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    plan.add(PlanStep("2", "b", "h", deps=["1"]))
    ready = plan.ready_steps()
    assert [s.step_id for s in ready] == ["1"]


def test_ready_steps_includes_root_steps_when_deps_done() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    plan.add(PlanStep("2", "b", "h", deps=["1"]))
    plan.steps["1"].status = StepStatus.DONE
    ready = plan.ready_steps()
    assert [s.step_id for s in ready] == ["2"]


def test_ready_steps_excludes_blocked_and_done() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    plan.steps["1"].status = StepStatus.BLOCKED
    assert plan.ready_steps() == []


# ---- Approval gate --------------------------------------------------------


def test_executor_refuses_unapproved_plan() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    with pytest.raises(PlanError):
        Executor({}).run(plan)


def test_approve_sets_token() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "h"))
    approve(plan, "tok-1")
    assert plan.approved
    assert plan.approval_token == "tok-1"


# ---- Execution happy path -------------------------------------------------


def _ok_handler(args, prior):
    return f"ran with prior_keys={list(prior.keys())}"


def test_linear_dag_executes_in_order() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "b", "ok", deps=["1"]))
    plan.add(PlanStep("3", "c", "ok", deps=["2"]))
    approve(plan, "t")
    Executor({"ok": _ok_handler}).run(plan)
    assert all(s.status == StepStatus.DONE for s in plan.steps.values())


def test_parallel_steps_both_run() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "b", "ok"))    # no deps — parallel with 1
    plan.add(PlanStep("3", "c", "ok", deps=["1", "2"]))
    approve(plan, "t")
    Executor({"ok": _ok_handler}).run(plan)
    assert plan.steps["1"].status == StepStatus.DONE
    assert plan.steps["2"].status == StepStatus.DONE
    assert plan.steps["3"].status == StepStatus.DONE


def test_handler_sees_prior_outputs() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "first"))
    plan.add(PlanStep("2", "b", "second", deps=["1"]))
    approve(plan, "t")

    def first(args, prior):
        return {"data": 42}

    captured: dict = {}

    def second(args, prior):
        captured.update(prior)
        return True

    Executor({"first": first, "second": second}).run(plan)
    assert captured == {"1": {"data": 42}}


# ---- Human blocks ---------------------------------------------------------


def test_requires_human_step_blocks_not_runs() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "human", "ok", deps=["1"], requires_human=True))
    plan.add(PlanStep("3", "after", "ok", deps=["2"]))
    approve(plan, "t")
    Executor({"ok": _ok_handler}).run(plan)
    assert plan.steps["1"].status == StepStatus.DONE
    assert plan.steps["2"].status == StepStatus.BLOCKED
    assert plan.steps["3"].status == StepStatus.TODO


def test_release_blocked_unblocks_and_run_completes() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "human", "ok", deps=["1"], requires_human=True))
    plan.add(PlanStep("3", "after", "ok", deps=["2"]))
    approve(plan, "t")
    exec = Executor({"ok": _ok_handler})
    exec.run(plan)
    assert plan.steps["2"].status == StepStatus.BLOCKED
    release_blocked(plan, "2")
    exec.run(plan)
    assert plan.steps["3"].status == StepStatus.DONE


def test_release_blocked_rejects_non_blocked_step() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    with pytest.raises(PlanError):
        release_blocked(plan, "1")


# ---- Failure cascade ------------------------------------------------------


def test_step_failure_skips_downstream() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "explode", "bad", deps=["1"]))
    plan.add(PlanStep("3", "after", "ok", deps=["2"]))
    plan.add(PlanStep("4", "deeper", "ok", deps=["3"]))
    approve(plan, "t")

    def bad(args, prior):
        raise ValueError("boom")

    Executor({"ok": _ok_handler, "bad": bad}).run(plan)
    assert plan.steps["1"].status == StepStatus.DONE
    assert plan.steps["2"].status == StepStatus.FAILED
    assert plan.steps["3"].status == StepStatus.SKIPPED
    assert plan.steps["4"].status == StepStatus.SKIPPED


def test_unknown_handler_marks_failed() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "nonexistent"))
    approve(plan, "t")
    Executor({}).run(plan)
    assert plan.steps["1"].status == StepStatus.FAILED


# ---- Local replan --------------------------------------------------------


def test_replan_local_grafts_new_steps_within_cap() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "fail", "bad", deps=["1"]))
    plan.add(PlanStep("3", "tail", "ok", deps=["2"]))
    approve(plan, "t")

    def bad(args, prior):
        raise ValueError("boom")

    Executor({"ok": _ok_handler, "bad": bad}).run(plan)
    assert plan.steps["2"].status == StepStatus.FAILED

    def replanner(goal):
        new = Plan(goal=goal)
        new.add(PlanStep("2", "retry-fix", "ok", deps=["1"]))
        return new

    replan_local(plan, replanner, failed_step_id="2", cap=5)
    assert plan.steps["2"].handler == "ok"
    # The downstream skipped step is reset to TODO so the next run picks it up.
    assert plan.steps["3"].status == StepStatus.TODO


def test_replan_local_rejects_when_above_cap() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "fail", "bad"))
    approve(plan, "t")

    def bad(args, prior):
        raise ValueError("boom")

    Executor({"bad": bad}).run(plan)

    def big_replanner(goal):
        new = Plan(goal=goal)
        for i in range(20):
            new.add(PlanStep(f"new-{i}", f"step{i}", "ok"))
        return new

    with pytest.raises(PlanError):
        replan_local(plan, big_replanner, failed_step_id="1", cap=5)


# ---- Completion check ----------------------------------------------------


def test_is_complete_false_with_blocked_step() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.steps["1"].status = StepStatus.BLOCKED
    assert plan.is_complete() is False


def test_is_complete_true_when_all_done_or_skipped() -> None:
    plan = Plan(goal="x")
    plan.add(PlanStep("1", "a", "ok"))
    plan.add(PlanStep("2", "b", "ok"))
    plan.steps["1"].status = StepStatus.DONE
    plan.steps["2"].status = StepStatus.SKIPPED
    assert plan.is_complete() is True
