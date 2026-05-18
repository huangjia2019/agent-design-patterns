"""Invariants the Hierarchical Retention pattern must preserve."""
from __future__ import annotations

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    DEFAULT_LAYERS,
    HierarchicalRetention,
    Layer,
)


# ───────────────────── invariants ─────────────────────

def _new() -> HierarchicalRetention:
    return HierarchicalRetention("u1", "p1", "s1")


def test_write_then_read_returns_value_and_source_layer() -> None:
    mem = _new()
    mem.write(Layer.USER, "name", "alice")
    val, layer = mem.read("name")
    assert val == "alice"
    assert layer == Layer.USER


def test_read_missing_key_returns_none_pair() -> None:
    mem = _new()
    assert mem.read("nothing") == (None, None)


def test_inner_layer_overrides_outer_for_same_key() -> None:
    mem = _new()
    mem.write(Layer.USER, "pref", "OOP")
    mem.write(Layer.SESSION, "pref", "functional")
    val, layer = mem.read("pref")
    assert val == "functional"
    assert layer == Layer.SESSION


def test_turn_overrides_session_overrides_project_overrides_user() -> None:
    mem = _new()
    mem.write(Layer.USER, "k", "u")
    mem.write(Layer.PROJECT, "k", "p")
    mem.write(Layer.SESSION, "k", "s")
    mem.write(Layer.TURN, "k", "t")
    assert mem.read("k") == ("t", Layer.TURN)


def test_assemble_prompt_context_renders_outer_to_inner_order() -> None:
    mem = _new()
    mem.write(Layer.USER, "a", 1)
    mem.write(Layer.SESSION, "b", 2)
    text = mem.assemble_prompt_context()
    user_idx = text.find("USER CONTEXT")
    session_idx = text.find("SESSION CONTEXT")
    assert 0 <= user_idx < session_idx


def test_assemble_skips_empty_layers() -> None:
    mem = _new()
    mem.write(Layer.SESSION, "b", 2)
    text = mem.assemble_prompt_context()
    assert "SESSION CONTEXT" in text
    assert "USER CONTEXT" not in text
    assert "PROJECT CONTEXT" not in text


def test_expired_turn_layer_is_skipped_during_read() -> None:
    mem = HierarchicalRetention(
        "u", "p", "s",
        layer_config={
            Layer.USER:    {"backend": "pg", "ttl_seconds": None, "token_budget": 2000},
            Layer.PROJECT: {"backend": "fs", "ttl_seconds": None, "token_budget": 4000},
            Layer.SESSION: {"backend": "rd", "ttl_seconds": 100,  "token_budget": 8000},
            Layer.TURN:    {"backend": "mm", "ttl_seconds": 1,    "token_budget": 2000},
        },
    )
    mem.write(Layer.USER, "k", "u")
    mem.write(Layer.TURN, "k", "t")
    time.sleep(1.1)
    val, layer = mem.read("k")
    assert val == "u"
    assert layer == Layer.USER


def test_evict_expired_clears_layer_and_reports_name() -> None:
    mem = HierarchicalRetention(
        "u", "p", "s",
        layer_config={
            **DEFAULT_LAYERS,
            Layer.TURN: {"backend": "mm", "ttl_seconds": 1, "token_budget": 2000},
        },
    )
    mem.write(Layer.TURN, "x", 1)
    time.sleep(1.1)
    evicted = mem.evict_expired()
    assert "turn" in evicted
    assert mem.layers[Layer.TURN].content == {}


def test_health_report_lists_all_four_layers_with_backend_and_ttl() -> None:
    mem = _new()
    mem.write(Layer.USER, "k", "v")
    report = mem.health_report()
    assert set(report["layers"].keys()) == {"user", "project", "session", "turn"}
    assert report["layers"]["user"]["items"] == 1
    assert report["layers"]["user"]["backend"] == "postgres"
    assert report["layers"]["session"]["ttl_seconds"] == 86_400


def test_custom_layer_config_overrides_defaults() -> None:
    mem = HierarchicalRetention(
        "u", "p", "s",
        layer_config={
            Layer.USER:    {"backend": "custom-pg", "ttl_seconds": None,  "token_budget": 500},
            Layer.PROJECT: {"backend": "custom-fs", "ttl_seconds": None,  "token_budget": 500},
            Layer.SESSION: {"backend": "custom-rd", "ttl_seconds": 60,    "token_budget": 500},
            Layer.TURN:    {"backend": "custom-mm", "ttl_seconds": 10,    "token_budget": 500},
        },
    )
    assert mem.layers[Layer.USER].backend == "custom-pg"
    assert mem.layers[Layer.SESSION].ttl_seconds == 60


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
