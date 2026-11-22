# experiment.py
import csv
import math
import os
import random
from game_manager import GameManager
from drone import PATTERNS
from settings import KALMAN_WARMUP_FRAMES, PROJECTILE_SPEED

DT = 1 / 60                       # fixed time step: results don't depend on FPS
NOISE_LEVELS = (5, 15, 30, 60, 100)
SEEDS = range(1, 31)              # 30 runs per setting
OUTPUT_FILE = os.path.join("results", "results.csv")
FIELDS = ["turret", "trajectory", "noise", "seed",
          "shots", "hits", "hit_rate", "rmse",
          "pred_error", "first_hit_time"]


def run_trial(pattern, noise, seed):
    # the seed fixes both the radar noise and the drone's starting height
    rng = random.Random(seed)
    start_y = rng.uniform(60, 160)
    game = GameManager(noise, seed, pattern, start_y, auto_reset=False)

    raw_sq = 0.0
    kalman_sq = 0.0
    count = 0

    # for the prediction error: the true path, and what each turret predicted
    # at the moment it fired
    path = []                         # true drone position after each frame
    pending = []                      # (frame to check, turret name, point)
    shots_seen = {"Raw radar": 0, "Kalman": 0}
    hits_seen = {"Raw radar": 0, "Kalman": 0}
    first_hit = {"Raw radar": None, "Kalman": None}
    enter_frame = None                # first frame with the drone on screen
    frame = 0

    while not game.drone.is_out():
        game.update(DT)
        path.append((game.drone.x, game.drone.y))
        if enter_frame is None and game.drone.x > 0:
            enter_frame = frame

        # position error, measured only while the drone is on screen and
        # after the filter warm-up, and on the same frames for both methods
        if game.drone.x > 0 and game.warmup_frames >= KALMAN_WARMUP_FRAMES:
            true_x, true_y = game.drone.x, game.drone.y
            raw_x, raw_y = game.radar_dots[-1]
            est_x, est_y = game.kalman.position()
            raw_sq += (raw_x - true_x) ** 2 + (raw_y - true_y) ** 2
            kalman_sq += (est_x - true_x) ** 2 + (est_y - true_y) ** 2
            count += 1

        # each turret's prediction: where the drone will be when the bullet
        # arrives (raw radar: the latest reading, Kalman: the lead point)
        for turret, point in ((game.raw_turret, game.radar_dots[-1]),
                              (game.kalman_turret, game.aim_point)):
            if turret.shots > shots_seen[turret.name]:
                shots_seen[turret.name] = turret.shots
                travel = math.hypot(point[0] - turret.x,
                                    point[1] - turret.y) / PROJECTILE_SPEED
                pending.append((frame + round(travel / DT), turret.name, point))
            # response time: first hit, counted from the drone entering
            if turret.hits > hits_seen[turret.name]:
                hits_seen[turret.name] = turret.hits
                if first_hit[turret.name] is None:
                    first_hit[turret.name] = (frame - enter_frame) * DT
        frame += 1

    # prediction error = distance between the predicted point and the drone's
    # true position at the time the bullet was due to arrive
    errors = {"Raw radar": [], "Kalman": []}
    for check_frame, name, point in pending:
        if check_frame < len(path):   # skip if the drone had already left
            true_x, true_y = path[check_frame]
            errors[name].append(math.hypot(point[0] - true_x,
                                           point[1] - true_y))

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
            "pred_error": (round(sum(errors[turret.name])
                                 / len(errors[turret.name]), 2)
                           if errors[turret.name] else ""),
            "first_hit_time": (round(first_hit[turret.name], 2)
                               if first_hit[turret.name] is not None else ""),
        })
    return rows


def print_summary(rows):
    groups = {}
    for r in rows:
        key = (r["trajectory"], r["noise"], r["turret"])
        groups.setdefault(key, []).append(r)

    print()
    print("trajectory  noise  turret     hit rate   mean RMSE  pred error  "
          "first hit (s)  runs with hit")
    for key in sorted(groups, key=lambda k: (PATTERNS.index(k[0]), k[1], k[2])):
        trials = groups[key]
        shots = sum(t["shots"] for t in trials)
        hits = sum(t["hits"] for t in trials)
        hit_rate = 100 * hits / shots if shots > 0 else 0.0
        rmse = sum(t["rmse"] for t in trials) / len(trials)
        errors = [t["pred_error"] for t in trials if t["pred_error"] != ""]
        pred_error = sum(errors) / len(errors) if errors else 0.0
        times = [t["first_hit_time"] for t in trials
                 if t["first_hit_time"] != ""]
        first_hit = f"{sum(times) / len(times):.2f}" if times else "-"
        print(f"{key[0]:<11} {key[1]:>5}  {key[2]:<9} {hit_rate:7.1f}%  "
              f"{rmse:9.1f}  {pred_error:10.1f}  {first_hit:>13}  "
              f"{len(times):>7}/{len(trials)}")


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