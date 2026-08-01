"""Shared deterministic fixture contract for the Self-Heal notebooks."""
from __future__ import annotations

import ast
import copy
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import BaseModel, ConfigDict, Field

HERE = Path(__file__).parent
LANGGRAPH_NOTEBOOK = HERE / "langgraph" / "tutorial.ipynb"
LANGGRAPH_MARKDOWN = HERE / "langgraph" / "tutorial.md"
LANGGRAPH_HTML = HERE / "langgraph" / "tutorial.html"
LANGCHAIN_NOTEBOOK = HERE / "langchain" / "tutorial.ipynb"
LANGCHAIN_MARKDOWN = HERE / "langchain" / "tutorial.md"
LANGCHAIN_HTML = HERE / "langchain" / "tutorial.html"
GRAPH_ALT = "Self-Heal transaction with bounded repair loop and compensation path"
LANGCHAIN_GRAPH_ALT = (
    "Self-Heal LCEL model roles, transaction boundary, and terminal branch"
)
PATTERN_SOURCE = HERE / "pattern.py"
sys.path.insert(0, str(HERE))
sys.modules.pop("pattern", None)
sys.modules.pop("shared", None)

from pattern import (  # noqa: E402
    ApplyReceipt,
    FailureSignal,
    HealStage,
    HealStatus,
    Patch,
    PatchReview,
    SelfHealLoop,
)
from shared import (  # noqa: E402
    RECORD_FIELDS,
    SCENARIO_ORDER,
    assert_expected_record,
    format_scenario_matrix,
    format_scenario_walkthrough,
    new_runtime,
    parse_diagnosis_json,
    parse_patch_json,
    run_core_reference,
    trace_record,
)

CANONICAL_NOTEBOOK_IMPORTS = {
    "pattern": sys.modules["pattern"],
    "shared": sys.modules["shared"],
}


def run_core(name: str) -> tuple[dict[str, object], object]:
    trace, runtime = run_core_reference(name)
    return trace_record(name, trace), runtime


def notebook_data(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def code_source(path: Path) -> str:
    data = notebook_data(path)
    return "\n".join(
        "".join(cell["source"])
        for cell in data["cells"]
        if cell["cell_type"] == "code"
    )


def markdown_source(path: Path) -> str:
    data = notebook_data(path)
    return "\n".join(
        "".join(cell["source"])
        for cell in data["cells"]
        if cell["cell_type"] == "markdown"
    )


def saved_text_output(path: Path) -> str:
    chunks: list[str] = []
    for cell in notebook_data(path)["cells"]:
        for output in cell.get("outputs", []):
            if output["output_type"] == "stream":
                chunks.append("".join(output.get("text", [])))
            elif output["output_type"] in {"display_data", "execute_result"}:
                chunks.append(
                    "".join(output.get("data", {}).get("text/plain", []))
                )
            elif output["output_type"] == "error":
                chunks.append(f"{output.get('ename', '')}: {output.get('evalue', '')}")
    return "\n".join(chunks)


STRUCTURED_BOUNDARY_SYMBOLS = {
    "DiagnosisOutput",
    "PatchPayload",
    "PatchOutput",
    "_parsed_structured",
    "build_structured_role_models",
    "parse_structured_diagnosis",
    "parse_structured_patch",
}


def structured_boundary_namespace(path: Path) -> dict[str, object]:
    """Load only the notebook's real-model schema boundary for focused tests."""
    definitions: list[ast.stmt] = []
    for cell in notebook_data(path)["cells"]:
        if cell["cell_type"] != "code":
            continue
        tree = ast.parse("".join(cell["source"]), filename=str(path))
        definitions.extend(
            node
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef))
            and node.name in STRUCTURED_BOUNDARY_SYMBOLS
        )
    namespace = {
        "BaseModel": BaseModel,
        "ConfigDict": ConfigDict,
        "Field": Field,
        "json": json,
        "Patch": Patch,
        "parse_diagnosis_json": parse_diagnosis_json,
        "parse_patch_json": parse_patch_json,
    }
    module = ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[]))
    exec(compile(module, str(path), "exec"), namespace)
    namespace["PatchOutput"].model_rebuild(_types_namespace=namespace)
    return namespace


