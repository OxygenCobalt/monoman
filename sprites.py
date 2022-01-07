import pygame
import res
import display
import random
import decor
import lvl
import math

g_bg       = pygame.sprite.LayeredUpdates() # Drawn in the background, no shake
g_stage    = pygame.sprite.LayeredUpdates() # Drawn with the shake effect
g_fg       = pygame.sprite.LayeredUpdates() # Drawn above both layers, no shake

# All entities
g_entity   = pygame.sprite.Group()

# All decoration sprites
g_decor    = pygame.sprite.Group()

# All collidable sprites, requites a method named "flash" that brightens
# the sprite whenever it's in the way of a flip operation.
g_collide  = pygame.sprite.Group()

# All interactable sprites
g_interact = pygame.sprite.Group()

# All sprites that need to be regenerated, requires a method named "regen" that
# regenerates the sprite when called.
g_regen    = pygame.sprite.Group()

def destroy():
    '''Completely wipes the game of any preexisting entities.'''
    for sprite in g_bg:
        sprite.kill()

    for sprite in g_stage:
        sprite.kill()

    for sprite in g_fg:
        sprite.kill()

class Player(pygame.sprite.Sprite):
    '''The main player sprite.'''
    WIDTH  = 16
    HEIGHT = 16

    ACCELERATION = 0.15
    FRICTION     = 0.925

    JUMP_VEL     = -2.75
    SPRING_VEL   = -3.5
    GRAVITY      = 0.1
    TERMINAL_VEL = 10

    FLIP_COOLDOWN = 0.85

    ANIM_IDLE    = res.load_strip((0, 0,          WIDTH, HEIGHT), 4)
    ANIM_WALKING = res.load_strip((0, HEIGHT,     WIDTH, HEIGHT), 4)
    ANIM_JUMPING = res.load_strip((0, HEIGHT * 2, WIDTH, HEIGHT), 4)
    ANIM_FALLING = res.load_strip((0, HEIGHT * 3, WIDTH, HEIGHT), 4)
    TICK_LIMIT   = 10

    LEFT  = True
    RIGHT = False

    def __init__(self, pos, direction):
        super().__init__(g_stage, g_entity, g_regen)

        # --- APPEARANCE ---
        self.anim = Player.ANIM_IDLE
        self.anim_ticks = 0
        self.anim_index = 0

        self.image = self.anim[self.anim_index].get("white")
        self.direction = direction

        g_stage.change_layer(self, display.STAGE_LAYER_PLAYER)

        # --- POSITIONING ---
        self.pos = pygame.math.Vector2(pos[0] * Player.WIDTH, pos[1] * Player.HEIGHT)

        self.vel = pygame.math.Vector2(0, 0)
        self.rect = self.image.get_rect(topleft = self.pos)
        self.on_ground = True
        self.moving = False

        # --- STATE ---
        self.flip_cooldown = 0
        self.init_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
        self.init_direction = direction

    def update(self):
        self.interact()
        self.x_physics()
        self.y_physics()
        self.update_state()
        self.update_appearance()

    def interact(self):
        collided = pygame.sprite.spritecollide(self, g_interact, False)

        for sprite in collided:
            if sprite.color == display.bg_color:
                continue

            if type(sprite) in [Spike, Kill]:
                self.die()

            if type(sprite) is Spring:
                res.play_audio("spring")
                self.rect.bottom = sprite.rect.top + 1
                self.vel.y = Player.SPRING_VEL

            if type(sprite) is Exit:
                lvl.complete()
                return

            if type(sprite) is RgbExit:
                # The RgbExit is meant to be at the end of the game, so when we touch it:
                # 1. Remove the player from all groups
                # 2. Complete the level, which will trigger the shake effect but not a level switch
                # This makes it look like that the player has entered a new world but the
                # camera could not follow, which is a good ending.
                # If this is used outside of the last level, then it will just transport the player
                # without problem.
                self.kill()
                lvl.player = None
                lvl.complete()
                return

    def x_physics(self):
        # Apply any existing velocity
        self.pos.x += self.vel.x
        self.rect.x = self.pos.x

        # Apply friction. Make sure to round to zero if the velocity
        # is too low to be signifigant. 
        self.vel.x *= Player.FRICTION

        if abs(self.vel.x) < 0.01:
            self.vel.x = 0

        # Check for collisions
        collided = pygame.sprite.spritecollide(self, g_collide, False)

        for block in collided:
            if block.color == display.bg_color:
                continue

            # Clamp our colliding side to the side of the wall.
            if self.vel.x > 0:
                self.rect.right = block.rect.left # We hit the left side of a wall
            if self.vel.x < 0:
                self.rect.left  = block.rect.right # We hit the right side of a wall

            # Both collisions should result in the velocity becoming zero.
            self.pos.x = self.rect.x
            self.vel.x = 0

        if self.rect.left > display.SWIDTH: # If player is offscreen
            self.rect.left = 0 # Move player to opposite end of screen
            self.pos.x = self.rect.left 

        elif self.rect.right < 0: # Opposite case
            self.rect.right = display.SWIDTH
            self.pos.x = self.rect.left

    def y_physics(self):
        self.pos.y += self.vel.y
        self.rect.y = self.pos.y

        self.vel.y += Player.GRAVITY

        if self.vel.y >= Player.TERMINAL_VEL:
            self.vel.y = Player.TERMINAL_VEL

        collided = pygame.sprite.spritecollide(self, g_collide, False)

        for block in collided:
            if block.color == display.bg_color:
                continue

            if self.vel.y > 0:
                # We've hit the top of a block after going down.
                # This means we are on the ground, so make sure that state is set.
                self.rect.bottom = block.rect.top
                self.on_ground = True
                self.vel.y = 0

            if self.vel.y < 0:
                # We've hit the bottom of a block after going up.
                # Reset the velocity to prevent clipping and clamp our top.
                self.rect.top = block.rect.bottom
                self.vel.y = 0

            self.pos.y = self.rect.y

            if type(block) is Unstable:
                block.destroy()

        # If we still have a y velocity after we check for collisions, we are not on the ground.
        if abs(self.vel.y) > 0.5:
            self.on_ground = False

        # Die if we've fallen out of the map
        if self.rect.y > display.SHEIGHT:
            self.die()

    def update_state(self):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= display.dt

    def update_appearance(self):
        if not self.on_ground:
            # We're not on the ground, so were jumping or falling
            if self.vel.y < 0:
                self.anim = Player.ANIM_JUMPING
            elif self.vel.y >= 0:
                self.anim = Player.ANIM_FALLING
        elif self.moving:
            # We're moving, so were walking.
            self.anim = Player.ANIM_WALKING
        else:
            # We're idle.
            self.anim = Player.ANIM_IDLE

        # Update the animation counter. This is not reset every time the animation changes
        # for simplicity.
        self.anim_ticks += 1

        if self.anim_ticks >= Player.TICK_LIMIT:
            self.anim_ticks = 0
            self.anim_index = (self.anim_index + 1) % 4

        # Then get the correct frame to use in the correct direction.
        if display.bg_color == display.BLACK:
            frame = self.anim[self.anim_index].get("white")
        elif display.bg_color == display.WHITE:
            frame = self.anim[self.anim_index].get("black")

        if self.direction:
            self.image = pygame.transform.flip(frame, True, False)
        else:
            self.image = frame

    def move(self, direction):
        '''Moves the  player in the specified direction, either Player.LEFT or Player.RIGHT'''
        # We keep a dedicated moving state so that the animation still shows
        # up when the player is running up against a wall.
        self.moving = True
        self.direction = direction

        if self.direction:
            self.vel.x -= Player.ACCELERATION
        else:
            self.vel.x += Player.ACCELERATION

        lvl.has_moved = True

    def jump(self):
        if self.on_ground:
            res.play_audio("jump")
            self.on_ground = False
            self.vel.y = Player.JUMP_VEL
            lvl.has_moved = True

    def flip(self):
        '''Flip the background, if possible. If not, the "denied" sound will play and nothing will occur.'''
        if self.flip_cooldown > 0:
            # Cooldown has not finished
            res.play_audio("denied")
            return

        self.flip_cooldown = Player.FLIP_COOLDOWN

        collided = pygame.sprite.spritecollide(self, g_collide, False)

        for sprite in collided:
            if sprite.color == display.bg_color:
                # We will flip into a solid object, deny this too and indicate
                # the solid objects we can into. The cooldown is still applied 
                # in this case as a punishment for trying to spam the flip action.
                res.play_audio("denied")

                for sprite in g_collide:
                    if sprite.color == display.bg_color:
                        sprite.flash(self.rect.center[0], self.rect.center[1])
                
                return

        res.play_audio("flip")
        display.shake = 15
        display.bg_color = display.bg_inv()
        lvl.has_flipped = True

    def die(self):
        # Generate some particles before regenerating the level.
        for i in range(0, 25):
            decor.DeathParticle(self.rect.center)

        res.play_audio("die")
        lvl.regen()

    def regen(self):
        self.pos.x = self.init_pos.x
        self.pos.y = self.init_pos.y
        self.vel.x = 0
        self.vel.y = 0
        self.direction = self.init_direction
        self.flip_cooldown = 0

