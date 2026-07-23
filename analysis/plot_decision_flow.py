"""
Renders a compact, print-ready decision-flow figure for the report's Design section
(condensed version of the reference tree kept elsewhere - just the four top-level
branches and their trigger conditions, no nested sub-branches/formulas, so it fits the
report's 6-page budget as a single half-page-ish figure).

Not part of the graded submission - free to read/write files, same as the other
analysis/ scripts.

Usage:
    pokemon/bin/python analysis/plot_decision_flow.py
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pathlib import Path

FIGURES_DIR = Path(__file__).resolve().parent / "figures"

INK = "#20241f"
INK_SOFT = "#5c625a"
LINE = "#9aa298"
BOX_FACE = "#f7f8f5"
BOX_EDGE = "#5c625a"
ACCENT_FACE = "#efe3cd"
ACCENT_EDGE = "#b8721f"

BRANCHES = [
    ("Forced switch", "battle.force_switch\n(fainted / pivoted out)", "best_switch()\nhighest-scoring switch"),
    ("Ribombee opening", "active = Ribombee\nturn ≤ 2", "Fixed script:\nSticky Web → retreat / Stun Spore"),
    ("Guaranteed KO", "a move's estimated\ndamage ≥ opponent HP%", "Execute that\nKO move"),
    ("General scoring", "(fallback —\nalways reached)", "Score every legal move\n& switch, pick the max"),
]


def main():
    fig, ax = plt.subplots(figsize=(10, 3.3), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.3)
    ax.axis("off")

    box_w, box_h = 1.9, 0.85
    gap = 0.55
    top_y = 2.35
    start_x = 0.2

    centers = []
    for i, (title, cond, _) in enumerate(BRANCHES):
        x = start_x + i * (box_w + gap)
        centers.append(x + box_w / 2)
        is_last = i == len(BRANCHES) - 1
        face = ACCENT_FACE if is_last else BOX_FACE
        edge = ACCENT_EDGE if is_last else BOX_EDGE
        box = FancyBboxPatch(
            (x, top_y), box_w, box_h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.1, edgecolor=edge, facecolor=face, zorder=3,
        )
        ax.add_patch(box)
        ax.text(x + box_w / 2, top_y + box_h - 0.22, title, ha="center", va="center",
                 fontsize=9.5, fontweight="bold", color=INK, zorder=4)
        ax.text(x + box_w / 2, top_y + 0.24, cond, ha="center", va="center",
                 fontsize=7.3, color=INK_SOFT, zorder=4, linespacing=1.35)

    # horizontal "no" arrows between gate boxes (not into the last, fallback, box)
    for i in range(len(BRANCHES) - 2):
        x0 = start_x + i * (box_w + gap) + box_w
        x1 = x0 + gap
        y = top_y + box_h / 2
        ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=11,
                                      linewidth=1.1, color=LINE, zorder=2))
        ax.text((x0 + x1) / 2, y + 0.16, "no", ha="center", va="bottom", fontsize=7, color=INK_SOFT)

    # the third gate's "no" arrow leads into the fallback box
    x0 = start_x + 2 * (box_w + gap) + box_w
    x1 = start_x + 3 * (box_w + gap)
    y = top_y + box_h / 2
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=11,
                                  linewidth=1.1, color=LINE, zorder=2))
    ax.text((x0 + x1) / 2, y + 0.16, "no", ha="center", va="bottom", fontsize=7, color=INK_SOFT)

    # vertical "yes" arrows down to the outcome for the first three gates
    action_y = 0.62
    for i in range(3):
        cx = centers[i]
        ax.add_patch(FancyArrowPatch((cx, top_y), (cx, action_y + 0.42), arrowstyle="-|>",
                                      mutation_scale=11, linewidth=1.1, color=ACCENT_EDGE, zorder=2))
        ax.text(cx - 0.12, (top_y + action_y + 0.42) / 2, "yes", ha="right", va="center",
                fontsize=7, color=ACCENT_EDGE)
        ax.text(cx, action_y, BRANCHES[i][2], ha="center", va="center", fontsize=7.4,
                color=INK, linespacing=1.4)

    # fallback box always executes - short down-arrow with no condition label
    cx = centers[3]
    ax.add_patch(FancyArrowPatch((cx, top_y), (cx, action_y + 0.42), arrowstyle="-|>",
                                  mutation_scale=11, linewidth=1.1, color=ACCENT_EDGE, zorder=2))
    ax.text(cx, action_y, BRANCHES[3][2], ha="center", va="center", fontsize=7.4,
            color=INK, linespacing=1.4)

    fig.suptitle("wche652 · _choose_move decision cascade (v1)", fontsize=10.5, fontweight="bold",
                 color=INK, x=0.02, ha="left", y=0.995)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "decision_flow.png"
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
