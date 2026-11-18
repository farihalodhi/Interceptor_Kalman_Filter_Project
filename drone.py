# drone.py
import math
from settings import DRONE_RADIUS, DRONE_SPEED, TURN_TIME, TURN_ANGLE, WIDTH

PATTERNS = ("straight", "diagonal", "turning")


class Drone:
    def __init__(self, pattern="straight", start_y=None, speed=None):
        if pattern not in PATTERNS:
            raise ValueError("pattern must be one of " + str(PATTERNS))
        self.pattern = pattern
        self.start_y = start_y      # None = use the pattern's default height
        self.speed = DRONE_SPEED if speed is None else speed
        self.reset()

    def set_pattern(self, pattern):
        if pattern not in PATTERNS:
            raise ValueError("pattern must be one of " + str(PATTERNS))
        self.pattern = pattern
        self.reset()

    def reset(self):
        self.time = 0.0             # seconds since the round started
        self.turned = False
        self.x = -DRONE_RADIUS

        if self.pattern == "straight":
            default_y, angle = 200, 0
        elif self.pattern == "diagonal":
            default_y, angle = 100, 18
        else:                       # turning: starts straight
            default_y, angle = 150, 0

        self.y = default_y if self.start_y is None else self.start_y
        self.set_heading(angle)

    def set_heading(self, angle_degrees):
        angle = math.radians(angle_degrees)
        self.vx = self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

    def update(self, dt):
        self.time += dt

        # the sudden turn happens once, at a fixed time
        if self.pattern == "turning" and not self.turned \
                and self.time >= TURN_TIME:
            self.set_heading(TURN_ANGLE)
            self.turned = True

        # distance = speed * time
        self.x += self.vx * dt
        self.y += self.vy * dt

    def is_out(self):
        return self.x > WIDTH + DRONE_RADIUS