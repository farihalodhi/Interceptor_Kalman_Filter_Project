# main.py
import math
import pygame

from settings import (WIDTH, HEIGHT, FPS, DRONE_RADIUS, HUD_HEIGHT, LEVELS,
                      TURRET_COOLDOWN)
from drone import PATTERNS
from game_manager import GameManager
from sounds import SoundFX
from music import Music
from scores import load_scores, save_score
from ui import Slider, Button, draw_hud_background
from screens import (show_menu, show_loading, show_levels, show_results,
                     LEVEL_COLORS)
from overlay import (Trail, ErrorTracker, draw_stats, draw_legend,
                     draw_uncertainty)
from sprites import (draw_drone, draw_turret, draw_projectile, draw_reticle,
                     Effects)
from theme import (SPACE, PANEL_LIGHT, WHITE, MUTED, GOLD, CYAN, GREEN, ORANGE,
                   RED, PURPLE, BLUE, blend, draw_text, draw_outlined_text,
                   draw_panel, draw_scanlines, background, arena_grid,
                   Starfield, make_screen, poll_events)

WHO_COLORS = {"Player": GREEN, "Raw radar": ORANGE, "Kalman": PURPLE}
WHO_TEXT = {"Player": "YOU +1", "Raw radar": "RAW +1", "Kalman": "KALMAN +1"}


def draw_chip(screen, x, y, width, label, value, value_color=WHITE):
    rect = pygame.Rect(x, y, width, 52)
    draw_panel(screen, rect, fill=SPACE, border=PANEL_LIGHT, radius=8)
    draw_text(screen, label, 12, MUTED, (x + 8, y + 6), anchor="topleft",
              shadow=False)
    draw_text(screen, value, 16, value_color, (x + 8, y + 26),
              anchor="topleft")


