# sprites.py
import math
import random

import pygame

from settings import PROJECTILE_RADIUS
from theme import (SPACE, OUTLINE, WHITE, GOLD, CYAN, RED, VISOR, blend,
                   draw_text, draw_glow)


def draw_drone(surface, x, y, t, body=RED):
    """A small quadcopter with spinning rotors and a crewmate-style visor.
    Its body is about as big as the collision circle."""
    x = int(x)
    y = int(y + math.sin(t * 6) * 2)         # gentle hover bob
    arm = (150, 156, 184)

    draw_glow(surface, CYAN, (x, y + 10), 22, 70)

    for side in (-1, 1):                      # landing legs
        pygame.draw.line(surface, OUTLINE, (x + side * 8, y + 7),
                         (x + side * 12, y + 15), 5)
        pygame.draw.line(surface, arm, (x + side * 8, y + 7),
                         (x + side * 12, y + 15), 2)

    spin = abs(math.cos(t * 40))              # rotors blur as they spin
    half = int(4 + 8 * spin)
    for side in (-1, 1):                      # arms and rotors
        hub = (x + side * 14, y - 11)
        pygame.draw.line(surface, OUTLINE, (x + side * 8, y - 4), hub, 7)
        pygame.draw.line(surface, arm, (x + side * 8, y - 4), hub, 3)
        rotor = pygame.Rect(hub[0] - half, hub[1] - 6, half * 2, 5)
        pygame.draw.ellipse(surface, OUTLINE, rotor.inflate(4, 4))
        pygame.draw.ellipse(surface, (210, 218, 240), rotor)

    body_rect = pygame.Rect(x - 14, y - 8, 28, 18)
    pygame.draw.rect(surface, OUTLINE, body_rect.inflate(6, 6),
                     border_radius=10)
    pygame.draw.rect(surface, body, body_rect, border_radius=8)
    pygame.draw.rect(surface, blend(body, OUTLINE, 0.35),
                     (x - 12, y + 4, 24, 5), border_radius=3)

    visor = pygame.Rect(x + 2, y - 5, 11, 8)  # the drone faces right
    pygame.draw.rect(surface, OUTLINE, visor.inflate(4, 4), border_radius=5)
    pygame.draw.rect(surface, VISOR, visor, border_radius=4)
    pygame.draw.rect(surface, WHITE, (x + 4, y - 4, 5, 2), border_radius=1)

    if int(t * 3) % 2 == 0:                   # blinking light
        pygame.draw.circle(surface, GOLD, (x - 9, y + 1), 2)


def _barrel(surface, x, y, dx, dy, start, end, half_width, color):
    px, py = -dy, dx                          # perpendicular direction
    points = [(x + dx * start + px * half_width, y + dy * start + py * half_width),
              (x + dx * end + px * half_width, y + dy * end + py * half_width),
              (x + dx * end - px * half_width, y + dy * end - py * half_width),
              (x + dx * start - px * half_width, y + dy * start - py * half_width)]
    pygame.draw.polygon(surface, color, points)


