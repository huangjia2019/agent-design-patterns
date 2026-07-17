"""Generate docs/INTERFACE-REGISTRY.md from the pattern.py sources.

Single source of truth for *interfaces* is the code: each pattern's
``pattern.py`` module docstring (the contract) plus its public API.
This script extracts both, adds git state, and writes a generated view.
Never edit INTERFACE-REGISTRY.md by hand — rerun this script instead:

    python3 docs/gen_interface_registry.py

Truth for *coordinates and taxonomy* lives on the ADPS side (the master
control board and the adpsagent.com pattern pages). The COORDINATES map
below is a labeled cache of that source, stamped with its sync date;
on any conflict the ADPS side wins and this map must be resynced.
"""
from __future__ import annotations

import ast
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "INTERFACE-REGISTRY.md"

COORDINATE_SYNC_DATE = "2026-07-16"

# Labeled cache of ADPS canonical coordinates (control board, synced above).
# Format: dir -> (code, name_zh, name_en, coordinate)
COORDINATES: dict[str, tuple[str, str, str, str]] = {
    "perception/a-context-triage": ("P1", "上下文分诊", "Context Triage", "感知 × 路由"),
    "perception/b-semantic-compaction": ("P2", "语义压缩", "Semantic Compaction", "感知 × 链式"),
    "perception/c-progressive-discovery": ("P3", "渐进发现", "Progressive Discovery", "感知 × 循环"),
    "perception/d-multimodal-fusion": ("P4", "多模态融合", "Multi-Modal Fusion", "感知 × 并行"),
    "memory/a-hierarchical-retention": ("M1", "分层保留", "Hierarchical Retention", "记忆 × 层级"),
    "memory/b-rag": ("M2", "RAG", "Retrieval-Augmented Generation", "记忆 × 链式"),
    "memory/c-progress-tracking": ("M3", "进度追踪", "Progress Tracking", "记忆 × 编排"),
    "memory/d-failure-journals": ("M4", "失败日记", "Failure Journals", "记忆 × 循环"),
    "reasoning/a-chain-of-thought": ("R1", "思维链", "Chain-of-Thought", "推理 × 链式"),
    "reasoning/b-complexity-routing": ("R2", "复杂度路由", "Complexity-Based Routing", "推理 × 路由"),
    "reasoning/c-parallel-exploration": ("R3", "并行探索", "Parallel Exploration", "推理 × 并行"),
    "reasoning/d-iterative-hypothesis": ("R4", "迭代假设验证", "Iterative Hypothesis Testing", "推理 × 循环"),
    "action/a-tool-dispatch": ("A1", "工具调度", "Tool Dispatch", "行动 × 路由"),
    "action/b-plan-and-execute": ("A2", "规划执行", "Plan-and-Execute", "行动 × 编排"),
    "action/c-prompt-chaining": ("A3", "提示链", "Prompt Chaining", "行动 × 链式"),
    "action/d-guardrail-sandwich": ("A4", "守卫三明治", "Guardrail Sandwich", "行动 × 层级"),
    "reflection/a-generator-critic": ("F1", "生成批评", "Generator-Critic", "反思 × 链式"),
    "reflection/b-skill-package": ("F2", "技能包", "Skill Package", "反思 × 路由"),
    "reflection/c-experience-replay": ("F3", "经验回放", "Experience Replay", "反思 × 层级"),
    "reflection/d-self-heal-loop": ("F4", "自愈循环", "Self-Heal Loop", "反思 × 循环"),
    "collaboration/a-hierarchical-delegation": ("C1", "层级委派", "Hierarchical Delegation", "协作 × 层级"),
    "collaboration/b-fan-out-gather": ("C2", "扇出聚合", "Fan-out / Gather", "协作 × 并行"),
    "collaboration/c-adversarial-review": ("C3", "对抗评审", "Adversarial Review", "协作 × 循环"),
    "collaboration/d-handoff-chain": ("C4", "交接链", "Handoff Chain", "协作 × 链式"),
}

# Governance patterns are README-only (no reference implementation yet).
GOVERNANCE_PLACEHOLDERS: dict[str, tuple[str, str, str, str]] = {
    "governance/a-approval-gate": ("G1", "审批门", "Approval Gate", "治理 × 路由"),
    "governance/b-blast-radius": ("G2", "爆炸半径控制", "Blast Radius Control", "治理 × 层级"),
    "governance/c-progressive-commitment": ("G3", "渐进承诺", "Progressive Commitment", "治理 × 链式"),
    "governance/d-observability-harness": ("G4", "可观测性", "Observability Harness", "治理 × 编排"),
}

