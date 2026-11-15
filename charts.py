# charts.py
import csv
import os
import random

import matplotlib
matplotlib.use("Agg")                 # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np

from drone import PATTERNS
from experiments import DT
from game_manager import GameManager
from settings import TURN_TIME

RESULTS_FILE = os.path.join("results", "results.csv")
OUTPUT_DIR = "results"
COLORS = {"Raw radar": "#e67e22", "Kalman": "#8e44ad"}
RADAR_COLOR = "#4a90d9"


def load_results():
    rows = []
    with open(RESULTS_FILE, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "turret": r["turret"],
                "trajectory": r["trajectory"],
                "noise": int(r["noise"]),
                "hit_rate": float(r["hit_rate"]),
                "rmse": float(r["rmse"]),
            })
    return rows


def grouped(rows, pattern, turret, field):
    # collect the 30 per-seed values at each noise level
    groups = {}
    for r in rows:
        if r["trajectory"] == pattern and r["turret"] == turret:
            groups.setdefault(r["noise"], []).append(r[field])
    noises = sorted(groups)
    means = np.array([np.mean(groups[n]) for n in noises])
    stds = np.array([np.std(groups[n]) for n in noises])
    return noises, means, stds


def plot_metric(rows, field, ylabel, title, filename, ylim=None):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, pattern in zip(axes, PATTERNS):
        for turret in ("Raw radar", "Kalman"):
            noises, means, stds = grouped(rows, pattern, turret, field)
            lower = np.minimum(stds, means)       # keep bars above zero
            ax.errorbar(noises, means, yerr=[lower, stds], marker="o",
                        capsize=3, color=COLORS[turret], label=turret)
        ax.set_title(pattern.capitalize() + " path")
        ax.set_xlabel("Radar noise (pixels, standard deviation)")
        ax.set_xticks(noises)
        ax.grid(alpha=0.3)
        if ylim is not None:
            ax.set_ylim(*ylim)
    axes[0].set_ylabel(ylabel)
    axes[0].legend()
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, filename), dpi=200)
    plt.close(fig)


def record_trial(pattern, noise, seed):
    # same setup as experiments.run_trial, but keeps every frame
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False)

    trace = []
    while not game.drone.is_out():
        game.update(DT)
        if game.drone.x > 0:
            raw_x, raw_y = game.radar_dots[-1]
            est_x, est_y = game.kalman.position()
            trace.append((game.drone.time, game.drone.x, game.drone.y,
                          raw_x, raw_y, est_x, est_y))
    return trace


def save_trace(trace, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "true_x", "true_y", "radar_x", "radar_y",
                         "kalman_x", "kalman_y"])
        writer.writerows(trace)


def plot_trace(trace, pattern, noise, seed):
    data = np.array(trace)
    time = data[:, 0]
    true_x, true_y = data[:, 1], data[:, 2]
    radar_x, radar_y = data[:, 3], data[:, 4]
    est_x, est_y = data[:, 5], data[:, 6]
    subtitle = f"{pattern} path, noise = {noise}, seed = {seed}"

    # chart 3: the paths in the arena
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.scatter(radar_x, radar_y, s=8, color=RADAR_COLOR, alpha=0.5,
               label="Radar readings (noisy)")
    ax.plot(true_x, true_y, color="black", linewidth=2, label="True path")
    ax.plot(est_x, est_y, color=COLORS["Kalman"], linewidth=2,
            label="Kalman estimate")
    ax.invert_yaxis()                 # screen coordinates: y grows downward
    ax.set_aspect("equal")
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    ax.set_title("True, noisy and estimated trajectory\n" + subtitle)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart3_trajectory.png"), dpi=200)
    plt.close(fig)

    # chart 4: how far each position estimate is from the truth over time
    raw_error = np.hypot(radar_x - true_x, radar_y - true_y)
    kalman_error = np.hypot(est_x - true_x, est_y - true_y)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(time, raw_error, color=COLORS["Raw radar"], alpha=0.7,
            label="Raw radar error")
    ax.plot(time, kalman_error, color=COLORS["Kalman"], linewidth=2,
            label="Kalman estimate error")
    if pattern == "turning":
        ax.axvline(TURN_TIME, color="gray", linestyle="--", label="Sudden turn")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Position error (pixels)")
    ax.set_title("Position error over time\n" + subtitle)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT_DIR, "chart4_error_over_time.png"), dpi=200)
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rows = load_results()

    plot_metric(rows, "rmse", "Position RMSE (pixels)",
                "Position estimation error vs sensor noise",
                "chart1_rmse_vs_noise.png")
    plot_metric(rows, "hit_rate", "Hit rate (%)",
                "Hit rate vs sensor noise",
                "chart2_hit_rate_vs_noise.png", ylim=(0, 100))

    pattern, noise, seed = "turning", 30, 1
    trace = record_trial(pattern, noise, seed)
    save_trace(trace, "trace_turning.csv")
    plot_trace(trace, pattern, noise, seed)

    print("saved 4 charts and trace_turning.csv to", OUTPUT_DIR)


if __name__ == "__main__":
    main()