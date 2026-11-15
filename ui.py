# ui.py
import pygame

TEXT = (240, 240, 240)
HUD_BACKGROUND = (30, 32, 46)
HUD_LINE = (70, 74, 96)
TRACK = (70, 74, 96)
ACCENT = (200, 120, 255)
BUTTON = (52, 56, 80)
BUTTON_HOVER = (74, 80, 112)
ACTIVE_TEXT = (20, 20, 30)


def draw_hud_background(screen, y, width, height):
    pygame.draw.rect(screen, HUD_BACKGROUND, (0, y, width, height))
    pygame.draw.line(screen, HUD_LINE, (0, y), (width, y), 2)


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

    def draw(self, screen, font):
        label = font.render(f"{self.label}: {self.value}", True, TEXT)
        screen.blit(label, (self.rect.x, self.rect.y - 28))
        pygame.draw.rect(screen, TRACK, self.rect, border_radius=4)
        knob_x = self.rect.x + int(self._ratio() * self.rect.width)
        filled = pygame.Rect(self.rect.x, self.rect.y,
                             knob_x - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, ACCENT, filled, border_radius=4)
        pygame.draw.circle(screen, TEXT, (knob_x, self.rect.centery), 9)


class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text

    def handle_event(self, event):
        # returns True when this button was clicked
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, screen, font, active=False):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if active:
            color = ACCENT
        elif hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        text_color = ACTIVE_TEXT if active else TEXT
        label = font.render(self.text, True, text_color)
        screen.blit(label, label.get_rect(center=self.rect.center))