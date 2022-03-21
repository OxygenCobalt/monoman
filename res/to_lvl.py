# This script transforms traditional .tmx files into the custom .lvl format,
# which is both smaller and more efficent than .tmx.
# For more info on .lvl, see the lvl.md document in this directory.

from xml.etree import ElementTree
import os
import glob

# --- TMX DATATYPES ---

# Tiled GID transformation flags. This is meant for internal use by Tiled, but who cares.
GID_TRANS_FLIPX = 1 << 31
GID_TRANS_FLIPY = 1 << 30
GID_TRANS_ROT = 1 << 29
GID_MASK = GID_TRANS_FLIPX | GID_TRANS_FLIPY | GID_TRANS_ROT

# Basic representation of a Tiled tile, with its decoded GID and transformations.
class Tile():
    def __init__(self, raw_gid):
        if raw_gid < GID_TRANS_ROT:
            self.gid = raw_gid
            self.flipx = False
            self.flipy = False
            self.rot = False
        else:
            self.gid = raw_gid & ~GID_MASK
            self.flipx = raw_gid & GID_TRANS_FLIPX == GID_TRANS_FLIPX
            self.flipy = raw_gid & GID_TRANS_FLIPY == GID_TRANS_FLIPY
            self.rot = raw_gid & GID_TRANS_ROT == GID_TRANS_ROT

    def __repr__(self):
        return str(self.gid)

# Parse a tiled layer into Tile instances.
def parse_layer(layer):
    data = layer.find("data").text.replace("\n", "").split(",")
    tiles = []

    for gid in data:
        tiles.append(Tile(int(gid)))

    return tiles

# --- CLV DATATYPES ---

class Player():
    def __init__(self, flipped, wrapping):
        self.flipped = flipped
        self.wrapping = wrapping

    def render(self):
        bits = 0x80

        if self.flipped:
            bits |= 0x8

        if self.wrapping:
            bits |= 0x4

        return bits

class Block():
    def __repr__(self):
        return "block"

    def render(self):
        return 0b10010000

class Unstable():
    def __repr__(self):
        return "unstable"

    def render(self):
        return 0b10100000

class Spike():
    DIR_UP    = 0
    DIR_LEFT  = 1
    DIR_DOWN  = 2
    DIR_RIGHT = 3
    
    def __init__(self, direction):
        self.direction = direction

    def __repr__(self):
        return f"spike direction={self.direction}"

    def render(self):
        return 0b10110000 | (self.direction << 2)

class Spring():
    def __repr__(self):
        return "spring"

    def render(self):
        return 0b11000000

class Exit():
    def __repr__(self):
        return "exit"

    def render(self):
        return 0b11010000

class RgbExit():
    def __repr__(self):
        return "rgbexit"

    def render(self):
        return 0b11100000

class Kill():
    def __repr__(self):
        return "kill"

    def render(self):
        return 0b11110000

# CLV representation of empty space. The size provided
# must not exceed 128 and must not be 0 or lower.
class Empty():
    MAX = 128

    def __init__(self, amount):
        assert amount > 0 and amount <= Empty.MAX
        self.amount = amount

    def __repr__(self):
        return f"empty for {self.amount} blocks"

    def render(self):
        return self.amount - 1

