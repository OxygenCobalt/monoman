import pygame
import display
import sys
import os

def media_path(filename):
    return path(os.path.join("res", "media", filename))

def clv_path(idx):
    return path(os.path.join("res", "lvl", str(idx) + ".lvl"))

def path(relative_path):
    try:
        # When packing to an executable, PyInstaller makes a temp folder
        # and stores the path to it in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

spritesheet = pygame.image.load(media_path("spritesheet.png"))

audios = {}
audio_enabled = True

AUDIOS_CANCEL = ["spring", "die", "exit"]

def image_at(rectangle):
    # Find images at rect
    rect = pygame.Rect(rectangle)
    image = pygame.Surface(rect.size, pygame.SRCALPHA)
    image.fill((0, 0, 0, 0))
    image.blit(spritesheet, (0, 0), rect)

    return image

def load_strip(rect, image_count):
    # Load a strip of sprites, all with the same rect
    rects = [(rect[0] + (rect[2] * x), rect[1], rect[2], rect[3])
            for x in range(image_count)]

    # Find images at several rects
    return [MonoSurface(image_at(rect)) for rect in rects]

def play_audio(name):
    if not audio_enabled:
        return

    if name not in audios:
        # Generate the audio, was we haven't already.
        audios[name] = pygame.mixer.Sound(media_path(name + ".ogg"))

    if name in AUDIOS_CANCEL:
        # Cancel any previous playback if we need to.
        # This is mostly to band-aid certain bugs and make sure
        # important sounds play.
        audios[name].stop()

    audios[name].play()

class MonoSurface():
    '''A surface that dynamically generates different monochrome palettes for it's image.'''

    COLORS = {
        "black": display.BLACK_RGB,
        "grey": display.GREY_RGB,
        "white": display.WHITE_RGB
    }

    def __init__(self, surf):
        self.base = surf
        self.surfs = {
            "white": self.base
        }

    def get(self, color):
        '''Get a black/grey/white variation of the surface.'''
        assert color in MonoSurface.COLORS

        if color not in self.surfs:
            self.surfs[color] = self.ppc(self.base, MonoSurface.COLORS[color])

        return self.surfs[color]

    def ppc(self, surf, to):
        '''
        Converts a surface to the target color. This is expensive, hence it's done
        dynamically.
        '''
        inv = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)

        for x in range(inv.get_width()):
            for y in range(surf.get_height()):
                r, g, b, a = surf.get_at((x, y))

                if (r, g, b, a) == (255, 255, 255, 255):
                    r, g, b = to

                inv.set_at((x, y), (r, g, b, a))

        return inv

