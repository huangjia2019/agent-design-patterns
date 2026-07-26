"""Invariants the Multi-Modal Fusion pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    ModalityInput,
    ModalityType,
    MultiModalFuser,
)


# ───────────────────── invariants ─────────────────────

def test_text_input_passes_through_directly() -> None:
    f = MultiModalFuser()
    result = f.fuse([ModalityInput(type=ModalityType.TEXT, payload="hello")])
    assert result.content[0] == {"type": "text", "text": "hello"}


def test_image_input_emits_image_block_with_base64_payload() -> None:
    f = MultiModalFuser()
    result = f.fuse([ModalityInput(type=ModalityType.IMAGE, payload=b"\x89PNG-data")])
    block = result.content[0]
    assert block["type"] == "image"
    assert block["source"]["type"] == "base64"
    assert block["source"]["data"]   # non-empty base64


def test_table_converts_to_markdown_format() -> None:
    rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    f = MultiModalFuser()
    result = f.fuse([ModalityInput(type=ModalityType.TABLE, payload=rows)])
    md = result.content[0]["text"]
    assert "| a | b |" in md
    assert "| 1 | 2 |" in md
    assert "| 3 | 4 |" in md


def test_pdf_uses_extract_tool_when_provided() -> None:
    calls = []

    def fake_extract(path: str) -> dict:
        calls.append(path)
        return {
            "toc": "1. Intro\n2. Body",
            "key_pages": [{"page": 5, "text": "important content"}],
        }

    f = MultiModalFuser(pdf_extract=fake_extract)
    result = f.fuse([
        ModalityInput(type=ModalityType.PDF, payload="report.pdf", hint="focus = market size"),
    ])
    assert calls == ["report.pdf"]
    text = result.content[0]["text"]
    assert "PDF TOC" in text
    assert "Page 5" in text
    assert "important content" in text
    assert "focus = market size" in text


def test_log_pipeline_uses_filter_then_subagent() -> None:
    seen = {"filter": None, "subagent": None}

    def bash_filter(text: str, hint: str) -> str:
        seen["filter"] = (text, hint)
        return text.replace("noise", "")

    def log_subagent(filtered: str) -> dict:
        seen["subagent"] = filtered
        return {"errors": 3, "pattern": "TimeoutError"}

    f = MultiModalFuser(bash_filter=bash_filter, log_subagent=log_subagent)
    f.fuse([
        ModalityInput(type=ModalityType.LOG, payload="ERROR noise ERROR", hint="db"),
    ])
    assert seen["filter"] == ("ERROR noise ERROR", "db")
    assert seen["subagent"] == "ERROR  ERROR"


def test_sql_result_compacted_with_total_row_marker() -> None:
    rows = [{"id": i, "name": f"row{i}"} for i in range(100)]
    f = MultiModalFuser()
    result = f.fuse([ModalityInput(type=ModalityType.SQL_RESULT, payload=rows)])
    text = result.content[0]["text"]
    assert "| id | name |" in text
    assert "(100 rows total, showing top 30)" in text
    assert "row99" not in text   # truncated to first 30


def test_fusion_trace_emits_one_event_per_input() -> None:
    f = MultiModalFuser(pdf_extract=lambda p: {"toc": ""})
    f.fuse([
        ModalityInput(type=ModalityType.TEXT, payload="a"),
        ModalityInput(type=ModalityType.IMAGE, payload=b"img"),
        ModalityInput(type=ModalityType.TABLE, payload=[{"x": 1}]),
    ])
    assert len(f.events) == 3
    assert [e.modality for e in f.events] == [
        ModalityType.TEXT, ModalityType.IMAGE, ModalityType.TABLE
    ]


def test_total_tokens_estimate_sums_per_modality_tokens() -> None:
    f = MultiModalFuser()
    result = f.fuse([
        ModalityInput(type=ModalityType.TEXT, payload="x" * 400),   # ~100 tokens
        ModalityInput(type=ModalityType.IMAGE, payload=b"img"),     # 1400 tokens
    ])
    expected = sum(e.tokens_out for e in result.fusion_trace)
    assert result.total_tokens_estimate == expected
    assert result.total_tokens_estimate >= 1400   # image alone


def test_health_check_flags_image_token_overshoot() -> None:
    f = MultiModalFuser(image_token_estimate=1400)
    f.fuse([
        ModalityInput(type=ModalityType.TEXT, payload="short"),
        ModalityInput(type=ModalityType.IMAGE, payload=b"img1"),
        ModalityInput(type=ModalityType.IMAGE, payload=b"img2"),
        ModalityInput(type=ModalityType.IMAGE, payload=b"img3"),
    ])
    report = f.health_check()
    assert "image_token_overshoot" in report


def test_keep_as_image_overrides_default_routing() -> None:
    f = MultiModalFuser()
    result = f.fuse([
        # Even if upstream sends as a different type, keep_as_image=True wins
        ModalityInput(type=ModalityType.TEXT, payload=b"\x89PNG", keep_as_image=True),
    ])
    assert result.content[0]["type"] == "image"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
