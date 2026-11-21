# game_manager.py
import math
from collections import deque
from settings import WIDTH, HEIGHT, PROJECTILE_SPEED, KALMAN_WARMUP_FRAMES
from drone import Drone, PATTERNS
from turret import Turret
from radar_sensor import RadarSensor
from kalman_filter import KalmanFilter

LEAD_WINDOW = 0.5     # seconds of radar readings used by the "raw + lead" turret


class GameManager:
    def __init__(self, noise=15, seed=42, pattern="straight",
                 start_y=None, auto_reset=True, speed=None,
                 control_turret=False):
        # auto_reset=True: a hit or the drone leaving restarts the round (game)
        # auto_reset=False: the drone always flies its full path (experiments)
        # control_turret=True: adds two extra turrets for the control
        # experiment (never used by the game itself)
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
        self.radar_dots = []          # recent noisy readings, for drawing
        self.readings = deque()       # (time, x, y) readings for raw + lead
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

    def _update_control_turrets(self, reading):
        # control 1: aim at the latest raw reading, from the Kalman position
        self.raw_same.aim_at(reading[0], reading[1])
        if self.drone.x > 0:
            self.raw_same.fire()

        # control 2: raw reading plus a lead, with the velocity estimated by
        # differencing the readings over the last LEAD_WINDOW seconds (no filter)
        old_t, old_x, old_y = self.readings[0]
        new_t, new_x, new_y = self.readings[-1]
        span = new_t - old_t
        if self.warmup_frames >= KALMAN_WARMUP_FRAMES and span >= LEAD_WINDOW / 2:
            vx = (new_x - old_x) / span
            vy = (new_y - old_y) / span
            ax, ay = self._lead_from(new_x, new_y, vx, vy, self.lead_turret)
            self.lead_turret.aim_at(ax, ay)
            if self.drone.x > 0:
                self.lead_turret.fire()

    def update(self, dt):
        self.drone.update(dt)

        # the radar is the only thing that sees the drone's true position
        reading = self.radar.measure(self.drone)
        self.radar_dots.append(reading)
        if len(self.radar_dots) > 30:
            self.radar_dots.pop(0)

        self.sim_time += dt
        if self.control_turret:
            self.readings.append((self.sim_time, reading[0], reading[1]))
            while self.readings[0][0] < self.sim_time - LEAD_WINDOW:
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

        for turret in self.all_turrets():
            turret.update(dt)
            if turret.check_hit(self.drone):
                self._event("hit",turret.name)
                if self.auto_reset:
                    self.reset_round()

        if self.drone.is_out() and self.auto_reset:
            self.reset_round()