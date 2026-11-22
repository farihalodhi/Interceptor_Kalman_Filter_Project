# Interceptor: Hitting Moving Targets with a Kalman Filter

AI-2002 Artificial Intelligence Lab, Fall 2026, FAST-NUCES Karachi

Interceptor is a 2D arcade game in which a drone flies across the screen and a
radar reports its position with random noise. You control a turret and compete
against two automatic turrets:

| Turret | What it does |
|---|---|
| **Raw radar** (orange) | Aims straight at the latest noisy radar reading. This is the baseline. |
| **Kalman** (purple) | Runs a Kalman filter to estimate the drone's position and velocity, then aims ahead of it at the predicted interception point. |

The game shows the true drone (red), the noisy radar dots (blue), the Kalman
estimate (purple ring) and the predicted aim point (white cross). Hit rate and
position error are measured with fixed-seed experiments.

## Screenshots

| Title page | Level select |
|---|---|
| ![Title page](report_assets/ui_menu.png) | ![Level select](report_assets/ui_levels.png) |

| Easy level (straight path, noise 15) | Hard level (turning path, noise 80) |
|---|---|
| ![Easy level](report_assets/ui_game_easy.png) | ![Hard level](report_assets/ui_game_hard.png) |

In the game, the red drone is the true target, blue dots are the noisy radar readings, the purple ring is the
Kalman estimate and the white cross is the predicted aim point.

## Course connection

This project applies the filtering topic of Lab 7 (Dynamic Bayesian Networks, HMM and Kalman filters) of
AL-2002 Artificial Intelligence Lab. The Kalman filter keeps a belief about the hidden state of the drone
(position and velocity) and updates it with every noisy radar reading.

## Requirements

- Python 3.10 or newer
- `pygame-ce`, `numpy`, `matplotlib`

```bash
pip install -r requirements.txt
```

Install `pygame-ce`, not `pygame`. If both are installed the game may fail to start; run
`pip uninstall pygame` first.

## Run the game

```bash
python main.py
```

Flow: title page (enter your name) -> loading bar -> level select -> game ->
results screen. The game opens in full screen; press `F11` to switch to a window.

| Level | Path | Drone speed | Radar noise | Time |
|---|---|---|---|---|
| Easy | straight | 100 | 15 | 60 s |
| Medium | diagonal | 130 | 40 | 60 s |
| Hard | turning (sudden turn) | 180 | 80 | 60 s |
| Lab | free play | adjustable | adjustable | untimed |

Your score is the number of hits in 60 seconds. The top 5 players of each timed level (one line per player,
best score only) are shown on the **leaderboard** (press `L` on the level-select page). Scores are saved in
`scores.json` on your own computer; the file is not part of the repository, so the leaderboard starts empty
on a fresh clone.

### Controls

| Key / mouse | Action |
|---|---|
| Mouse | Aim the green turret |
| Left click | Fire |
| P | Pause or resume (timed levels) |
| M | Mute or unmute sound |
| L (level select page) | Open the leaderboard (top 5 players per level) |
| F11 | Switch between full screen and a window |
| Esc | Back to level select |
| Results screen: Enter or R | Play the level again |
| Results screen: Esc | Back to level select |
| Lab only: slider, Up / Down | Change radar noise |
| Lab only: Trajectory buttons, T | Change drone path |

## How it works

**Drone and radar.** The drone moves along a straight, diagonal or turning path.
`RadarSensor` adds Gaussian noise (standard deviation in pixels) to its true
x and y position. The automatic turrets only ever see these noisy readings.

**Kalman filter** (`kalman_filter.py`, own implementation with NumPy).
A linear filter with a constant-velocity model.

- State: `[x, y, vx, vy]`; measurement: `[x, y]`.
- `predict(dt)` moves the estimate forward and grows its uncertainty.
- `update(z)` corrects the estimate with a new radar reading, weighted by the
  Kalman gain.
- `accel_noise` (process noise) controls how much the filter trusts its motion
  model compared with the radar.

**Lead aiming.** The Kalman turret estimates how long a projectile needs to
reach the drone, projects the estimated position forward by that time, and
aims at that point.

**This project does not use machine learning.** It is probabilistic state
estimation: the filter's matrices come from the motion model and the noise
level, not from training data. Neural-network training was out of scope in the
proposal.

## Experiments

All experiments run without a window, use a fixed time step and fixed seeds
(1 to 30), and can be reproduced. Each script takes from a few seconds to about two minutes.

```bash
python experiments.py    # 3 paths x 5 noise levels x 30 runs x 2 turrets -> results/results.csv
python charts.py         # charts 1-4 and 9 from results.csv
python sweep.py          # accel_noise sweep -> results/sweep.csv and chart 5
python control.py        # control turrets -> results/control.csv and chart 6
python control_window.py # stronger baselines (differencing, least-squares fit) -> results/control_window.csv, charts 7-8
python test_kalman.py    # quick test plot: true, noisy and estimated path
```