class ObstacleSprite(pygame.sprite.Sprite):
    '''The superclass for any non-moving sprite, collideable or interactable.'''
    WIDTH_MAX = 16
    HEIGHT_MAX = 16

    INVIS_SURFACE = pygame.Surface((WIDTH_MAX, HEIGHT_MAX), pygame.SRCALPHA)

    def __init__(self, pos, color, width, height, *groups):
        super().__init__(g_stage, g_entity, groups)

        # Transform the 32x16 coordinates into pixel coordinates.
        self.rect = pygame.Rect(
            ObstacleSprite.WIDTH_MAX * pos[0], ObstacleSprite.HEIGHT_MAX * pos[1], width, height
        )

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.color = color

        self.x, self.y = pos
        self.flash_intensity = 0

    def flash(self, x, y):
        # Find the distance from this object and the other object.
        distance = ((self.rect.center[0] - x) ** 2 + (self.rect.center[1] - y) ** 2) ** 0.5

        if distance > 96:
            # Too far away to flash.
            return

        self.flash_intensity = ((96 - distance) / 96) * 128

class AnimatedSprite(ObstacleSprite):
    '''A sprite with animation.'''
    TICK_LIMIT = 10

    def __init__(self, pos, color, width, height, *groups):
        super().__init__(pos, color, width, height, groups)

        self.anim_index = 0
        self.anim_ticks = 0

    def update(self):
        self.anim_ticks += 1

        if self.anim_ticks == AnimatedSprite.TICK_LIMIT:
            self.anim_ticks = 0
            self.anim_index = (self.anim_index + 1) % 4

    def apply_anim(self, anim):
        if self.color != display.bg_color:
            if self.color == display.BLACK:
                self.image = anim[self.anim_index].get("black")
            elif self.color == display.WHITE:
                self.image = anim[self.anim_index].get("white")
            else:
                self.image = anim[self.anim_index].get("grey")
        else:
            self.image = ObstacleSprite.INVIS_SURFACE

