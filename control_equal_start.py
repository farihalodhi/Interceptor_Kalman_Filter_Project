# control_equal_start.py
# Checks whether the least-squares baselines (control_window.py) lead Kalman
# because of a better estimate or only because they start firing later.
#
# In the other experiments the Kalman turret starts firing after 20 frames
# (0.33 s), but a least-squares fit over a 2 s window waits until it has 1 s of
# readings. Hit rate is hits / shots, so Kalman's early, less accurate shots
# count against it. Here every turret waits at least 60 frames (1 s) before
# its first shot, so all of them start together.
import csv
import os
import random
from collections import defaultdict

import game_manager
from drone import PATTERNS
from experiments import DT, NOISE_LEVELS, SEEDS
from game_manager import GameManager

EQUAL_START_FRAMES = 60           # 1 s at 60 frames per second
OUTPUT_DIR = "results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "control_equal_start.csv")
FIELDS = ["turret", "trajectory", "noise", "seed", "shots", "hits", "hit_rate"]
VARIANTS = [("diff 2 s", "diff", 2.0), ("fit 1 s", "fit", 1.0),
            ("fit 2 s", "fit", 2.0)]
ORDER = ("Kalman", "diff 2 s", "fit 1 s", "fit 2 s")


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
        rows.append({"turret": turret.name, "trajectory": pattern,
                     "noise": noise, "seed": seed, "shots": turret.shots,
                     "hits": turret.hits,
                     "hit_rate": round(turret.hit_rate(), 2)})
    return rows


def pooled(rows):
    totals = defaultdict(lambda: [0, 0])
    for r in rows:
        key = (r["trajectory"], r["noise"], r["turret"])
        totals[key][0] += r["shots"]
        totals[key][1] += r["hits"]
    return {k: (100 * h / s if s else 0.0) for k, (s, h) in totals.items()}


def print_summary(rows):
    rate = pooled(rows)
    print()
    print("hit rate (%), all turrets start firing after 1 s, shots pooled "
          "over 30 runs")
    print("trajectory  noise  kalman  diff2s   fit1s   fit2s  "
          "best fit - kalman")
    for pattern in PATTERNS:
        for noise in NOISE_LEVELS:
            values = [rate[(pattern, noise, t)] for t in ORDER]
            gap = max(values[2], values[3]) - values[0]
            print(f"{pattern:<11} {noise:>5}  "
                  + "  ".join(f"{v:6.1f}" for v in values)
                  + f"  {gap:+10.1f}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # every turret in game_manager reads this value before it may fire
    game_manager.KALMAN_WARMUP_FRAMES = EQUAL_START_FRAMES
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
    print_summary(rows)


if __name__ == "__main__":
    main()