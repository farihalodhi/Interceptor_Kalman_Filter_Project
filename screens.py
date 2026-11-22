# screens.py
import math
import random

import pygame

from settings import WIDTH, HEIGHT, HUD_HEIGHT, FPS, LEVELS
from theme import (SCREEN_H, SPACE, PANEL, PANEL_LIGHT, OUTLINE, WHITE, MUTED,
                   GOLD, CYAN, GREEN, ORANGE, RED, PURPLE, BLUE, blend,
                   draw_text, draw_outlined_text, draw_panel, draw_scanlines,
                   wrap_text, Starfield, background, poll_events)
from ui import TextBox, Button
from sprites import draw_drone, draw_turret
from scores import load_scores, load_leaderboard

LEVEL_COLORS = {"Easy": GREEN, "Medium": ORANGE, "Hard": RED, "Lab": PURPLE}
BLURB = {"Easy": "WARM UP", "Medium": "STEP UP", "Hard": "NO MERCY",
         "Lab": "FREE PLAY"}


class Backdrop:
    """Space background with a demo flight at the bottom: the drone, its
    noisy radar dots and the Kalman estimate ring."""

    def __init__(self):
        self.stars = Starfield(WIDTH, SCREEN_H, 110, seed=5)
        self.x = -40.0
        self.y = SCREEN_H - 55
        self.dots = []
        self.timer = 0.0
        self.time = 0.0
        self.rng = random.Random(7)

    def update(self, dt):
        self.time += dt
        self.stars.update(dt)
        self.x += 110 * dt
        if self.x > WIDTH + 40:
            self.x = -40.0
            self.dots = []
        self.timer += dt
        if self.timer >= 0.05:
            self.timer = 0.0
            self.dots.append((self.x + self.rng.gauss(0, 18),
                              self.y + self.rng.gauss(0, 18)))
            self.dots = self.dots[-25:]

    def draw(self, screen):
        screen.blit(background(), (0, 0))
        self.stars.draw(screen)
        for dot_x, dot_y in self.dots:
            pygame.draw.circle(screen, blend(SPACE, BLUE, 0.7),
                               (int(dot_x), int(dot_y)), 3)
        draw_drone(screen, self.x, self.y, self.time)
        pygame.draw.circle(screen, PURPLE, (int(self.x), int(self.y)), 24, 2)


