import math
from settings import TURRET_COOLDOWN
from projectile import Projectile


class Turret:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = -math.pi / 2     # pointing straight up
        self.timer = 0                # time left until it can fire again

    def aim_at(self, target_x, target_y):
        self.angle = math.atan2(target_y - self.y, target_x - self.x)

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    def fire(self):
        if self.timer > 0:
            return None               # still cooling down
        self.timer = TURRET_COOLDOWN
        return Projectile(self.x, self.y, self.angle)