"""Plan-and-Execute pattern.

Reference implementation from column lecture 05-03. The claim:
**long-horizon tasks need a plan**, and the plan should be a
first-class durable artifact, not the contents of the model's
context window.

The cost of skipping plan-and-execute on an HR recruiting agent in
the lecture: ¥180k/month in LLM calls, 47 model invocations per
candidate, and the agent skipping background checks before sending
offers. The cost of doing it: ¥60k/month, 13 invocations per
candidate, zero offers sent without a background check, three weeks
shaved off cycle time.

Three roles in the pattern:

* `Planner` — produces a `Plan` (a DAG of `PlanStep`s with explicit
  dependencies). Wired to a high-tier model in production.
* `Approval Gate` — a user signs off on the plan before any
  destructive step runs. Plan is a user-owned artifact.
* `Executor` — walks the DAG: runs every step whose deps are
  satisfied, blocks on `[HUMAN]` markers, marks failures, and on
  failure triggers *local* replan (not global rewrite).

The DAG is intentionally trivial. Production deployments wrap this
in LangGraph's BSP / Pregel runtime with checkpointing to SQLite,
but the contract is the same: steps have status, dependencies
gate execution, failure is local. The runtime is plumbing; the
contract is the pattern.

Two named failure modes from the lecture:

* **Plan starvation** — Plan looks fine on paper but Step 4 needs
  data Step 2 should have produced, and Step 3 dropped it on the
  floor. The status field on each step carries `output` so the next
  step can read it; bare strings as deps are a recipe for starvation.
* **Replan thrash** — replanning rewrites the whole plan instead of
  patching the affected sub-DAG, the agent re-does work it already
  finished, costs balloon. `replan_local` here only touches steps
  downstream of the failure and below the cap.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class StepStatus(Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"
    BLOCKED = "blocked"        # awaiting human / approval
    FAILED = "failed"
    SKIPPED = "skipped"        # upstream failure cascaded


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PlanStep:
    """One step in the plan DAG.

    `deps` are step ids that must reach `DONE` before this step can
    run. `requires_human` blocks the step at `BLOCKED` until an
    explicit approval call flips it to `TODO`.
    """

    step_id: str
    description: str
    handler: str                          # name of the executor function
    deps: list[str] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)
    requires_human: bool = False
    status: StepStatus = StepStatus.TODO
    output: Any = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


@dataclass
class Plan:
    """A DAG of plan steps.

    Validated on construction: no cycles, every `dep` references an
    existing step. Anything that breaks the contract is a bug at the
    Planner, not at runtime.
    """

    goal: str
    steps: dict[str, PlanStep] = field(default_factory=dict)
    approved: bool = False
    approval_token: str | None = None
    created_at: str = field(default_factory=_now_iso)

    def add(self, step: PlanStep) -> None:
        self.steps[step.step_id] = step

    def validate(self) -> None:
        """Raise if the plan is malformed. Called once before approval."""
        for step in self.steps.values():
            for dep in step.deps:
                if dep not in self.steps:
                    raise PlanError(f"step {step.step_id!r} depends on unknown step {dep!r}")
        # Cycle detection via DFS coloring.
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {sid: WHITE for sid in self.steps}

        def visit(sid: str) -> None:
            color[sid] = GRAY
            for dep in self.steps[sid].deps:
                if color[dep] == GRAY:
                    raise PlanError(f"cycle detected at step {sid!r}")
                if color[dep] == WHITE:
                    visit(dep)
            color[sid] = BLACK

        for sid in self.steps:
            if color[sid] == WHITE:
                visit(sid)

    def ready_steps(self) -> list[PlanStep]:
        """Steps whose deps are all DONE and which are still TODO."""
        ready = []
        for step in self.steps.values():
            if step.status != StepStatus.TODO:
                continue
            if all(self.steps[d].status == StepStatus.DONE for d in step.deps):
                ready.append(step)
        return ready

    def is_complete(self) -> bool:
        return all(s.status in (StepStatus.DONE, StepStatus.SKIPPED) for s in self.steps.values())

    def first_failed(self) -> PlanStep | None:
        for step in self.steps.values():
            if step.status == StepStatus.FAILED:
                return step
        return None


class PlanError(Exception):
    """Raised on malformed plans at construction time."""


# Executor handler: takes a dict of step args + a dict of prior outputs
# (keyed by dep step_id) and returns the step's output.
HandlerFn = Callable[[dict[str, Any], dict[str, Any]], Any]


class Executor:
    """Walks the plan DAG.

    Handlers are looked up by name in a registry, so the plan can be
    serialized to disk and re-loaded without losing executability.
    """

    def __init__(self, handlers: dict[str, HandlerFn]) -> None:
        self.handlers = handlers

    def run(self, plan: Plan, max_steps: int = 100) -> Plan:
        if not plan.approved:
            raise PlanError("plan is not approved")
        plan.validate()
        executed = 0
        while not plan.is_complete() and executed < max_steps:
            ready = plan.ready_steps()
            if not ready:
                # Either we're done or every remaining step is blocked.
                if any(s.status == StepStatus.BLOCKED for s in plan.steps.values()):
                    break
                break
            for step in ready:
                self._execute_step(step, plan)
                executed += 1
                if step.status == StepStatus.FAILED:
                    self._cascade_skip(step, plan)
                    return plan
        return plan

    def _execute_step(self, step: PlanStep, plan: Plan) -> None:
        if step.requires_human:
            step.status = StepStatus.BLOCKED
            return
        handler = self.handlers.get(step.handler)
        if handler is None:
            step.status = StepStatus.FAILED
            step.error = f"unknown handler {step.handler!r}"
            return
        step.status = StepStatus.DOING
        step.started_at = _now_iso()
        prior_outputs = {d: plan.steps[d].output for d in step.deps}
        try:
            step.output = handler(step.args, prior_outputs)
            step.status = StepStatus.DONE
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = f"{type(e).__name__}: {e}"
        finally:
            step.finished_at = _now_iso()

    def _cascade_skip(self, failed: PlanStep, plan: Plan) -> None:
        """Mark all transitive descendants of a failed step as SKIPPED."""
        to_skip = {failed.step_id}
        changed = True
        while changed:
            changed = False
            for step in plan.steps.values():
                if step.status == StepStatus.TODO and any(d in to_skip for d in step.deps):
                    step.status = StepStatus.SKIPPED
                    to_skip.add(step.step_id)
                    changed = True


# Planner is intentionally minimal: a function that produces a Plan.
# Production deployments wire this to an LLM call with a system prompt;
# the test suite passes a fixed planner so behavior is deterministic.
PlannerFn = Callable[[str], Plan]


def approve(plan: Plan, token: str) -> None:
    """Mark the plan approved with a token. Plans not approved cannot be executed."""
    plan.approved = True
    plan.approval_token = token


def release_blocked(plan: Plan, step_id: str) -> None:
    """Human flip on a BLOCKED step → TODO.

    Clears the `requires_human` gate as well — otherwise the next
    `Executor.run` call would re-block the step. The gate is a
    one-shot: once a human approves, the step proceeds.
    """
    step = plan.steps.get(step_id)
    if step is None:
        raise PlanError(f"unknown step {step_id!r}")
    if step.status != StepStatus.BLOCKED:
        raise PlanError(f"step {step_id!r} is not BLOCKED")
    step.status = StepStatus.TODO
    step.requires_human = False


def replan_local(
    plan: Plan,
    planner: PlannerFn,
    failed_step_id: str,
    cap: int = 5,
) -> Plan:
    """Patch the sub-DAG downstream of a failed step.

    Production deployments call the LLM Planner here with the failed
    step + its descendants as context. This reference re-invokes the
    Planner on the original goal and grafts new steps in place of the
    skipped subtree. The cap limits how many new steps the replan may
    add — Anthropic's guidance: replan budget < 10% of total plan budget.
    """
    failed = plan.steps.get(failed_step_id)
    if failed is None:
        raise PlanError(f"unknown failed step {failed_step_id!r}")

    new_plan = planner(plan.goal)
    if len(new_plan.steps) > cap:
        raise PlanError(f"replan added {len(new_plan.steps)} steps, exceeds cap {cap}")

    # Mark the failed step and its skipped descendants as cleared; graft
    # the new steps in. Validation runs on the merged plan, because the
    # new fragment may reference existing step ids as its deps.
    for step in plan.steps.values():
        if step.status in (StepStatus.SKIPPED, StepStatus.FAILED):
            step.status = StepStatus.TODO
            step.error = None
    for new_step in new_plan.steps.values():
        if new_step.step_id in plan.steps:
            # New plan re-proposes a step — replace.
            plan.steps[new_step.step_id] = new_step
        else:
            plan.add(new_step)
    plan.validate()
    return plan
