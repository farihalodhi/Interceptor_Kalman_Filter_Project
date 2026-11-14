# game_manager.py
from settings import WIDTH, HEIGHT, DRONE_RADIUS
from drone import Drone
from turret import Turret
from radar_sensor import RadarSensor


class GameManager:
    def __init__(self, noise=15, seed=42):
        self.drone = Drone(-DRONE_RADIUS, 150, 120, 30)
        self.radar = RadarSensor(noise, seed)
        self.player = Turret(WIDTH // 2, HEIGHT - 40, "Player")
        self.raw_turret = Turret(WIDTH // 4, HEIGHT - 40, "Raw radar")
        self.radar_dots = []          # recent noisy readings, for drawing

    def aim_player(self, x, y):
        self.player.aim_at(x, y)

    def player_fire(self):
        self.player.fire()

    def change_noise(self, amount):
        self.radar.set_noise(max(0, self.radar.noise + amount))

    def reset_round(self):
        self.drone.reset()
        self.radar_dots = []

    def update(self, dt):
        self.drone.update(dt)

        # the radar is the only thing that sees the drone's true position
        reading = self.radar.measure(self.drone)
        self.radar_dots.append(reading)
        if len(self.radar_dots) > 30:
            self.radar_dots.pop(0)

        # raw-radar turret: aim at the latest noisy reading, fire when ready
        self.raw_turret.aim_at(reading[0], reading[1])
        if self.drone.x > 0:
            self.raw_turret.fire()

        for turret in (self.player, self.raw_turret):
            turret.update(dt)
            if turret.check_hit(self.drone):
                self.reset_round()

        if self.drone.is_out():
            self.reset_round()