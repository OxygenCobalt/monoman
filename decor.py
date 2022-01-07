import sprites
import pygame
import random
import math
import res
import lvl
import display

class DeathParticle(pygame.sprite.Sprite):
    '''The particle used when the player dies.'''
    SIZE = 8

    def __init__(self, pos):
        super().__init__(sprites.g_stage, sprites.g_decor)

        # --- POSITIONING ---
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.rect = pygame.Rect(self.pos.x, self.pos.y, DeathParticle.SIZE, DeathParticle.SIZE)
        self.vel = random.randint(2, 3)
        self.direction = math.radians(random.randint(0, 360))

        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        sprites.g_stage.change_layer(self, display.STAGE_LAYER_PLAYER)

    def update(self):
        self.update_x()

        # Steadily fade out as we go on. Once we are fully transparent, we remove this particle.
        self.image.fill([display.bg_inv()] * 3)
        self.image.set_alpha(self.image.get_alpha() - 15)

        if self.image.get_alpha() <= 0:
            self.kill()

    def update_x(self):
        # Move in our randomly assigned direction with some trig.
        self.pos.x += (self.vel * math.cos(self.direction))
        self.pos.y += (self.vel * math.sin(self.direction))

        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

class CrumbleParticle(pygame.sprite.Sprite):
    '''The particle used when an unstable block is broken.'''
    SIZE = 4

    def __init__(self, pos, color):
        super().__init__(sprites.g_stage, sprites.g_decor)

        # --- POSITIONING ---
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.rect = pygame.Rect(self.pos.x, self.pos.y, CrumbleParticle.SIZE, CrumbleParticle.SIZE)
        self.vel = random.randint(1, 2)
        self.direction = math.radians(random.randint(0, 360))

        # --- APPEARANCE ---
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.color = color

        sprites.g_stage.change_layer(self, display.STAGE_LAYER_PLAYER)

    def update(self):
        self.update_x()

        # Similar to DeathParticle, also fade out, but also make sure this does
        # not display when the background matches the particle.
        self.image.fill([self.color, self.color, self.color, (self.color != display.bg_color) * 255])
        self.image.set_alpha(self.image.get_alpha() - 15)

        if self.image.get_alpha() <= 0:
            self.kill()

    def update_x(self):
        # Move in our randomly assigned direction with some trig.
        self.pos.x += (self.vel * math.cos(self.direction))
        self.pos.y += (self.vel * math.sin(self.direction))

        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

class RgbParticle(pygame.sprite.Sprite):
    '''The particle shown on the RGBExit sprite.'''
    SIZE = 4
    DISTANCE = 16

    def __init__(self, pos):
        super().__init__(sprites.g_stage, sprites.g_decor)

        # --- POSITIONING ---
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.rect = pygame.Rect(self.pos.x, self.pos.y, RgbParticle.SIZE, RgbParticle.SIZE)
        self.vel = 24
        self.distance = 24
        self.direction = math.radians(random.randint(0, 360))

        # --- APPEARANCE ---
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image.set_alpha(0)

        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        self.update_x()

        self.vel = -1

    def update(self):
        self.update_x()
        self.update_alpha()
        self.image.fill(self.color)

    def update_x(self):
        # Move in our randomly assigned direction with some trig.
        self.pos.x += (self.vel * math.cos(self.direction))
        self.pos.y += (self.vel * math.sin(self.direction))

        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

    def update_alpha(self):
        self.distance -= 1

        # Slowly fade in and then fade out as we get closer to the sprite.
        if self.distance >= 16:
            self.image.set_alpha(self.image.get_alpha() + 31.875)
        elif self.distance < 8:
            self.image.set_alpha(self.image.get_alpha() - 31.875)

        # Once we are colliding with the RGBExit, we disappear.
        if self.distance == 0:
            self.kill()          

