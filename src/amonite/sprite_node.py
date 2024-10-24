from typing import Callable
import pyglet
import pyglet.gl as gl

from amonite.shaded_sprite import ShadedSprite
from amonite.node import PositionNode
from amonite.settings import GLOBALS, Keys
from amonite.utils import utils

class SpriteNode(PositionNode):
    def __init__(
        self,
        resource: pyglet.image.Texture | pyglet.image.animation.Animation,
        batch: pyglet.graphics.Batch | None = None,
        on_animation_end: Callable | None = None,
        x: float = 0,
        y: float = 0,
        z: float | None = None,
        shader: pyglet.graphics.shader.ShaderProgram | None = None,
        samplers_2d: dict[str, pyglet.image.ImageData] | None = None,
    ) -> None:
        super().__init__(
            x = x,
            y = y,
            z = z if z is not None else y
        )
        # Make sure the given resource is filtered using a nearest neighbor filter.
        utils.set_filter(resource = resource, filter = gl.GL_NEAREST)

        self.sprite = ShadedSprite(
            img = resource,
            x = x * GLOBALS[Keys.SCALING],
            y = y * GLOBALS[Keys.SCALING],
            z = z if z is not None else -y,
            program = shader,
            samplers_2d = samplers_2d,
            batch = batch
        )
        self.sprite.scale = GLOBALS[Keys.SCALING]
        self.sprite.push_handlers(self)

        self.__on_animation_end = on_animation_end

    def delete(self) -> None:
        self.sprite.delete()

    def get_image(self):
        return self.sprite.image

    def set_position(
        self,
        position: tuple[float, float],
        z: float | None = None
    ) -> None:
        super().set_position(position = position, z = z if z is not None else -position[1])

        self.sprite.position = (
            self.x * GLOBALS[Keys.SCALING],
            self.y * GLOBALS[Keys.SCALING],
            self.z
        )

    def set_scale(
        self,
        x_scale: int | None = None,
        y_scale: int | None = None
    ) -> None:
        if x_scale is not None:
            self.sprite.scale_x = x_scale

        if y_scale is not None:
            self.sprite.scale_y = y_scale

    def set_image(
        self,
        image: pyglet.image.Texture | pyglet.image.animation.Animation
    ) -> None:
        self.sprite.image = image

    def get_frames_num(self) -> int:
        """
        Returns the amount of frames in the current animation.
        Always returns 0 if the sprite image is not an animation.
        """

        return self.sprite.get_frames_num()

    def get_frame_index(self) -> int:
        """
        Returns the current animation frame.
        Always returns 0 if the sprite image is not an animation.
        """
        return self.sprite.get_frame_index()

    def on_animation_end(self):
        if self.__on_animation_end is not None:
            self.__on_animation_end()

    def draw(self) -> None:
        self.sprite.draw()

    def get_bounding_box(self):
        if isinstance(self.sprite.image, pyglet.image.TextureRegion):
            return (
                self.sprite.x - self.sprite.image.anchor_x * GLOBALS[Keys.SCALING],
                self.sprite.y - self.sprite.image.anchor_y * GLOBALS[Keys.SCALING],
                self.sprite.width,
                self.sprite.height
            )
        elif isinstance(self.sprite.image, pyglet.image.animation.Animation):
            return (
                self.sprite.x - self.sprite.image.frames[0].image.anchor_x * GLOBALS[Keys.SCALING],
                self.sprite.y - self.sprite.image.frames[0].image.anchor_y * GLOBALS[Keys.SCALING],
                self.sprite.width,
                self.sprite.height
            )

        return super().get_bounding_box()