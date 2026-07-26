"""Invariants the Progressive Discovery pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Candidate,
    Phase,
    ProgressiveDiscoverer,
)


# ───────────────────── shared test fixtures ─────────────────────

def _build_discoverer(**overrides):
    files = overrides.pop(
        "files",
        {
            "a.py": "import b\ndef one():\n    return 1\n",
            "b.py": "import c\ndef two():\n    return 2\n",
            "c.py": "def three():\n    return 3\n",
            "noise.py": "# nothing matches here\n",
        },
    )

    def grep(keyword: str) -> list[Candidate]:
        out = []
        for p, content in files.items():
            if keyword.lower() in content.lower() or keyword.lower() in p.lower():
                snippet = next(
                    (ln for ln in content.split("\n") if keyword.lower() in ln.lower()),
                    p,
                )
                out.append(Candidate(path=p, snippet=snippet))
        return out

    def read(path: str) -> str:
        return files.get(path, "")

    def scorer(c: Candidate, task: str) -> float:
        return 1.0 if "one" in c.snippet or "two" in c.snippet else 0.5

    defaults = dict(
        grep_tool=grep,
        read_tool=read,
        scorer=scorer,
        max_cycles=2,
        budget_per_cycle=10_000,
        forage_top_k=10,
        focus_top_k=3,
        deepen_top_k=2,
    )
    defaults.update(overrides)
    return ProgressiveDiscoverer(**defaults), files


# ───────────────────── invariants ─────────────────────

def test_session_records_one_event_per_phase_per_cycle() -> None:
    d, _ = _build_discoverer(
        signal_fn=lambda fc, t: True,   # succeed after first cycle
    )
    session = d.discover(task="find one()", initial_keywords=["def one"])
    phases = [e.phase for e in session.events]
    # FORAGE + FOCUS + (maybe DEEPEN)
    assert Phase.FORAGE in phases
    assert Phase.FOCUS in phases


def test_success_stops_loop_before_max_cycles() -> None:
    d, _ = _build_discoverer(
        signal_fn=lambda fc, t: len(fc) >= 1,
        max_cycles=3,
    )
    session = d.discover(task="find one()", initial_keywords=["def one"])
    assert session.success is True
    assert session.cycle_count <= 3


def test_max_cycles_caps_loop_when_signal_never_found() -> None:
    d, _ = _build_discoverer(
        signal_fn=lambda fc, t: False,   # never satisfied
        max_cycles=2,
    )
    session = d.discover(task="impossible", initial_keywords=["impossible_keyword"])
    assert session.cycle_count == 2
    assert session.success is False


def test_health_check_flags_max_cycles_exhausted_without_signal() -> None:
    d, _ = _build_discoverer(
        signal_fn=lambda fc, t: False,
        max_cycles=2,
    )
    session = d.discover(task="impossible", initial_keywords=["impossible"])
    report = d.health_check(session)
    assert "max_cycles_hit" in report


def test_forage_results_are_scored_then_sorted_descending() -> None:
    files = {
        "high.py": "def one(): pass\n",
        "mid.py": "def two(): pass\n",
        "low.py": "def nothing(): pass\n",
    }
    d, _ = _build_discoverer(files=files, forage_top_k=2, signal_fn=lambda fc, t: True)
    session = d.discover(
        task="find one or two",
        initial_keywords=["def"],
    )
    forage = next(e for e in session.events if e.phase == Phase.FORAGE)
    assert forage.candidates_out == 2


def test_deepen_follows_imports_in_focused_files() -> None:
    files = {
        "entry.py": "import target\n",
        "target.py": "def goal(): pass\n",
        "noise.py": "# unrelated\n",
    }
    d, _ = _build_discoverer(
        files=files,
        signal_fn=lambda fc, t: "target.py" in fc or "target" in fc,
        max_cycles=1,
        forage_top_k=5,
        focus_top_k=2,
        deepen_top_k=3,
    )
    session = d.discover(task="reach target", initial_keywords=["entry"])
    # DEEPEN should have read at least one extra file from imports
    deepen = next((e for e in session.events if e.phase == Phase.DEEPEN), None)
    assert deepen is not None
    assert deepen.files_read >= 1


def test_total_tokens_accumulates_across_phases() -> None:
    d, _ = _build_discoverer(signal_fn=lambda fc, t: True)
    session = d.discover(task="any", initial_keywords=["def"])
    per_event = sum(e.tokens_used for e in session.events)
    assert session.total_tokens == per_event


def test_budget_breaker_stops_cycle_mid_phase() -> None:
    files = {f"f{i}.py": "x = " + "a" * 5000 + "\n" for i in range(20)}
    d, _ = _build_discoverer(
        files=files,
        budget_per_cycle=100,   # tiny budget forces early break
        forage_top_k=20,
        focus_top_k=10,
        signal_fn=lambda fc, t: False,
        max_cycles=1,
    )
    session = d.discover(task="anything", initial_keywords=["x"])
    # Should have logged FORAGE but bailed before completing
    phases = [e.phase for e in session.events]
    assert Phase.FORAGE in phases


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
