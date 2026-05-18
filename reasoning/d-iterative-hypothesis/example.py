"""Runnable demo for the Iterative Hypothesis Testing pattern.

Replays the 3 AM chemical plant incident from the lecture opening:
a polyethylene reactor temperature climbs from 80°C (normal) to 92°C
(alarm). The on-call agent posts five candidate hypotheses, ordered
by prior probability:

    H1  78%   cooling-water pump failure
    H2  12%   temperature sensor drift
    H3   5%   feedstock recipe anomaly
    H4   3%   catalyst activity spike
    H5   2%   PID parameters tampered with

The on-call engineer eliminates H1, H2, H3 by checking the
corresponding telemetry — none of them match the live data. H4
requires a 30-minute lab run. Then a fresh observation arrives:
**"there's a remote login at 02:33 modifying the PID logs."** That
piece of evidence resets the tree, the agent re-proposes H5 with
prior 0.95, finds the P-parameter changed from 0.8 to 2.5, confirms
the new prior, and lab returns confirming catalyst activity is normal.

The loop in this file walks through the same sequence. Three Anthropic
three-agent harness functions (planner / generator / evaluator) are
stand-ins so the demo runs without API calls. The planner adds H5
when iteration 2 starts with all other hypotheses falsified.

Run:
    python reasoning/d-iterative-hypothesis/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Hypothesis,
    IterativeHypothesisLoop,
)


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# The five candidate hypotheses, plus the recovery H5' that the planner
# proposes on iteration 2 after the operator surfaces the remote-login
# fact.
INITIAL = [
    ("cooling-water pump failure", 0.78),
    ("temperature sensor drift", 0.12),
    ("feedstock recipe anomaly", 0.05),
    ("catalyst activity spike", 0.03),
]
RECOVERY = [
    ("PID parameters tampered with at 02:33", 0.95),
]


def _planner(problem: str, existing: list[Hypothesis], iteration: int):
    """Iteration 1: propose the four initial hypotheses (sensor team's
    starting list). Iteration 2: once all four are falsified, surface
    the new fact and propose H5'."""
    if iteration == 1:
        return INITIAL
    # If iteration 2 starts with everything falsified, the operator's
    # fresh fact prompts a reset.
    if all(h.status.value == "falsified" for h in existing) and existing:
        return RECOVERY
    return []


def _generator(h: Hypothesis):
    """Returns the diagnostic checks the agent would run for each
    hypothesis. The (description, source) shape mirrors how the
    Generator would log tool calls in production."""
    checks = {
        "cooling-water pump failure": [
            ("cooling-water flow telemetry shows normal 240L/min", "metric:cool_water_flow"),
        ],
        "temperature sensor drift": [
            ("redundant sensor #2 also reads 92°C", "metric:temp_sensor_redundant"),
        ],
        "feedstock recipe anomaly": [
            ("feedstock log for 02:00-03:00 within spec", "log:feedstock"),
        ],
        "catalyst activity spike": [
            ("lab activity assay returns nominal 4.2 mol/g·s", "lab:catalyst_assay"),
        ],
        "PID parameters tampered with at 02:33": [
            ("PID log shows P changed from 0.8 to 2.5 at 02:33 by user 'qa-test'",
             "log:pid_changes"),
        ],
    }
    return checks.get(h.description, [])


def _evaluator(h: Hypothesis, evidence_desc: str, source: str):
    """Decide what each piece of evidence does to the hypothesis.

    The classic falsification framing: if telemetry contradicts the
    hypothesis, that's "refutes" with a hard delta; if telemetry
    matches, that's "supports" with a strong delta.
    """
    desc = h.description.lower()
    ev = evidence_desc.lower()

    if "cooling-water" in desc and "normal" in ev:
        return "refutes", -1.0
    if "sensor drift" in desc and "also reads 92" in ev:
        return "refutes", -1.0
    if "feedstock" in desc and "within spec" in ev:
        return "refutes", -1.0
    if "catalyst" in desc and "nominal" in ev:
        return "refutes", -1.0
    if "pid" in desc and "p changed from 0.8 to 2.5" in ev:
        return "supports", 0.5
    return "neutral", 0.0


def main() -> None:
    loop = IterativeHypothesisLoop(
        planner=_planner,
        generator=_generator,
        evaluator=_evaluator,
        max_iterations=5,
    )

    _print_section("Problem")
    problem = "Polyethylene reactor temperature climbed from 80°C to 92°C at 03:47"
    print(f"  {problem}")

    tree, outcome = loop.run(problem)

    _print_section("Hypothesis tree after the loop")
    for h in tree.hypotheses.values():
        marker = {
            "confirmed": "✓",
            "falsified": "✗",
            "testing": "·",
            "proposed": "·",
            "inconclusive": "?",
        }[h.status.value]
        print(f"  {marker} [{h.status.value:11s}] {h.description}")
        print(f"      prior={h.prior:.2f}  posterior={h.posterior:.2f}  ev={len(h.evidence)}")
        if h.falsified_by:
            print(f"      falsified by: {h.falsified_by}")

    _print_section("Outcome")
    print(f"  converged       : {outcome.converged}")
    print(f"  needs_hitl      : {outcome.needs_hitl}")
    print(f"  iterations_used : {outcome.iterations_used}")
    print(f"  reason          : {outcome.reason}")
    if outcome.confirmed_id:
        confirmed = tree.by_id(outcome.confirmed_id)
        if confirmed:
            print(f"  root cause      : {confirmed.description}")


if __name__ == "__main__":
    main()
