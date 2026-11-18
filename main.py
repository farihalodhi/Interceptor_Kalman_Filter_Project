# main.py
import math
import pygame
from settings import (WIDTH, HEIGHT, FPS, DRONE_RADIUS, PROJECTILE_RADIUS,
                      HUD_HEIGHT, LEVELS)
from drone import PATTERNS
from game_manager import GameManager
from sounds import SoundFX
from ui import Slider, Button, draw_hud_background, TEXT
from screens import show_menu, show_loading, show_levels, LEVEL_COLORS

def draw_turret(screen, turret, color):
    tip_x = turret.x + 30 * math.cos(turret.angle)
    tip_y = turret.y + 30 * math.sin(turret.angle)
    pygame.draw.line(screen, color, (turret.x, turret.y), (tip_x, tip_y), 6)
    pygame.draw.circle(screen, color, (turret.x, turret.y), 14)
    for p in turret.projectiles:
        pygame.draw.circle(screen, color, (int(p.x), int(p.y)),
                           PROJECTILE_RADIUS)

def draw_cross(screen, color, x, y, size=8):
    pygame.draw.line(screen, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(screen, color, (x, y - size), (x, y + size), 2)

def play_level(screen, clock, sfx, name, level):
    """Runs one game at the chosen level.
    Returns "levels" (Esc, back to level select) or "quit" (window closed)."""
    font = pygame.font.SysFont(None, 26)
    small_font = pygame.font.SysFont(None, 22)

    # the level decides the drone's path, speed and the radar noise
    cfg = LEVELS[level]
    game = GameManager(noise=cfg["noise"], seed=42, pattern=cfg["pattern"],
                       speed=cfg["speed"])
    game.record_events = True      # so we can play a sound for each event

    # controls in the strip below the arena
    slider = Slider(40, HEIGHT + 46, 260, 0, 100, cfg["noise"], 5, "Radar noise")
    buttons = []
    for i, pattern in enumerate(PATTERNS):
        buttons.append(Button(400 + i * 98, HEIGHT + 36, 90, 26,
                              pattern.capitalize()))

    while True:
        dt = clock.tick(FPS) / 1000

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "levels"

            # the slider and buttons get first use of mouse events
            if slider.handle_event(event):
                if slider.value != game.radar.noise:
                    game.change_noise(slider.value - game.radar.noise)
                continue

            clicked_button = False
            for i, button in enumerate(buttons):
                if button.handle_event(event):
                    game.set_pattern(PATTERNS[i])
                    clicked_button = True
            if clicked_button:
                continue

            # clicks inside the arena fire the player turret
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and event.pos[1] < HEIGHT):
                game.player_fire()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.change_noise(5)
                if event.key == pygame.K_DOWN:
                    game.change_noise(-5)
                if event.key == pygame.K_t:
                    game.next_pattern()
                if event.key == pygame.K_m:
                    sfx.toggle_mute()

        # keep the slider in step with the noise when keys change it
        if not slider.dragging:
            slider.value = game.radar.noise

        mouse_x, mouse_y = pygame.mouse.get_pos()
        game.aim_player(mouse_x, mouse_y)

        # 2. update
        game.update(dt)

        # play a sound for everything that happened this frame
        for kind, who in game.events:
            sfx.play(kind, who)
        game.events.clear()

        # 3. draw
        screen.fill((20, 20, 30))

        for rx, ry in game.radar_dots:
            pygame.draw.circle(screen, (90, 160, 255),
                               (int(rx), int(ry)), 3)

        pygame.draw.circle(screen, (220, 60, 60),
                           (int(game.drone.x), int(game.drone.y)),
                           DRONE_RADIUS)

        # Kalman estimate (ring) and predicted interception point (cross),
        # drawn after the drone so they stay visible on top of it
        if game.kalman.initialized:
            ex, ey = game.kalman.position()
            pygame.draw.circle(screen, (200, 120, 255),
                               (int(ex), int(ey)), DRONE_RADIUS + 4, 2)
        if game.aim_point is not None:
            draw_cross(screen, (255, 255, 255),
                       int(game.aim_point[0]), int(game.aim_point[1]))

        draw_turret(screen, game.player, (80, 200, 120))
        draw_turret(screen, game.raw_turret, (240, 170, 60))
        draw_turret(screen, game.kalman_turret, (200, 120, 255))

        y = 10
        for turret in (game.player, game.raw_turret, game.kalman_turret):
            line = (f"{turret.name}: {turret.hits}/{turret.shots} hits "
                    f"({turret.hit_rate():.0f}%)")
            screen.blit(font.render(line, True, TEXT), (10, y))
            y += 24

        # player name and level, top right
        who = font.render(f"{name}  |  {level}", True, LEVEL_COLORS[level])
        screen.blit(who, (WIDTH - who.get_width() - 10, 10))
        hint = small_font.render("Esc: level select", True, (150, 155, 180))
        screen.blit(hint, (WIDTH - hint.get_width() - 10, 34))

        # control strip
        draw_hud_background(screen, HEIGHT, WIDTH, HUD_HEIGHT)
        slider.draw(screen, font)
        screen.blit(font.render("Trajectory", True, TEXT), (400, HEIGHT + 8))
        for i, button in enumerate(buttons):
            button.draw(screen, small_font,
                        active=(game.drone.pattern == PATTERNS[i]))
        screen.blit(small_font.render("T: next path", True, TEXT),
                    (730, HEIGHT + 20))
        screen.blit(small_font.render("Up/Down: noise", True, TEXT),
                    (730, HEIGHT + 42))
        screen.blit(small_font.render("M: sound " + ("off" if sfx.muted else "on"),
                                      True, TEXT), (730, HEIGHT + 2))

        pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    sfx = SoundFX()

    name = ""
    running = True
    while running:
        # 1. main page: big title + enter your name
        name = show_menu(screen, clock, name)
        if name is None:
            break

        # 2. loading bar
        if not show_loading(screen, clock, name):
            break

        # 3. title + level select (Easy / Medium / Hard), then play
        while True:
            level = show_levels(screen, clock, name)
            if level is None:            # window closed
                running = False
                break
            if level == "back":          # Esc: change name
                break
            if play_level(screen, clock, sfx, name, level) == "quit":
                running = False
                break

    pygame.quit()


if __name__ == "__main__":
    main()
