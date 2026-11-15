import numpy as np

class KalmanFilter:

    def __init__(self, noise=15, accel_noise=60):
        # noise       = radar standard deviation in pixels (same as RadarSensor)
        # accel_noise = how much we allow the drone's velocity to wander
        #               (bigger -> trusts radar more, smaller -> trusts model more)
        self.noise = noise
        self.accel_noise = accel_noise
        self.x = np.zeros(4)                      # state estimate
        self.P = np.eye(4)                        # covariance (uncertainty)
        self.H = np.array([[1, 0, 0, 0],          # we only measure x and y
                           [0, 1, 0, 0]], dtype=float)
        self.R = np.eye(2) * max(noise, 1e-3) ** 2    # measurement noise
        self.initialized = False

    def set_noise(self, noise):
        # call this when the noise keys/slider change
        self.noise = noise
        self.R = np.eye(2) * max(noise, 1e-3) ** 2

    def reset(self):
        self.x = np.zeros(4)
        self.P = np.eye(4)
        self.initialized = False

    def _init_from(self, z):
        # start at the first reading, velocity unknown -> very uncertain
        self.x = np.array([z[0], z[1], 0.0, 0.0])
        self.P = np.diag([self.noise ** 2, self.noise ** 2, 200.0 ** 2, 200.0 ** 2])
        self.initialized = True

    def predict(self, dt): # previous estimate ko dt seconds aage badhata hai
        # position = position + velocity * dt
        if not self.initialized:
            return
        F = np.array([[1, 0, dt, 0],
                      [0, 1, 0, dt],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]], dtype=float)
        # process noise for a constant-velocity model (random acceleration)
        q = self.accel_noise ** 2
        Q = q * np.array([[dt**4 / 4, 0, dt**3 / 2, 0],
                          [0, dt**4 / 4, 0, dt**3 / 2],
                          [dt**3 / 2, 0, dt**2, 0],
                          [0, dt**3 / 2, 0, dt**2]])
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, z): #based on noise reading, update the estimate. how much to trust radar.
        # the trust thing will decide Kalman gain(K)
        z = np.asarray(z, dtype=float)
        if not self.initialized:
            self._init_from(z)
            return
        y = z - self.H @ self.x                       # innovation
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)      # Kalman gain
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P

    # ---- helpers the Kalman turret will use later ----
    def position(self):
        return float(self.x[0]), float(self.x[1])

    def velocity(self):
        return float(self.x[2]), float(self.x[3])

    def predict_ahead(self, t):
        """Where will the drone be after t seconds (constant velocity)?"""
        return float(self.x[0] + self.x[2] * t), float(self.x[1] + self.x[3] * t)