class Block(ObstacleSprite):
    '''A static, collideable block.'''
    WIDTH = 16
    HEIGHT = 16

    def __init__(self, pos, color):
        super().__init__(pos, color, Block.WIDTH, Block.HEIGHT, g_collide)

    def update(self):
        self.image.fill([self.color, self.color, self.color, (self.color != display.bg_color) * 255])

        # Handle flash component from ObstacleSprite.
        if self.color != display.bg_color:
            self.flash_intensity = 0

        if self.flash_intensity > 0:
            bg = display.bg_inv()
            self.image.fill([bg, bg, bg, self.flash_intensity])
            self.flash_intensity = max(self.flash_intensity - 5, 0)

class Unstable(ObstacleSprite):
    '''A static, collideable block that disappears when collided with.'''
    WIDTH = 16
    HEIGHT = 8

    GRACE_TICKS = 0.1
    DEAD_TICKS  = 3

    def __init__(self, pos, color):
        super().__init__(pos, color, Unstable.WIDTH, Unstable.HEIGHT, g_collide, g_regen)

        # --- STATE ---
        self.broken = False
        self.grace_ticks = 0
        self.dead_ticks = 0

        # --- APPEARANCE ---
        self.color = color

    def update(self):
        if self.broken:
            if self.grace_ticks > 0:
                # Give some grace time before the tile breaks.
                self.grace_ticks -= display.dt

                if self.grace_ticks <= 0:
                    res.play_audio("break")

                    # When the sprite breaks, just make it uncollideable and invisible
                    # and generate some particles to denote it.
                    g_collide.remove(self)
                    self.image.set_alpha(0)
                    self.dead_ticks = Unstable.DEAD_TICKS

                    for i in range(0, 10):
                        decor.CrumbleParticle(self.rect.center, self.color)

            if self.dead_ticks > 0:
                # Give some time until we respawn
                self.dead_ticks -= display.dt

            # "broken" period ended, time to fade back in.
            if self.dead_ticks <= 0 and self.image.get_alpha() < 255:
                self.image.set_alpha(self.image.get_alpha() + 15)

                if self.image.get_alpha() == 255:
                    # Only become collideable when we are fully opaque.
                    g_collide.add(self)
                    self.broken = False

        # Since we already tinker with the overall alpha component in the above blocks, here
        # just fill in the alpha component with whether this sprite should be visible
        self.image.fill(
            [self.color, self.color, self.color, (self.color != display.bg_color) * 255]
        )

        # Handle flash component from ObstacleSprite.
        if self.color != display.bg_color:
            self.flash_intensity = 0

        if self.flash_intensity > 0:
            bg = display.bg_inv()
            self.image.fill([bg, bg, bg, self.flash_intensity])
            self.flash_intensity = max(self.flash_intensity - 5, 0)
            
    def destroy(self):
        '''"Breaks" this block.'''
        if not self.broken:
            self.broken = True
            self.grace_ticks = Unstable.GRACE_TICKS

    def regen(self):
        self.image.set_alpha(255)
        self.broken = False
        self.grace_ticks = 0
        self.dead_ticks = 0

        if self not in g_collide:
            g_collide.add(self)