def draw_turret(surface, x, y, angle, color, kick=0.0, label=None):
    """A chunky turret with a visor that looks where it aims.
    kick (0 to 1) pulls the barrel back just after a shot."""
    x, y = int(x), int(y)
    dx, dy = math.cos(angle), math.sin(angle)

    base = pygame.Rect(x - 28, y + 8, 56, 16)
    pygame.draw.rect(surface, OUTLINE, base.inflate(6, 6), border_radius=9)
    pygame.draw.rect(surface, blend(color, OUTLINE, 0.55), base,
                     border_radius=7)

    length = 38 - 6 * kick
    _barrel(surface, x, y, dx, dy, 4, length + 3, 8, OUTLINE)
    _barrel(surface, x, y, dx, dy, 4, length, 5, blend(color, OUTLINE, 0.25))
    tip = (int(x + dx * length), int(y + dy * length))
    pygame.draw.circle(surface, OUTLINE, tip, 7)
    pygame.draw.circle(surface, color, tip, 5)
    if kick > 0.5:                            # muzzle flash
        pygame.draw.circle(surface, GOLD, tip, 10)
        pygame.draw.circle(surface, WHITE, tip, 5)

    pygame.draw.circle(surface, OUTLINE, (x, y), 21)
    pygame.draw.circle(surface, color, (x, y), 18)
    pygame.draw.circle(surface, blend(color, WHITE, 0.55), (x - 7, y - 8), 5)

    vx, vy = int(x + dx * 7), int(y + dy * 7 - 1)
    visor = pygame.Rect(0, 0, 18, 12)
    visor.center = (vx, vy)
    pygame.draw.rect(surface, OUTLINE, visor.inflate(4, 4), border_radius=7)
    pygame.draw.rect(surface, VISOR, visor, border_radius=6)
    pygame.draw.rect(surface, WHITE, (vx - 5, vy - 4, 6, 3), border_radius=1)

    if label:
        draw_text(surface, label, 12, color, (x, y + 33))


def draw_projectile(surface, p, color):
    x, y = int(p.x), int(p.y)
    tail = (int(p.x - p.vx * 0.03), int(p.y - p.vy * 0.03))
    pygame.draw.line(surface, blend(color, OUTLINE, 0.3), tail, (x, y), 4)
    pygame.draw.circle(surface, OUTLINE, (x, y), PROJECTILE_RADIUS + 2)
    pygame.draw.circle(surface, color, (x, y), PROJECTILE_RADIUS + 1)
    pygame.draw.circle(surface, WHITE, (x, y), 2)


def draw_reticle(surface, x, y, t, color=WHITE):
    # pulsing target marker (also used as the mouse crosshair with t = 0)
    x, y = int(x), int(y)
    r = 11 + int(2 * math.sin(t * 8))
    pygame.draw.circle(surface, OUTLINE, (x, y), r + 2, 4)
    pygame.draw.circle(surface, color, (x, y), r, 2)
    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(surface, color,
                         (x + ddx * (r - 4), y + ddy * (r - 4)),
                         (x + ddx * (r + 6), y + ddy * (r + 6)), 2)


class Effects:
    """Explosions, shock rings and floating score popups."""

    def __init__(self):
        self.particles = []   # x, y, vx, vy, age, life, colour, size
        self.rings = []       # x, y, age, colour
        self.popups = []      # x, y, age, text, colour

    def explode(self, x, y, color, text=None):
        for _ in range(26):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 260)
            self.particles.append([x, y, math.cos(angle) * speed,
                                   math.sin(angle) * speed, 0.0,
                                   random.uniform(0.35, 0.7),
                                   random.choice((color, GOLD, WHITE)),
                                   random.randint(2, 4)])
        self.rings.append([x, y, 0.0, color])
        if text:
            self.popups.append([x, y - 24, 0.0, text, color])

    def update(self, dt):
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 200 * dt
            p[4] += dt
        self.particles = [p for p in self.particles if p[4] < p[5]]
        for ring in self.rings:
            ring[2] += dt
        self.rings = [r for r in self.rings if r[2] < 0.4]
        for popup in self.popups:
            popup[1] -= 40 * dt
            popup[2] += dt
        self.popups = [p for p in self.popups if p[2] < 1.0]

    def draw(self, surface):
        for x, y, vx, vy, age, life, color, size in self.particles:
            fade = 1 - age / life
            pygame.draw.rect(surface, blend(SPACE, color, fade),
                             (int(x), int(y), size, size))
        for x, y, age, color in self.rings:
            radius = int(10 + age * 160)
            width = max(1, int(5 * (1 - age / 0.4)))
            pygame.draw.circle(surface, color, (int(x), int(y)), radius, width)
        for x, y, age, text, color in self.popups:
            draw_text(surface, text, 16, color, (int(x), int(y)))