| Chart | File |
|---|---|
| 1. Position RMSE vs radar noise | `results/chart1_rmse_vs_noise.png` |
| 2. Hit rate vs radar noise | `results/chart2_hit_rate_vs_noise.png` |
| 3. True, noisy and estimated trajectory | `results/chart3_trajectory.png` |
| 4. Estimation error over time | `results/chart4_error_over_time.png` |
| 5. Effect of `accel_noise` | `results/chart5_accel_noise_sweep.png` |
| 6. Control turrets | `results/chart6_control_turret.png` |
| 7. Stronger non-Kalman baselines (best window) | `results/chart7_stronger_baselines.png` |
| 8. Effect of the baseline window length | `results/chart8_window_length.png` |
| 9. Future-position prediction error vs radar noise | `results/chart9_prediction_error_vs_noise.png` |

### Metrics

| Metric | Meaning |
|---|---|
| Hit rate (%) | Hits divided by shots fired |
| Position RMSE (px) | Distance between the estimate (radar reading or Kalman) and the true position, while the drone is on screen |
| Prediction error (px) | At each shot, how far the predicted point (raw: latest reading, Kalman: lead point) was from the drone's true position when the bullet was due to arrive |
| Response time (s) | Time from the drone entering the screen to the turret's first hit (only runs with a hit) |
| Shots | Ammunition used |

### Main results (30 runs per setting)

| Path | Noise | Raw hit rate | Kalman hit rate | Raw RMSE (px) | Kalman RMSE (px) | Raw pred. error (px) | Kalman pred. error (px) |
|---|---|---|---|---|---|---|---|
| Straight | 15 | 0.0% | 72.6% | 21.2 | 4.4 | 165.4 | 14.3 |
| Straight | 100 | 5.0% | 39.5% | 141.5 | 23.0 | 204.5 | 63.5 |
| Diagonal | 15 | 0.0% | 87.1% | 21.2 | 4.4 | 137.0 | 12.3 |
| Turning | 15 | 0.0% | 58.9% | 21.2 | 6.1 | 158.4 | 25.3 |
| Turning | 100 | 4.9% | 29.1% | 141.5 | 28.6 | 199.3 | 79.3 |

The full table, with prediction error and response time, is in `results/summary.txt`.

The raw-radar turret has no velocity estimate and does not aim ahead, so it
misses a moving drone almost every time, even at low noise. To separate the
effect of **filtering** from the effect of **lead aiming**, `control.py` adds
two control turrets: a raw turret placed at the Kalman turret's position, and
a raw turret that also leads its shot using only raw readings. Kalman
filtering still comes out ahead of the raw-plus-lead turret at every noise
level (for example, straight path at noise 15: 17.9% vs 72.6%). See
`results/control_summary.txt`.

### Stronger baselines (honest result)

`control_window.py` compares Kalman with raw-reading turrets that lead their shot using velocity from
differencing or a least-squares line fit over a window of 0.25 to 2 s. Kalman matches or beats every differencing
baseline in all 15 settings, but a least-squares fit over a 1 to 2 s window is ahead of Kalman in 11 of 15 settings
(at low and medium noise), by 1.6 to 10.2 points. Kalman is best at high noise (60 and 100) on straight and
diagonal paths. The fit needs 1 to 2 s of data, a window chosen in advance (we report the best window per
setting) and reacts slowly to a turn. Kalman works online, needs no window and gives an uncertainty estimate.
See `results/control_window_summary.txt`.

### Limitations

- The filter uses a constant-velocity model, so a sudden turn lowers accuracy
  until the filter catches up (the turning path has the lowest hit rates).
- Very high radar noise lowers hit rate for every method.
- The simulation is 2D and uses simulated data only.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Game loop and screen flow |
| `screens.py` | Menu, loading, level select and results screens |
| `game_manager.py` | Game state, turrets, drone, radar and Kalman filter wiring |
| `drone.py`, `radar_sensor.py`, `turret.py`, `projectile.py` | Game objects |
| `kalman_filter.py` | Kalman filter |
| `test_kalman.py` | Quick test plot of the filter (true, noisy and estimated path) |
| `overlay.py`, `ui.py` | Trails, live stats, sliders, buttons |
| `sounds.py`, `music.py` | Sound effects and background music |
| `scores.py` | Saved scores and the top-5 leaderboard |
| `theme.py`, `sprites.py` | Arcade look: colours, fonts, drone and turret sprites |
| `settings.py` | Constants and level settings |
| `experiments.py`, `charts.py`, `sweep.py`, `control.py`, `control_window.py` | Experiments and charts |
| `assets/` | Pixel font used by the interface |
| `results/`, `report_assets/` | Experiment outputs (CSV, summaries, charts) and screenshots |

## Team

| Name | Roll number | Role |
|---|---|---|
| Hira Bashir | 24K-3064 | Game loop, interface, drone, player controls, projectiles |
| Fariha Nasir | 24K-3058 | Kalman filter, radar-noise model, baselines, metrics, charts |