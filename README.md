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

## Requirements

- Python 3.10 or newer
- `pygame-ce`, `numpy`, `matplotlib`

```bash
pip install -r requirements.txt
```

## Run the game

```bash
python main.py
```

Flow: title page (enter your name) -> loading bar -> level select -> game ->
results screen.

| Level | Path | Drone speed | Radar noise | Time |
|---|---|---|---|---|
| Easy | straight | 100 | 15 | 60 s |
| Medium | diagonal | 130 | 40 | 60 s |
| Hard | turning (sudden turn) | 180 | 80 | 60 s |
| Lab | free play | adjustable | adjustable | untimed |

Your best score for each level is saved locally in `scores.json`.

### Controls

| Key / mouse | Action |
|---|---|
| Mouse | Aim the green turret |
| Left click | Fire |
| P | Pause or resume (timed levels) |
| M | Mute or unmute sound |
| Esc | Back to level select |
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
(1 to 30), and can be reproduced.

```bash
python experiments.py    # 3 paths x 5 noise levels x 30 runs x 2 turrets -> results/results.csv
python charts.py         # charts 1-4 from results.csv
python sweep.py          # accel_noise sweep -> results/sweep.csv and chart 5
python control.py        # control turrets -> results/control.csv and chart 6
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

### Main results (30 runs per setting)

| Path | Noise | Raw hit rate | Kalman hit rate | Raw RMSE (px) | Kalman RMSE (px) |
|---|---|---|---|---|---|
| Straight | 15 | 0.0% | 72.6% | 21.2 | 4.4 |
| Straight | 100 | 5.0% | 39.5% | 141.5 | 23.0 |
| Diagonal | 15 | 0.0% | 87.1% | 21.2 | 4.4 |
| Turning | 15 | 0.0% | 58.9% | 21.2 | 6.1 |
| Turning | 100 | 4.9% | 29.1% | 141.5 | 28.6 |

The full table is in `results/summary.txt`.

The raw-radar turret has no velocity estimate and does not aim ahead, so it
misses a moving drone almost every time, even at low noise. To separate the
effect of **filtering** from the effect of **lead aiming**, `control.py` adds
two control turrets: a raw turret placed at the Kalman turret's position, and
a raw turret that also leads its shot using only raw readings. Kalman
filtering still comes out ahead of the raw-plus-lead turret at every noise
level (for example, straight path at noise 15: 17.9% vs 72.6%). See
`results/control_summary.txt`.

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
| `overlay.py`, `ui.py` | Trails, live stats, sliders, buttons |
| `sounds.py`, `scores.py` | Sound effects and saved best scores |
| `settings.py` | Constants and level settings |
| `experiments.py`, `charts.py`, `sweep.py`, `control.py` | Experiments and charts |
| `results/`, `report_assets/` | Experiment outputs and screenshots |

## Team

| Name | Roll number | 
|---|---|
| Fariha Nasir | [24K-3058] | 
| Hira Bashir | [24K-3064] |