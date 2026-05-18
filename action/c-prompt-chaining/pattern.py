"""Prompt Chaining pattern.

Reference implementation from column lecture 05-04. The claim:
**Unix pipes, ported to LLMs.** A pipeline of single-purpose steps,
each running its own prompt against a model picked for that step,
with a cheap programmatic *gate* between consecutive steps. The
opening story:

A content-editing agent for a financial-news outlet tried to do
seven things in one prompt (proofread, rewrite, restyle, fact-check,
title, summary, image suggestions). It published a piece where the
original "GMV up 35%" became "GMV up 53%" — the rewrite step had
already mutated the source the fact-check step needed. Splitting
the pipeline into seven independent steps + a fact-check gate that
goes back to the *original* source moved the number-check accuracy
from 87% to 99.4%.

The pattern is two classes and one named function:

* `ChainStep` — one prompt step. Carries its own `system_prompt`,
  `model`, output spec, and *gate* (a `Callable[[str], bool]` plus
  `gate_description`). The gate is cheap programmatic code, *not* an
  LLM call. The gate runs after the step's LLM call and either lets
  the output flow downstream or triggers retry.
* `PromptChain` — runs steps in order, passes outputs forward,
  retries on gate failure (bounded), records the trace.
* Two named failure modes from the lecture, called out as gate types:
  `length_gate` and `keys_gate` exist to short-circuit them.

Two named failure modes worth knowing:

* **Information starvation** — Step 3 needs data Step 1 produced,
  but Step 2 didn't pass it through. Track it by giving each step
  access to all *prior* outputs (not just the immediately previous
  one).
* **Gate tyranny** — Gate set too strictly ("exactly 500 words")
  rejects 499 and 501 forever, infinite retry. Gates should describe
  *tolerable* outputs, not perfect ones; the retry budget is the
  safety valve when they don't.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StepResult(Enum):
    SUCCESS = "success"
    GATE_FAILED = "gate_failed"
    LLM_ERROR = "llm_error"
    RETRY_EXHAUSTED = "retry_exhausted"


# An LLM call: takes (prompt, system_prompt, model) → output string.
LLMCallFn = Callable[[str, str, str], str]
# A gate: takes the step's output → True if accepted.
GateFn = Callable[[str], bool]


@dataclass
class ChainStep:
    """One step in the chain.

    `prompt_template` is interpolated with `prior_outputs` and any
    `static_args` at run time. `gate` is a cheap programmatic check
    — *not* an LLM call. If the gate returns False, the chain retries
    up to `max_retries` times before giving up.

    The default gate accepts anything non-empty; a real chain will
    override it with format / length / keyword / schema checks.
    """

    step_id: str
    description: str
    system_prompt: str
    prompt_template: str
    model: str = "claude-sonnet-4-6"
    gate: GateFn = lambda output: bool(output and output.strip())
    gate_description: str = "non-empty"
    max_retries: int = 2
    static_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepRun:
    """The audit record of running one step."""

    step_id: str
    attempt: int
    output: str
    result: StepResult
    gate_description: str
    started_at: str = field(default_factory=_now_iso)
    error: str | None = None


@dataclass
class ChainTrace:
    """Full audit of running a chain."""

    user_input: str
    runs: list[StepRun] = field(default_factory=list)
    final_output: str = ""
    completed: bool = False
    failure_reason: str | None = None

    def step_outputs(self) -> dict[str, str]:
        """Latest successful output per step."""
        out: dict[str, str] = {}
        for run in self.runs:
            if run.result == StepResult.SUCCESS:
                out[run.step_id] = run.output
        return out


class PromptChain:
    """A linear sequence of `ChainStep`s with gates between them.

    Each step sees the user input + every prior step's output. The
    pattern's value is in the *gate between steps*: a cheap check
    that stops bad output from polluting the rest of the chain.
    """

    def __init__(self, steps: list[ChainStep], llm_call: LLMCallFn) -> None:
        if not steps:
            raise ValueError("chain needs at least one step")
        # Step ids must be unique so prior outputs can be referenced by id.
        ids = [s.step_id for s in steps]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate step ids: {ids}")
        self.steps = steps
        self.llm_call = llm_call

    def run(self, user_input: str) -> ChainTrace:
        trace = ChainTrace(user_input=user_input)
        prior: dict[str, str] = {"user_input": user_input}

        for step in self.steps:
            success = False
            for attempt in range(1, step.max_retries + 2):  # initial + retries
                run = self._run_step(step, prior, attempt)
                trace.runs.append(run)
                if run.result == StepResult.SUCCESS:
                    prior[step.step_id] = run.output
                    success = True
                    break
                if run.result == StepResult.LLM_ERROR:
                    # LLM errors don't retry inside the chain — that's the
                    # retry pattern's job. Fail fast here.
                    trace.failure_reason = f"step {step.step_id!r} LLM error: {run.error}"
                    return trace
            if not success:
                trace.failure_reason = (
                    f"step {step.step_id!r} gate {step.gate_description!r} "
                    f"failed after {step.max_retries + 1} attempts"
                )
                # Mark the last run as exhaustion.
                trace.runs[-1].result = StepResult.RETRY_EXHAUSTED
                return trace

        trace.completed = True
        trace.final_output = prior[self.steps[-1].step_id]
        return trace

    def _run_step(self, step: ChainStep, prior: dict[str, str], attempt: int) -> StepRun:
        prompt = self._render(step, prior)
        try:
            output = self.llm_call(prompt, step.system_prompt, step.model)
        except Exception as e:
            return StepRun(
                step_id=step.step_id, attempt=attempt, output="",
                result=StepResult.LLM_ERROR, gate_description=step.gate_description,
                error=f"{type(e).__name__}: {e}",
            )
        if step.gate(output):
            return StepRun(
                step_id=step.step_id, attempt=attempt, output=output,
                result=StepResult.SUCCESS, gate_description=step.gate_description,
            )
        return StepRun(
            step_id=step.step_id, attempt=attempt, output=output,
            result=StepResult.GATE_FAILED, gate_description=step.gate_description,
        )

    @staticmethod
    def _render(step: ChainStep, prior: dict[str, str]) -> str:
        # Templates use {step_id} placeholders + {user_input} +
        # any static_args by name. Missing keys are left as literal
        # placeholders so a debug pass can see exactly what was
        # missing — better than KeyError surprise.
        merged = {**prior, **step.static_args}
        try:
            return step.prompt_template.format(**merged)
        except KeyError as missing:
            return step.prompt_template + f"\n\n[chain: missing template key: {missing}]"


# ---- Common gate factories -------------------------------------------------


def length_gate(min_chars: int, max_chars: int, *, description: str | None = None) -> GateFn:
    """Length-bound gate. The most common gate; also the most prone to
    *gate tyranny* when set too tight."""
    def gate(output: str) -> bool:
        return min_chars <= len(output) <= max_chars
    gate.__name__ = description or f"length[{min_chars}-{max_chars}]"
    return gate


def keys_gate(required_keys: list[str]) -> GateFn:
    """Output must contain all required substrings. Cheap defense
    against *information starvation*."""
    def gate(output: str) -> bool:
        return all(key in output for key in required_keys)
    return gate


def regex_gate(pattern: str) -> GateFn:
    """Output must match a regex pattern."""
    import re
    compiled = re.compile(pattern, re.DOTALL)

    def gate(output: str) -> bool:
        return bool(compiled.search(output))
    return gate


def any_gate(*gates: GateFn) -> GateFn:
    """OR composition — accept if any sub-gate passes."""
    def gate(output: str) -> bool:
        return any(g(output) for g in gates)
    return gate


def all_gate(*gates: GateFn) -> GateFn:
    """AND composition — accept only if every sub-gate passes."""
    def gate(output: str) -> bool:
        return all(g(output) for g in gates)
    return gate
