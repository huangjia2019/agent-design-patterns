"""Invariants for the Prompt Chaining pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    ChainStep,
    ChainTrace,
    PromptChain,
    StepResult,
    all_gate,
    any_gate,
    keys_gate,
    length_gate,
    regex_gate,
)


# ---- Gate factories -------------------------------------------------------


def test_length_gate_bounds() -> None:
    gate = length_gate(5, 10)
    assert gate("hello") is True
    assert gate("hi") is False
    assert gate("way too long here") is False


def test_keys_gate_requires_all() -> None:
    gate = keys_gate(["alpha", "beta"])
    assert gate("alpha and beta both") is True
    assert gate("only alpha") is False


def test_regex_gate_matches_pattern() -> None:
    gate = regex_gate(r"\d{4}-\d{2}-\d{2}")
    assert gate("date: 2026-05-19") is True
    assert gate("no date here") is False


def test_any_gate_or_composition() -> None:
    gate = any_gate(keys_gate(["foo"]), keys_gate(["bar"]))
    assert gate("foo only") is True
    assert gate("bar only") is True
    assert gate("nothing") is False


def test_all_gate_and_composition() -> None:
    gate = all_gate(keys_gate(["foo"]), keys_gate(["bar"]))
    assert gate("foo and bar") is True
    assert gate("foo only") is False


# ---- Chain construction ---------------------------------------------------


def test_empty_chain_rejected() -> None:
    with pytest.raises(ValueError):
        PromptChain(steps=[], llm_call=lambda p, s, m: "")


def test_duplicate_step_ids_rejected() -> None:
    s1 = ChainStep("id-a", "A", "sys", "Hello {user_input}")
    s2 = ChainStep("id-a", "B", "sys", "Hello {user_input}")
    with pytest.raises(ValueError):
        PromptChain(steps=[s1, s2], llm_call=lambda p, s, m: "")


# ---- Happy path -----------------------------------------------------------


def test_single_step_chain_completes() -> None:
    step = ChainStep(
        step_id="echo", description="echo",
        system_prompt="sys", prompt_template="say hi about {user_input}",
    )
    chain = PromptChain([step], llm_call=lambda p, s, m: "hi everyone")
    trace = chain.run("apples")
    assert trace.completed is True
    assert trace.final_output == "hi everyone"
    assert trace.runs[0].result == StepResult.SUCCESS


def test_multi_step_chain_passes_prior_outputs() -> None:
    captured: list[str] = []

    def llm(prompt: str, system: str, model: str) -> str:
        captured.append(prompt)
        if "step1" not in prompt:
            return "first output"
        return "uses: " + prompt

    s1 = ChainStep("step1", "first", "sys", "Q: {user_input}")
    s2 = ChainStep("step2", "second", "sys", "step1={step1}")
    chain = PromptChain([s1, s2], llm_call=llm)
    trace = chain.run("topic")
    assert trace.completed
    # Second prompt should have step1's output embedded.
    assert "first output" in captured[1]


def test_step_sees_all_prior_outputs() -> None:
    # The lecture's information-starvation guard: a downstream step
    # can reference a non-immediate predecessor by id.
    s1 = ChainStep("a", "a", "sys", "{user_input}")
    s2 = ChainStep("b", "b", "sys", "ignore")
    s3 = ChainStep(
        "c", "c", "sys",
        "use both a={a} and b={b}",
    )
    captured = {}

    def llm(prompt, system, model):
        if "step" not in prompt:
            captured["prompt_for_c" if "use both" in prompt else "earlier"] = prompt
        else:
            captured["prompt_for_c" if "use both" in prompt else "earlier"] = prompt
        if "use both" in prompt:
            return "ok"
        if "ignore" in prompt:
            return "b-out"
        return "a-out"

    chain = PromptChain([s1, s2, s3], llm_call=llm)
    trace = chain.run("hello")
    assert trace.completed
    assert "a-out" in captured["prompt_for_c"]
    assert "b-out" in captured["prompt_for_c"]


# ---- Gate retry behavior --------------------------------------------------


def test_gate_failure_retries_up_to_max() -> None:
    attempts: list[int] = []

    def llm(prompt, system, model):
        attempts.append(1)
        return "bad output"

    step = ChainStep(
        step_id="strict", description="strict",
        system_prompt="sys", prompt_template="{user_input}",
        gate=keys_gate(["never-matches-this-key"]),
        gate_description="impossible gate",
        max_retries=2,
    )
    chain = PromptChain([step], llm_call=llm)
    trace = chain.run("anything")
    assert trace.completed is False
    # Initial attempt + 2 retries = 3 attempts.
    assert len(attempts) == 3
    assert trace.runs[-1].result == StepResult.RETRY_EXHAUSTED


def test_gate_success_on_retry_finishes_chain() -> None:
    call_count = [0]

    def llm(prompt, system, model):
        call_count[0] += 1
        # First call returns bad, second returns good.
        return "ok" if call_count[0] >= 2 else "bad"

    step = ChainStep(
        step_id="eventually_ok", description="eventually",
        system_prompt="sys", prompt_template="{user_input}",
        gate=keys_gate(["ok"]),
        gate_description="contains 'ok'",
        max_retries=2,
    )
    chain = PromptChain([step], llm_call=llm)
    trace = chain.run("anything")
    assert trace.completed
    assert call_count[0] == 2


# ---- LLM errors fail fast -------------------------------------------------


def test_llm_error_fails_fast_no_retry() -> None:
    call_count = [0]

    def llm(prompt, system, model):
        call_count[0] += 1
        raise RuntimeError("provider down")

    step = ChainStep("x", "x", "sys", "{user_input}", max_retries=5)
    chain = PromptChain([step], llm_call=llm)
    trace = chain.run("anything")
    assert trace.completed is False
    assert trace.failure_reason and "LLM error" in trace.failure_reason
    # Should not retry past the first error.
    assert call_count[0] == 1


# ---- Missing template keys -----------------------------------------------


def test_missing_template_key_does_not_crash() -> None:
    # The chain stays alive but the model sees a missing-key marker
    # — that's how a downstream debug pass finds the broken wiring.
    s1 = ChainStep("first", "first", "sys", "uses {nonexistent}")
    chain = PromptChain([s1], llm_call=lambda p, s, m: p)
    trace = chain.run("input")
    assert trace.completed
    # The output should carry the missing-key marker.
    assert "missing template key" in trace.final_output


# ---- Trace bookkeeping ---------------------------------------------------


def test_step_outputs_returns_latest_successes() -> None:
    s1 = ChainStep("a", "a", "sys", "{user_input}")
    s2 = ChainStep("b", "b", "sys", "{a}")
    chain = PromptChain([s1, s2], llm_call=lambda p, s, m: f"out-of-{p[:5]}")
    trace = chain.run("hello")
    outputs = trace.step_outputs()
    assert set(outputs.keys()) == {"a", "b"}
