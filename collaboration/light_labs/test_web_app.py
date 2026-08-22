"""Contract tests for the lightweight collaboration Web workbench."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import web_app  # noqa: E402


def test_every_lesson_builds_a_json_serializable_comparison() -> None:
    for lesson_id in ("32", "33", "34", "35", "B1"):
        payload = web_app.build_comparison(lesson_id)
        assert payload["lesson"] == lesson_id
        assert payload["baseline"]["tone"] == "danger"
        assert payload["pattern"]["tone"] == "success"
        assert payload["baseline"]["trace"]
        assert payload["pattern"]["trace"]
        json.dumps(payload, ensure_ascii=False)


def test_unknown_lesson_is_rejected() -> None:
    try:
        web_app.build_comparison("99")
    except KeyError as exc:
        assert exc.args == ("99",)
    else:
        raise AssertionError("unknown lessons must fail loudly")


def test_ui_assets_exist() -> None:
    assert (web_app.UI_ROOT / "index.html").is_file()
    assert (web_app.UI_ROOT / "app.js").is_file()
    assert (web_app.UI_ROOT / "styles.css").is_file()
