from typing import Optional, Sequence
import xml.etree.ElementTree as xml
import pyglet
import pyglet.gl as gl

from amonite.shaded_sprite import ShadedSprite
from amonite.node import PositionNode
from amonite.scene_node import Bounds
from amonite.settings import GLOBALS, SETTINGS, Keys

# Tile scaling factor, used to avoid texture bleeding.
# If tiles are slightly bigger, then they slightly overlap with each other, effectively never causing texture bleeding.
TILE_SCALING = 1.01

class Tileset:
    __slots__ = (
        "__textures",
        "tile_width",
        "tile_height",
        "margin",
        "spacing",
        "tiles"
    )

    def __init__(
        self,
        sources: list,
        tile_width: int,
        tile_height: int,
        margin: int = 0,
        spacing: int = 0
    ):
        # Load the provided texture.
        self.__textures = [pyglet.resource.image(source) for source in sources]
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.margin = margin
        self.spacing = spacing
        self.tiles = []
        self._fetch_tiles()

    def _fetch_tiles(self):
        """
        Splits the provided texture (in source) by tile width, tile height, margin and spacing
        and saves all tiles as TextureRegions.
        """

        for texture in self.__textures:
            for y in range(self.margin, texture.height - self.spacing, self.tile_height + self.spacing):
                for x in range(self.margin, texture.width - self.spacing, self.tile_width + self.spacing):
                    # Cut the needed region from the given texture and save it.
                    tile: pyglet.image.TextureRegion = texture.get_region(x, texture.height - y - self.tile_height, self.tile_width, self.tile_height)

                    gl.glBindTexture(tile.target, tile.id)

                    gl.glTexParameteri(tile.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
                    gl.glTexParameteri(tile.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

                    # Set texture clamping to avoid mis-rendering subpixel edges.
                    gl.glTexParameteri(tile.target, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(tile.target, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(tile.target, gl.GL_TEXTURE_WRAP_R, gl.GL_CLAMP_TO_EDGE)

                    gl.glBindTexture(tile.target, 0)

                    self.tiles.append(tile)

class TilemapNode(PositionNode):
    def __init__(
        self,
        tileset: Tileset,
        data: Sequence[int],
        map_width: int,
        map_height: int,
        x: float = 0,
        y: float = 0,
        z_offset: int = 0,
        batch: Optional[pyglet.graphics.Batch] = None
    ):
        super().__init__(
            x = x,
            y = y
        )
        self.__tileset = tileset
        self.__map = data
        self.map_width = map_width
        self.map_height = map_height

        self.__sprites = [
            ShadedSprite(
                img = tileset.tiles[tex_index],
                x = int(x + (index % map_width) * tileset.tile_width * float(GLOBALS[Keys.SCALING])),
                y = int(y + (map_height - 1 - (index // map_width)) * tileset.tile_height * float(GLOBALS[Keys.SCALING])),
                z = int(-((y + (map_height - 1 - (index // map_width)) * tileset.tile_height) + z_offset)),
                batch = batch
            ) for (index, tex_index) in enumerate(data) if tex_index >= 0
        ]


        for spr in self.__sprites:
            # Tile sprites are scaled up a bit in order to avoid texture bleeding.
            spr.scale = float(GLOBALS[Keys.SCALING]) * TILE_SCALING

        self.grid_lines = []
        if SETTINGS[Keys.DEBUG] and SETTINGS[Keys.SHOW_TILES_GRID]:
            # Horizontal lines.
            for i in range(map_height + 1):
                self.grid_lines.append(
                    pyglet.shapes.Line(
                        x = 0,
                        y = i * tileset.tile_height * float(GLOBALS[Keys.SCALING]),
                        x2 = map_width * tileset.tile_width * float(GLOBALS[Keys.SCALING]),
                        y2 = i * tileset.tile_height * float(GLOBALS[Keys.SCALING]),
                        thickness = 1.0,
                        color = (0xFF, 0xFF, 0xFF, 0x22),
                        batch = batch
                    )
                )

            # Vertical lines.
            for i in range(map_width + 1):
                self.grid_lines.append(
                    pyglet.shapes.Line(
                        y = 0,
                        x = i * tileset.tile_width * float(GLOBALS[Keys.SCALING]),
                        y2 = map_height * tileset.tile_height * float(GLOBALS[Keys.SCALING]),
                        x2 = i * tileset.tile_width * float(GLOBALS[Keys.SCALING]),
                        thickness = 1.0,
                        color = (0xFF, 0xFF, 0xFF, 0x22),
                        batch = batch
                    )
                )

        # Compute bounds.
        self.bounds = Bounds(
            bottom = int(SETTINGS[Keys.TILEMAP_BUFFER]) * tileset.tile_height,
            right = (map_width - int(SETTINGS[Keys.TILEMAP_BUFFER])) * tileset.tile_width,
            left = int(SETTINGS[Keys.TILEMAP_BUFFER]) * tileset.tile_width,
            top = (map_height - int(SETTINGS[Keys.TILEMAP_BUFFER])) * tileset.tile_height
        )

    def delete(self) -> None:
        for sprite in self.__sprites:
            sprite.delete()

        for line in self.grid_lines:
            line.delete()

        self.__sprites.clear()

    @staticmethod
    def from_tmx_file(
        # Path to the tmx file.
        source: str,
        tilesets_path: str,
        x: float = 0.0,
        y: float = 0.0,
        # Distance (z-axis) between tilemap layers.
        layers_spacing: int | None = None,
        # Starting z-offset for all layers in the file.
        z_offset: int = 0,
        batch: pyglet.graphics.Batch | None = None
    ) -> list:
        """
        Constructs a new TileMap from the given TMX (XML) file.
        Layers naming in the supplied file is critical:
        dig_x -> layer below the playing level (meaning tiles will always be behind actors on the map).
        rat_x -> layer on the playing level (meaning tiles will be sorted z-sorted along with actors on the map).
        pid_x -> layer above the playing level (meaning tiles will always be in front of actors on the map).

        Arguments
        ---------
        source: str
            The path to the tmx file (starting from the defined assets directory).
        tilesets_path: str
            The path to the tileset files (starting from the defined assets directory).
        x: float
        y: float
        layers_spacing: int | None
        z_offset: int
        batch: pyglet.graphics.Batch | None
        """

        root: xml.Element[str] = xml.parse(f"{pyglet.resource.path[0]}/{source}").getroot()

        map_width: int = int(root.attrib["width"])
        map_height: int = int(root.attrib["height"])

        tile_width: int = int(root.attrib["tilewidth"])
        tile_height: int = int(root.attrib["tileheight"])

        tilemap_tilesets: list[xml.Element[str]] = root.findall("tileset")

        # Read layers spacing from settings if not provided.
        spacing = layers_spacing if layers_spacing is not None else int(SETTINGS[Keys.LAYERS_Z_SPACING])

        # Extract a tileset from all the given file.
        tileset = Tileset(
            sources = [f"{tilesets_path if tilesets_path is not None else 'tilesets/rughai/'}{ts.attrib['source'].split('/')[-1].split('.')[0]}.png" for ts in tilemap_tilesets],
            tile_width = tile_width,
            tile_height = tile_height
        )

        tilemap_layers = root.findall("layer")
        layers = []
        for layer in tilemap_layers:
            # Check layer name in order to know whether to z-sort tiles or not.
            layer_name = layer.attrib["name"]

            layer_data = layer.find("data")

            if layer_data is None or layer_data.text is None:
                # The provided file does not contain valid information.
                raise ValueError("TMX layer data not found")

            # Remove all newline characters and split by comma.
            layer_content = layer_data.text.replace("\n", "").split(",")

            layers.append((layer_name, layer_content))

        return [
            TilemapNode(
                tileset = tileset,
                data = [int(i) - 1 for i in layer[1]],
                map_width = map_width,
                map_height = map_height,
                x = x,
                y = y,
                # Only apply layers offset if not a rat layer.
                z_offset = 0 if "rat" in layer[0] else z_offset + spacing * (len(layers) - layer_index),
                batch = batch
            ) for layer_index, layer in enumerate(layers)
        ]

    def get_bounding_box(self):
        return (
            self.x * float(GLOBALS[Keys.SCALING]),
            self.y * float(GLOBALS[Keys.SCALING]),
            self.map_width * self.__tileset.tile_width * float(GLOBALS[Keys.SCALING]),
            self.map_height * self.__tileset.tile_height * float(GLOBALS[Keys.SCALING])
        )

    def get_tile_size(self) -> tuple[int, int]:
        return (self.__tileset.tile_width, self.__tileset.tile_height)