# game_manager.py
import math
from settings import WIDTH, HEIGHT, PROJECTILE_SPEED, KALMAN_WARMUP_FRAMES
from drone import Drone, PATTERNS
from turret import Turret
from radar_sensor import RadarSensor
from kalman_filter import KalmanFilter


class GameManager:
    def __init__(self, noise=15, seed=42, pattern="straight"):
        self.drone = Drone(pattern)
        self.radar = RadarSensor(noise, seed)
        self.kalman = KalmanFilter(noise)
        self.player = Turret(WIDTH // 2, HEIGHT - 40, "Player")
        self.raw_turret = Turret(WIDTH // 4, HEIGHT - 40, "Raw radar")
        self.kalman_turret = Turret(3 * WIDTH // 4, HEIGHT - 40, "Kalman")
        self.radar_dots = []          # recent noisy readings, for drawing
        self.aim_point = None         # Kalman turret's predicted intercept point
        self.warmup_frames = 0

    def aim_player(self, x, y):
        self.player.aim_at(x, y)

    def player_fire(self):
        self.player.fire()

    def change_noise(self, amount):
        noise = max(0, self.radar.noise + amount)
        self.radar.set_noise(noise)
        self.kalman.set_noise(noise)
        self.reset_scores()

    def reset_scores(self):
        for turret in (self.player, self.raw_turret, self.kalman_turret):
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

    def update(self, dt):
        self.drone.update(dt)

        # the radar is the only thing that sees the drone's true position
        reading = self.radar.measure(self.drone)
        self.radar_dots.append(reading)
        if len(self.radar_dots) > 30:
            self.radar_dots.pop(0)

        # Kalman filter: predict forward, then correct with the new reading
        self.kalman.predict(dt)
        self.kalman.update(reading)
        self.warmup_frames += 1

        # raw-radar turret: aim at the latest noisy reading
        self.raw_turret.aim_at(reading[0], reading[1])
        if self.drone.x > 0:
            self.raw_turret.fire()

        # Kalman turret: aim ahead of the estimated position
        if self.warmup_frames >= KALMAN_WARMUP_FRAMES:
            self.aim_point = self.lead_point()
            self.kalman_turret.aim_at(self.aim_point[0], self.aim_point[1])
            if self.drone.x > 0:
                self.kalman_turret.fire()

        for turret in (self.player, self.raw_turret, self.kalman_turret):
            turret.update(dt)
            if turret.check_hit(self.drone):
                self.reset_round()

        if self.drone.is_out():
            self.reset_round()