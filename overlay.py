# overlay.py
import math
from collections import deque

import numpy as np
import pygame

from settings import KALMAN_WARMUP_FRAMES
from theme import (SPACE, MUTED, WHITE, RED, BLUE, PURPLE, GREEN, ORANGE,
                   blend, draw_panel, draw_text)


class Trail:
    """The last few positions of something, drawn as a fading, tapering line."""

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
            color = blend(SPACE, self.color, fade)
            pygame.draw.line(screen, color, self.points[i - 1],
                             self.points[i], 1 + int(3 * fade))


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
    # the filter's own belief about its position error: an ellipse two
    # standard deviations wide, taken from the covariance matrix P
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
    for k in range(48):
        t = 2 * math.pi * k / 48
        px = major * math.cos(t)
        py = minor * math.sin(t)
        points.append((center_x + px * math.cos(angle) - py * math.sin(angle),
                       center_y + px * math.sin(angle) + py * math.cos(angle)))

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    left = int(min(xs)) - 3
    top = int(min(ys)) - 3
    width = int(max(xs)) - left + 6
    height = int(max(ys)) - top + 6
    if width <= 0 or height <= 0 or width > 2000 or height > 2000:
        return
    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    local = [(px - left, py - top) for px, py in points]
    pygame.draw.polygon(layer, (*color, 45), local)
    pygame.draw.lines(layer, (*color, 210), True, local, 2)
    screen.blit(layer, (left, top))


def draw_stats(screen, game, tracker):
    draw_panel(screen, pygame.Rect(10, 10, 280, 162), alpha=165, radius=10)
    draw_text(screen, "SCOREBOARD", 12, MUTED, (24, 20), anchor="topleft",
              shadow=False)
    rows = ((game.player, GREEN, "YOU"),
            (game.raw_turret, ORANGE, "RAW RADAR"),
            (game.kalman_turret, PURPLE, "KALMAN"))
    y = 50
    for turret, color, name in rows:
        pygame.draw.circle(screen, color, (30, y), 6)
        draw_text(screen, name, 12, WHITE, (44, y), anchor="midleft",
                  shadow=False)
        stats = f"{turret.hits}/{turret.shots} {turret.hit_rate():.0f}%"
        draw_text(screen, stats, 12, WHITE, (276, y), anchor="midright",
                  shadow=False)
        y += 20

    draw_text(screen, "ERROR, LAST 2 S", 12, MUTED, (24, 108),
              anchor="topleft", shadow=False)
    averages = tracker.averages()
    for i, (name, color) in enumerate((("RAW RADAR", ORANGE),
                                       ("KALMAN", PURPLE))):
        row_y = 138 + i * 20
        pygame.draw.circle(screen, color, (30, row_y), 6)
        draw_text(screen, name, 12, WHITE, (44, row_y), anchor="midleft",
                  shadow=False)
        value = "-" if averages is None else f"{averages[i]:.1f} PX"
        draw_text(screen, value, 12, WHITE, (276, row_y), anchor="midright",
                  shadow=False)


def draw_legend(screen, x, y):
    draw_panel(screen, pygame.Rect(x, y, 190, 126), alpha=150, radius=10)
    items = ("DRONE", "RADAR", "ESTIMATE", "UNCERTAINTY", "AIM POINT")
    for i, label in enumerate(items):
        cx = x + 22
        cy = y + 20 + i * 22
        if i == 0:
            pygame.draw.circle(screen, RED, (cx, cy), 7)
        elif i == 1:
            pygame.draw.circle(screen, BLUE, (cx, cy), 4)
        elif i == 2:
            pygame.draw.circle(screen, PURPLE, (cx, cy), 8, 3)
        elif i == 3:
            pygame.draw.ellipse(screen, PURPLE,
                                pygame.Rect(cx - 11, cy - 6, 22, 12), 2)
        else:
            pygame.draw.line(screen, WHITE, (cx - 7, cy), (cx + 7, cy), 2)
            pygame.draw.line(screen, WHITE, (cx, cy - 7), (cx, cy + 7), 2)
        draw_text(screen, label, 12, WHITE, (x + 44, cy), anchor="midleft",
                  shadow=False)