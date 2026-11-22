# theme.py
import math
import os
import random

import pygame

from settings import WIDTH, HEIGHT, HUD_HEIGHT

SCREEN_H = HEIGHT + HUD_HEIGHT
START_FULLSCREEN = True           # F11 switches between full screen and a window

# palette: bright flat colours with dark outlines on a deep-space background
SPACE = (12, 14, 30)
PANEL = (26, 28, 56)
PANEL_LIGHT = (52, 56, 104)
OUTLINE = (8, 8, 20)
WHITE = (240, 244, 255)
MUTED = (140, 148, 190)
GOLD = (255, 211, 79)
CYAN = (80, 220, 255)
GREEN = (82, 214, 120)
ORANGE = (255, 160, 60)
RED = (255, 82, 92)
PURPLE = (188, 120, 255)
BLUE = (90, 160, 255)
VISOR = (150, 232, 255)

FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "assets", "fonts", "PressStart2P-Regular.ttf")
_fonts = {}


def get_font(size):
    # the arcade font if its file is present, otherwise a bold system font
    if size not in _fonts:
        font = None
        if os.path.exists(FONT_FILE):
            try:
                font = pygame.font.Font(FONT_FILE, size)
            except (pygame.error, OSError):
                font = None
        if font is None:
            font = pygame.font.SysFont("bahnschrift,consolas,verdana",
                                       size, bold=True)
        _fonts[size] = font
    return _fonts[size]


def blend(a, b, t):
    # colour a at t=0, colour b at t=1
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_text(surface, text, size, color, pos, anchor="center", shadow=True):
    font = get_font(size)
    label = font.render(text, True, color)
    rect = label.get_rect()
    setattr(rect, anchor, pos)
    if shadow:
        surface.blit(font.render(text, True, OUTLINE), rect.move(2, 2))
    surface.blit(label, rect)
    return rect


def draw_outlined_text(surface, text, size, color, center, thickness=3):
    # big headline text with a thick dark outline
    font = get_font(size)
    label = font.render(text, True, color)
    edge = font.render(text, True, OUTLINE)
    rect = label.get_rect(center=center)
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx * dx + dy * dy <= thickness * thickness + 1:
                surface.blit(edge, rect.move(dx, dy))
    surface.blit(label, rect)
    return rect


def wrap_text(text, size, max_width):
    font = get_font(size)
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_panel(surface, rect, fill=PANEL, border=PANEL_LIGHT, radius=12,
               alpha=255, border_width=2):
    rect = pygame.Rect(rect)
    if alpha >= 255:
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        pygame.draw.rect(surface, border, rect, border_width,
                         border_radius=radius)
        return
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    local = panel.get_rect()
    pygame.draw.rect(panel, (*fill, alpha), local, border_radius=radius)
    pygame.draw.rect(panel, (*border, min(255, alpha + 40)), local,
                     border_width, border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_glow(surface, color, center, radius, strength=60):
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(4, 0, -1):
        r = int(radius * i / 4)
        alpha = int(strength * (5 - i) / 4)
        pygame.draw.circle(glow, (*color, alpha), (radius, radius), r)
    surface.blit(glow, (center[0] - radius, center[1] - radius))


class Starfield:
    """Twinkling stars that drift slowly to the left, in three depth layers."""

    def __init__(self, width=WIDTH, height=SCREEN_H, count=90, seed=3):
        rng = random.Random(seed)
        self.width = width
        self.time = 0.0
        self.stars = []
        for _ in range(count):
            self.stars.append([rng.uniform(0, width), rng.uniform(0, height),
                               rng.choice((1, 2, 3)), rng.uniform(0, 6.28)])

    def update(self, dt):
        self.time += dt
        for star in self.stars:
            star[0] -= 12 * star[2] * dt
            if star[0] < 0:
                star[0] += self.width

    def draw(self, surface):
        for x, y, layer, phase in self.stars:
            twinkle = 0.6 + 0.4 * math.sin(self.time * 2 + phase)
            level = int((80 + 50 * layer) * twinkle)
            color = (level, level, min(255, level + 30))
            pygame.draw.rect(surface, color, (int(x), int(y), layer, layer))


_background = None
_grid = None
_scanlines = None


def background():
    # vertical gradient, built once
    global _background
    if _background is None:
        surface = pygame.Surface((WIDTH, SCREEN_H))
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            color = (int(10 + 16 * t), int(12 + 8 * t), int(28 + 26 * t))
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        _background = surface
    return _background


def arena_grid():
    # faint radar grid and range rings over the arena, built once
    global _grid
    if _grid is None:
        grid = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in range(0, WIDTH, 50):
            pygame.draw.line(grid, (120, 140, 255, 16), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(grid, (120, 140, 255, 16), (0, y), (WIDTH, y))
        for radius in (150, 300, 450, 600):
            pygame.draw.circle(grid, (120, 140, 255, 22),
                               (WIDTH // 2, HEIGHT - 40), radius, 1)
        _grid = grid
    return _grid


def draw_scanlines(surface):
    # subtle CRT lines and darkened corners, built once
    global _scanlines
    if _scanlines is None:
        overlay = pygame.Surface((WIDTH, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 3):
            pygame.draw.line(overlay, (0, 0, 0, 38), (0, y), (WIDTH, y))
        for i in range(40):
            alpha = int(70 * (1 - i / 40) ** 2)
            pygame.draw.rect(overlay, (0, 0, 0, alpha),
                             (i, i, WIDTH - 2 * i, SCREEN_H - 2 * i), 1)
        _scanlines = overlay
    surface.blit(_scanlines, (0, 0))


def toggle_fullscreen():
    try:
        pygame.display.toggle_fullscreen()
    except pygame.error:
        pass


def poll_events():
    # like pygame.event.get(), but F11 toggles full screen everywhere
    events = []
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            toggle_fullscreen()
        else:
            events.append(event)
    return events


def make_screen():
    # SCALED keeps the 900 x 670 game and stretches it to the monitor
    flags = pygame.SCALED
    if START_FULLSCREEN:
        flags |= pygame.FULLSCREEN
    try:
        return pygame.display.set_mode((WIDTH, SCREEN_H), flags)
    except pygame.error:
        return pygame.display.set_mode((WIDTH, SCREEN_H))