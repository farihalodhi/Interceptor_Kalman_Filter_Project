# music.py
import numpy as np
import pygame

NOTE = {"F2": 87.31, "G2": 98.00, "A2": 110.00, "C3": 130.81,
        "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.00}

# (bass note, three arpeggio notes) for Am - F - C - G
CHORDS = (("A2", ("A3", "C4", "E4")),
          ("F2", ("F3", "A3", "C4")),
          ("C3", ("C4", "E4", "G4")),
          ("G2", ("G3", "B3", "D4")))
PATTERN_A = (0, 1, 2, 1, 0, 1, 2, 1)
PATTERN_B = (2, 1, 0, 1, 2, 1, 0, 1)


def _note(freq, seconds, rate, shape, volume, decay, rng):
    n = int(rate * seconds)
    t = np.arange(n) / rate
    phase = (t * freq) % 1.0
    if shape == "square":
        wave = np.where(phase < 0.5, 1.0, -1.0)
    elif shape == "triangle":
        wave = 4.0 * np.abs(phase - 0.5) - 1.0
    else:
        wave = rng.uniform(-1.0, 1.0, n)
    attack = np.minimum(1.0, t / 0.004)
    release = np.clip((seconds - t) / 0.01, 0.0, 1.0)   # no clicks
    return wave * attack * release * np.exp(-decay * t) * volume


def build_loop(rate):
    # 8 chords x 2 seconds = a 16 second loop
    rng = np.random.default_rng(1)
    step = 0.25                                # one eighth note at 120 bpm
    chords = CHORDS + CHORDS
    total = int(rate * step * 8 * len(chords))
    mix = np.zeros(total)
    for c, (bass, arp) in enumerate(chords):
        pattern = PATTERN_A if c < 4 else PATTERN_B
        for i in range(8):
            start = int(rate * step * (c * 8 + i))
            lead = _note(NOTE[arp[pattern[i]]] * 2, step * 0.9, rate,
                         "square", 0.10, 6, rng)
            mix[start:start + len(lead)] += lead
            if i % 4 == 0:
                low = _note(NOTE[bass], 0.9, rate, "triangle", 0.28, 2, rng)
                mix[start:start + len(low)] += low
            if i % 2 == 1:
                hat = _note(0, 0.05, rate, "noise", 0.06, 60, rng)
                mix[start:start + len(hat)] += hat
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.8
    return (mix * 32767).astype(np.int16)


class Music:
    """A looping chiptune on its own mixer channel."""

    def __init__(self, volume=0.30):
        self.volume = volume
        self.muted = False
        self.sound = None
        self.channel = None
        try:
            settings = pygame.mixer.get_init()
            if settings is None:
                return
            rate, size, channels = settings
            if size != -16 or channels not in (1, 2):
                return
            mono = build_loop(rate)
            data = np.column_stack((mono, mono)) if channels == 2 else mono
            self.sound = pygame.sndarray.make_sound(np.ascontiguousarray(data))
            pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(1)       # channel 0 is kept for music
            self.channel = pygame.mixer.Channel(0)
        except Exception:
            self.sound = None
            self.channel = None

    def start(self):
        if self.sound is None or self.channel is None:
            return
        if not self.channel.get_busy():
            self.channel.play(self.sound, loops=-1)
        self.channel.set_volume(0.0 if self.muted else self.volume)

    def set_muted(self, muted):
        self.muted = muted
        if self.channel is not None:
            self.channel.set_volume(0.0 if muted else self.volume)