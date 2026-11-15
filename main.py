# main.py
import math
import pygame
from settings import (WIDTH, HEIGHT, FPS, DRONE_RADIUS, PROJECTILE_RADIUS,
                      HUD_HEIGHT)
from drone import PATTERNS
from game_manager import GameManager
from ui import Slider, Button, draw_hud_background, TEXT


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


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)
    small_font = pygame.font.SysFont(None, 22)

    game = GameManager(noise=15, seed=42)

    # controls in the strip below the arena
    slider = Slider(40, HEIGHT + 46, 260, 0, 100, 15, 5, "Radar noise")
    buttons = []
    for i, name in enumerate(PATTERNS):
        buttons.append(Button(400 + i * 98, HEIGHT + 36, 90, 26,
                              name.capitalize()))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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

        # keep the slider in step with the noise when keys change it
        if not slider.dragging:
            slider.value = game.radar.noise

        mouse_x, mouse_y = pygame.mouse.get_pos()
        game.aim_player(mouse_x, mouse_y)

        # 2. update
        game.update(dt)

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

        pygame.display.flip()

    pygame.quit()


main()