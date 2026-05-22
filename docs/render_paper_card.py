"""arXiv paper preview card · agent-design-patterns

Renders a preview card for the framework's source paper
(arXiv:2605.13850) into the repo's `docs/` directory. The card is
embedded near the top of the README so repo visitors land on the
paper, and the Citation section points at the paper rather than the
repo.

Metadata is taken verbatim from the arXiv abstract page.
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams["font.sans-serif"] = ["DejaVu Sans", "Liberation Sans", "Arial"]
rcParams["axes.unicode_minus"] = False

# Palette mirrors docs/render_matrix.py so the card sits next to the matrix.
BG = "#0a1628"
PANEL = "#0f1d33"
DIM = "#1a2942"
GREY = "#3a4a62"
WHITE = "#ffffff"
MUTED = "#c7d4e8"
FAINT = "#8b9bb4"
CYAN = "#00d4ff"
ARXIV = "#b31b1b"   # arXiv brand red

FIG_W, FIG_H = 12.0, 6.2

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")

# Outer card panel.
card = mpatches.FancyBboxPatch(
    (0.25, 0.25), FIG_W - 0.5, FIG_H - 0.5,
    boxstyle="round,pad=0.04,rounding_size=0.14",
    facecolor=PANEL, edgecolor=GREY, linewidth=1.2,
)
ax.add_patch(card)

LEFT = 0.85
RIGHT = FIG_W - 0.85
TOP = FIG_H - 0.55          # y of the first row's vertical centre

# --- top row: arXiv badge + identifier --------------------------------------
badge_h = 0.46
badge = mpatches.FancyBboxPatch(
    (LEFT, TOP - badge_h / 2), 1.05, badge_h,
    boxstyle="round,pad=0.02,rounding_size=0.06",
    facecolor=ARXIV, edgecolor="none",
)
ax.add_patch(badge)
ax.text(LEFT + 0.525, TOP, "arXiv", color=WHITE,
        fontsize=15, fontweight="bold", ha="center", va="center",
        fontstyle="italic")
ax.text(LEFT + 1.28, TOP, "arXiv:2605.13850", color=MUTED,
        fontsize=14, ha="left", va="center", family="monospace")
ax.text(RIGHT, TOP, "cs.AI   ·   Submitted 16 Mar 2026",
        color=FAINT, fontsize=11.5, ha="right", va="center")

# divider
div_y = TOP - 0.55
ax.plot([LEFT, RIGHT], [div_y, div_y], color=DIM, linewidth=1.0)

# --- title (two lines) ------------------------------------------------------
ax.text(LEFT, div_y - 0.55,
        "A Two-Dimensional Framework for AI Agent Design Patterns:",
        color=WHITE, fontsize=17, fontweight="bold", ha="left", va="center")
ax.text(LEFT, div_y - 1.05,
        "Cognitive Function × Execution Topology",
        color=CYAN, fontsize=17, fontweight="bold", ha="left", va="center")

# --- authors ----------------------------------------------------------------
ax.text(LEFT, div_y - 1.62,
        "Jia Huang   ·   Joey Tianyi Zhou",
        color=MUTED, fontsize=12.5, ha="left", va="center")

# --- abstract snippet (anchored top so line count is predictable) -----------
abstract = (
    "A 7×6 matrix pairs seven cognitive functions (Context Engineering, Memory,\n"
    "Reasoning, Action, Reflection, Collaboration, Governance) with six execution\n"
    "topologies (Chain, Route, Parallel, Orchestrate, Loop, Hierarchy) — yielding\n"
    "27 named architectural patterns, validated across four real-world domains."
)
ax.text(LEFT, div_y - 2.05, abstract,
        color=FAINT, fontsize=11.3, ha="left", va="top", linespacing=1.6)

# --- footer chips -----------------------------------------------------------
chips = ["10 pages", "6 tables", "27 named patterns", "13 original"]
x = LEFT
chip_y = 0.62
chip_h = 0.40
for label in chips:
    w = 0.30 + 0.108 * len(label)
    chip = mpatches.FancyBboxPatch(
        (x, chip_y), w, chip_h,
        boxstyle="round,pad=0.015,rounding_size=0.05",
        facecolor=DIM, edgecolor=GREY, linewidth=0.8,
    )
    ax.add_patch(chip)
    ax.text(x + w / 2, chip_y + chip_h / 2, label, color=MUTED,
            fontsize=10.5, ha="center", va="center")
    x += w + 0.25

ax.text(RIGHT, chip_y + chip_h / 2, "arxiv.org/abs/2605.13850",
        color=CYAN, fontsize=11.5, ha="right", va="center",
        family="monospace")

out = Path(__file__).parent / "paper-card.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight", pad_inches=0.15)
print(f"wrote {out}")
