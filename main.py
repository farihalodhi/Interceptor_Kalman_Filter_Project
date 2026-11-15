# main.py
import math
import pygame
from settings import WIDTH, HEIGHT, FPS, DRONE_RADIUS, PROJECTILE_RADIUS
from game_manager import GameManager


def draw_turret(screen, turret, color):
    tip_x = turret.x + 30 * math.cos(turret.angle)
    tip_y = turret.y + 30 * math.sin(turret.angle)
    pygame.draw.line(screen, color, (turret.x, turret.y), (tip_x, tip_y), 6)
    pygame.draw.circle(screen, color, (turret.x, turret.y), 14)
    for p in turret.projectiles:
        pygame.draw.circle(screen, color, (int(p.x), int(p.y)),
                           PROJECTILE_RADIUS)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)

    game = GameManager(noise=15, seed=42)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.player_fire()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    game.change_noise(5)
                if event.key == pygame.K_DOWN:
                    game.change_noise(-5)

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

        draw_turret(screen, game.player, (80, 200, 120))
        draw_turret(screen, game.raw_turret, (240, 170, 60))

        y = 10
        for turret in (game.player, game.raw_turret):
            line = (f"{turret.name}: {turret.hits}/{turret.shots} hits "
                    f"({turret.hit_rate():.0f}%)")
            screen.blit(font.render(line, True, (240, 240, 240)), (10, y))
            y += 24
        noise_text = f"Radar noise: {game.radar.noise}  (Up/Down keys)"
        screen.blit(font.render(noise_text, True, (240, 240, 240)), (10, y))

        pygame.display.flip()

    pygame.quit()

main()