class Wrapping(pygame.sprite.Sprite):
    '''A gradient used to indicate wrapping.'''
    POS_START = 0
    POS_END = 1

    def __init__(self, pos):
        super().__init__(sprites.g_fg, sprites.g_decor)

        self.image = pygame.Surface((16, display.SHEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = (pos * (display.SWIDTH - 16), 0))

        for i in range(16):
            pygame.draw.rect(self.image, [128, 128, 128, 255 - (255 / 15) * i], (i, 0, 1, display.SHEIGHT))

        if pos == Wrapping.POS_END:
            self.image = pygame.transform.flip(self.image, True, False)

class Cloud(pygame.sprite.Sprite):
    '''A sprite for the "cloud" squares in the background.'''
    def __init__(self, pos):
        super().__init__(sprites.g_bg)

        # Randomly pick if we are a small cloud or not.
        self.small = bool(random.getrandbits(1))

        # Then generate our attributes depending on our size.
        size = 8 if self.small else 16

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = pos)

        self.pos = pygame.math.Vector2(pos)
        self.vel = 0.2 if self.small else 0.4

        self.image.set_alpha(100 if self.small else 150)

        # If we ended up colliding with another cloud, just remove ourselves.
        if len(pygame.sprite.spritecollide(self, sprites.g_bg, False)) > 1:
            self.kill()

    def update(self):
        # Move in different directions depending on the background color.
        self.vel = abs(self.vel)

        if display.bg_color == display.WHITE:
            self.vel = -abs(self.vel)

        self.image.fill([display.bg_inv()] * 3)

        self.pos.x += self.vel
        self.rect.x = self.pos.x

        if self.pos.x > display.SWIDTH + 16 or self.pos.x < -16:
            # If we have exceeded the display bounds, generate a new cloud
            # at a new random position before removing outselves.
            if self.vel > 0:
                new_x = -16
            else:
                new_x = display.SWIDTH + 16

            new_y = random.randint(0, display.SHEIGHT)

            Cloud((new_x, new_y))

            self.kill()

class Text(pygame.sprite.Sprite):
    '''A superclass that displays ASCII text.'''
    CHAR_SIZE = 8

    def generate_text(self, text):
        '''Generates a list of surfaces that correspond to the given text.'''
        self.text = []

        for i, char in enumerate(text.upper()):
            char_x = ord(char)

            # Drop control characters
            if char_x < ord(' '):
                char_x = ord('?')

            # To save space we just use uppercase ASCII chars, so we make all
            # text uppercase and then handle the special symbol exceptions.
            # All other characters are dropped in this system.
            if char_x > ord('`'):
                char_map = {
                    ord('{'): ord('`') + 1,
                    ord('|'): ord('`') + 2,
                    ord('}'): ord('`') + 3,
                    ord('~'): ord('`') + 4
                }

                try:
                    char_x = char_map[char_x]
                except:
                    char_x = ord('?')

            if char_x != ord(' '):
                # Not a space, locate where our character should be on the spritesheet.
                char_x -= ord('!')
                char_y = 0

                while char_x > 7:
                    char_x -= 8
                    char_y += 1

                self.text.append(
                    res.MonoSurface(
                        res.image_at((
                            64 + (char_x * Text.CHAR_SIZE),
                            char_y * Text.CHAR_SIZE,
                            Text.CHAR_SIZE,
                            Text.CHAR_SIZE
                        ))
                    )
                )
            else:
                # Space, just append an empty surface.
                self.text.append(
                    res.MonoSurface(
                        pygame.Surface((Text.CHAR_SIZE, Text.CHAR_SIZE), pygame.SRCALPHA)
                    )
                )

