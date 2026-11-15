# experiment.py
import csv
import math
import os
import random
from game_manager import GameManager
from drone import PATTERNS
from settings import KALMAN_WARMUP_FRAMES

DT = 1 / 60                       # fixed time step: results don't depend on FPS
NOISE_LEVELS = (5, 15, 30, 60, 100)
SEEDS = range(1, 31)              # 30 runs per setting
OUTPUT_FILE = os.path.join("results", "results.csv")
FIELDS = ["turret", "trajectory", "noise", "seed",
          "shots", "hits", "hit_rate", "rmse"]


def run_trial(pattern, noise, seed):
    # the seed fixes both the radar noise and the drone's starting height
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False)

    raw_sq = 0.0
    kalman_sq = 0.0
    count = 0

    while not game.drone.is_out():
        game.update(DT)

        # position error, measured only while the drone is on screen and
        # after the filter warm-up, and on the same frames for both methods
        if game.drone.x > 0 and game.warmup_frames >= KALMAN_WARMUP_FRAMES:
            true_x, true_y = game.drone.x, game.drone.y
            raw_x, raw_y = game.radar_dots[-1]
            est_x, est_y = game.kalman.position()
            raw_sq += (raw_x - true_x) ** 2 + (raw_y - true_y) ** 2
            kalman_sq += (est_x - true_x) ** 2 + (est_y - true_y) ** 2
            count += 1

    rows = []
    for turret, squared_error in ((game.raw_turret, raw_sq),
                                  (game.kalman_turret, kalman_sq)):
        rmse = math.sqrt(squared_error / count) if count > 0 else 0.0
        rows.append({
            "turret": turret.name,
            "trajectory": pattern,
            "noise": noise,
            "seed": seed,
            "shots": turret.shots,
            "hits": turret.hits,
            "hit_rate": round(turret.hit_rate(), 2),
            "rmse": round(rmse, 2),
        })
    return rows


def print_summary(rows):
    groups = {}
    for r in rows:
        key = (r["trajectory"], r["noise"], r["turret"])
        groups.setdefault(key, []).append(r)

    print()
    print("trajectory  noise  turret     hit rate   mean RMSE")
    for key in sorted(groups, key=lambda k: (PATTERNS.index(k[0]), k[1], k[2])):
        trials = groups[key]
        shots = sum(t["shots"] for t in trials)
        hits = sum(t["hits"] for t in trials)
        hit_rate = 100 * hits / shots if shots > 0 else 0.0
        rmse = sum(t["rmse"] for t in trials) / len(trials)
        print(f"{key[0]:<11} {key[1]:>5}  {key[2]:<9} {hit_rate:7.1f}%  "
              f"{rmse:9.1f}")


def main():
    os.makedirs("results", exist_ok=True)
    all_rows = []
    for pattern in PATTERNS:
        for noise in NOISE_LEVELS:
            for seed in SEEDS:
                all_rows.extend(run_trial(pattern, noise, seed))
        print("finished", pattern)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)
    print("saved", len(all_rows), "rows to", OUTPUT_FILE)

    print_summary(all_rows)


if __name__ == "__main__":
    main()