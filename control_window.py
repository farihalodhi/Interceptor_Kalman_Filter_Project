# control_window.py
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

OUTPUT_DIR = "results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "control_window.csv")
RESULTS_FILE = os.path.join(OUTPUT_DIR, "results.csv")
CONTROL_FILE = os.path.join(OUTPUT_DIR, "control.csv")
FIELDS = ["turret", "trajectory", "noise", "seed", "shots", "hits", "hit_rate"]

WINDOWS = (0.25, 0.5, 1.0, 2.0)
METHODS = (("diff", "differencing"), ("fit", "least-squares fit"))
VARIANTS = [(f"{method} {window:g} s", method, window)
            for method, _ in METHODS for window in WINDOWS]
COLORS = {"diff": ("#1b9e77", "^"), "fit": ("#e6ab02", "s"),
          "kalman": ("#8e44ad", "D")}


def run_trial(pattern, noise, seed):
    # same seed rule as experiments.py, so the trials match the main results
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False,
                       lead_variants=VARIANTS)
    while not game.drone.is_out():
        game.update(DT)

    rows = []
    for turret in [game.kalman_turret] + game.variant_turrets:
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


def load_expected(path, turret_name):
    expected = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["turret"] == turret_name:
                key = (r["trajectory"], int(r["noise"]), int(r["seed"]))
                expected[key] = (int(r["shots"]), int(r["hits"]))
    return expected


def check(rows, turret_name, path, expected_name, description):
    # the same trials must give the same shots and hits as an earlier run
    if not os.path.exists(path):
        print(f"Skipped check ({description}): {path} not found")
        return True
    expected = load_expected(path, expected_name)
    compared = 0
    mismatches = 0
    for r in rows:
        if r["turret"] != turret_name:
            continue
        key = (r["trajectory"], r["noise"], r["seed"])
        if key in expected:
            compared += 1
            if expected[key] != (r["shots"], r["hits"]):
                mismatches += 1
    print(f"Check ({description}): {compared} trials compared, "
          f"{mismatches} mismatches")
    return compared > 0 and mismatches == 0


def pooled(rows, pattern, noise, turret):
    trials = [r for r in rows if r["trajectory"] == pattern
              and r["noise"] == noise and r["turret"] == turret]
    shots = sum(t["shots"] for t in trials)
    hits = sum(t["hits"] for t in trials)
    return 100 * hits / shots if shots > 0 else 0.0


def mean_std(rows, pattern, noise, turret):
    rates = [r["hit_rate"] for r in rows if r["trajectory"] == pattern
             and r["noise"] == noise and r["turret"] == turret]
    return float(np.mean(rates)), float(np.std(rates))


def print_summary(rows):
    shorts = [f"{method[0]}{window:g}" for _, method, window in VARIANTS]
    print()
    print("hit rate (%), shots pooled over 30 runs")
    print("dN = differencing over N seconds, fN = least-squares fit over N seconds")
    print("trajectory  noise  kalman " + " ".join(f"{s:>6}" for s in shorts))
    for pattern in PATTERNS:
        for noise in NOISE_LEVELS:
            cells = [f"{pooled(rows, pattern, noise, 'Kalman'):6.1f}"]
            for name, _, _ in VARIANTS:
                cells.append(f"{pooled(rows, pattern, noise, name):6.1f}")
            print(f"{pattern:<11} {noise:>5}  " + " ".join(cells))


def plot_best(rows):
    # for each method, the best window at each point: the most favourable
    # reading for the baselines, so it is a conservative test of the Kalman turret
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, pattern in zip(axes, PATTERNS):
        for method, label in METHODS:
            means, stds = [], []
            for noise in NOISE_LEVELS:
                best = None
                for name, m, _ in VARIANTS:
                    if m != method:
                        continue
                    mean, std = mean_std(rows, pattern, noise, name)
                    if best is None or mean > best[0]:
                        best = (mean, std)
                means.append(best[0])
                stds.append(best[1])
            color, marker = COLORS[method]
            lower = np.minimum(stds, means)
            ax.errorbar(NOISE_LEVELS, means, yerr=[lower, stds], color=color,
                        marker=marker, capsize=3,
                        label=f"raw + lead, {label} (best window)")
        means, stds = [], []
        for noise in NOISE_LEVELS:
            mean, std = mean_std(rows, pattern, noise, "Kalman")
            means.append(mean)
            stds.append(std)
        color, marker = COLORS["kalman"]
        ax.errorbar(NOISE_LEVELS, means, yerr=[np.minimum(stds, means), stds],
                    color=color, marker=marker, capsize=3, label="Kalman")
        ax.set_title(pattern.capitalize() + " path")
        ax.set_xlabel("Radar noise (pixels, standard deviation)")
        ax.set_xticks(NOISE_LEVELS)
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Hit rate (%)")
    axes[0].legend(fontsize=7)
    fig.suptitle("Stronger non-Kalman baselines: best window per point "
                 "(mean of 30 runs)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart7_stronger_baselines.png"),
                dpi=200)
    plt.close(fig)


def plot_windows(rows):
    # how the window size matters, at a low and a high noise level
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
    for ax, pattern in zip(axes, PATTERNS):
        for noise, style in ((15, "-"), (60, "--")):
            for method, label in METHODS:
                means = [mean_std(rows, pattern, noise,
                                  f"{method} {w:g} s")[0] for w in WINDOWS]
                color, marker = COLORS[method]
                ax.plot(WINDOWS, means, color=color, marker=marker,
                        linestyle=style, label=f"{label}, noise {noise}")
            kalman = mean_std(rows, pattern, noise, "Kalman")[0]
            ax.axhline(kalman, color=COLORS["kalman"][0], linestyle=style,
                       linewidth=1.5, alpha=0.8, label=f"Kalman, noise {noise}")
        ax.set_xscale("log")
        ax.set_xticks(WINDOWS)
        ax.set_xticklabels([f"{w:g}" for w in WINDOWS])
        ax.minorticks_off()
        ax.set_title(pattern.capitalize() + " path")
        ax.set_xlabel("Window length (seconds)")
        ax.set_ylim(0, 100)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("Hit rate (%)")
    axes[0].legend(fontsize=7)
    fig.suptitle("Effect of the window length on the raw + lead turrets "
                 "(mean of 30 runs)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart8_window_length.png"), dpi=200)
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

    ok_kalman = check(rows, "Kalman", RESULTS_FILE, "Kalman",
                      "Kalman vs results.csv")
    ok_diff = check(rows, "diff 0.5 s", CONTROL_FILE, "Raw + lead",
                    "diff 0.5 s vs the earlier raw + lead turret")
    if ok_kalman and ok_diff:
        print("OK: both checks passed")
    else:
        print("WARNING: a check failed, do not use these results yet")

    print_summary(rows)
    plot_best(rows)
    plot_windows(rows)
    print("saved chart7_stronger_baselines.png and chart8_window_length.png")


if __name__ == "__main__":
    main()