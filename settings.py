WIDTH = 900
HEIGHT = 600
FPS = 60
DRONE_RADIUS = 15
PROJECTILE_RADIUS = 4
PROJECTILE_SPEED = 400      # pixels per second
TURRET_COOLDOWN = 0.5    # seconds between shots
KALMAN_WARMUP_FRAMES = 20
DRONE_SPEED = 130           # pixels per second
TURN_TIME = 3.0             # seconds of flight before the sudden turn
TURN_ANGLE = 25             # degrees the heading changes at the turn
HUD_HEIGHT = 70             # height of the control strip below the arena

# difficulty levels chosen on the level-select screen
LEVELS = {
    "Easy":   {"pattern": "straight", "speed": 100, "noise": 15,
               "info": "Straight path, low noise"},
    "Medium": {"pattern": "diagonal", "speed": 130, "noise": 40,
               "info": "Diagonal path, more noise"},
    "Hard":   {"pattern": "turning",  "speed": 180, "noise": 80,
               "info": "Fast, turning, very noisy"},
}