def draw_timer(screen, time_left, time_limit):
    shown = max(0, math.ceil(time_left))
    urgent = shown <= 10
    color = RED if urgent else WHITE
    draw_text(screen, f"{shown // 60}:{shown % 60:02d}", 32, color,
              (WIDTH // 2, 28))
    bar = pygame.Rect(WIDTH // 2 - 100, 54, 200, 8)
    pygame.draw.rect(screen, (60, 64, 110), bar, border_radius=4)
    fill = int(bar.width * max(0.0, time_left) / time_limit)
    if fill > 0:
        pygame.draw.rect(screen, RED if urgent else CYAN,
                         pygame.Rect(bar.x, bar.y, fill, bar.height),
                         border_radius=4)


def draw_hud(screen, game, level, cfg, locked, time_limit, slider, buttons,
             sfx):
    top = HEIGHT
    draw_hud_background(screen, top, WIDTH, HUD_HEIGHT)
    if locked:
        x = 20
        chips = (("LEVEL", level.upper(), LEVEL_COLORS[level], 110),
                 ("PATH", cfg["pattern"].upper(), WHITE, 140),
                 ("SPEED", str(cfg["speed"]), WHITE, 80),
                 ("NOISE", str(cfg["noise"]), WHITE, 80),
                 ("TIME", f"{time_limit} S", WHITE, 90))
        for label, value, color, width in chips:
            draw_chip(screen, x, top + 12, width, label, value, color)
            x += width + 8
    else:
        slider.draw(screen)
        draw_text(screen, "TRAJECTORY", 12, WHITE, (270, top + 10),
                  anchor="topleft")
        for i, button in enumerate(buttons):
            button.draw(screen, active=(game.drone.pattern == PATTERNS[i]))

    col_a = ["M SOUND " + ("OFF" if sfx.muted else "ON"), "F11 SCREEN",
             "ESC LEVELS"]
    col_b = ["P PAUSE"] if locked else ["T PATH", "UP/DN NOISE"]
    for i, line in enumerate(col_a):
        draw_text(screen, line, 12, MUTED, (630, top + 10 + i * 18),
                  anchor="topleft", shadow=False)
    for i, line in enumerate(col_b):
        draw_text(screen, line, 12, MUTED, (765, top + 10 + i * 18),
                  anchor="topleft", shadow=False)


def _play_level(screen, clock, sfx, music, name, level):
    cfg = LEVELS[level]
    locked = cfg.get("locked", True)      # only the Lab lets you change them
    time_limit = cfg.get("time")          # None = untimed (Lab)
    game = GameManager(noise=cfg["noise"], seed=42, pattern=cfg["pattern"],
                       speed=cfg["speed"])
    game.record_events = True      # so we can play a sound for each event

    time_left = time_limit
    countdown = 3.0 if time_limit else 0.0     # 3-2-1 before a timed round
    go_timer = 0.0
    paused = False
    anim = 0.0
    stars = Starfield(WIDTH, HEIGHT, 70, seed=11)
    effects = Effects()
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((8, 8, 20, 170))

    true_trail = Trail(RED)
    estimate_trail = Trail(PURPLE)
    tracker = ErrorTracker()
    last_x = game.drone.x

    slider = None
    buttons = []
    if not locked:
        slider = Slider(20, HEIGHT + 50, 230, 0, 100, cfg["noise"], 5,
                        "RADAR NOISE")
        for i, pattern in enumerate(PATTERNS):
            buttons.append(Button(270 + i * 112, HEIGHT + 34, 104, 28,
                                  pattern.upper(), 12))

    while True:
        dt = clock.tick(FPS) / 1000
        anim += dt

        # 1. input
        for event in poll_events():
            if event.type == pygame.QUIT:
                return "quit", None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "levels", None

            if not locked:
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
                    and event.pos[1] < HEIGHT
                    and countdown <= 0 and not paused):
                game.player_fire()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    sfx.toggle_mute()
                    music.set_muted(sfx.muted)
                if event.key == pygame.K_p and time_limit and countdown <= 0:
                    paused = not paused
                if not locked:
                    if event.key == pygame.K_UP:
                        game.change_noise(5)
                    if event.key == pygame.K_DOWN:
                        game.change_noise(-5)
                    if event.key == pygame.K_t:
                        game.next_pattern()

        # keep the slider in step with the noise when keys change it
        if slider is not None and not slider.dragging:
            slider.value = game.radar.noise

        mouse_x, mouse_y = pygame.mouse.get_pos()
        game.aim_player(mouse_x, mouse_y)

        # 2. update
        if not paused:
            stars.update(dt)
        if paused:
            pass                                  # everything is frozen
        elif countdown > 0:
            countdown -= dt                       # 3-2-1, the game waits
            if countdown <= 0:
                go_timer = 0.7
        else:
            before = (game.drone.x, game.drone.y)
            game.update(dt)

            # a sound and an explosion for everything that happened
            for kind, who in game.events:
                sfx.play(kind, who)
                if kind == "hit":
                    effects.explode(before[0], before[1],
                                    WHO_COLORS.get(who, WHITE),
                                    WHO_TEXT.get(who))
            game.events.clear()
            effects.update(dt)
            go_timer = max(0.0, go_timer - dt)

            # a new round has started when the drone jumps back to the left
            if game.drone.x < last_x:
                true_trail.clear()
                estimate_trail.clear()
                tracker.clear()
            last_x = game.drone.x
            true_trail.add(game.drone.x, game.drone.y)
            if game.kalman.initialized:
                ex, ey = game.kalman.position()
                estimate_trail.add(ex, ey)
            tracker.add(game)

            if time_limit is not None:
                time_left -= dt
                if time_left <= 0:
                    result = {
                        "player": (game.player.hits, game.player.shots),
                        "raw": (game.raw_turret.hits, game.raw_turret.shots),
                        "kalman": (game.kalman_turret.hits,
                                   game.kalman_turret.shots),
                    }
                    return "done", result

        # 3. draw
        screen.blit(background(), (0, 0))
        screen.blit(arena_grid(), (0, 0))
        stars.draw(screen)

        draw_stats(screen, game, tracker)         # panels first, so the
        draw_legend(screen, WIDTH - 200, 44)      # game objects stay on top

        true_trail.draw(screen)
        estimate_trail.draw(screen)

        count = len(game.radar_dots)
        for i, (rx, ry) in enumerate(game.radar_dots):
            fade = (i + 1) / count
            pygame.draw.circle(screen, blend(SPACE, BLUE, 0.25 + 0.75 * fade),
                               (int(rx), int(ry)), 2 + int(2 * fade))

        draw_drone(screen, game.drone.x, game.drone.y, anim)

        # Kalman estimate (ring), its uncertainty (ellipse) and the predicted
        # interception point (reticle), drawn after the drone so they stay visible
        if game.kalman.initialized:
            ex, ey = game.kalman.position()
            draw_uncertainty(screen, game.kalman, PURPLE)
            pygame.draw.circle(screen, PURPLE, (int(ex), int(ey)),
                               DRONE_RADIUS + 5, 3)
        if game.aim_point is not None:
            draw_reticle(screen, game.aim_point[0], game.aim_point[1], anim)

        for turret, color, label in ((game.player, GREEN, "YOU"),
                                     (game.raw_turret, ORANGE, "RAW"),
                                     (game.kalman_turret, PURPLE, "KALMAN")):
            kick = max(0.0, (turret.timer - (TURRET_COOLDOWN - 0.12)) / 0.12)
            draw_turret(screen, turret.x, turret.y, turret.angle, color, kick,
                        label)
            for p in turret.projectiles:
                draw_projectile(screen, p, color)

        effects.draw(screen)

        # mouse crosshair inside the arena, normal cursor elsewhere
        if mouse_y < HEIGHT and not paused:
            pygame.mouse.set_visible(False)
            draw_reticle(screen, mouse_x, mouse_y, 0.0, GREEN)
        else:
            pygame.mouse.set_visible(True)

        if time_limit is not None:
            draw_timer(screen, time_left, time_limit)

        pill = pygame.Rect(WIDTH - 210, 8, 200, 28)
        draw_panel(screen, pill, fill=SPACE, border=LEVEL_COLORS[level],
                   radius=8, alpha=190)
        draw_text(screen, name.upper()[:14], 12, WHITE, pill.center,
                  shadow=False)

        if paused:
            screen.blit(shade, (0, 0))
            draw_outlined_text(screen, "PAUSED", 64, CYAN,
                               (WIDTH // 2, HEIGHT // 2 - 20), thickness=4)
            draw_text(screen, "PRESS P TO RESUME", 16, WHITE,
                      (WIDTH // 2, HEIGHT // 2 + 50))
        elif countdown > 0:
            screen.blit(shade, (0, 0))
            draw_text(screen, "GET READY", 24, WHITE,
                      (WIDTH // 2, HEIGHT // 2 - 100))
            draw_outlined_text(screen, str(math.ceil(countdown)), 128, GOLD,
                               (WIDTH // 2, HEIGHT // 2 + 10), thickness=5)
        elif go_timer > 0:
            draw_outlined_text(screen, "GO!", 96, GREEN,
                               (WIDTH // 2, HEIGHT // 2), thickness=4)

        draw_hud(screen, game, level, cfg, locked, time_limit, slider,
                 buttons, sfx)
        draw_scanlines(screen)
        pygame.display.flip()


def play_level(screen, clock, sfx, music, name, level):
    """Runs one round at the chosen level.
    Returns (status, result). status is "done" (the timer ran out, result
    holds everyone's hits and shots), "levels" (Esc) or "quit" (window closed)."""
    try:
        return _play_level(screen, clock, sfx, music, name, level)
    finally:
        pygame.mouse.set_visible(True)


def main():
    pygame.init()
    screen = make_screen()
    pygame.display.set_caption("Interceptor")
    clock = pygame.time.Clock()
    sfx = SoundFX()
    music = Music()
    music.set_muted(sfx.muted)
    music.start()

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

        # 3. level select, play a round, results, then play again or go back
        while running:
            level = show_levels(screen, clock, name)
            if level is None:            # window closed
                running = False
                break
            if level == "back":          # Esc: change name
                break

            replay = True
            while replay:
                replay = False
                status, result = play_level(screen, clock, sfx, music, name,
                                            level)
                if status == "quit":
                    running = False
                elif status == "done":
                    record = save_score(level, name, result["player"][0])
                    best = load_scores().get(level)
                    choice = show_results(screen, clock, name, level, result,
                                          record, best)
                    if choice is None:
                        running = False
                    elif choice == "again":
                        replay = True

    pygame.quit()


if __name__ == "__main__":
    main()