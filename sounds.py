import numpy as np
import pygame

SAMPLE_RATE = 44100
def _to_sound(wave,volume=1.0):
    wave = np.clip(wave,-1,1)
    data = (wave * 32767).astype(np.int16)
    sound = pygame.sndarray.make_sound(np.column_stack((data,data)))
    sound.set_volume(volume)
    return sound

def _make_pew(volume=1.0):
    n = int(SAMPLE_RATE * 0.18)
    t = np.linspace(0,0.18,n,endpoint=False)
    freq = 1500*np.exp(-t*14)+200
    phase = 2*np.pi*np.cumsum(freq) / SAMPLE_RATE
    wave = 0.7 * np.sin(phase) + 0.3 * np.sign(np.sin(phase))
    wave *= np.exp(-t * 12) 
    return _to_sound(wave * 0.5,volume) 

def _make_hit(volume=1.0):
    n = int(SAMPLE_RATE * 0.45)
    t = np.linspace(0,0.45,n,endpoint=False)
    rng = np.random.default_rng(1)
    noise = rng.uniform(-1,1,n) * np.exp(-t * 9)
    freq = 140 * np.exp(-t*6) + 40
    thump = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * np.exp(-t * 7)
    return _to_sound((0.6 * noise + 0.8 * thump) * 0.7, volume)

class SoundFX:
    def __init__(self):
        self.enabled = False
        self.muted = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
            # separate Sound objects, because volume belongs to the Sound
            self.pew = _make_pew(1.0)              # player's shot (loud)
            self.pew_quiet = _make_pew(0.15)       # automatic turrets
            self.hit = _make_hit(1.0)              # player's hit
            self.hit_soft = _make_hit(0.5)         # automatic turrets
            self.enabled = True
        except Exception as error:                  # no audio device, etc.
            print("Sound disabled:", error)          

    def toggle_mute(self):
        self.muted = not self.muted

    def play(self,event,who):
        #event: "fire" or "hit"
        # who: name of turret
        if not self.enabled or self.muted:
            return
        player = (who == "Player")
        if event == "fire":
            (self.pew if player else self.pew_quiet).play()
        elif event == "hit":
            (self.hit if player else self.hit_soft).play()
                  