class Spike(AnimatedSprite):
    '''A bed of spikes that kills the player.'''
    WIDTH_V = 16
    HEIGHT_V = 8

    WIDTH_H = 8
    HEIGHT_H = 16

    # Make our anim a static member so we can re-use its surfaces
    # We don't transform them like we do with the player, since that would be
    # a severe performance drain with the amount of spikes in a level.
    ANIM_UP    = res.load_strip((0,  64, WIDTH_V, HEIGHT_V), 4)
    ANIM_DOWN  = res.load_strip((0,  72, WIDTH_V, HEIGHT_V), 4)
    ANIM_LEFT  = res.load_strip((64, 72, WIDTH_H, HEIGHT_H), 4)
    ANIM_RIGHT = res.load_strip((96, 72, WIDTH_H, HEIGHT_H), 4)

    DIR_UP    = 0
    DIR_LEFT  = 1
    DIR_DOWN  = 2
    DIR_RIGHT = 3
    
    def __init__(self, pos, color, direction):
        if direction == Spike.DIR_UP:
            super().__init__(pos, color, Spike.WIDTH_V, Spike.HEIGHT_V, g_interact)
            self.anim = Spike.ANIM_UP
            self.rect.y += self.rect.height
        elif direction == Spike.DIR_DOWN:
            super().__init__(pos, color, Spike.WIDTH_V, Spike.HEIGHT_V, g_interact)
            self.anim = Spike.ANIM_DOWN
        elif direction == Spike.DIR_LEFT:
            super().__init__(pos, color, Spike.WIDTH_H, Spike.HEIGHT_H, g_interact)
            self.anim = Spike.ANIM_LEFT
            self.rect.x += self.rect.width
        elif direction == Spike.DIR_RIGHT:
            self.anim = Spike.ANIM_RIGHT
            super().__init__(pos, color, Spike.WIDTH_H, Spike.HEIGHT_H, g_interact)
        else:
            raise Exception("invalid direction was provided")

    def update(self):
        super().update()
        super().apply_anim(self.anim)

