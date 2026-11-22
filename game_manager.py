# game_manager.py
import math
from collections import deque

import numpy as np

from settings import WIDTH, HEIGHT, PROJECTILE_SPEED, KALMAN_WARMUP_FRAMES
from drone import Drone, PATTERNS
from turret import Turret
from radar_sensor import RadarSensor
from kalman_filter import KalmanFilter

LEAD_WINDOW = 0.5     # seconds of readings used by the "raw + lead" control turret


class GameManager:
    def __init__(self, noise=15, seed=42, pattern="straight",
                 start_y=None, auto_reset=True, speed=None,
                 control_turret=False, lead_variants=None):
        # auto_reset=True: a hit or the drone leaving restarts the round (game)
        # auto_reset=False: the drone always flies its full path (experiments)
        # control_turret=True: adds two extra turrets for the control
        # experiment (never used by the game itself)
        # lead_variants: list of (name, method, window) for the baseline sweep;
        # each adds a turret at the Kalman position that leads its shot using
        # a velocity estimated from raw readings (never used by the game)
        self.auto_reset = auto_reset
        self.control_turret = control_turret
        self.drone = Drone(pattern, start_y, speed)
        self.radar = RadarSensor(noise, seed)
        self.kalman = KalmanFilter(noise)
        self.player = Turret(WIDTH // 2, HEIGHT - 40, "Player")
        self.raw_turret = Turret(WIDTH // 4, HEIGHT - 40, "Raw radar")
        self.kalman_turret = Turret(3 * WIDTH // 4, HEIGHT - 40, "Kalman")
        self.raw_same = None
        self.lead_turret = None
        if control_turret:
            # both sit at the Kalman turret's position, so the only
            # difference between them and the Kalman turret is the method
            self.raw_same = Turret(3 * WIDTH // 4, HEIGHT - 40,
                                   "Raw radar (same position)")
            self.lead_turret = Turret(3 * WIDTH // 4, HEIGHT - 40,
                                      "Raw + lead")
        self.variant_turrets = []
        self.variant_specs = []
        for name, method, window in (lead_variants or []):
            self.variant_turrets.append(Turret(3 * WIDTH // 4, HEIGHT - 40,
                                               name))
            self.variant_specs.append((method, window))
        windows = [LEAD_WINDOW] + [w for _, _, w in (lead_variants or [])]
        self.buffer_window = max(windows)
        self.keep_readings = control_turret or bool(lead_variants)

        self.radar_dots = []          # recent noisy readings, for drawing
        self.readings = deque()       # (time, x, y) readings for the controls
        self.sim_time = 0.0
        self.aim_point = None         # Kalman turret's predicted intercept point
        self.warmup_frames = 0
        self.record_events = False #main.py turns this on to play sound
        self.events = []

    def _event(self,kind,who):
        if self.record_events:
            self.events.append((kind,who))

    def all_turrets(self):
        turrets = [self.player, self.raw_turret, self.kalman_turret]
        if self.control_turret:
            turrets += [self.raw_same, self.lead_turret]
        turrets += self.variant_turrets
        return turrets

    def aim_player(self, x, y):
        self.player.aim_at(x, y)

    def player_fire(self):
        if self.player.fire():
            self._event("fire",self.player.name)

    def change_noise(self, amount):
        noise = max(0, self.radar.noise + amount)
        self.radar.set_noise(noise)
        self.kalman.set_noise(noise)
        self.reset_scores()

    def reset_scores(self):
        for turret in self.all_turrets():
            turret.shots = 0
            turret.hits = 0
            turret.projectiles = []

    def set_pattern(self, pattern):
        self.drone.set_pattern(pattern)
        self.reset_round()
        self.reset_scores()

    def next_pattern(self):
        i = PATTERNS.index(self.drone.pattern)
        self.set_pattern(PATTERNS[(i + 1) % len(PATTERNS)])

    def reset_round(self):
        self.drone.reset()
        self.radar_dots = []
        self.readings.clear()
        self.kalman.reset()
        self.aim_point = None
        self.warmup_frames = 0

    def lead_point(self):
        # where should the Kalman turret aim so the bullet meets the drone?
        t = 0.0
        for _ in range(3):
            ax, ay = self.kalman.predict_ahead(t)
            distance = math.hypot(ax - self.kalman_turret.x,
                                  ay - self.kalman_turret.y)
            t = distance / PROJECTILE_SPEED
        return self.kalman.predict_ahead(t)

    def _lead_from(self, x, y, vx, vy, turret):
        # same calculation as lead_point, but from a raw position and velocity
        t = 0.0
        for _ in range(3):
            ax, ay = x + vx * t, y + vy * t
            distance = math.hypot(ax - turret.x, ay - turret.y)
            t = distance / PROJECTILE_SPEED
        return x + vx * t, y + vy * t

    def _estimate(self, method, window):
        # position and velocity of the drone from the raw readings of the
        # last `window` seconds, or None if there are too few of them yet
        start = self.sim_time - window
        data = [r for r in self.readings if r[0] >= start]
        old_t, old_x, old_y = data[0]
        new_t, new_x, new_y = data[-1]
        span = new_t - old_t
        if span < window / 2:
            return None
        if method == "diff":
            # velocity from the oldest and the newest reading only
            return (new_x, new_y,
                    (new_x - old_x) / span, (new_y - old_y) / span)
        # "fit": least-squares straight line through every reading in the
        # window; its value at the newest time is a smoothed position
        times = np.array([r[0] for r in data]) - new_t
        xs = np.array([r[1] for r in data])
        ys = np.array([r[2] for r in data])
        slope_x, x_now = np.polyfit(times, xs, 1)
        slope_y, y_now = np.polyfit(times, ys, 1)
        return float(x_now), float(y_now), float(slope_x), float(slope_y)

    def _update_control_turrets(self, reading):
        # control 1: aim at the latest raw reading, from the Kalman position
        self.raw_same.aim_at(reading[0], reading[1])
        if self.drone.x > 0:
            self.raw_same.fire()

        # control 2: raw reading plus a lead, with the velocity estimated by
        # differencing the readings over the last LEAD_WINDOW seconds (no filter)
        if self.warmup_frames >= KALMAN_WARMUP_FRAMES:
            estimate = self._estimate("diff", LEAD_WINDOW)
            if estimate is not None:
                x, y, vx, vy = estimate
                ax, ay = self._lead_from(x, y, vx, vy, self.lead_turret)
                self.lead_turret.aim_at(ax, ay)
                if self.drone.x > 0:
                    self.lead_turret.fire()

    def _update_variants(self):
        if self.warmup_frames < KALMAN_WARMUP_FRAMES:
            return
        for turret, (method, window) in zip(self.variant_turrets,
                                            self.variant_specs):
            estimate = self._estimate(method, window)
            if estimate is None:
                continue
            x, y, vx, vy = estimate
            ax, ay = self._lead_from(x, y, vx, vy, turret)
            turret.aim_at(ax, ay)
            if self.drone.x > 0:
                turret.fire()

    def update(self, dt):
        self.drone.update(dt)

        # the radar is the only thing that sees the drone's true position
        reading = self.radar.measure(self.drone)
        self.radar_dots.append(reading)
        if len(self.radar_dots) > 30:
            self.radar_dots.pop(0)

        self.sim_time += dt
        if self.keep_readings:
            self.readings.append((self.sim_time, reading[0], reading[1]))
            while self.readings[0][0] < self.sim_time - self.buffer_window:
                self.readings.popleft()

        # Kalman filter: predict forward, then correct with the new reading
        self.kalman.predict(dt)
        self.kalman.update(reading)
        self.warmup_frames += 1

        # raw-radar turret: aim at the latest noisy reading
        self.raw_turret.aim_at(reading[0], reading[1])
        if self.drone.x > 0 and self.raw_turret.fire():
            self._event("fire",self.raw_turret.name)

        # Kalman turret: aim ahead of the estimated position
        if self.warmup_frames >= KALMAN_WARMUP_FRAMES:
            self.aim_point = self.lead_point()
            self.kalman_turret.aim_at(self.aim_point[0], self.aim_point[1])
            if self.drone.x > 0 and self.kalman_turret.fire():
                self._event("fire",self.kalman_turret.name)

        if self.control_turret:
            self._update_control_turrets(reading)
        if self.variant_turrets:
            self._update_variants()

        for turret in self.all_turrets():
            turret.update(dt)
            if turret.check_hit(self.drone):
                self._event("hit",turret.name)
                if self.auto_reset:
                    self.reset_round()

        if self.drone.is_out() and self.auto_reset:
            self.reset_round()