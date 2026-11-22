# ui.py
import pygame

from theme import (PANEL, PANEL_LIGHT, OUTLINE, WHITE, CYAN, PURPLE, MUTED,
                   blend, draw_panel, draw_text, get_font)

TEXT = WHITE
ACCENT = PURPLE
TRACK = (60, 64, 110)
BUTTON = PANEL_LIGHT
BUTTON_HOVER = blend(PANEL_LIGHT, WHITE, 0.15)


def draw_hud_background(screen, y, width, height):
    pygame.draw.rect(screen, PANEL, (0, y, width, height))
    pygame.draw.line(screen, CYAN, (0, y), (width, y), 3)
    pygame.draw.line(screen, OUTLINE, (0, y + 3), (width, y + 3), 2)


class Slider:
    def __init__(self, x, y, width, min_value, max_value, value, step, label):
        self.rect = pygame.Rect(x, y, width, 8)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.step = step
        self.label = label
        self.dragging = False

    def _ratio(self):
        clamped = max(self.min_value, min(self.max_value, self.value))
        return (clamped - self.min_value) / (self.max_value - self.min_value)

    def _value_from_mouse(self, mouse_x):
        ratio = (mouse_x - self.rect.x) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        raw = self.min_value + ratio * (self.max_value - self.min_value)
        return int(round(raw / self.step)) * self.step

    def handle_event(self, event):
        # returns True when the slider used the event
        grab_area = self.rect.inflate(20, 28)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and grab_area.collidepoint(event.pos)):
            self.dragging = True
            self.value = self._value_from_mouse(event.pos[0])
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.value = self._value_from_mouse(event.pos[0])
            return True
        if (event.type == pygame.MOUSEBUTTONUP and event.button == 1
                and self.dragging):
            self.dragging = False
            return True
        return False

    def draw(self, screen, font=None):
        draw_text(screen, f"{self.label}: {self.value}", 12, WHITE,
                  (self.rect.x, self.rect.y - 24), anchor="topleft")
        pygame.draw.rect(screen, OUTLINE, self.rect.inflate(6, 6),
                         border_radius=8)
        pygame.draw.rect(screen, TRACK, self.rect, border_radius=4)
        knob_x = self.rect.x + int(self._ratio() * self.rect.width)
        filled = pygame.Rect(self.rect.x, self.rect.y,
                             knob_x - self.rect.x, self.rect.height)
        if filled.width > 0:
            pygame.draw.rect(screen, CYAN, filled, border_radius=4)
        center = (knob_x, self.rect.centery)
        pygame.draw.circle(screen, OUTLINE, center, 12)
        pygame.draw.circle(screen, WHITE, center, 9)
        pygame.draw.circle(screen, PURPLE, center, 4)


class Button:
    def __init__(self, x, y, width, height, text, size=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.size = size

    def handle_event(self, event):
        # returns True when this button was clicked
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, screen, font=None, active=False):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if active:
            color = PURPLE
        elif hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON
        face = self.rect.move(0, -2 if hovered else 0)
        pygame.draw.rect(screen, OUTLINE, self.rect.move(0, 3).inflate(6, 6),
                         border_radius=10)
        pygame.draw.rect(screen, blend(color, OUTLINE, 0.4), self.rect.move(0, 3),
                         border_radius=8)
        pygame.draw.rect(screen, color, face, border_radius=8)
        pygame.draw.rect(screen, OUTLINE, face, 3, border_radius=8)
        text_color = OUTLINE if active else WHITE
        draw_text(screen, self.text, self.size, text_color, face.center,
                  shadow=not active)


class TextBox:
    def __init__(self, x, y, width, height, max_chars=14, text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_chars = max_chars
        self.text = text
        self.timer = 0.0              # drives the blinking cursor

    def handle_event(self, event):
        # returns True when Enter is pressed
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif (event.unicode and len(self.text) < self.max_chars
                    and (event.unicode.isalnum() or event.unicode in " _-.")):
                self.text += event.unicode
        return False

    def update(self, dt):
        self.timer += dt

    def value(self):
        return self.text.strip()

    def draw(self, screen, font=None):
        draw_panel(screen, self.rect, fill=PANEL, border=CYAN, radius=10,
                   border_width=3)
        x = self.rect.x + 16
        if self.text:
            draw_text(screen, self.text, 24, WHITE, (x, self.rect.centery),
                      anchor="midleft")
        else:
            draw_text(screen, "TYPE YOUR NAME", 16, MUTED,
                      (x, self.rect.centery), anchor="midleft", shadow=False)
        if int(self.timer * 2) % 2 == 0:          # blinking cursor
            width = get_font(24).size(self.text)[0] if self.text else 0
            pygame.draw.rect(screen, CYAN, (x + width + 4, self.rect.y + 12,
                                            10, self.rect.height - 24))