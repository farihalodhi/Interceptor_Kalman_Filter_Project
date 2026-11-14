# main.py
import math
import pygame
from settings import WIDTH, HEIGHT, FPS, DRONE_RADIUS, PROJECTILE_RADIUS
from drone import Drone
from turret import Turret


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    drone = Drone(-DRONE_RADIUS, 150, 120, 30)
    player = Turret(WIDTH // 2, HEIGHT - 40)
    projectiles = []
    hits = 0
    shots = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                bullet = player.fire()
                if bullet is not None:
                    projectiles.append(bullet)
                    shots += 1

        mouse_x, mouse_y = pygame.mouse.get_pos()
        player.aim_at(mouse_x, mouse_y)

        # 2. update
        player.update(dt)
        drone.update(dt)
        for p in projectiles:
            p.update(dt)
            if p.alive and p.hits(drone):
                p.alive = False
                hits += 1
                drone.reset()
        projectiles = [p for p in projectiles if p.alive]
        if drone.is_out():
            drone.reset()

        # 3. draw
        screen.fill((20, 20, 30))
        pygame.draw.circle(screen, (220, 60, 60),
                           (int(drone.x), int(drone.y)), DRONE_RADIUS)

        tip_x = player.x + 30 * math.cos(player.angle)
        tip_y = player.y + 30 * math.sin(player.angle)
        pygame.draw.line(screen, (80, 200, 120),
                         (player.x, player.y), (tip_x, tip_y), 6)
        pygame.draw.circle(screen, (80, 200, 120),
                           (player.x, player.y), 14)

        for p in projectiles:
            pygame.draw.circle(screen, (255, 255, 120),
                               (int(p.x), int(p.y)), PROJECTILE_RADIUS)

        text = font.render(f"Hits: {hits}   Shots: {shots}",
                           True, (240, 240, 240))
        screen.blit(text, (10, 10))
        pygame.display.flip()

    pygame.quit()


main()