from settings import WIDTH, HEIGHT, DRONE_RADIUS


class Drone:
    def __init__(self, x, y, vx, vy):
        self.start = (x, y, vx, vy)   # remember the start so reset() can use it
        self.x = x
        self.y = y
        self.vx = vx                  # velocity in pixels per second
        self.vy = vy

    def update(self, dt):
        # distance = speed * time
        self.x += self.vx * dt
        self.y += self.vy * dt

        # bounce off the top and a lower limit so it stays in view
        if self.y < DRONE_RADIUS or self.y > HEIGHT - 150:
            self.vy = -self.vy

    def is_out(self):
        return self.x > WIDTH + DRONE_RADIUS

    def reset(self):
        self.x, self.y, self.vx, self.vy = self.start