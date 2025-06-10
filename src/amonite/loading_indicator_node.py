import os
from typing import Callable
import pyglet

from amonite.node import PositionNode
from amonite.sprite_node import SpriteNode
from amonite.utils.tween import Tween
from amonite.utils.types import OptionalSpriteRes, SpriteRes
from amonite.utils.utils import set_offset

fragment_source: str = """
#version 150 core
in vec4 vertex_colors;
in vec3 texture_coords;

out vec4 final_color;

uniform sampler2D sprite_texture;

// The current fill value (between 0 and 1).
uniform float fill;
uniform vec3 sw_coord;
uniform vec3 ne_coord;


/// Scale the given fill from the scale of src to the scale of dst.
float scale(float val, float src_start, float src_end, float dst_start, float dst_end) {
    return ((val - src_start) / (src_end - src_start)) * (dst_end - dst_start) + dst_start;
}

void main() {
    // Fetch the current texture size.
    ivec2 texture_size = textureSize(sprite_texture, 0);

    // Fetch the current color.
    final_color = texture(sprite_texture, texture_coords.xy) * vertex_colors;

    // Coordinates greater than fill on the x axis should not be rendered.
    if (texture_coords.x > (ne_coord.x - sw_coord.x) * fill + sw_coord.x) {
        final_color.a = 0.0;
    }
}
"""

class LoadingIndicatorNode(PositionNode):
    def __init__(
        self,
        foreground_sprite_res: SpriteRes,
        background_sprite_res: OptionalSpriteRes = None,
        frame_sprite_res: OptionalSpriteRes = None,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        offset_x: int = 0,
        offset_y: int = 0,
        starting_fill: float = 1.0,
        start_visible: bool = False,
        ease_function: Callable[[float], float] = Tween.linear,
        batch: pyglet.graphics.Batch | None = None
    ) -> None:
        super().__init__(x, y, z)

        self.__ease_function: Callable[[float], float] = ease_function
        self.__fill: float= starting_fill
        self.__batch: pyglet.graphics.Batch | None = batch
        self.__foreground_sprite_res: OptionalSpriteRes = foreground_sprite_res
        self.__background_sprite_res: OptionalSpriteRes = background_sprite_res
        self.__frame_sprite_res: OptionalSpriteRes = frame_sprite_res
        self.foreground_sprite: SpriteNode | None = None
        self.background_sprite: SpriteNode | None = None
        self.frame_sprite: SpriteNode | None = None

        # Center all sprites.
        set_offset(
            resource = self.__foreground_sprite_res,
            x = offset_x,
            y = offset_y,
            center = True
        )
        if self.__background_sprite_res is not None:
            set_offset(
                resource = self.__background_sprite_res,
                x = offset_x,
                y = offset_y,
                center = True
            )
        if self.__frame_sprite_res is not None:
            set_offset(
                resource = self.__frame_sprite_res,
                x = offset_x,
                y = offset_y,
                center = True
            )

        # Create shader program from vector and fragment.
        vert_shader = pyglet.graphics.shader.Shader(pyglet.sprite.vertex_source, "vertex")
        frag_shader = pyglet.graphics.shader.Shader(fragment_source, "fragment")
        self.shader_program = pyglet.graphics.shader.ShaderProgram(vert_shader, frag_shader)

        # Pass non sampler uniforms to the shader.
        self.shader_program["fill"] = self.__fill

        if start_visible:
            self.__init_sprites()

    def __init_sprites(self) -> None:
        if self.foreground_sprite is None and self.__foreground_sprite_res is not None:
            self.foreground_sprite = SpriteNode(
                resource = self.__foreground_sprite_res,
                x = self.x,
                y = self.y,
                z = self.y,
                shader = self.shader_program,
                batch = self.__batch
            )

        if self.background_sprite is None and self.__background_sprite_res is not None:
            self.background_sprite = SpriteNode(
                resource = self.__background_sprite_res,
                x = self.x,
                y = self.y,
                z = self.y - 1,
                batch = self.__batch
            ) if self.__background_sprite_res is not None else None

        if self.frame_sprite is None and self.__background_sprite_res is not None:
            self.frame_sprite = SpriteNode(
                resource = self.__frame_sprite_res,
                x = self.x,
                y = self.y,
                z = self.y + 1,
                batch = self.__batch
            ) if self.__frame_sprite_res is not None else None

    def set_position(
        self,
        position: tuple[float, float],
        z: float | None = None
    ) -> None:
        super().set_position(position, z)

        if self.foreground_sprite is not None:
            self.foreground_sprite.set_position(position = position, z = z if z is not None else position[1])

        if self.background_sprite is not None:
            self.background_sprite.set_position(position = position, z = (z if z is not None else position[1]) - 1)

        if self.frame_sprite is not None:
            self.frame_sprite.set_position(position = position, z = (z if z is not None else position[1]) + 1)

    def set_fill(self, fill: float) -> None:
        """
        Sets the current fill value to the provided one.
        """

        # Make sure the provided value lies in the valid range.
        assert fill >= 0.0 and fill <= 1.0, "Value out of range"

        self.__fill = fill

        if self.foreground_sprite is not None:
            # Fetch texture coordinates from sprite.
            sprite_texture: pyglet.image.Texture = self.foreground_sprite.sprite.get_texture()
            texture_coords: tuple[
                # South west.
                float, float, float,
                # North west.
                float, float, float,
                # North east.
                float, float, float,
                # South east.
                float, float, float
            ] = sprite_texture.tex_coords

            # Also pass bottom-left and top-right texture coords.
            self.shader_program["sw_coord"] = texture_coords[0:3]
            self.shader_program["ne_coord"] = texture_coords[6:9]
            self.shader_program["fill"] = Tween.compute(fill, self.__ease_function)

    def show(self) -> None:
        self.__init_sprites()

    def hide(self) -> None:
        self.clear_sprites()

    def clear_sprites(self) -> None:
        if self.foreground_sprite is not None:
            self.foreground_sprite.delete()
            self.foreground_sprite = None

        if self.background_sprite is not None:
            self.background_sprite.delete()
            self.background_sprite = None

        if self.frame_sprite is not None:
            self.frame_sprite.delete()
            self.frame_sprite = None

    def delete(self) -> None:
        self.clear_sprites()