# Standing editorial notes that a reader of the registry must see.
NOTES: dict[str, str] = {
    "memory/b-rag": (
        "Coordinate tension: canonical M2 = 记忆 × 链式 (single cell, fixed "
        "2026-07-09), but this implementation demonstrates the *agentic* "
        "variant (`AgenticRAG.research()` is loop-shaped). The loop variant "
        "is a teaching footnote on the ADPS side; the coordinate stays 链式."
    ),
    "action/a-tool-dispatch": (
        "Also carries A5 最简工具集 (Minimal Tool Set), the extension pattern "
        "folded into Tool Dispatch on the teaching side. (Numbering rule "
        "2026-07-16: core patterns hold 1-4 per row, extensions start at 5.)"
    ),
    "collaboration/c-adversarial-review": (
        "Interface is single-round (run once, gate decides); the canonical "
        "coordinate 协作 × 循环 refers to the review-revise cycle owned by "
        "the outer workflow, mirroring how Generator-Critic keeps its loop "
        "outside the interface."
    ),
}

MODULE_ORDER = ["perception", "memory", "reasoning", "action", "reflection", "collaboration"]
MODULE_ZH = {
    "perception": "感知 Perception",
    "memory": "记忆 Memory",
    "reasoning": "推理 Reasoning",
    "action": "行动 Action",
    "reflection": "反思 Reflection",
    "collaboration": "协作 Collaboration",
}

SHARED_BOUNDARY_INTERFACE = "collaboration/boundary_contract.py"

