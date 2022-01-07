# .lvl

.lvl is a highly compressed level format used by monoman used to avoid much of the bloat
that default .tmx data uses. Not only does this take up less space, but it also allows
for faster level parsing and easier bundling into a single executable.

#### Header

```
lvl $title
```

`lvl` is a three-byte sequence that acts as the identifier for this level.

`$title` is a nul-terminated string that contains the level title. for example, `"To Begin..." $00`

#### Tile Data

Tile data is organized into three "planes".
These planes contain tile bytes in sequential order from (0, 0) to (32, 16).

Each plane corresponds to a specific colored tile:
- Plane 0 contains all black objects for the level
- Plane 1 contains all grey objects for the level
- Plane 2 contains all white objects for the level

To parse a tile plane, one goes through each byte and scrolls to the next
position as is indicated by the byte. Sometimes scroll operations will be
larger than 1.

#### Tile Bytes

Tile Bytes represent either a single tile or an instruction for the cursor.

```
V (TTTFFFF) or (NNNNNNN)
```

`V` is the visibility flag. If it is 1, then the rest of the byte should be treated
as a tile. If the value is zero, then the rest of the byte should be treated as the
amount of empty blocks the parser should skip plus 1 [e.g 0 is one block, 1 is two blocks]

`T` is a 3-bit integer representing the the tile type. All possible tile types are
shown below.

```
0 player
1 block
2 unstable
3 spike
4 pad
5 exit
6 rgbexit
7 kill
```

`F` are tile-specific flags. The meaning of these change depending on the tile type,
and are zeroed if unused.

A tile value of 0 should be treated as empty space for 1 block, or effectively a no-op for that tile.

# Player Tile

0000DW00

There is only one player tile in each map, and it's presence determines
the level state as well.

`D` is the flag for the players direction.
	- `0` represents Right
	- `1` represents Left

`W` is the flag for whether to turn on wrapping.

**Note:** The plane that the player tile is placed in determines the initial background color.

# Block Tile

```
00010000
```

# Unstable Tile

```
00100000
```

# Spike Tile

```
0011DD00
```

`D` is the direction of the spike.
	- `0` is facing up
	- `1` is facing right
	- `2` is facing down
	- `3` is facing left

# Pad Tile

```
01000000
```

# Exit Tile

```
01010000
```

# RgbExit Tile

```
01100000
```

**Note:** RgbExit will always be placed in the grey plane

# Kill Tile

```
01110000
```

**Note:** Kill will always be placed in the grey plane