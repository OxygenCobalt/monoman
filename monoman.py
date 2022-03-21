#!/usr/bin/env python3

import pygame
import sprites
import display
import lvl
import decor
import random

def title(screen):
    sprites.destroy()

    START_Y = 60

    clock = pygame.time.Clock()

    # Set up the UI.
    decor.LargeText("MONOMAN!", START_Y)
    selector = decor.Selector(
        decor.PlayButton("Play", START_Y + 48),
        decor.SoundButton(START_Y + 80),
        decor.ExitButton(START_Y + 112)
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Handle the event in the UI.
                if event.key in [pygame.K_w, pygame.K_UP]:
                    selector.prev()

                if event.key in [pygame.K_s, pygame.K_DOWN]:
                    selector.next()

                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    btn_type = selector.select()
                    
                    if btn_type == decor.PlayButton.TYPE:
                        # Play, so return a "continue" flag.
                        return True
                    elif btn_type == decor.ExitButton.TYPE:
                        # Exit, so return a "stop" flag.
                        return False

        # All UI places itself on the stage.
        sprites.g_stage.update()

        screen.fill(display.BLACK_RGB)
        sprites.g_stage.draw(screen)

        pygame.display.flip()
        clock.tick(display.FPS)

def main(screen):
    sprites.destroy()

    clock = pygame.time.Clock()
    stage_surf = pygame.Surface((display.SWIDTH, display.SHEIGHT), pygame.SRCALPHA)

    fade_alpha = 0
    fade_ticks = 30

    lvl.init()

    for i in range(20):
        decor.Cloud((random.randint(0, display.SWIDTH), random.randint(0, display.SHEIGHT)))

    decor.FlipIndicator()

    # These two text boxes are used as instructions once certain cases are met.
    move_text = decor.FadingText("use wasd to move", (16, 160), 255, 15)
    flip_text = decor.FadingText("use space to flip", (100, 160), 0, 15)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if lvl.player is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        lvl.player.jump()

                    if event.key == pygame.K_SPACE:
                        lvl.player.flip()

        if lvl.player is not None:
            keys = pygame.key.get_pressed()

            if keys[pygame.K_d]:
                lvl.player.move(sprites.Player.RIGHT)
            elif keys[pygame.K_a]:
                lvl.player.move(sprites.Player.LEFT)
            else:
                lvl.player.moving = False

        sprites.g_bg.update()
        sprites.g_stage.update()
        sprites.g_fg.update()

        # The only time the player is gone is if they completed the game
        # By entering the RGBExit. If thats the case, fade out and return
        # The continue flag.
        if lvl.player is None:
            if fade_ticks > 0:
                fade_ticks -= 1
            else:
                fade_alpha += 1

                if fade_alpha == 255:
                    return True
        else:
            # Keep marking time and handling the instruction display.
            lvl.time += display.dt

            if not lvl.has_moved:
                move_text.show()
            else:
                move_text.hide()

                if not lvl.has_flipped and lvl.player.rect.x >= 96:
                    flip_text.show()
                elif lvl.has_flipped:
                    flip_text.hide()

        # First step is to draw the stage sprites, handling any shaking effect.
        stage_surf.fill(display.TRANSPARENT_RGB)
        sprites.g_stage.draw(stage_surf)

        if display.shake > 0:
            display.shake_surface(stage_surf)
            display.shake -= 1

        # Then fill the screen with the background color
        screen.fill(display.bg_rgb())

        # Then draw the foreground, stage, and foreground.
        sprites.g_bg.draw(screen)
        screen.blit(stage_surf, pygame.Rect(0, 0, display.SWIDTH, display.SHEIGHT))
        sprites.g_fg.draw(screen)

        # Apply the alpha to the surface, if we even have any.
        display.fade_surface(screen, fade_alpha)

        pygame.display.flip()
        clock.tick(display.FPS)

    return False

def end(screen):
    sprites.destroy()

    START_Y = 68

    clock = pygame.time.Clock()
    fade_alpha = 255

    # Set up the UI.
    decor.StaticText("You escaped!", START_Y)
    decor.StaticText(f"Time: {lvl.get_time()}", START_Y + 16)
    decor.StaticText(f"Deaths: {lvl.deaths}", START_Y + 32)

    selector = decor.Selector(
        decor.PlayButton("Play again", START_Y + 64),
        decor.ExitButton(START_Y + 96)
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Handle the event in the UI.
                if event.key in [pygame.K_w, pygame.K_UP]:
                    selector.prev()

                if event.key in [pygame.K_s, pygame.K_DOWN]:
                    selector.next()

                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    btn_type = selector.select()
                    
                    if btn_type == decor.PlayButton.TYPE:
                        return True
                    elif btn_type == decor.ExitButton.TYPE:
                        return False

        sprites.g_stage.update()

        # We actually fade into this screen, so we keep track of
        # an alpha value and apply it drawing to the screen.
        if fade_alpha > 0:
            fade_alpha -= 5

        screen.fill(display.BLACK_RGB)
        sprites.g_stage.draw(screen)
        display.fade_surface(screen, fade_alpha)

        pygame.display.flip()
        clock.tick(display.FPS)

if __name__ == "__main__":
    pygame.init()

    screen = display.create()

    if title(screen): # If title tells us to continue, go ahead to main, exit if not.
        while main(screen): # And if main tells us to continue, go ahead to the end screen, exit if not.
            if not end(screen): # If the player replays at the end screen, redo main, exit if not.
                break

    pygame.quit()