def draw_title(screen, t, y=100, size=64):
    bob = int(math.sin(t * 2) * 3)
    draw_outlined_text(screen, "INTERCEPTOR", size, PURPLE,
                       (WIDTH // 2 + 3, y + bob + 6), thickness=4)
    draw_outlined_text(screen, "INTERCEPTOR", size, WHITE,
                       (WIDTH // 2, y + bob), thickness=4)


def show_menu(screen, clock, name=""):
    """Title page. Returns the entered name, or None if the window is closed."""
    backdrop = Backdrop()
    box = TextBox(WIDTH // 2 - 220, 320, 440, 56, 14, name)
    start = Button(WIDTH // 2 - 100, 400, 200, 48, "START", 24)
    warning = 0.0
    elapsed = 0.0

    while True:
        dt = clock.tick(FPS) / 1000
        elapsed += dt
        for event in poll_events():
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

        backdrop.draw(screen)
        draw_title(screen, elapsed, 100)
        draw_text(screen, "HITTING MOVING TARGETS WITH A KALMAN FILTER", 12,
                  MUTED, (WIDTH // 2, 168))
        draw_text(screen, "ENTER YOUR NAME", 24, WHITE, (WIDTH // 2, 290))
        box.draw(screen)
        start.draw(screen)
        if warning > 0:
            draw_text(screen, "PLEASE TYPE A NAME FIRST", 12, RED,
                      (WIDTH // 2, 478))
        elif int(elapsed * 2) % 2 == 0:
            draw_text(screen, "PRESS ENTER OR CLICK START", 12, GOLD,
                      (WIDTH // 2, 478))
        draw_text(screen, "F11: FULL SCREEN", 12, MUTED, (WIDTH - 12, 12),
                  anchor="topright", shadow=False)
        draw_scanlines(screen)
        pygame.display.flip()


def show_loading(screen, clock, name, duration=3.0):
    """Task-bar style loading screen. Returns True when finished, False if
    the window is closed."""
    backdrop = Backdrop()
    bar = pygame.Rect(WIDTH // 2 - 260, 360, 520, 36)
    elapsed = 0.0

    while elapsed < duration + 0.4:
        dt = clock.tick(FPS) / 1000
        for event in poll_events():
            if event.type == pygame.QUIT:
                return False
        elapsed += dt
        backdrop.update(dt)

        x = min(1.0, elapsed / duration)
        progress = x * x * (3 - 2 * x)            # starts and ends slowly
        if progress < 0.3:
            message = "CALIBRATING RADAR..."
        elif progress < 0.6:
            message = "INITIALIZING KALMAN FILTER..."
        elif progress < 0.95:
            message = "ARMING TURRETS..."
        else:
            message = "READY!"

        backdrop.draw(screen)
        draw_title(screen, elapsed, 100)
        draw_text(screen, f"WELCOME, {name.upper()}", 24, WHITE,
                  (WIDTH // 2, 290))
        draw_text(screen, "TOTAL TASKS COMPLETED", 12, WHITE,
                  (WIDTH // 2, 336))
        frame = bar.inflate(10, 10)
        pygame.draw.rect(screen, OUTLINE, frame, border_radius=8)
        pygame.draw.rect(screen, (60, 64, 90), bar, border_radius=4)
        filled = pygame.Rect(bar.x, bar.y, int(bar.width * progress),
                             bar.height)
        if filled.width > 0:
            pygame.draw.rect(screen, GREEN, filled, border_radius=4)
        for i in range(1, 5):                     # segments, like the task bar
            seg_x = bar.x + bar.width * i // 5
            pygame.draw.line(screen, OUTLINE, (seg_x, bar.y),
                             (seg_x, bar.bottom), 4)
        pygame.draw.rect(screen, WHITE, frame, 3, border_radius=8)
        draw_text(screen, f"{int(progress * 100)}%", 24, GOLD,
                  (WIDTH // 2, 424))
        draw_text(screen, message, 12, MUTED, (WIDTH // 2, 458))
        draw_scanlines(screen)
        pygame.display.flip()
    return True


def _path_points(pattern, box):
    left, right = box.left + 10, box.right - 10
    if pattern == "diagonal":
        return [(left, box.top + 10), (right, box.bottom - 10)]
    if pattern == "turning":
        mid = left + int((right - left) * 0.45)
        return [(left, box.top + 14), (mid, box.top + 14),
                (right, box.bottom - 10)]
    return [(left, box.centery), (right, box.centery)]


def draw_level_card(screen, level, cfg, card, hovered, index, record):
    color = LEVEL_COLORS[level]
    locked = cfg.get("locked", True)
    r = card.move(0, -6 if hovered else 0)
    pygame.draw.rect(screen, OUTLINE, r.move(0, 6), border_radius=14)
    draw_panel(screen, r, fill=PANEL, border=color, radius=14,
               border_width=4 if hovered else 3)

    strip = pygame.Rect(r.x + 8, r.y + 8, r.width - 16, 38)
    pygame.draw.rect(screen, color, strip, border_radius=8)
    draw_text(screen, level.upper(), 24, OUTLINE, strip.center, shadow=False)
    draw_text(screen, BLURB[level], 12, MUTED, (r.centerx, r.y + 62),
              shadow=False)

    box = pygame.Rect(r.x + 16, r.y + 78, r.width - 32, 56)
    pygame.draw.rect(screen, SPACE, box, border_radius=8)
    pygame.draw.rect(screen, PANEL_LIGHT, box, 2, border_radius=8)
    if locked:
        points = _path_points(cfg["pattern"], box)
        pygame.draw.lines(screen, color, False, points, 3)
        pygame.draw.circle(screen, RED, points[-1], 5)
        pygame.draw.circle(screen, WHITE, points[0], 3)
    else:
        draw_text(screen, "?", 32, color, box.center)

    if locked:
        rows = (("PATH", cfg["pattern"].upper()), ("SPEED", str(cfg["speed"])),
                ("NOISE", str(cfg["noise"])), ("TIME", f"{cfg['time']} S"))
    else:
        rows = (("PATH", "ANY"), ("SPEED", str(cfg["speed"])),
                ("NOISE", "ANY"), ("TIME", "FREE"))
    for i, (label, value) in enumerate(rows):
        row_y = r.y + 154 + i * 22
        draw_text(screen, label, 12, MUTED, (r.x + 16, row_y),
                  anchor="midleft", shadow=False)
        draw_text(screen, value, 12, WHITE, (r.right - 16, row_y),
                  anchor="midright", shadow=False)

    if cfg.get("time"):
        draw_text(screen, "HI-SCORE", 12, MUTED, (r.centerx, r.y + 246),
                  shadow=False)
        if record:
            best = f"{record.get('hits', 0)}  {str(record.get('name', ''))[:8].upper()}"
            draw_text(screen, best, 16, GOLD, (r.centerx, r.y + 268))
        else:
            draw_text(screen, "---", 16, MUTED, (r.centerx, r.y + 268))
    draw_text(screen, f"[{index + 1}]", 12, MUTED, (r.centerx, r.bottom - 12),
              shadow=False)


RANK_COLORS = (GOLD, (205, 212, 230), (214, 140, 80), WHITE, WHITE)


def show_leaderboard(screen, clock, name, level="Easy"):
    """Top 5 players of each timed level (names and scores only).
    Returns "back" (Esc) or None (window closed)."""
    backdrop = Backdrop()
    levels = [lv for lv in LEVELS if LEVELS[lv].get("time")]
    tabs = [pygame.Rect(WIDTH // 2 - 195 + i * 135, 158, 125, 36)
            for i in range(len(levels))]
    table = pygame.Rect(WIDTH // 2 - 250, 212, 500, 280)
    current = levels.index(level) if level in levels else 0
    boards = {lv: load_leaderboard(lv) for lv in levels}
    elapsed = 0.0

    while True:
        dt = clock.tick(FPS) / 1000
        elapsed += dt
        for event in poll_events():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_l):
                    return "back"
                if pygame.K_1 <= event.key < pygame.K_1 + len(levels):
                    current = event.key - pygame.K_1
                if event.key == pygame.K_LEFT:
                    current = (current - 1) % len(levels)
                if event.key == pygame.K_RIGHT:
                    current = (current + 1) % len(levels)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, tab in enumerate(tabs):
                    if tab.collidepoint(event.pos):
                        current = i
        backdrop.update(dt)

        backdrop.draw(screen)
        draw_title(screen, elapsed, 62, 48)
        draw_text(screen, "LEADERBOARD", 22, GOLD, (WIDTH // 2, 130))

        for i, (lv, tab) in enumerate(zip(levels, tabs)):
            color = LEVEL_COLORS[lv]
            if i == current:
                pygame.draw.rect(screen, color, tab, border_radius=8)
                draw_text(screen, lv.upper(), 14, OUTLINE, tab.center,
                          shadow=False)
            else:
                draw_panel(screen, tab, fill=PANEL, border=color, radius=8,
                           border_width=2)
                draw_text(screen, lv.upper(), 14, color, tab.center,
                          shadow=False)

        level_name = levels[current]
        draw_panel(screen, table, fill=PANEL, border=LEVEL_COLORS[level_name],
                   radius=14, border_width=3)
        draw_text(screen, "RANK", 12, MUTED, (table.x + 40, table.y + 26),
                  anchor="midleft", shadow=False)
        draw_text(screen, "PLAYER", 12, MUTED, (table.x + 130, table.y + 26),
                  anchor="midleft", shadow=False)
        draw_text(screen, "HITS", 12, MUTED, (table.right - 40, table.y + 26),
                  anchor="midright", shadow=False)

        entries = boards[level_name]
        for rank in range(5):
            row_y = table.y + 70 + rank * 44
            color = RANK_COLORS[rank]
            if rank < len(entries):
                player = str(entries[rank].get("name", ""))[:14].upper()
                hits = str(entries[rank]["hits"])
                if player == name.upper():
                    row = pygame.Rect(table.x + 14, row_y - 18,
                                      table.width - 28, 36)
                    pygame.draw.rect(screen, PANEL_LIGHT, row, border_radius=8)
            else:
                player, hits = "---", "---"
                color = MUTED
            draw_text(screen, f"{rank + 1}.", 18, color,
                      (table.x + 40, row_y), anchor="midleft")
            draw_text(screen, player, 18, color, (table.x + 130, row_y),
                      anchor="midleft")
            draw_text(screen, hits, 18, color, (table.right - 40, row_y),
                      anchor="midright")

        draw_text(screen, f"1-{len(levels)} OR LEFT/RIGHT: LEVEL     "
                          "ESC: BACK", 12, MUTED, (WIDTH // 2, 520),
                  shadow=False)
        draw_scanlines(screen)
        pygame.display.flip()


def show_levels(screen, clock, name):
    """Level select. Returns "Easy"/"Medium"/"Hard"/"Lab", "back" or None."""
    backdrop = Backdrop()
    scores = load_scores()
    names = list(LEVELS)
    cards = [pygame.Rect(27 + i * 215, 185, 200, 300)
             for i in range(len(names))]
    board_link = pygame.Rect(WIDTH // 2 - 130, 524, 260, 22)
    elapsed = 0.0

    while True:
        dt = clock.tick(FPS) / 1000
        elapsed += dt
        for event in poll_events():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
                if event.key == pygame.K_l:
                    if show_leaderboard(screen, clock, name) is None:
                        return None
                if pygame.K_1 <= event.key < pygame.K_1 + len(names):
                    return names[event.key - pygame.K_1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if board_link.collidepoint(event.pos):
                    if show_leaderboard(screen, clock, name) is None:
                        return None
                for level, card in zip(names, cards):
                    if card.collidepoint(event.pos):
                        return level
        backdrop.update(dt)

        backdrop.draw(screen)
        draw_title(screen, elapsed, 62, 48)
        draw_text(screen, f"{name.upper()}, CHOOSE YOUR LEVEL", 16, WHITE,
                  (WIDTH // 2, 138))
        mouse = pygame.mouse.get_pos()
        for i, (level, card) in enumerate(zip(names, cards)):
            draw_level_card(screen, level, LEVELS[level], card,
                            card.collidepoint(mouse), i, scores.get(level))
        draw_text(screen, f"CLICK A LEVEL OR PRESS 1-{len(names)}     "
                          "ESC: CHANGE NAME", 12, MUTED, (WIDTH // 2, 512),
                  shadow=False)
        draw_text(screen, "L: LEADERBOARD", 12,
                  GOLD if board_link.collidepoint(mouse) else CYAN,
                  board_link.center, shadow=False)
        draw_scanlines(screen)
        pygame.display.flip()


def verdict_text(player, raw, kalman):
    # what the round meant, judged by hits scored
    if player == 0 and raw == 0 and kalman == 0:
        return "Nobody scored a hit this round."
    if player > kalman:
        return "You outsmarted the Kalman filter!"
    if player == kalman and player > 0:
        return "Level with the Kalman filter!"
    if player > raw:
        return "You beat the raw radar. The Kalman turret is still ahead."
    if player == raw and player > 0:
        return "Tied with the raw radar turret."
    return "The automated turrets won this round. Try again!"


def result_headline(player, raw, kalman):
    if player == 0 and raw == 0 and kalman == 0:
        return "NO CONTACT", MUTED
    if player > kalman:
        return "VICTORY", GOLD
    if player == kalman and player > 0:
        return "DRAW", WHITE
    if player > raw or (player == raw and player > 0):
        return "GOOD TRY", CYAN
    return "DEFEAT", RED


def show_results(screen, clock, name, level, result, record, best):
    """Shown when the timer runs out. result holds (hits, shots) for the
    player, the raw turret and the Kalman turret. Returns "again", "levels"
    or None (window closed)."""
    backdrop = Backdrop()
    again = Button(WIDTH // 2 - 250, 545, 240, 48, "PLAY AGAIN", 16)
    back = Button(WIDTH // 2 + 10, 545, 240, 48, "LEVEL SELECT", 16)
    entries = (("YOU", GREEN, "player"), ("RAW RADAR", ORANGE, "raw"),
               ("KALMAN", PURPLE, "kalman"))
    cards = [pygame.Rect(80 + i * 255, 200, 230, 210) for i in range(3)]

    player_hits = result["player"][0]
    raw_hits = result["raw"][0]
    kalman_hits = result["kalman"][0]
    most = max(player_hits, raw_hits, kalman_hits)
    headline, headline_color = result_headline(player_hits, raw_hits,
                                               kalman_hits)
    verdict_lines = wrap_text(verdict_text(player_hits, raw_hits, kalman_hits),
                              16, 780)
    verdict_color = GOLD if player_hits >= kalman_hits and player_hits > 0 \
        else WHITE

    while True:
        dt = clock.tick(FPS) / 1000
        for event in poll_events():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                 pygame.K_r):
                    return "again"
                if event.key == pygame.K_ESCAPE:
                    return "levels"
            if again.handle_event(event):
                return "again"
            if back.handle_event(event):
                return "levels"
        backdrop.update(dt)

        backdrop.draw(screen)
        draw_outlined_text(screen, headline, 64, headline_color,
                           (WIDTH // 2, 70), thickness=4)
        draw_text(screen, f"{name.upper()}  |  {level.upper()}", 16,
                  LEVEL_COLORS[level], (WIDTH // 2, 134))

        for card, (label, color, key) in zip(cards, entries):
            hits, shots = result[key]
            accuracy = 100 * hits / shots if shots > 0 else 0.0
            winner = hits == most and most > 0
            draw_panel(screen, card, fill=PANEL, border=color, radius=14,
                       border_width=4 if winner else 2)
            draw_turret(screen, card.centerx, card.y + 52, -math.pi / 2,
                        color)
            draw_text(screen, label, 16, color, (card.centerx, card.y + 106))
            draw_text(screen, str(hits), 48, WHITE,
                      (card.centerx, card.y + 148))
            draw_text(screen, "HITS", 12, MUTED, (card.centerx, card.y + 182),
                      shadow=False)
            draw_text(screen, f"{hits}/{shots} SHOTS  {accuracy:.0f}%", 12,
                      WHITE, (card.centerx, card.y + 198), shadow=False)
            if winner:
                draw_text(screen, "MOST HITS", 12, GOLD,
                          (card.centerx, card.y - 12))

        for i, line in enumerate(verdict_lines):
            draw_text(screen, line, 16, verdict_color,
                      (WIDTH // 2, 448 + i * 24))
        record_y = 448 + len(verdict_lines) * 24 + 14
        if record:
            draw_text(screen, f"NEW BEST SCORE ON {level.upper()}!", 12, GOLD,
                      (WIDTH // 2, record_y))
        elif best:
            draw_text(screen, f"BEST ON {level.upper()}: {best.get('hits', 0)} "
                              f"HITS ({str(best.get('name', ''))[:14].upper()})",
                      12, MUTED, (WIDTH // 2, record_y), shadow=False)

        again.draw(screen, active=True)
        back.draw(screen)
        draw_text(screen, "R OR ENTER: PLAY AGAIN     ESC: LEVEL SELECT", 12,
                  MUTED, (WIDTH // 2, 652), shadow=False)
        draw_scanlines(screen)
        pygame.display.flip()