def create_lvl(idx):
    # --- STAGE 1: TRANSLATION ---

    # Parse the tiled document and extract the properties we want from it.
    # PyTMX would have been used for this task, but it auto-decodes the
    # GID and doesn't expose the transformations applied. This is because
    # the dev thinks it would be better to just graft PyTMX onto your
    # existing pygame project, but that's overkill for monoman and also a
    # total joke. Dependency moment.
    document = ElementTree.parse("./tmx/" + str(idx) + ".tmx")
    root = document.getroot()
    props = {}

    for prop in root.find("properties"):
        name = prop.attrib["name"]

        # Look for three properties. Title, Background Color, and whether
        # wrapping is enabled.
        if name == "title":
            props[name] = str(prop.attrib["value"])
        elif name == "bg_color":
            props[name] = int(prop.attrib["value"])
        elif name == "wrapping":
            props[name] = prop.attrib["value"] == "true"
        else:
            raise ValueError(f"unknown property {name}")

    # Now find every layer that we will parse.
    layers = [parse_layer(layer) for layer in root.findall("layer")]

    # Set up each CLV plane. By default, all spaces in these planes will
    # be None, the precursor to the Empty object that is created in stage 2.
    black_plane = [None for i in range(16 * 32)]
    grey_plane  = [None for i in range(16 * 32)]
    white_plane = [None for i in range(16 * 32)]
    obstacle_planes = [black_plane, grey_plane, white_plane]

    player_exists = False

    for layer in layers:
        for cursor, tile in enumerate(layer):
            if tile.gid == 0: # Empty tile, move on
                continue

            # First handle the special player/kill/rgbexit tiles
            if tile.gid == 1:
                # Make sure we only have one player per map
                if player_exists:
                    raise ValueError("Cannot generate multiple players in a level")

                player = Player(tile.flipx, props["wrapping"])

                if props["bg_color"] == 0:
                    black_plane[cursor] = player
                elif props["bg_color"] == 255:
                    white_plane[cursor] = player
                else:
                    raise ValueError(f"Invalid background color, should be 0 or 255")

                player_exists = True

            if tile.gid == 2:
                grey_plane[cursor] = Kill()

            if tile.gid == 3:
                grey_plane[cursor] = RgbExit()

            # Then handle the obstacle tiles, this can be done pretty universally
            # save some special directional tiles. Just normalize the GID so it
            # lines up with the tileset, find the type by seeing which row it's on,
            # and then find it's color, which will always be in order of Black, Grey,
            # and White in the tileset.
            gid = tile.gid - 1
            obstacle_type = gid // 3
            plane = obstacle_planes[gid % 3] 

            if obstacle_type == 1:
                plane[cursor] = Block()

            if obstacle_type == 2:
                plane[cursor] = Unstable()

            if obstacle_type == 3:
                direction = Spike.DIR_UP

                if tile.rot:
                    if tile.flipx:
                        direction = Spike.DIR_RIGHT
                    else:
                        direction = Spike.DIR_LEFT
                else:
                    if tile.flipy:
                        direction = Spike.DIR_DOWN

                plane[cursor] = Spike(direction)

            if obstacle_type == 4:
                plane[cursor] = Spring()

            if obstacle_type == 5:
                plane[cursor] = Exit()

    if not player_exists:
        raise ValueError("A player tile must be present in the level")

    # --- STAGE 2: COMPRESSION AND MERGER ---

    # Now we need to merge and shrink these object planes.
    # Merger is pretty each, just add each plane together in order
    # to a single list.
    # However, compression involves merging all the None tiles into
    # empty tile representations, which is a bit more involved.
    map_data = []
    empty_amount = 0

    for plane in [black_plane, grey_plane, white_plane]:
        for tile in plane:
            if tile is None:
                # Empty tile, increment the counter
                empty_amount += 1

                if empty_amount == Empty.MAX:
                    # The maximum amount of empty space that can be represented has been reached
                    map_data.append(Empty(empty_amount))
                    empty_amount = 0

            else:
                if empty_amount > 0:
                    # Empty space preceded this tile
                    map_data.append(Empty(empty_amount))
                    empty_amount = 0w

                map_data.append(tile)

        if empty_amount > 0:
            # The remainder of this level was empty space
            map_data.append(Empty(empty_amount))
            empty_amount = 0

    # --- STAGE 3: SERIALIZATION ---

    # Now we can turn every single tile into their binary representations.
    # This is the most straightfoward process

    # Add our identifier and title first.
    lvl = bytearray(b"lvl")

    for ch in props["title"]:
        lvl.append(ord(ch))

    lvl.append(0)

    # Then append our tiles. These were already ordered in Stage 2.
    for tile in map_data:
        lvl.append(tile.render())

    # Open up our output .lvl file and write out our data.
    with open("./lvl/" + str(idx) + ".lvl", "wb") as file:
        file.write(lvl)

if __name__ == "__main__":
    # Assume that each .tmx is named N.tmx, where N is the level number.
    levels = glob.glob("tmx/*.tmx")

    for level in levels:
        idx = int(level.split(".")[0][4:])
        print(f"processing level {idx}")
        create_lvl(idx)
