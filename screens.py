import math
import random
import pygame
from settings import WIDTH, HEIGHT, HUD_HEIGHT, FPS, DRONE_RADIUS, LEVELS
from ui import TextBox, Button, TEXT, ACCENT, BUTTON, BUTTON_HOVER, TRACK

BACKGROUND = (20, 20, 30)
MUTED = (150, 155, 180)
SCREEN_H = HEIGHT + HUD_HEIGHT
LEVEL_COLORS = {"Easy": (80, 200, 120),
                "Medium": (240, 170, 60),
                "Hard": (230, 80, 80),
                "Lab": (200, 120, 255)}


def make_fonts():
    return {"title": pygame.font.Font(None, 120),
            "big": pygame.font.Font(None, 52),
            "normal": pygame.font.Font(None, 32),
            "small": pygame.font.Font(None, 24)}


def draw_text(screen, font, text, color, center):
    label = font.render(text, True, color)
    screen.blit(label, label.get_rect(center=center))


def draw_title(screen, fonts, y=110):
    text = fonts["title"].render("INTERCEPTOR", True, ACCENT)
    shadow = fonts["title"].render("INTERCEPTOR", True, (60, 30, 90))
    rect = text.get_rect(center=(WIDTH // 2, y))
    screen.blit(shadow, rect.move(5, 5))
    screen.blit(text, rect)
    draw_text(screen, fonts["normal"], "Hitting moving targets with a Kalman filter",
              MUTED, (WIDTH // 2, y + 62))


class Backdrop:
    """A small demo at the bottom of every page: the drone (red), the noisy
    radar dots (blue) and the Kalman estimate (purple ring)."""

    def __init__(self):
        self.x = -DRONE_RADIUS
        self.y = SCREEN_H - 55
        self.dots = []
        self.timer = 0.0
        self.rng = random.Random(7)

    def update(self, dt):
        self.x += 110 * dt
        if self.x > WIDTH + DRONE_RADIUS:
            self.x = -DRONE_RADIUS
            self.dots = []
        self.timer += dt
        if self.timer >= 0.05:
            self.timer = 0.0
            self.dots.append((self.x + self.rng.gauss(0, 18),
                              self.y + self.rng.gauss(0, 18)))
            self.dots = self.dots[-25:]

    def draw(self, screen):
        for dot_x, dot_y in self.dots:
            pygame.draw.circle(screen, (90, 160, 255),
                               (int(dot_x), int(dot_y)), 3)
        pygame.draw.circle(screen, (220, 60, 60),
                           (int(self.x), int(self.y)), DRONE_RADIUS)
        pygame.draw.circle(screen, (200, 120, 255),
                           (int(self.x), int(self.y)), DRONE_RADIUS + 4, 2)


def show_menu(screen, clock, name=""):
    """Title page. Returns the entered name, or None if the window is closed."""
    fonts = make_fonts()
    backdrop = Backdrop()
    box = TextBox(WIDTH // 2 - 210, 330, 420, 54, 14, name)
    start = Button(WIDTH // 2 - 80, 410, 160, 44, "Start")
    warning = 0.0

    while True:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            pressed_enter = box.handle_event(event)
            if pressed_enter or start.handle_event(event):
                if box.value():
                    return box.value()
                warning = 1.5

        box.update(dt)
        backdrop.update(dt)
        warning = max(0.0, warning - dt)

        screen.fill(BACKGROUND)
        backdrop.draw(screen)
        draw_title(screen, fonts)
        draw_text(screen, fonts["big"], "Enter your name", TEXT, (WIDTH // 2, 290))
        box.draw(screen, fonts["big"])
        start.draw(screen, fonts["normal"])
        if warning > 0:
            draw_text(screen, fonts["small"], "Please type a name first",
                      (230, 80, 80), (WIDTH // 2, 478))
        else:
            draw_text(screen, fonts["small"], "Press Enter or click Start",
                      MUTED, (WIDTH // 2, 478))
        pygame.display.flip()


def show_loading(screen, clock, name, duration=3.0):
    """Loading bar. Returns True when finished, False if the window is closed."""
    fonts = make_fonts()
    backdrop = Backdrop()
    bar = pygame.Rect(WIDTH // 2 - 250, 350, 500, 28)
    elapsed = 0.0

    while elapsed < duration + 0.4:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        elapsed += dt
        backdrop.update(dt)

        x = min(1.0, elapsed / duration)
        progress = x * x * (3 - 2 * x)            # starts and ends slowly
        if progress < 0.3:
            message = "Calibrating radar..."
        elif progress < 0.6:
            message = "Initializing Kalman filter..."
        elif progress < 0.95:
            message = "Arming turrets..."
        else:
            message = "Ready!"

        screen.fill(BACKGROUND)
        backdrop.draw(screen)
        draw_title(screen, fonts)
        draw_text(screen, fonts["big"], f"Welcome, {name}", TEXT, (WIDTH // 2, 290))
        pygame.draw.rect(screen, TRACK, bar, border_radius=8)
        filled = pygame.Rect(bar.x, bar.y, int(bar.width * progress), bar.height)
        pygame.draw.rect(screen, ACCENT, filled, border_radius=8)
        draw_text(screen, fonts["normal"], f"{int(progress * 100)}%", TEXT,
                  (WIDTH // 2, 405))
        draw_text(screen, fonts["small"], message, MUTED, (WIDTH // 2, 435))
        pygame.display.flip()
    return True


def wrap_text(font, text, max_width):
    # split text into lines that each fit inside max_width pixels
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def show_levels(screen, clock, name):
    """Level select. Returns "Easy"/"Medium"/"Hard"/"Lab", "back" or None (quit)."""
    fonts = make_fonts()
    backdrop = Backdrop()
    names = list(LEVELS)
    cards = []
    for i, level in enumerate(names):
        cards.append(pygame.Rect(27 + i * 215, 270, 200, 240))

    while True:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
                if pygame.K_1 <= event.key < pygame.K_1 + len(names):
                    return names[event.key - pygame.K_1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for level, card in zip(names, cards):
                    if card.collidepoint(event.pos):
                        return level
        backdrop.update(dt)

        screen.fill(BACKGROUND)
        backdrop.draw(screen)
        draw_title(screen, fonts)
        draw_text(screen, fonts["big"], f"{name}, choose your level", TEXT,
                  (WIDTH // 2, 235))

        mouse = pygame.mouse.get_pos()
        for i, (level, card) in enumerate(zip(names, cards)):
            cfg = LEVELS[level]
            locked = cfg.get("locked", True)
            color = LEVEL_COLORS[level]
            hovered = card.collidepoint(mouse)
            pygame.draw.rect(screen, BUTTON_HOVER if hovered else BUTTON,
                             card, border_radius=12)
            pygame.draw.rect(screen, color, card, 4 if hovered else 2,
                             border_radius=12)
            draw_text(screen, fonts["big"], level.upper(), color,
                      (card.centerx, card.y + 38))

            info_lines = wrap_text(fonts["small"], cfg["info"], card.width - 20)
            for j, line in enumerate(info_lines):
                draw_text(screen, fonts["small"], line, MUTED,
                          (card.centerx, card.y + 78 + j * 20))

            if locked:
                lines = [f"Path: {cfg['pattern'].capitalize()}",
                         f"Speed: {cfg['speed']}",
                         f"Noise: {cfg['noise']}"]
            else:
                lines = ["Path: your choice",
                         f"Speed: {cfg['speed']}",
                         "Noise: your choice"]
            for j, line in enumerate(lines):
                draw_text(screen, fonts["small"], line, TEXT,
                          (card.centerx, card.y + 135 + j * 26))
            draw_text(screen, fonts["small"], f"Press {i + 1}", MUTED,
                      (card.centerx, card.bottom - 22))

        draw_text(screen, fonts["small"],
                  f"Click a level or press 1-{len(names)}     Esc: change name",
                  MUTED, (WIDTH // 2, 545))
        pygame.display.flip()