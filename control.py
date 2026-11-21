# control.py
import csv
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drone import PATTERNS
from experiments import DT, NOISE_LEVELS, SEEDS
from game_manager import GameManager

RESULTS_FILE = os.path.join("results", "results.csv")
OUTPUT_DIR = "results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "control.csv")
FIELDS = ["turret", "trajectory", "noise", "seed", "shots", "hits", "hit_rate"]
TURRET_ORDER = ("Raw radar", "Raw radar (same position)", "Raw + lead",
                "Kalman")
SHORT = {"Raw radar": "raw",
         "Raw radar (same position)": "raw@Kalman pos",
         "Raw + lead": "raw+lead",
         "Kalman": "kalman"}
STYLES = {"Raw radar": ("#e67e22", "o", "-"),
          "Raw radar (same position)": ("#f0b27a", "s", "--"),
          "Raw + lead": ("#1b9e77", "^", "-"),
          "Kalman": ("#8e44ad", "D", "-")}


def run_trial(pattern, noise, seed):
    # same seed rule as experiments.py, so the trials match the main results
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False,
                       control_turret=True)
    while not game.drone.is_out():
        game.update(DT)

    rows = []
    for turret in (game.raw_turret, game.raw_same, game.lead_turret,
                   game.kalman_turret):
        rows.append({
            "turret": turret.name,
            "trajectory": pattern,
            "noise": noise,
            "seed": seed,
            "shots": turret.shots,
            "hits": turret.hits,
            "hit_rate": round(turret.hit_rate(), 2),
        })
    return rows


def verify_against_results(rows):
    # the raw and Kalman rows must equal the main experiment, trial by trial
    expected = {}
    with open(RESULTS_FILE, newline="") as f:
        for r in csv.DictReader(f):
            key = (r["turret"], r["trajectory"], int(r["noise"]),
                   int(r["seed"]))
            expected[key] = (int(r["shots"]), int(r["hits"]))
    checked = 0
    mismatches = 0
    for r in rows:
        key = (r["turret"], r["trajectory"], r["noise"], r["seed"])
        if key in expected:
            checked += 1
            if expected[key] != (r["shots"], r["hits"]):
                mismatches += 1
    print(f"Check against results.csv: {checked} rows compared, "
          f"{mismatches} mismatches")
    return mismatches == 0


def print_summary(rows):
    groups = {}
    for r in rows:
        key = (r["trajectory"], r["noise"], r["turret"])
        groups.setdefault(key, []).append(r)

    print()
    print("hit rate (%), shots pooled over 30 runs")
    header = "trajectory  noise  "
    header += "  ".join(f"{SHORT[t]:>15}" for t in TURRET_ORDER)
    print(header)
    for pattern in PATTERNS:
        for noise in NOISE_LEVELS:
            cells = []
            for turret in TURRET_ORDER:
                trials = groups[(pattern, noise, turret)]
                shots = sum(t["shots"] for t in trials)
                hits = sum(t["hits"] for t in trials)
                rate = 100 * hits / shots if shots > 0 else 0.0
                cells.append(f"{rate:14.1f}%")
            print(f"{pattern:<11} {noise:>5}  " + "  ".join(cells))


def plot_control(rows):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, pattern in zip(axes, PATTERNS):
        for turret in TURRET_ORDER:
            means = []
            stds = []
            for noise in NOISE_LEVELS:
                rates = [r["hit_rate"] for r in rows
                         if r["trajectory"] == pattern
                         and r["turret"] == turret and r["noise"] == noise]
                means.append(np.mean(rates))
                stds.append(np.std(rates))
            means = np.array(means)
            stds = np.array(stds)
            lower = np.minimum(stds, means)
            color, marker, style = STYLES[turret]
            ax.errorbar(NOISE_LEVELS, means, yerr=[lower, stds], color=color,
                        marker=marker, linestyle=style, capsize=3,
                        label=turret)
        ax.set_title(pattern.capitalize() + " path")
        ax.set_xlabel("Radar noise (pixels, standard deviation)")
        ax.set_xticks(NOISE_LEVELS)
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Hit rate (%)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Control experiment: separating smoothing from leading "
                 "(mean of 30 runs)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart6_control_turret.png"),
                dpi=200)
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = []
    for pattern in PATTERNS:
        for noise in NOISE_LEVELS:
            for seed in SEEDS:
                rows.extend(run_trial(pattern, noise, seed))
        print("finished", pattern)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print("saved", len(rows), "rows to", OUTPUT_FILE)

    if verify_against_results(rows):
        print("OK: raw and Kalman results are identical to the main experiment")
    else:
        print("WARNING: results differ from results.csv, do not use them yet")

    print_summary(rows)
    plot_control(rows)


if __name__ == "__main__":
    main()