
import math
from settings import TURRET_COOLDOWN
from projectile import Projectile


class Turret:
    def __init__(self, x, y, name="Turret"):
        self.x = x
        self.y = y
        self.name = name
        self.angle = -math.pi / 2     # pointing straight up
        self.timer = 0                # time left until it can fire again
        self.projectiles = []         # this turret's own bullets
        self.shots = 0
        self.hits = 0

    def aim_at(self, target_x, target_y):
        self.angle = math.atan2(target_y - self.y, target_x - self.x)

    def fire(self):
        if self.timer > 0:
            return False              # still cooling down
        self.timer = TURRET_COOLDOWN
        self.projectiles.append(Projectile(self.x, self.y, self.angle))
        self.shots += 1
        return True

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
        for p in self.projectiles:
            p.update(dt)
        self.projectiles = [p for p in self.projectiles if p.alive]

    def check_hit(self, drone):
        for p in self.projectiles:
            if p.hits(drone):
                p.alive = False
                self.hits += 1
                return True
        return False

    def hit_rate(self):
        if self.shots == 0:
            return 0.0
        return 100 * self.hits / self.shots