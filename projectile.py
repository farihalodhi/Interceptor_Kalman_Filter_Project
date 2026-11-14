import math
from settings import (WIDTH, HEIGHT, PROJECTILE_SPEED,
                      PROJECTILE_RADIUS, DRONE_RADIUS)


class Projectile:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.vx = PROJECTILE_SPEED * math.cos(angle)
        self.vy = PROJECTILE_SPEED * math.sin(angle)
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        # remove the bullet once it leaves the screen
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.alive = False

    def hits(self, drone):
        # collision: distance between centres <= sum of the two radii
        distance = math.hypot(self.x - drone.x, self.y - drone.y)
        return distance <= DRONE_RADIUS + PROJECTILE_RADIUS