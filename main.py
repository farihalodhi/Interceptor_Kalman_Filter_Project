import pygame
from settings import WIDTH, HEIGHT, FPS


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000      # seconds since the last frame

        # 1. input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. update (nothing to update yet)

        # 3. draw
        screen.fill((20, 20, 30))        # dark background
        pygame.display.flip()            # show what we drew

    pygame.quit()


main()