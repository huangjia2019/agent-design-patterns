"""28-pattern Two-Axis Matrix · English version

Renders the canonical 7 cognitive functions × 6 execution topologies matrix
into the agent-design-patterns repo's `docs/` directory.

Source of truth for placements: `01-Agent设计模式之美/v4/final/01-范式觉醒/
pictures/01-02/render_matrix_28.py` in the private content repo. English
labels mirror the Manning Ch2 Table 2.11 pattern names.
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["DejaVu Sans", "Liberation Sans", "Arial"]
rcParams["axes.unicode_minus"] = False

BG = "#0a1628"
BG_DARK = "#07101e"
DIM = "#1a2942"
GREY = "#3a4a62"
WHITE = "#ffffff"
MUTED = "#c7d4e8"
CYAN = "#00d4ff"

ROWS = ["Perceive", "Remember", "Reason", "Act", "Reflect", "Collaborate", "Govern"]
# Canonical column order (matches ZH render_matrix_28_orchestrate_right): Orchestrate moved to rightmost.
COLS = ["Chain", "Route", "Parallel", "Loop", "Hierarchy", "Orchestrate"]

ROW_COLORS = {
    0: "#00d4ff",   # Perceive
    1: "#9b7dff",   # Remember
    2: "#ffa500",   # Reason
    3: "#2ecc71",   # Act
    4: "#ffd700",   # Reflect
    5: "#f89fc4",   # Collaborate
    6: "#e74c3c",   # Govern
}

# (row, col, English name, lecture code)
# Column order: 0 Chain, 1 Route, 2 Parallel, 3 Loop, 4 Hierarchy, 5 Orchestrate
PATTERNS = [
    # Perceive (row 0)
    (0, 0, "Semantic Compaction",        "02-03"),
    (0, 1, "Context Triage",             "02-02"),
    (0, 2, "Multi-Modal Fusion",         "02-05"),
    (0, 3, "Progressive Discovery",      "02-04"),
    # Remember (row 1)
    (1, 0, "RAG",                        "03-03"),
    (1, 3, "Failure Journals",           "03-05"),
    (1, 4, "Hierarchical Retention",     "03-02"),
    (1, 5, "Progress Tracking",          "03-04"),
    # Reason (row 2)
    (2, 0, "Chain of Thought",           "04-02"),
    (2, 1, "Complexity Routing",         "04-03"),
    (2, 2, "Parallel Exploration",       "04-04"),
    (2, 3, "Iterative Hypothesis",       "04-05"),
    # Act (row 3)
    (3, 0, "Prompt Chaining",            "05-04"),
    (3, 1, "Tool Dispatch",              "05-02"),
    (3, 4, "Guardrail Sandwich",         "05-05"),
    (3, 5, "Plan & Execute",             "05-03"),
    # Reflect (row 4)
    (4, 0, "Generator-Critic",           "06-02"),
    (4, 1, "Skill Package",              "06-03"),
    (4, 3, "Self-Heal Loop",             "06-05"),
    (4, 4, "Experience Replay",          "06-04"),
    # Collaborate (row 5)
    (5, 0, "Handoff Chain",              "07-05"),
    (5, 2, "Fan-out & Gather",           "07-03"),
    (5, 3, "Adversarial Review",         "07-04"),
    (5, 4, "Hierarchical Delegation",    "07-02"),
    # Govern (row 6)
    (6, 0, "Progressive Commitment",     "08-04"),
    (6, 1, "Approval Gate",              "08-02"),
    (6, 4, "Blast Radius",               "08-03"),
    (6, 5, "Observability Harness",      "08-05"),
]


def render(out_path: Path, clean: bool = False, show_codes: bool = True) -> None:
    """Render the matrix.

    clean=False, show_codes=True  → titled version with subtitle + lecture codes
    clean=True,  show_codes=True  → no title/subtitle, lecture codes kept
    clean=True,  show_codes=False → minimal pure matrix
    """
    fig, ax = plt.subplots(figsize=(20, 12 if not clean else 11))
    ax.set_facecolor(BG)
    fig.patch.set_facecolor(BG)

    cell_w, cell_h, gap = 2.45, 1.35, 0.13
    n_rows, n_cols = len(ROWS), len(COLS)

    border_lw = 2.6 if clean else 2.0
    glow_alpha = 0.26 if clean else 0.18

    cell_map = {(r, c): (name, code) for r, c, name, code in PATTERNS}

    for r in range(n_rows):
        for c in range(n_cols):
            x = c * (cell_w + gap)
            y = (n_rows - 1 - r) * (cell_h + gap)
            if (r, c) in cell_map:
                name, code = cell_map[(r, c)]
                color = ROW_COLORS[r]
                ax.add_patch(mpatches.FancyBboxPatch(
                    (x - 0.05, y - 0.05), cell_w + 0.1, cell_h + 0.1,
                    boxstyle="round,pad=0.02", fc=color, ec=color,
                    alpha=glow_alpha, linewidth=0))
                ax.add_patch(mpatches.FancyBboxPatch(
                    (x, y), cell_w, cell_h, boxstyle="round,pad=0.02",
                    fc=DIM, ec=color, linewidth=border_lw, alpha=0.95))
                # 2-line wrap for long names with space
                if " " in name and len(name) > 13:
                    parts = name.split(" ", 1)
                    display_name = parts[0] + "\n" + parts[1]
                    name_fs = 10
                else:
                    display_name = name
                    name_fs = 11.5
                if show_codes:
                    ax.text(x + cell_w / 2, y + cell_h * 0.62, display_name,
                            color=color, fontsize=name_fs, ha="center", va="center",
                            fontweight="bold", linespacing=0.95)
                    ax.text(x + cell_w / 2, y + cell_h * 0.18, code,
                            color=MUTED, fontsize=8.5, ha="center", va="center",
                            family="monospace")
                else:
                    ax.text(x + cell_w / 2, y + cell_h / 2, display_name,
                            color=color, fontsize=name_fs + 1, ha="center", va="center",
                            fontweight="bold", linespacing=0.95)
            else:
                ax.add_patch(mpatches.FancyBboxPatch(
                    (x, y), cell_w, cell_h, boxstyle="round,pad=0.02",
                    fc=BG_DARK, ec=GREY, linewidth=0.8, linestyle=":",
                    alpha=0.6))
                ax.text(x + cell_w / 2, y + cell_h / 2, "—",
                        color=GREY, fontsize=15, ha="center", va="center")

    # Row labels (left)
    for r, name in enumerate(ROWS):
        y = (n_rows - 1 - r) * (cell_h + gap) + cell_h / 2
        ax.text(-0.5, y, name, color=ROW_COLORS[r], fontsize=12.5,
                ha="right", va="center", fontweight="bold")

    # Column labels (bottom)
    for c, name in enumerate(COLS):
        x = c * (cell_w + gap) + cell_w / 2
        ax.text(x, -0.6, name, color=WHITE, fontsize=12.5,
                ha="center", va="top", fontweight="bold")

    # Axis labels
    ax.text(-1.7, n_rows * (cell_h + gap) / 2 - 0.05, "Cognitive Function · 7 rows",
            color=CYAN, fontsize=13, ha="center", va="center",
            fontweight="bold", rotation=90)
    ax.text(n_cols * (cell_w + gap) / 2 - 0.05, -1.25, "Execution Topology · 6 cols",
            color=CYAN, fontsize=13, ha="center", va="top", fontweight="bold")

    if not clean:
        ax.text(n_cols * (cell_w + gap) / 2 - 0.05,
                n_rows * (cell_h + gap) + 0.95,
                "Two-Axis Framework · 7 rows × 6 cols = 42 cells · 28 patterns",
                color=CYAN, fontsize=19, ha="center", va="bottom",
                fontweight="bold")
        ax.text(n_cols * (cell_w + gap) / 2 - 0.05,
                n_rows * (cell_h + gap) + 0.35,
                "Cognitive function (Perceive / Remember / Reason / Act / "
                "Reflect / Collaborate / Govern)  ×  Execution topology "
                "(Chain / Route / Parallel / Loop / Hierarchy / Orchestrate)  ·  "
                "14 cells blank (industry gap / future research)",
                color=MUTED, fontsize=10, ha="center", va="bottom",
                style="italic")

    ax.set_xlim(-2.4, n_cols * (cell_w + gap) + 0.3)
    top_pad = 1.6 if not clean else 0.25
    ax.set_ylim(-1.8, n_rows * (cell_h + gap) + top_pad)
    ax.set_aspect("equal")
    ax.axis("off")

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"✓ {out_path.name}")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    render(base / "matrix.png", clean=False, show_codes=True)
    render(base / "matrix-clean.png", clean=True, show_codes=True)
