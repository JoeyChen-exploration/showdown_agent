"""
Plots the multi-repeat ablation summary (analysis/results/summary.csv) as a bar chart
for the report. Not part of the graded submission (only players/<upi>.py is) - free to
read/write files on disk, same as run_ablation.py.

Usage (from the repo root, after analysis/run_ablation.py --repeats 3 has produced
analysis/results/summary.csv):
    pokemon/bin/python analysis/plot_ablation.py
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_CSV = REPO_ROOT / "analysis" / "results" / "summary.csv"
OUT_PNG = REPO_ROOT / "analysis" / "figures" / "ablation_mean_beaten.png"

# Only the 7 configs that were actually multi-repeat-confirmed (repeats == 3 in the
# CSV) - the two switch_defense_weight_* configs only have single-run screening data
# with no stdev, so they don't belong on a mean +/- stdev chart.
DISPLAY_ORDER = [
    "baseline", "no_hard_ko", "no_opening_script",
    "setup_weight_15", "setup_weight_45", "switch_cost_0", "switch_cost_50",
]
LABELS = {
    "baseline": "baseline",
    "no_hard_ko": "no_hard_ko",
    "no_opening_script": "no_opening\n_script",
    "setup_weight_15": "setup_weight\n=15",
    "setup_weight_45": "setup_weight\n=45",
    "switch_cost_0": "switch_cost\n=0",
    "switch_cost_50": "switch_cost\n=50",
}


def main():
    rows = {}
    with open(SUMMARY_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["config"]] = row

    configs = [c for c in DISPLAY_ORDER if c in rows]
    means = [float(rows[c]["mean_beaten"]) for c in configs]
    stdevs = [float(rows[c]["stdev_beaten"]) if "stdev_beaten" in rows[c] else 0.0 for c in configs]
    # summary.csv doesn't carry stdev_beaten directly (only stdev_mark) - approximate
    # the error bar from min/max beaten instead, which is what the CSV does have.
    mins = [float(rows[c]["min_beaten"]) for c in configs]
    maxs = [float(rows[c]["max_beaten"]) for c in configs]
    lower_err = [m - lo for m, lo in zip(means, mins)]
    upper_err = [hi - m for m, hi in zip(means, maxs)]

    colors = ["#4C72B0" if c == "baseline" else
              ("#55A868" if means[i] > means[0] else
               ("#C44E52" if means[i] < means[0] else "#8172B2"))
              for i, c in enumerate(configs)]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(configs))
    ax.bar(x, means, yerr=[lower_err, upper_err], capsize=4, color=colors)
    ax.set_xticks(list(x))
    ax.set_xticklabels([LABELS[c] for c in configs], fontsize=9)
    ax.set_ylabel("bots beaten / 15 (mean of 3 repeats, range shown)")
    ax.set_title("Ablation: mean bots beaten per config (3 repeats each)")
    ax.set_ylim(11, 15)
    ax.axhline(means[0], color="#4C72B0", linestyle="--", linewidth=1, alpha=0.5)
    fig.tight_layout()

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=150)
    print(f"wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