CONTRACT_MARKERS = (
    "not ", "never", "belongs", "boundary", "must", "only", "does not",
    "outer", "explicit", "cannot", "invariant",
)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def public_api(tree: ast.Module) -> tuple[list[str], list[str]]:
    classes: list[str] = []
    functions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(base) for base in node.bases]
            if any("Enum" in base for base in bases):
                kind = "enum"
            elif any(
                (isinstance(dec, ast.Name) and dec.id == "dataclass")
                or (isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "dataclass")
                for dec in node.decorator_list
            ):
                kind = "dataclass"
            else:
                kind = "class"
            methods = [
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not item.name.startswith("_")
            ]
            suffix = f"({', '.join(methods)})" if methods else ""
            classes.append(f"`{node.name}` *{kind}*{suffix}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                functions.append(f"`{node.name}`")
    return classes, functions


def contract_lines(doc: str) -> list[str]:
    lines = []
    for raw in doc.split("\n"):
        stripped = raw.strip().lstrip("*").strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if any(marker in lowered for marker in CONTRACT_MARKERS):
            lines.append(stripped)
    return lines


def pattern_block(rel_dir: str) -> str:
    code, name_zh, name_en, coordinate = COORDINATES[rel_dir]
    path = ROOT / rel_dir / "pattern.py"
    source = path.read_text()
    tree = ast.parse(source)
    doc = ast.get_docstring(tree) or ""
    classes, functions = public_api(tree)

    last_commit = git("log", "-1", "--format=%h %ad", "--date=format:%Y-%m-%d", "--", f"{rel_dir}/pattern.py")
    dirty = bool(git("status", "--porcelain", "--", f"{rel_dir}/pattern.py"))
    tests = (ROOT / rel_dir / "test_pattern.py").exists()

    out = [f"### {code} {name_zh} {name_en} — `{rel_dir}/`", ""]
    out.append(f"- **Coordinate**: {coordinate}")
    state = f"`pattern.py` {len(source.splitlines())} lines · last commit {last_commit or 'n/a'}"
    state += " · **UNCOMMITTED CHANGES**" if dirty else " · clean"
    state += " · tests: " + ("yes" if tests else "none")
    out.append(f"- **State**: {state}")
    summary = doc.split("\n", 1)[0] if doc else "(no docstring)"
    out.append(f"- **Summary**: {summary}")
    if classes:
        out.append(f"- **Public API**: {'; '.join(classes)}")
    if functions:
        out.append(f"- **Module functions**: {', '.join(functions)}")
    contracts = contract_lines(doc)
    if contracts:
        out.append("- **Contract lines (from docstring)**:")
        out.extend(f"  - {line}" for line in contracts)
    if rel_dir in NOTES:
        out.append(f"- **Note**: {NOTES[rel_dir]}")
    out.append("")
    return "\n".join(out)


def shared_boundary_block() -> str:
    path = ROOT / SHARED_BOUNDARY_INTERFACE
    source = path.read_text()
    tree = ast.parse(source)
    doc = ast.get_docstring(tree) or ""
    classes, functions = public_api(tree)
    last_commit = git(
        "log",
        "-1",
        "--format=%h %ad",
        "--date=format:%Y-%m-%d",
        "--",
        SHARED_BOUNDARY_INTERFACE,
    )
    dirty = bool(git("status", "--porcelain", "--", SHARED_BOUNDARY_INTERFACE))

    out = [
        "### Shared 协作边界契约 Collaboration Boundary Contract",
        "",
        "- **Role**: cross-cutting interface shared by C1-C4; not a fifth pattern",
    ]
    state = (
        f"`boundary_contract.py` {len(source.splitlines())} lines"
        f" · last commit {last_commit or 'n/a'}"
        f" · {'**UNCOMMITTED CHANGES**' if dirty else 'clean'}"
    )
    out.append(f"- **State**: {state}")
    out.append(f"- **Summary**: {doc.split(chr(10), 1)[0]}")
    if classes:
        out.append(f"- **Public API**: {'; '.join(classes)}")
    if functions:
        out.append(f"- **Module functions**: {', '.join(functions)}")
    paragraphs = [" ".join(part.split()) for part in doc.split("\n\n")]
    chain = next((part.strip("`") for part in paragraphs if part.startswith("``")), "")
    invariant = next(
        (part for part in paragraphs if "content-addressed" in part),
        "",
    )
    if chain:
        out.append(f"- **Contract chain**: `{chain}`")
    if invariant:
        out.append(f"- **Version invariant**: {invariant}")
    out.append("")
    return "\n".join(out)


def main() -> None:
    head = git("rev-parse", "--short", "HEAD")
    dirty_any = bool(git("status", "--porcelain"))

    parts = [
        "# Interface Registry",
        "",
        "> **GENERATED FILE — DO NOT EDIT.** Regenerate with"
        " `python3 docs/gen_interface_registry.py`.",
        ">",
        "> **Truth for interfaces** = each pattern's `pattern.py`"
        " (module docstring contract + public API). This file is a view of it.",
        "> **Truth for coordinates and taxonomy** = the ADPS master control"
        " board and the [adpsagent.com](https://adpsagent.com) pattern pages;"
        f" the coordinates below are a labeled cache synced {COORDINATE_SYNC_DATE},"
        " and conflicts resolve toward the ADPS side.",
        ">",
        "> **Citation discipline**: course lectures, whitepapers, and book"
        " chapters that quote an interface must pin the commit"
        " (`pattern.py@<hash>` in the document header). Interfaces do"
        " refactor; a pinned quote stays honest, an unpinned one rots.",
        "",
        f"Generated {date.today().isoformat()} at HEAD `{head}`"
        + (" (working tree has uncommitted changes)" if dirty_any else " (working tree clean)")
        + ".",
        "",
        "## Summary",
        "",
        "| Pattern | Coordinate | Entry point | State |",
        "|:--|:--|:--|:--|",
    ]

    for module in MODULE_ORDER:
        for rel_dir in sorted(d for d in COORDINATES if d.startswith(module + "/")):
            code, name_zh, name_en, coordinate = COORDINATES[rel_dir]
            path = ROOT / rel_dir / "pattern.py"
            tree = ast.parse(path.read_text())
            entry = "—"
            for node in reversed(tree.body):
                if isinstance(node, ast.ClassDef) and not any(
                    "Enum" in ast.unparse(base) for base in node.bases
                ):
                    entry = f"`{node.name}`"
                    break
            dirty = bool(git("status", "--porcelain", "--", f"{rel_dir}/pattern.py"))
            last = git("log", "-1", "--format=%ad", "--date=format:%m-%d", "--", f"{rel_dir}/pattern.py")
            state = f"{last}{' ⚠ dirty' if dirty else ''}"
            parts.append(f"| {code} {name_zh} {name_en} | {coordinate} | {entry} | {state} |")

    shared_last = git(
        "log",
        "-1",
        "--format=%ad",
        "--date=format:%m-%d",
        "--",
        SHARED_BOUNDARY_INTERFACE,
    )
    shared_dirty = bool(
        git("status", "--porcelain", "--", SHARED_BOUNDARY_INTERFACE)
    )
    parts.append(
        "| Shared 协作边界契约 Collaboration Boundary Contract"
        " | 协作横切接口 | `TaskContract` → `AcceptanceReceipt`"
        f" | {shared_last}{' ⚠ dirty' if shared_dirty else ''} |"
    )

    for rel_dir, (code, name_zh, name_en, coordinate) in GOVERNANCE_PLACEHOLDERS.items():
        parts.append(f"| {code} {name_zh} {name_en} | {coordinate} | README only | no impl |")

    parts.append("")

    for module in MODULE_ORDER:
        parts.append(f"## {MODULE_ZH[module]}")
        parts.append("")
        for rel_dir in sorted(d for d in COORDINATES if d.startswith(module + "/")):
            parts.append(pattern_block(rel_dir))
        if module == "collaboration":
            parts.append(shared_boundary_block())

    parts.append("## 治理 Governance (placeholders)")
    parts.append("")
    parts.append(
        "The four governance patterns are README-only: no `pattern.py`,"
        " no interface to register yet. G5 钩子流水线 Hooks Pipeline has no"
        " directory (extension pattern, folded into the governance control"
        " layer on the teaching side)."
    )
    parts.append("")
    for rel_dir, (code, name_zh, name_en, coordinate) in GOVERNANCE_PLACEHOLDERS.items():
        parts.append(f"- {code} {name_zh} {name_en} — {coordinate} — `{rel_dir}/` (README only)")
    parts.append("")
    parts.append("## 组合 Composition")
    parts.append("")
    parts.append(
        "`composition/` holds methodology assets (selection card, six-step"
        " methodology, Argus case, checklist benchmark), not patterns; it is"
        " intentionally outside this registry's pattern list."
    )
    parts.append("")

    OUT.write_text("\n".join(parts))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(parts)} blocks)")


if __name__ == "__main__":
    main()
