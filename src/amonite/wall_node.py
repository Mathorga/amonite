import pyglet

from amonite import controllers
from amonite.collision.collision_node import CollisionType
from amonite.collision.collision_node import CollisionNode
from amonite.collision.collision_shape import CollisionRect
from amonite.node import PositionNode

WALL_COLOR: tuple[int, int, int, int] = (0xFF, 0x7F, 0xFF, 0x7F)

class WallNode(PositionNode):
    def __init__(
        self,
        x: float = 0,
        y: float = 0,
        width: int = 8,
        height: int = 8,
        tags: list[str] | None = None,
        batch: pyglet.graphics.Batch | None = None
    ) -> None:
        super().__init__(x, y)

        self.tags = tags if tags is not None else []
        self.width = width
        self.height = height

        # Collider.
        self.__collider = CollisionNode(
            # x = x,
            # y = y,
            collision_type = CollisionType.STATIC,
            passive_tags = self.tags,
            color = WALL_COLOR,
            shape = CollisionRect(
                # x = x,
                # y = y,
                width = width,
                height = height,
                batch = batch
            )
        )
        self.add_component(self.__collider)
        controllers.COLLISION_CONTROLLER.add_collider(self.__collider)