def assert_sections_in_order(markdown: str, headings: tuple[str, ...]) -> None:
    positions = [markdown.index(heading) for heading in headings]
    assert positions == sorted(positions)


def langgraph_namespace() -> dict[str, object]:
    """Load the notebook's real graph code without executing demo/output cells."""
    module = ModuleType("self_heal_langgraph_test")
    sys.modules[module.__name__] = module
    namespace = module.__dict__
    displaced = {
        name: sys.modules.get(name)
        for name in CANONICAL_NOTEBOOK_IMPORTS
    }
    sys.modules.update(CANONICAL_NOTEBOOK_IMPORTS)
    try:
        data = notebook_data(LANGGRAPH_NOTEBOOK)
        for cell in data["cells"]:
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell["source"])
            if (
                "langgraph_records = []" in source
                or "model = get_model()" in source
                or "format_scenario_walkthrough(_record_named(" in source
                or "len(langgraph_records)} scenarios matched" in source
            ):
                continue
            if "graph = build_self_heal_graph()" in source:
                tree = ast.parse(source, filename=str(LANGGRAPH_NOTEBOOK))
                definitions = [
                    node
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                tree = ast.Module(body=definitions, type_ignores=[])
                exec(compile(tree, str(LANGGRAPH_NOTEBOOK), "exec"), namespace)
                continue
            exec(compile(source, str(LANGGRAPH_NOTEBOOK), "exec"), namespace)
    finally:
        for name, previous in displaced.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
    return namespace


class ImageAltParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_alts: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "img":
            self.image_alts.append(dict(attrs).get("alt"))


def install_competing_pattern_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reproduce a later-collected sibling test replacing the short module name."""
    competing = ModuleType("pattern")
    monkeypatch.setitem(sys.modules, "pattern", competing)
    source = PATTERN_SOURCE.read_text(encoding="utf-8")
    exec(compile(source, str(PATTERN_SOURCE), "exec"), competing.__dict__)


def test_trace_record_uses_approved_ten_field_schema() -> None:
    """An extra notebook record field would break the approved comparison contract."""
    record, _runtime = run_core("convergence")
    expected = (
        "scenario",
        "status",
        "stop_reason",
        "baseline_digest",
        "final_digest",
        "baseline_restored",
        "apply_receipts",
        "verification_receipts",
        "rollback_receipts",
        "stage_errors",
    )

    assert RECORD_FIELDS == expected
    assert tuple(record) == expected


def test_scenario_order_is_the_literal_locked_matrix() -> None:
    """Fixture insertion order cannot silently redefine the approved curriculum."""
    assert SCENARIO_ORDER == (
        "convergence",
        "critic_block",
        "no_progress",
        "regression",
        "round_budget",
        "stage_error",
        "rollback_failure",
    )


def deterministic_records() -> list[dict[str, object]]:
    return [run_core(name)[0] for name in SCENARIO_ORDER]


def test_compact_scenario_matrix_surfaces_outcomes_without_raw_digests() -> None:
    records = deterministic_records()

    rendered = format_scenario_matrix(records)
    lines = rendered.splitlines()

    assert len(lines) == len(SCENARIO_ORDER) + 2
    assert all(name in rendered for name in SCENARIO_ORDER)
    assert "status" in lines[0]
    assert "apply" in lines[0]
    assert "verify" in lines[0]
    assert "rollback" in lines[0]
    assert "restored" in lines[0]
    assert "c2 -> c1" in rendered
    assert "c1 (failed)" in rendered
    assert max(map(len, lines)) <= 160
    for record in records:
        for field in ("baseline_digest", "final_digest"):
            digest = record[field]
            if isinstance(digest, str):
                assert digest not in rendered


@pytest.mark.parametrize(
    "name",
    ("convergence", "no_progress", "rollback_failure"),
)
def test_scenario_walkthrough_is_short_and_receipt_bound(name: str) -> None:
    record, _runtime = run_core(name)

    rendered = format_scenario_walkthrough(record)
    lines = rendered.splitlines()
    expected_receipt_lines = {
        "convergence": (
            "round 1: apply c1 patch dda1f6b5; verification failed e7e8a9de",
            "round 2: apply c2 patch f3926b7d; verification passed",
        ),
        "no_progress": (
            "round 1: apply c1 patch 7bbc2763; verification failed 1e0be10a",
            "rollback c1: succeeded",
        ),
        "rollback_failure": (
            "round 1: apply c1 patch bd0a4ab7; verification failed c924ae82",
            "rollback c1: failed",
        ),
    }

    assert name in rendered
    assert record["status"] in rendered
    assert record["stop_reason"] in rendered
    assert all(line in lines for line in expected_receipt_lines[name])
    assert len(lines) <= 12
    assert max(map(len, lines)) <= 120
    assert not any(
        isinstance(value, str) and len(value) == 64 and value in rendered
        for value in record.values()
    )


def test_critic_block_is_a_second_round_rejection_after_one_apply() -> None:
    """The critic contrast must compensate c1, not reject before any mutation."""
    trace, runtime = run_core_reference("critic_block")
    record = trace_record("critic_block", trace)

    assert [item["commit_id"] for item in record["apply_receipts"]] == ["c1"]
    assert [item["commit_id"] for item in record["verification_receipts"]] == ["c1"]
    assert [item["commit_id"] for item in record["rollback_receipts"]] == ["c1"]
    assert len(trace.rounds) == 2
    assert trace.rounds[0].apply_receipt is trace.apply_receipts[0]
    assert trace.rounds[1].patch_review is not None
    assert trace.rounds[1].patch_review.approved is False
    assert trace.rounds[1].apply_receipt is None
    assert runtime.workspace.rollback_attempts == ["c1"]
    assert record["baseline_restored"] is True
    assert record["baseline_digest"] == record["final_digest"]


def test_langgraph_notebook_has_required_contract_surface() -> None:
    """Removing a required stage or tutorial section breaks the executable contract."""
    data = notebook_data(LANGGRAPH_NOTEBOOK)
    code = code_source(LANGGRAPH_NOTEBOOK)
    markdown = markdown_source(LANGGRAPH_NOTEBOOK)

    assert data["metadata"]["kernelspec"]["name"] == "python3"
    for marker in ("shared.py", "model_config.py", "nbtools.py"):
        assert marker in code
    for node in (
        "capture_baseline",
        "diagnose",
        "draft_patch",
        "duplicate_guard",
        "review",
        "apply",
        "verify",
        "decide",
        "rollback",
        "finalize",
    ):
        assert f'add_node("{node}"' in code
    assert "StateGraph" in code
    assert "add_conditional_edges" in code
    assert "show_graph" in code
    assert "for scenario_name in SCENARIO_ORDER" in code
    assert "assert record == core_record" in code
    assert "FakeListChatModel" not in code
    assert "FakeMessagesListChatModel" not in code
    assert "diagnosis_model, patch_model = build_structured_role_models(model)" in code
    assert "../langchain/tutorial.ipynb" in markdown
    assert_sections_in_order(
        markdown,
        (
            "# Self-Heal Loop with LangGraph",
            "## What this pattern does",
            "## Setup",
            "## Transaction state",
            "## Build the graph",
            "## Deterministic scenarios",
            "## Optional real model",
            "## What to remember",
            "## Further reading",
        ),
    )


def test_langgraph_saved_output_is_bounded_and_interpretable() -> None:
    output = saved_text_output(LANGGRAPH_NOTEBOOK)

    assert all(name in output for name in SCENARIO_ORDER)
    assert "7 scenarios matched the sealed core across all 10 public fields" in output
    assert '"apply_receipts"' not in output
    assert '"baseline_digest"' not in output
    assert re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", output) is None
    assert max(map(len, output.splitlines())) <= 180
    assert len(output) <= 5_000


def test_langchain_saved_output_is_bounded_and_interpretable() -> None:
    output = saved_text_output(LANGCHAIN_NOTEBOOK)

    assert all(name in output for name in SCENARIO_ORDER)
    assert "7 scenarios matched the sealed core across all 10 public fields" in output
    assert '"apply_receipts"' not in output
    assert '"baseline_digest"' not in output
    assert re.search(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", output) is None
    assert max(map(len, output.splitlines())) <= 180
    assert len(output) <= 5_000


def test_langchain_notebook_has_required_contract_surface() -> None:
    data = notebook_data(LANGCHAIN_NOTEBOOK)
    code = code_source(LANGCHAIN_NOTEBOOK)
    markdown = markdown_source(LANGCHAIN_NOTEBOOK)

    assert data["metadata"]["kernelspec"]["name"] == "python3"
    for marker in ("shared.py", "model_config.py", "nbtools.py"):
        assert marker in code
    for symbol in (
        "FakeListChatModel",
        "ChatPromptTemplate",
        "RunnableLambda",
        "RunnableBranch",
        "SelfHealLoop",
        "diagnose_pipe",
        "draft_pipe",
        "show_graph",
    ):
        assert symbol in code
    assert "for scenario_name in SCENARIO_ORDER" in code
    assert ".with_retry(" not in code
    assert "assert record == core_record" in code
    assert "diagnose_pipe, draft_pipe = build_structured_role_pipes(model)" in code
    assert "../langgraph/tutorial.ipynb" in markdown
    assert_sections_in_order(
        markdown,
        (
            "# Self-Heal Loop with LangChain",
            "## What this pattern does",
            "## Setup",
            "## LCEL pipeline",
            "## Deterministic scenarios",
            "## Optional real model",
            "## What to remember",
            "## Further reading",
        ),
    )


def test_notebooks_share_scenario_order_and_record_schema() -> None:
    for path in (LANGGRAPH_NOTEBOOK, LANGCHAIN_NOTEBOOK):
        code = code_source(path)
        assert "for scenario_name in SCENARIO_ORDER" in code
        assert "record = trace_record(" in code
        assert "assert_expected_record(record)" in code

    assert RECORD_FIELDS == (
        "scenario",
        "status",
        "stop_reason",
        "baseline_digest",
        "final_digest",
        "baseline_restored",
        "apply_receipts",
        "verification_receipts",
        "rollback_receipts",
        "stage_errors",
    )


@pytest.mark.parametrize(
    "path",
    (LANGGRAPH_NOTEBOOK, LANGCHAIN_NOTEBOOK),
    ids=("langgraph", "langchain"),
)
def test_real_model_boundary_uses_native_schema_then_strict_parser(path: Path) -> None:
    """Provider parsing must not replace canonical patch validation."""
    namespace = structured_boundary_namespace(path)
    diagnosis_schema = namespace["DiagnosisOutput"]
    payload_schema = namespace["PatchPayload"]
    patch_schema = namespace["PatchOutput"]
    calls: list[tuple[str, dict[str, object]]] = []

    class StructuredOutputSpy:
        def with_structured_output(self, schema, **kwargs):
            calls.append((schema.__name__, kwargs))
            return schema

    diagnosis_model, patch_model = namespace["build_structured_role_models"](
        StructuredOutputSpy()
    )

    assert diagnosis_model is diagnosis_schema
    assert patch_model is patch_schema
    assert calls == [
        ("DiagnosisOutput", {"method": "json_schema", "include_raw": True}),
        ("PatchOutput", {"method": "json_schema", "include_raw": True}),
    ]

    diagnosis = diagnosis_schema(diagnosis="repair the failing branch")
    assert namespace["parse_structured_diagnosis"](
        {"raw": object(), "parsed": diagnosis, "parsing_error": None}
    ) == "repair the failing branch"

    patch_output = patch_schema(
        description="repair branch",
        payload=payload_schema(set={"app.py": "fixed"}),
        touches=["app.py"],
    )
    assert namespace["parse_structured_patch"](
        {"raw": object(), "parsed": patch_output, "parsing_error": None}
    ) == Patch(
        "repair branch",
        '{"set":{"app.py":"fixed"}}',
        ("app.py",),
    )

    mismatched = patch_schema(
        description="repair branch",
        payload=payload_schema(set={"app.py": "fixed"}),
        touches=["other.py"],
    )
    with pytest.raises(ValueError, match="strict validation failed"):
        namespace["parse_structured_patch"](
            {"raw": object(), "parsed": mismatched, "parsing_error": None}
        )

    blank_diagnosis = diagnosis_schema(diagnosis=" ")
    with pytest.raises(
        ValueError, match="DiagnosisOutput strict validation failed"
    ) as exc_info:
        namespace["parse_structured_diagnosis"](
            {"raw": object(), "parsed": blank_diagnosis, "parsing_error": None}
        )
    assert exc_info.value.__cause__ is None

    sensitive_error = "RAW_PROVIDER_MESSAGE_SHOULD_NOT_ESCAPE"
    with pytest.raises(ValueError, match="structured parsing failed") as exc_info:
        namespace["parse_structured_patch"](
            {
                "raw": {"content": sensitive_error},
                "parsed": None,
                "parsing_error": ValueError(sensitive_error),
            }
        )
    assert sensitive_error not in str(exc_info.value)
    assert exc_info.value.__cause__ is None

    sensitive_path = f"{sensitive_error}\\secret"
    invalid_path = patch_schema(
        description="repair branch",
        payload=payload_schema(set={sensitive_path: "fixed"}),
        touches=[sensitive_path],
    )
    with pytest.raises(ValueError, match="strict validation failed") as exc_info:
        namespace["parse_structured_patch"](
            {"raw": object(), "parsed": invalid_path, "parsing_error": None}
        )
    assert sensitive_error not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_langgraph_structured_parse_error_redacts_provider_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model parse failure must hand off without serializing raw provider data."""
    monkeypatch.chdir(LANGGRAPH_NOTEBOOK.parent)
    graph_namespace = langgraph_namespace()
    boundary = structured_boundary_namespace(LANGGRAPH_NOTEBOOK)
    runtime = new_runtime("convergence")
    baseline = dict(runtime.workspace.files)
    sensitive_error = "RAW_PROVIDER_MESSAGE_SHOULD_NOT_ESCAPE"

    def rejected_draft(_diagnosis: str) -> Patch:
        return boundary["parse_structured_patch"](
            {
                "raw": {"content": sensitive_error},
                "parsed": None,
                "parsing_error": ValueError(sensitive_error),
            }
        )

    completed = graph_namespace["build_self_heal_graph"]().invoke(
        {
            "runtime": runtime,
            "initial_failure": runtime.scenario.initial_failure,
            "diagnose_role": runtime.diagnose,
            "draft_role": rejected_draft,
        },
        {"recursion_limit": 64},
    )
    trace = completed["trace"]
    serialized = json.dumps(trace_record("redacted_parse_error", trace))

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:fix"
    assert trace.apply_receipts == ()
    assert trace.baseline_restored is True
    assert runtime.workspace.files == baseline
    assert sensitive_error not in serialized
    assert trace.stage_errors[-1].message == "PatchOutput structured parsing failed"


def test_langgraph_strict_structured_validation_redacts_provider_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strict patch rejection must not serialize provider-controlled field values."""
    monkeypatch.chdir(LANGGRAPH_NOTEBOOK.parent)
    graph_namespace = langgraph_namespace()
    boundary = structured_boundary_namespace(LANGGRAPH_NOTEBOOK)
    runtime = new_runtime("convergence")
    baseline = dict(runtime.workspace.files)
    sensitive_error = "RAW_PROVIDER_MESSAGE_SHOULD_NOT_ESCAPE"
    sensitive_path = f"{sensitive_error}\\secret"
    payload_schema = boundary["PatchPayload"]
    patch_schema = boundary["PatchOutput"]
    invalid_path = patch_schema(
        description="repair branch",
        payload=payload_schema(set={sensitive_path: "fixed"}),
        touches=[sensitive_path],
    )

    def rejected_draft(_diagnosis: str) -> Patch:
        return boundary["parse_structured_patch"](
            {"raw": object(), "parsed": invalid_path, "parsing_error": None}
        )

    completed = graph_namespace["build_self_heal_graph"]().invoke(
        {
            "runtime": runtime,
            "initial_failure": runtime.scenario.initial_failure,
            "diagnose_role": runtime.diagnose,
            "draft_role": rejected_draft,
        },
        {"recursion_limit": 64},
    )
    trace = completed["trace"]
    serialized = json.dumps(trace_record("redacted_strict_error", trace))

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:fix"
    assert trace.apply_receipts == ()
    assert trace.baseline_restored is True
    assert runtime.workspace.files == baseline
    assert sensitive_error not in serialized
    assert trace.stage_errors[-1].message == "PatchOutput strict validation failed"


@pytest.mark.parametrize("bad_evidence", [None, "character-by-character"])
def test_langgraph_malformed_review_evidence_fails_closed(
    bad_evidence: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed review evidence must become public error proof, not escape the graph."""
    monkeypatch.chdir(LANGGRAPH_NOTEBOOK.parent)
    install_competing_pattern_module(monkeypatch)
    namespace = langgraph_namespace()
    graph = namespace["build_self_heal_graph"]()
    runtime = new_runtime("critic_block")

    def malformed_review(patch: Patch, _failure: object) -> PatchReview:
        receipt = object.__new__(PatchReview)
        object.__setattr__(receipt, "patch_digest", patch.digest)
        object.__setattr__(receipt, "approved", True)
        object.__setattr__(receipt, "reason", "")
        object.__setattr__(receipt, "evidence", bad_evidence)
        return receipt

    runtime.review = malformed_review  # type: ignore[method-assign]
    completed = graph.invoke(
        {
            "runtime": runtime,
            "initial_failure": runtime.scenario.initial_failure,
            "diagnose_role": runtime.diagnose,
            "draft_role": runtime.fix,
        },
        {"recursion_limit": 64},
    )
    trace = completed["trace"]

    assert trace.status is HealStatus.STAGE_ERROR_HUMAN_HANDOFF
    assert trace.stop_reason == "stage_error:review"
    assert trace.baseline_restored is True
    assert trace.rollback_receipts == ()
    assert any(error.stage is HealStage.REVIEW for error in trace.stage_errors)


def test_langgraph_mixed_review_evidence_matches_core_predicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One nonblank evidence item is valid in both orchestrators."""
    monkeypatch.chdir(LANGGRAPH_NOTEBOOK.parent)
    namespace = langgraph_namespace()

    def mixed_review(patch: Patch, _failure: FailureSignal) -> PatchReview:
        return PatchReview(patch.digest, True, "", ("", "policy=mixed", " "))

    graph_runtime = new_runtime("convergence")
    graph_runtime.review = mixed_review  # type: ignore[method-assign]
    completed = namespace["build_self_heal_graph"]().invoke(
        {
            "runtime": graph_runtime,
            "initial_failure": graph_runtime.scenario.initial_failure,
            "diagnose_role": graph_runtime.diagnose,
            "draft_role": graph_runtime.fix,
        },
        {"recursion_limit": 64},
    )

    core_runtime = new_runtime("convergence")
    core_trace = SelfHealLoop(
        diagnose=core_runtime.diagnose,
        fix=core_runtime.fix,
        review=mixed_review,
        apply=core_runtime.workspace.apply,
        verify=core_runtime.verify,
        rollback=core_runtime.workspace.rollback,
        state_digest=core_runtime.workspace.state_digest,
        stability=core_runtime.scenario.stability,
    ).heal(core_runtime.scenario.initial_failure)

    graph_record = trace_record("convergence", completed["trace"])
    core_record = trace_record("convergence", core_trace)
    assert graph_record == core_record
    assert graph_record["status"] == HealStatus.FIXED.value


@pytest.mark.parametrize(
    "candidate",
    [
        Patch(
            "write outside the failure scope",
            '{"set":{"outside.py":"unrelated"}}',
            ("outside.py",),
        ),
        Patch(
            "replace the right file with the wrong behavior",
            '{"set":{"app.py":"semantically-wrong"}}',
            ("app.py",),
        ),
    ],
    ids=("out-of-scope", "semantically-wrong"),
)
def test_langgraph_rejects_unsafe_model_patch_before_apply(
    candidate: Patch,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A canonical model patch still needs deterministic scope and semantic policy."""
    monkeypatch.chdir(LANGGRAPH_NOTEBOOK.parent)
    namespace = langgraph_namespace()
    runtime = new_runtime("convergence")
    baseline = dict(runtime.workspace.files)

    completed = namespace["build_self_heal_graph"]().invoke(
        {
            "runtime": runtime,
            "initial_failure": runtime.scenario.initial_failure,
            "diagnose_role": runtime.diagnose,
            "draft_role": lambda _diagnosis: candidate,
        },
        {"recursion_limit": 64},
    )
    trace = completed["trace"]

    assert trace.status is HealStatus.BLOCKED_BY_CRITIC
    assert trace.stop_reason == "review_rejected"
    assert trace.apply_receipts == ()
    assert trace.rollback_receipts == ()
    assert trace.baseline_restored is True
    assert runtime.workspace.files == baseline


def test_scenario_verification_reads_workspace_before_claiming_green() -> None:
    """The scripted green result must be gated by the actual reviewed state."""
    runtime = new_runtime("convergence")
    first_patch = runtime.fix(runtime.diagnose(runtime.scenario.initial_failure))
    assert runtime.review(first_patch, runtime.scenario.initial_failure).approved is True
    first_receipt = runtime.workspace.apply(first_patch)
    first_verification = runtime.verify(first_receipt)
    assert first_verification.failure is not None

    second_patch = runtime.fix(runtime.diagnose(first_verification.failure))
    assert runtime.review(second_patch, first_verification.failure).approved is True
    forged_apply = ApplyReceipt("c2", second_patch.digest, second_patch.touches)

    verification = runtime.verify(forged_apply)

    assert verification.failure is not None
    assert verification.failure.code.startswith("STATE_MISMATCH")


def test_langgraph_markdown_export_has_informative_graph_alt() -> None:
    """The Markdown reader must receive the graph description, not a format label."""
    parser = ImageAltParser()
    parser.feed(LANGGRAPH_MARKDOWN.read_text(encoding="utf-8"))
    assert GRAPH_ALT in parser.image_alts


def test_langgraph_html_export_has_informative_graph_alt() -> None:
    """The HTML reader must receive the graph description, not nbconvert fallback text."""
    parser = ImageAltParser()
    parser.feed(LANGGRAPH_HTML.read_text(encoding="utf-8"))
    assert GRAPH_ALT in parser.image_alts


def test_langchain_markdown_export_has_informative_graph_alt() -> None:
    """The Markdown reader must receive the LCEL graph's real description."""
    parser = ImageAltParser()
    parser.feed(LANGCHAIN_MARKDOWN.read_text(encoding="utf-8"))
    assert LANGCHAIN_GRAPH_ALT in parser.image_alts


def test_langchain_html_export_has_informative_graph_alt() -> None:
    """The HTML reader must receive the LCEL graph's real description."""
    parser = ImageAltParser()
    parser.feed(LANGCHAIN_HTML.read_text(encoding="utf-8"))
    assert LANGCHAIN_GRAPH_ALT in parser.image_alts


@pytest.mark.parametrize("name", SCENARIO_ORDER)
def test_core_fixture_matches_expected_record(name: str) -> None:
    """A scenario drift must change its independently locked observable record."""
    record, _runtime = run_core(name)
    assert tuple(record) == RECORD_FIELDS
    assert_expected_record(record)


@pytest.mark.parametrize("name", SCENARIO_ORDER)
def test_scenario_runtime_carries_locked_name_without_changing_core(name: str) -> None:
    """The explicit fixture label must identify the same approved core behavior."""
    runtime = new_runtime(name)
    record, _core_runtime = run_core(name)

    assert runtime.scenario.name == name
    assert_expected_record(record)


def test_scenario_runtime_is_fresh_per_run() -> None:
    """Reusing mutable scenario state would leak an earlier repair into a new run."""
    first = new_runtime("convergence")
    first.workspace.files["leak.py"] = "changed"

    second = new_runtime("convergence")

    assert "leak.py" not in second.workspace.files
    assert second.workspace.snapshots == {}
    assert second.workspace.rollback_attempts == []


def test_regression_compensates_newest_first() -> None:
    """Reversing compensation would restore the wrong snapshot sequence."""
    record, runtime = run_core("regression")

    assert [item["commit_id"] for item in record["rollback_receipts"]] == [
        "c2",
        "c1",
    ]
    assert runtime.workspace.rollback_attempts == ["c2", "c1"]
    assert record["baseline_digest"] == record["final_digest"]


def test_rollback_failure_never_claims_restoration() -> None:
    """A failed compensation receipt must not be reported as baseline restoration."""
    record, _runtime = run_core("rollback_failure")

    assert record["status"] == HealStatus.ROLLBACK_FAILED_HUMAN_HANDOFF.value
    assert record["stop_reason"] == "review_rejected"
    assert record["baseline_restored"] is False
    assert record["baseline_digest"] != record["final_digest"]


@pytest.mark.parametrize(
    "forgery",
    [
        "failed_rollback",
        "rollback_digest_mismatch",
        "blank_rollback_detail",
        "verification_digest_mismatch",
        "blank_apply_digest",
    ],
)
def test_expected_record_rejects_forged_or_misbound_receipt_chain(
    forgery: str,
) -> None:
    """A plausible commit order is insufficient without full receipt binding."""
    scenario = (
        "regression"
        if "rollback" in forgery
        else "convergence"
    )
    record, _runtime = run_core(scenario)
    forged = copy.deepcopy(record)
    if forgery == "failed_rollback":
        forged["rollback_receipts"][0]["succeeded"] = False
    elif forgery == "rollback_digest_mismatch":
        forged["rollback_receipts"][0]["patch_digest"] = forged[
            "apply_receipts"
        ][0]["patch_digest"]
    elif forgery == "blank_rollback_detail":
        forged["rollback_receipts"][0]["detail"] = " "
    elif forgery == "verification_digest_mismatch":
        forged["verification_receipts"][0]["patch_digest"] = forged[
            "apply_receipts"
        ][1]["patch_digest"]
    else:
        forged["apply_receipts"][0]["patch_digest"] = ""

    with pytest.raises(AssertionError):
        assert_expected_record(forged)


def test_diagnosis_parser_accepts_only_exact_nonblank_schema() -> None:
    """Relaxing the model schema could admit ambiguous or unusable diagnoses."""
    assert parse_diagnosis_json('{"diagnosis":"failing branch"}') == "failing branch"
    for raw in (
        "not json",
        "{}",
        '{"diagnosis":""}',
        '{"diagnosis":"x","approved":true}',
        '{"diagnosis":"x","diagnosis":"y"}',
        '{"diagnosis":1}',
    ):
        with pytest.raises((TypeError, ValueError, json.JSONDecodeError)):
            parse_diagnosis_json(raw)


def test_patch_parser_fails_closed_before_apply() -> None:
    """Accepting noncanonical or mismatched patches would alter patch identity."""
    raw = json.dumps(
        {
            "description": "repair branch",
            "payload": json.dumps(
                {"set": {"app.py": "fixed"}},
                sort_keys=True,
                separators=(",", ":"),
            ),
            "touches": ["app.py"],
        }
    )
    assert parse_patch_json(raw) == Patch(
        "repair branch",
        '{"set":{"app.py":"fixed"}}',
        ("app.py",),
    )

    invalid = (
        "not json",
        json.dumps(
            {
                "description": "",
                "payload": '{"set":{"app.py":"fixed"}}',
                "touches": ["app.py"],
            }
        ),
        '{"description":"x","payload":"{}","touches":["app.py"]}',
        json.dumps(
            {
                "description": "x",
                "payload": '{ "set": {"app.py": "fixed"} }',
                "touches": ["app.py"],
            }
        ),
        json.dumps(
            {
                "description": "x",
                "payload": '{"set":{"app.py":"fixed"}}',
                "touches": ["../app.py"],
            }
        ),
        json.dumps(
            {
                "description": "x",
                "payload": '{"set":{"app.py":"fixed"}}',
                "touches": ["other.py"],
            }
        ),
    )
    for candidate in invalid:
        with pytest.raises((TypeError, ValueError, json.JSONDecodeError)):
            parse_patch_json(candidate)