class Spring(AnimatedSprite):
    '''A spring that allows the player to jump higher.'''
    WIDTH = 16
    HEIGHT = 8

    # Make our anim a static member so we can re-use it's surfaces
    ANIM = res.load_strip((0, 80, WIDTH, HEIGHT), 4) 

    def __init__(self, pos, color):
        super().__init__(pos, color, Spring.WIDTH, Spring.HEIGHT, g_interact)
        self.rect.y += self.rect.height

    def update(self):
        super().update()
        super().apply_anim(Spring.ANIM)

class Exit(AnimatedSprite):
    '''The level exit.'''
    WIDTH = 16
    HEIGHT = 16

    INSET_ANIM = [4, 5, 7, 5]

    def __init__(self, pos, color):
        super().__init__(pos, color, Exit.WIDTH, Exit.HEIGHT, g_interact)

    def update(self):
        super().update()

        # Be a bit clever and make a rect animation instead of a normal sprite
        # animation. This allows us to optimize space on the spritesheet.
        inset = Exit.INSET_ANIM[self.anim_index]

        self.image.fill(display.TRANSPARENT_RGB)
        pygame.draw.rect(
            self.image, 
            [self.color, self.color, self.color, (self.color != display.bg_color) * 255],
            pygame.Rect(inset, inset, Exit.WIDTH - inset * 2, Exit.HEIGHT - inset * 2),
            1
        )

class RgbExit(AnimatedSprite):
    '''Like Exit, but colorful and it also ends the game.'''
    WIDTH = 16
    HEIGHT = 16

    COLORS = [(255, 0, 0), (255, 128, 0), (255, 192, 0), (16, 200, 32), (0, 32, 255), (0, 128, 255), (128, 0, 255)]

    def __init__(self, pos):
        super().__init__(pos, display.GREY, RgbExit.WIDTH, RgbExit.HEIGHT, g_interact)
        self.color_index = 0

    def update(self):
        # We have to deal with animation logic ourselves, as this animation contains a far more complicated
        # sequence of frames and effects.
        if self.anim_ticks == 0:
            # Generate some particles every time we change a frame.
            decor.RgbParticle(self.rect.center)
            decor.RgbParticle(self.rect.center)

        self.anim_ticks += 1

        if self.anim_ticks == AnimatedSprite.TICK_LIMIT:
            self.anim_ticks = 0
            self.anim_index = (self.anim_index + 1) % 4

            if self.anim_index == 3:
                # Every time the exit animation "inverts", change the color.
                self.color_index = (self.color_index + 1) % 6
        
        # Then do the typical exit animation.
        inset = Exit.INSET_ANIM[self.anim_index]

        self.image.fill(display.TRANSPARENT_RGB)
        pygame.draw.rect(
            self.image, 
            RgbExit.COLORS[self.color_index],
            pygame.Rect(inset, inset, Exit.WIDTH - inset * 2, Exit.HEIGHT - inset * 2),
            1
        )

class Kill(ObstacleSprite):
    '''Unused sprite meant to kill the player if they do into out-of-bounds areas.'''
    WIDTH = 16
    HEIGHT = 16

    def __init__(self, pos):
        super().__init__(pos, display.GREY, Kill.WIDTH, Exit.HEIGHT, g_interact)