class StaticText(Text):
    '''Text at a static position. This will never disappear on it's own.'''
    def __init__(self, text, y):
        super().__init__(sprites.g_stage)

        self.image = pygame.Surface((Text.CHAR_SIZE * len(text), Text.CHAR_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = ((display.SWIDTH - self.image.get_width()) // 2, y))

        self.generate_text(text)

        for i, surf in enumerate(self.text):
            self.image.blit(
                surf.get("white"),
                (i * Text.CHAR_SIZE, 0, Text.CHAR_SIZE, Text.CHAR_SIZE)
            )

class LargeText(Text):
    '''A larger variation of StaticText.'''
    CHAR_SIZE = 16

    def __init__(self, text, y):
        super().__init__(sprites.g_stage)

        self.image = pygame.Surface((LargeText.CHAR_SIZE * len(text), LargeText.CHAR_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = ((display.SWIDTH - self.image.get_width()) // 2, y))

        self.generate_text(text)

        for i, surf in enumerate(self.text):
            self.image.blit(
                pygame.transform.scale(surf.get("white"), (LargeText.CHAR_SIZE, LargeText.CHAR_SIZE)),
                (i * LargeText.CHAR_SIZE, 0, LargeText.CHAR_SIZE, LargeText.CHAR_SIZE)
            )

class FadingText(Text):
    '''Text that will fade in or out on command.'''
    def __init__(self, text, pos, alpha, step):
        super().__init__(sprites.g_fg, sprites.g_decor)

        self.image = pygame.Surface((Text.CHAR_SIZE * len(text), Text.CHAR_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = pos)
        self.image.set_alpha(alpha)

        self.fade_in = False
        self.fade_out = False
        self.step = step

        self.generate_text(text)

        sprites.g_fg.change_layer(self, display.FG_LAYER_TEXT)

    def update(self):
        self.image.fill(display.TRANSPARENT_RGB)

        # Properly blit our text before we continue.
        for i, surf in enumerate(self.text):
            if display.bg_color == display.BLACK:
                s = surf.get("white")
            elif display.bg_color == display.WHITE:
                s = surf.get("black")

            self.image.blit(s, (i * Text.CHAR_SIZE, 0, Text.CHAR_SIZE, Text.CHAR_SIZE))

        if self.fade_in:
            # We're fading in, see if we need to increase the alpha.
            if self.image.get_alpha() < 255:
                self.image.set_alpha(self.image.get_alpha() + self.step)

        if self.fade_out:
            # We're fading out, see if we need to decrease the alpha.
            self.image.set_alpha(self.image.get_alpha() - self.step)

            if self.image.get_alpha() == 0:
                self.kill()

    def show(self):
        '''Fades in this text.'''
        self.fade_out = False
        self.fade_in = True

    def hide(self):
        '''Fades out this text.'''
        self.fade_in = False
        self.fade_out = True

class TitleText(FadingText):
    '''A FadingText that immediately pops in and then fades out after some time.'''
    def __init__(self, text):
        super().__init__(text, (Text.CHAR_SIZE, Text.CHAR_SIZE), 255, 5)
        self.grace_ticks = 60

    def update(self):
        if self.grace_ticks > 0:
            self.grace_ticks -= 1
        else:
            self.hide()

        super().update()

class FlipIndicator(pygame.sprite.Sprite):
    '''An indicator of the cooldown period between flips. This will fill up as the cooldown decreases.'''
    SIZE = 16
    INDICATOR = res.MonoSurface(res.image_at((96, 64, 8, 8)))

    def __init__(self):
        super().__init__(sprites.g_fg)

        self.image = pygame.Surface((FlipIndicator.SIZE, FlipIndicator.SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft = (display.SWIDTH - 24, 8))

        sprites.g_fg.change_layer(self, display.FG_LAYER_TEXT)

    def update(self):
        self.image.fill(display.TRANSPARENT_RGB)

        if lvl.player is not None:
            # Figure out how much the cooldown has completewd.
            ratio = max(lvl.player.flip_cooldown, 0) / sprites.Player.FLIP_COOLDOWN
            coord = math.ceil(16 * (1 - ratio))

            # Then fill up the screen with the correct bounded rectangle to reflect that.
            self.image.fill(
                [display.bg_inv()] * 3,
                (0, FlipIndicator.SIZE - coord, FlipIndicator.SIZE, coord)
            )

            # If the cooldown is over, show an icon that indicates it.
            if (coord == 16):
                if display.bg_color == 0:
                    indicator = FlipIndicator.INDICATOR.get("black")
                else:
                    indicator = FlipIndicator.INDICATOR.get("white")
                
                self.image.blit(indicator, (4, 4, 8, 8))

class Button(Text):
    '''A Text implementation that has an icon and can be selected.'''
    def generate_btn(self, label, icon, y):
        self.generate_text(label)

        self.label = label
        self.icon = icon

        self.image = pygame.Surface((32 + (Text.CHAR_SIZE * len(label)), 24))
        self.image.blit(icon, (8, 8, 8, 8))

        self.rect = self.image.get_rect(
            topleft = ((display.SWIDTH - self.image.get_width()) // 2, y)
        )

        for i, surf in enumerate(self.text):
            self.image.blit(
                surf.get("white"),
                (24 + (i * Text.CHAR_SIZE), 8, Text.CHAR_SIZE, Text.CHAR_SIZE)
            )

class PlayButton(Button):
    '''A button that (re)start the game.'''
    TYPE = 0
    ICON = res.image_at((104, 64, 8, 8))

    def __init__(self, label, y):
        super().__init__(sprites.g_stage)
        self.generate_btn(label, PlayButton.ICON, y)

    def select(self):
        '''Select this button.'''
        return PlayButton.TYPE

class SoundButton(Button):
    '''A button that configures sound.'''
    TYPE = 1
    ICON_ON = res.image_at((112, 64, 8, 8))
    ICON_OFF = ICON_ON.copy()
    ICON_OFF.fill(display.BLACK_RGB, (4, 0, 4, 8))

    def __init__(self, y):
        super().__init__(sprites.g_stage)
        self.generate_btn("sound on", SoundButton.ICON_ON, y)

    def select(self):
        '''Select this button.'''
        res.audio_enabled = not res.audio_enabled
        self.update_button()
        return SoundButton.TYPE

    def update_button(self):
        # Make sure this button updates to reflect the state. 
        # This also requires us to regen the whole button surface and bounds.
        if res.audio_enabled:
            icon = SoundButton.ICON_ON
            label = "sound on"
        else:
            icon = SoundButton.ICON_OFF
            label = "sound off"

        self.generate_btn(label, icon, self.rect.y)


class ExitButton(Button):
    '''A button to exit the game.'''
    TYPE = 2
    ICON = res.image_at((120, 64, 8, 8))

    def __init__(self, y):
        super().__init__(sprites.g_stage)
        self.generate_btn("exit", ExitButton.ICON, y)

    def select(self):
        '''Select this button.'''
        return ExitButton.TYPE

class Selector(pygame.sprite.Sprite):
    '''A selector for a group of buttons.'''
    def __init__(self, *buttons):
        super().__init__(sprites.g_stage)
        self.rect = None
        self.buttons = buttons

        self.set_button(0)

        sprites.g_stage.change_layer(self, display.STAGE_LAYER_PLAYER)

    def update(self):
        rect = self.buttons[self.button].rect

        if self.rect != rect:
            self.image = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            self.image.fill(display.WHITE_RGB)
            self.image.fill(display.TRANSPARENT_RGB, (2, 2, rect.width - 4, rect.height - 4))

            self.rect = pygame.Rect(rect)

    def set_button(self, idx):
        self.button = idx

    def next(self):
        '''Go to the next button, if possible.'''
        if self.button == (len(self.buttons) - 1):
            return

        self.set_button(self.button + 1)

    def prev(self):
        '''Go to the last button, if possible.'''
        if self.button == 0:
            return

        self.set_button(self.button - 1)

    def select(self):
        '''Select the current button.'''
        return self.buttons[self.button].select()
