import os
import display
import sprites
import decor
import res
import glob

# The starting level. In this case it's zero.
START = 0

# The maximum level. This is just how many .lvl files are in the directory.
# Monoman assumes every level is named in a sequential order.
MAX = len(glob.glob(res.path(os.path.join("res", "lvl", "*.lvl"))))

level = 0 # Current level
player = None # Current player if there is one
init_bg = display.BLACK # Initial background outlined by the level.

time = 0 # Total time the game has taken so far
deaths = 0 # Total amount of deaths

# State to handle the instruction text
has_moved = False 
has_flipped = False

def init():
    '''Re-initialize the level system, starting from the START constant.'''
    global time
    global deaths

    time = 0
    deaths = 0
    gen(START)

def complete():
    '''Complete a level, moving on to the next one.'''
    global level

    res.play_audio("exit")

    nxt = level + 1

    # Don't generate any further if we've exceeded the actual level count
    if (nxt < MAX):
        display.shake = 25
        destroy()
        gen(nxt)
    else:
        display.shake = 40

def destroy():
    '''Destroy the last level.'''
    for sprite in sprites.g_entity:
        sprite.kill()

    for sprite in sprites.g_decor:
        sprite.kill()   

def regen():
    '''Regenerate the level.'''
    global deaths

    display.shake = 10
    display.bg_color = init_bg
    deaths += 1

    for sprite in sprites.g_regen:
        sprite.regen()

def gen(idx):
    '''Generates the level at idx.'''
    global level
    global init_bg
    global player

    # Assume that the level name will be (idx).lvl
    path = res.clv_path(idx)

    with open(path, "rb") as clv:
        # Ensure the identifier is present.
        if clv.read(3) != b"lvl":
            raise ValueError(f"{path} is not a .lvl file")

        title = ""
        bg_color = display.BLACK
        wrapping = False

        # Read the title first. This is the only header information.
        while True:
            byte = clv.read(1)

            if byte == b'\0':
                break

            title += chr(ord(byte))

        # Generate a title sprite right now based on what we got.
        decor.TitleText(title)

        # Simple reference for which colors correspond to which plane in the format.
        plane_colors = [display.BLACK, display.GREY, display.WHITE]

        for plane in range(3):
            x = 0
            y = 0

            for byte in iter(lambda: clv.read(1), b''):
                tile = int.from_bytes(byte, "big")

                # If this tile isn't empty space...
                if tile & 0x80 != 0:
                    # Figure out the type of sprite we are reading here.
                    # Once we do that, then we parse any other information and add that
                    # to the sprite instantiation procedure.
                    typ = (tile >> 4) & 0b111

                    if typ == 0:
                        bg_color = plane_colors[plane]
                        wrapping = ((tile >> 2) & 1) != 0 
                        direction = ((tile >> 3) & 1) != 0

                        player = sprites.Player((x, y), direction)

                    if typ == 1:
                        sprites.Block((x, y), plane_colors[plane])

                    if typ == 2:
                        sprites.Unstable((x, y), plane_colors[plane])

                    if typ == 3:
                        direction = (tile >> 2) & 0b11
                        sprites.Spike((x, y), plane_colors[plane], direction)

                    if typ == 4:
                        sprites.Spring((x, y), plane_colors[plane])

                    if typ == 5:
                        sprites.Exit((x, y), plane_colors[plane])

                    if typ == 7:
                        sprites.Kill((x, y))

                    if typ == 6:
                        sprites.RgbExit((x, y))

                    x += 1

                    if x > 31:
                        x = 0
                        y += 1

                        if y > 15:
                            break
                else:
                    # This title is not empty space, figure out the amount to scroll and then
                    # update the cursor to reflect that.
                    scroll = tile + 1
                    x += scroll

                    while x > 31:
                        x -= 32
                        y += 1

                    if y > 15:
                        break

    if wrapping:
        # Add wrapping decorations if needed
        decor.Wrapping(decor.Wrapping.POS_START)
        decor.Wrapping(decor.Wrapping.POS_END)
    else:
        # Otherwise generate two walls of blocks around the edges of the screen.
        [sprites.Block((-1, y), display.GREY) for y in range(15)]
        [sprites.Block((32, y), display.GREY) for y in range(15)]

    # Make sure the state reflects what we have just generated.
    level = idx
    init_bg = bg_color
    display.bg_color = bg_color

def get_time():
    '''Formats the total time spent on this game, as a string.'''
    # Theres probably a standard library method I could have used, but I didn't
    # really care.
    fmt_time = ""

    seconds = round(time)
    minutes = seconds // 60
    hours = minutes // 60

    seconds %= 60
    minutes %= 60

    if hours > 0:
        if hours > 9:
            fmt_time += f"{hours}:"
        else:
            fmt_time += f"0{hours}:"

    if minutes > 9:
        fmt_time += f"{minutes}:"
    else:
        fmt_time += f"0{minutes}:"

    if seconds > 9:
        fmt_time += str(seconds)
    else:
        fmt_time += f"0{seconds}"

    return fmt_time
