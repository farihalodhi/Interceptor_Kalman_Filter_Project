# sweep.py
import csv
import math
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drone import PATTERNS
from experiments import DT, SEEDS
from game_manager import GameManager
from kalman_filter import KalmanFilter
from settings import KALMAN_WARMUP_FRAMES

ACCEL_NOISE_VALUES = (10, 30, 60, 120, 240)
SWEEP_NOISE_LEVELS = (15, 60)
OUTPUT_DIR = "results"
FIELDS = ["trajectory", "noise", "accel_noise", "seed",
          "shots", "hits", "hit_rate", "rmse"]
STYLES = [("#1b9e77", "o", "-"), ("#7570b3", "s", "--")]


def run_trial(pattern, noise, accel_noise, seed):
    # same seed rule as experiments.py, so seeds match the main results
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False)
    game.kalman = KalmanFilter(noise, accel_noise)    # the setting under test

    squared_error = 0.0
    count = 0
    while not game.drone.is_out():
        game.update(DT)
        if game.drone.x > 0 and game.warmup_frames >= KALMAN_WARMUP_FRAMES:
            est_x, est_y = game.kalman.position()
            squared_error += ((est_x - game.drone.x) ** 2
                              + (est_y - game.drone.y) ** 2)
            count += 1

    turret = game.kalman_turret
    rmse = math.sqrt(squared_error / count) if count > 0 else 0.0
    return {
        "trajectory": pattern,
        "noise": noise,
        "accel_noise": accel_noise,
        "seed": seed,
        "shots": turret.shots,
        "hits": turret.hits,
        "hit_rate": round(turret.hit_rate(), 2),
        "rmse": round(rmse, 2),
    }


def print_summary(rows):
    groups = {}
    for r in rows:
        key = (r["trajectory"], r["noise"], r["accel_noise"])
        groups.setdefault(key, []).append(r)

    print()
    print("trajectory  noise  accel_noise  hit rate   mean RMSE")
    for key in sorted(groups, key=lambda k: (PATTERNS.index(k[0]), k[1], k[2])):
        trials = groups[key]
        shots = sum(t["shots"] for t in trials)
        hits = sum(t["hits"] for t in trials)
        hit_rate = 100 * hits / shots if shots > 0 else 0.0
        rmse = sum(t["rmse"] for t in trials) / len(trials)
        print(f"{key[0]:<11} {key[1]:>5}  {key[2]:>11}  {hit_rate:7.1f}%  "
              f"{rmse:9.1f}")


def series(rows, pattern, noise, field):
    groups = {}
    for r in rows:
        if r["trajectory"] == pattern and r["noise"] == noise:
            groups.setdefault(r["accel_noise"], []).append(r[field])
    xs = sorted(groups)
    ys = [float(np.mean(groups[x])) for x in xs]
    return xs, ys


def plot_sweep(rows):
    panels = (("rmse", "Kalman position RMSE (pixels)"),
              ("hit_rate", "Kalman hit rate (%)"))
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True)
    for col, pattern in enumerate(PATTERNS):
        for row_index, (field, ylabel) in enumerate(panels):
            ax = axes[row_index][col]
            for i, noise in enumerate(SWEEP_NOISE_LEVELS):
                color, marker, style = STYLES[i]
                xs, ys = series(rows, pattern, noise, field)
                ax.plot(xs, ys, marker=marker, linestyle=style, color=color,
                        label=f"radar noise {noise}")
            ax.axvline(60, color="gray", linestyle=":", label="default (60)")
            ax.set_xscale("log")
            ax.set_xticks(ACCEL_NOISE_VALUES)
            ax.set_xticklabels([str(v) for v in ACCEL_NOISE_VALUES])
            ax.minorticks_off()
            ax.grid(alpha=0.3)
            if field == "hit_rate":
                ax.set_ylim(0, 100)
            if row_index == 0:
                ax.set_title(pattern.capitalize() + " path")
            else:
                ax.set_xlabel("accel_noise (process noise)")
            if col == 0:
                ax.set_ylabel(ylabel)
    axes[0][0].legend()
    fig.suptitle("Effect of the filter's accel_noise setting (mean of 30 runs)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart5_accel_noise_sweep.png"),
                dpi=200)
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = []
    for pattern in PATTERNS:
        for noise in SWEEP_NOISE_LEVELS:
            for accel_noise in ACCEL_NOISE_VALUES:
                for seed in SEEDS:
                    rows.append(run_trial(pattern, noise, accel_noise, seed))
        print("finished", pattern)

    path = os.path.join(OUTPUT_DIR, "sweep.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print("saved", len(rows), "rows to", path)

    print_summary(rows)
    plot_sweep(rows)


if __name__ == "__main__":
    main()