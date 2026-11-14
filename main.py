import pygame
from settings import WIDTH, HEIGHT, FPS,DRONE_RADIUS
from drone import Drone

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    drone = Drone(-DRONE_RADIUS, 150, 120, 30)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000      # seconds since the last frame

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. update
        drone.update(dt)
        if drone.is_out():
            drone.reset()
        # 3. draw
        screen.fill((20, 20, 30))        # dark background
        pygame.draw.circle(screen, (220, 60, 60),
                           (int(drone.x), int(drone.y)), DRONE_RADIUS)
        pygame.display.flip()            # show what we drew

    pygame.quit()


main()