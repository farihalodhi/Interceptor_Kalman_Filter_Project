# overlay.py
import math
from collections import deque

import numpy as np
import pygame

from settings import KALMAN_WARMUP_FRAMES

BACKGROUND = (20, 20, 30)
PANEL_COLOR = (30, 32, 46, 205)       # last number = transparency
MUTED = (150, 155, 180)
TEXT = (240, 240, 240)

DRONE_COLOR = (220, 60, 60)
RADAR_COLOR = (90, 160, 255)
KALMAN_COLOR = (200, 120, 255)
PLAYER_COLOR = (80, 200, 120)
RAW_COLOR = (240, 170, 60)


def draw_panel(screen, rect):
    # semi-transparent rounded box
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, PANEL_COLOR, panel.get_rect(), border_radius=10)
    screen.blit(panel, rect.topleft)


def draw_text(screen, font, text, color, x, y, right=False):
    label = font.render(text, True, color)
    if right:
        x -= label.get_width()
    screen.blit(label, (x, y))


class Trail:
    """The last few positions of something, drawn as a fading line."""

    def __init__(self, color, length=90):
        self.color = color
        self.length = length
        self.points = []

    def add(self, x, y):
        self.points.append((int(x), int(y)))
        if len(self.points) > self.length:
            self.points.pop(0)

    def clear(self):
        self.points = []

    def draw(self, screen):
        count = len(self.points)
        for i in range(1, count):
            fade = i / count              # 0 = oldest, 1 = newest
            color = tuple(int(BACKGROUND[c]
                              + (self.color[c] - BACKGROUND[c]) * fade)
                          for c in range(3))
            pygame.draw.line(screen, color, self.points[i - 1],
                             self.points[i], 2)


class ErrorTracker:
    """Average distance from the true position over the last 2 seconds,
    for the raw radar reading and for the Kalman estimate."""

    def __init__(self, frames=120):
        self.raw = deque(maxlen=frames)
        self.kalman = deque(maxlen=frames)

    def clear(self):
        self.raw.clear()
        self.kalman.clear()

    def add(self, game):
        if (game.drone.x <= 0 or not game.kalman.initialized
                or game.warmup_frames < KALMAN_WARMUP_FRAMES
                or not game.radar_dots):
            return
        true_x, true_y = game.drone.x, game.drone.y
        raw_x, raw_y = game.radar_dots[-1]
        est_x, est_y = game.kalman.position()
        self.raw.append(math.hypot(raw_x - true_x, raw_y - true_y))
        self.kalman.append(math.hypot(est_x - true_x, est_y - true_y))

    def averages(self):
        if not self.raw:
            return None
        return (sum(self.raw) / len(self.raw),
                sum(self.kalman) / len(self.kalman))


def draw_uncertainty(screen, kalman, color):
    # the filter's own belief about its position error: an ellipse
    # two standard deviations wide, taken from the covariance matrix P
    if not kalman.initialized:
        return
    cov = kalman.P[:2, :2]                       # x-y part of the 4x4 matrix
    values, vectors = np.linalg.eigh(cov)        # ascending order
    values = np.maximum(values, 0.0)
    major = 2 * math.sqrt(values[1])
    minor = 2 * math.sqrt(values[0])
    angle = math.atan2(vectors[1, 1], vectors[0, 1])

    center_x, center_y = kalman.position()
    points = []
    for k in range(40):
        t = 2 * math.pi * k / 40
        px = major * math.cos(t)
        py = minor * math.sin(t)
        x = center_x + px * math.cos(angle) - py * math.sin(angle)
        y = center_y + px * math.sin(angle) + py * math.cos(angle)
        points.append((int(x), int(y)))
    pygame.draw.lines(screen, color, True, points, 2)


def draw_stats(screen, font, game, tracker):
    draw_panel(screen, pygame.Rect(10, 10, 300, 172))
    draw_text(screen, font, "TURRETS", MUTED, 24, 18)
    turrets = ((game.player, PLAYER_COLOR),
               (game.raw_turret, RAW_COLOR),
               (game.kalman_turret, KALMAN_COLOR))
    y = 40
    for turret, color in turrets:
        pygame.draw.circle(screen, color, (30, y + 8), 6)
        draw_text(screen, font, turret.name, TEXT, 44, y)
        stats = f"{turret.hits}/{turret.shots}   {turret.hit_rate():.0f}%"
        draw_text(screen, font, stats, TEXT, 296, y, right=True)
        y += 22

    draw_text(screen, font, "POSITION ERROR, LAST 2 S", MUTED, 24, 114)
    averages = tracker.averages()
    for i, (name, color) in enumerate((("Raw radar", RAW_COLOR),
                                       ("Kalman", KALMAN_COLOR))):
        row_y = 136 + i * 22
        pygame.draw.circle(screen, color, (30, row_y + 8), 6)
        draw_text(screen, font, name, TEXT, 44, row_y)
        value = "-" if averages is None else f"{averages[i]:.1f} px"
        draw_text(screen, font, value, TEXT, 296, row_y, right=True)


def draw_legend(screen, font, x, y):
    draw_panel(screen, pygame.Rect(x, y, 190, 126))
    labels = ("Drone (true)", "Radar reading", "Kalman estimate",
              "Uncertainty (2 sd)", "Aim point")
    for i, label in enumerate(labels):
        cx = x + 20
        cy = y + 18 + i * 22
        if i == 0:
            pygame.draw.circle(screen, DRONE_COLOR, (cx, cy), 6)
        elif i == 1:
            pygame.draw.circle(screen, RADAR_COLOR, (cx, cy), 3)
        elif i == 2:
            pygame.draw.circle(screen, KALMAN_COLOR, (cx, cy), 7, 2)
        elif i == 3:
            pygame.draw.ellipse(screen, KALMAN_COLOR,
                                pygame.Rect(cx - 9, cy - 5, 18, 10), 1)
        else:
            pygame.draw.line(screen, TEXT, (cx - 6, cy), (cx + 6, cy), 2)
            pygame.draw.line(screen, TEXT, (cx, cy - 6), (cx, cy + 6), 2)
        draw_text(screen, font, label, TEXT, x + 38, cy - 8)