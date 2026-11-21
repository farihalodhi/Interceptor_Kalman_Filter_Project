import numpy as np
import matplotlib.pyplot as plt

from drone import Drone
from radar_sensor import RadarSensor
from kalman_filter import KalmanFilter

NOISE = 15
SEED = 42
DT = 1 / 60

drone = Drone("straight")                       # same path as the Easy level
radar = RadarSensor(NOISE, SEED)
kf = KalmanFilter(NOISE)

true_pts, noisy_pts, est_pts = [], [], []

while not drone.is_out():
    drone.update(DT)
    z = radar.measure(drone)

    kf.predict(DT)
    kf.update(z)

    true_pts.append((drone.x, drone.y))
    noisy_pts.append(z)
    est_pts.append(kf.position())

true_pts, noisy_pts, est_pts = map(np.array, (true_pts, noisy_pts, est_pts))

# skip the first second so the filter can "warm up"
skip = 60
raw_err = np.linalg.norm(noisy_pts[skip:] - true_pts[skip:], axis=1)
kf_err = np.linalg.norm(est_pts[skip:] - true_pts[skip:], axis=1)
print(f"Raw radar RMSE : {np.sqrt(np.mean(raw_err ** 2)):.2f} px")
print(f"Kalman RMSE    : {np.sqrt(np.mean(kf_err ** 2)):.2f} px")

plt.figure(figsize=(10, 5))
plt.scatter(noisy_pts[:, 0], noisy_pts[:, 1], s=4, c="lightskyblue", label="Noisy radar")
plt.plot(true_pts[:, 0], true_pts[:, 1], "r-", lw=2, label="True path")
plt.plot(est_pts[:, 0], est_pts[:, 1], "g-", lw=2, label="Kalman estimate")
plt.gca().invert_yaxis()                 # screen coordinates: y grows downward
plt.xlabel("x (pixels)")
plt.ylabel("y (pixels)")
plt.title(f"Kalman filter test (noise = {NOISE}px, seed = {SEED})")
plt.legend()
plt.tight_layout()
plt.savefig("kalman_test_plot.png", dpi=150)
plt.show()