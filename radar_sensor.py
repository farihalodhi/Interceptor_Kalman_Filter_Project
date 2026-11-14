import random


class RadarSensor:
    def __init__(self, noise=15, seed=None):
        self.noise = noise                  # standard deviation in pixels
        self.rng = random.Random(seed)      # own random generator

    def set_noise(self, noise):
        self.noise = noise

    def measure(self, drone):
        # true position + random error, separately for x and y
        measured_x = drone.x + self.rng.gauss(0, self.noise)
        measured_y = drone.y + self.rng.gauss(0, self.noise)
        return measured_x, measured_y