import pygame
import res
import random

FPS       = 60
SWIDTH    = 512 # Screen width
SHEIGHT   = 256 # Screen height

# Hard-coded color constants.
BLACK     = 0
BLACK_RGB = [BLACK] * 3
GREY      = 128
GREY_RGB  = [GREY] * 3
WHITE     = 255
WHITE_RGB = [WHITE] * 3
TRANSPARENT_RGB = [0] * 4

# Hard-coded layer constants for g_stage and g_fg.
STAGE_LAYER_PLAYER = 1
FG_LAYER_TEXT = 1

dt         = pygame.time.Clock().tick(FPS) / 1000 # Delta time
bg_color   = WHITE # Current BG color
shake      = 0 # Current "shake" value [used in shake_surface]

shake_surf = pygame.Surface((SWIDTH, SHEIGHT), pygame.SRCALPHA)
fade_surf = pygame.Surface((SWIDTH, SHEIGHT), pygame.SRCALPHA)
fade_surf.fill(BLACK_RGB)

def bg_inv():
    '''Returns the inverted variant of this color.'''
    return WHITE if bg_color == BLACK else BLACK

def bg_rgb():
    '''Returns the current background color as an RGB value.'''
    return [bg_color] * 3

def create():
    '''Initializes and configures the screen.'''
    screen = pygame.display.set_mode((SWIDTH, SHEIGHT))
    pygame.display.set_caption("monoman")
    pygame.display.set_icon(pygame.image.load(res.media_path("icon.png")))
    return screen

def shake_surface(surf):
    '''
    Shakes a surface based on the current shake value. This involves translating
    the surface a random value on another surface and then re-blitting the another 
    surface on the given surface.
    '''

    # Use different intensity values depending on the gravity of the event.
    # Usually entering an Exit [and especially an RGBExit] are the most powerful.
    intensity = 4 if shake > 25 else 2 if shake > 15 else 1

    shake_surf.fill(TRANSPARENT_RGB)
    shake_surf.blit(surf, pygame.Rect(random.randint(-intensity, intensity), random.randint(-intensity, intensity), SWIDTH, SHEIGHT))
    surf.fill(TRANSPARENT_RGB)
    surf.blit(shake_surf, pygame.Rect(0, 0, SWIDTH, SHEIGHT))

def fade_surface(surf, alpha):
    '''Fades out a surface to black via the specified alpha.'''
    fade_surf.set_alpha(alpha)
    surf.blit(fade_surf, pygame.Rect(0, 0, SWIDTH, SHEIGHT))