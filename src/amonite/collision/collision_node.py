from enum import Enum
from typing import Callable

from amonite.collision.collision_shape import CollisionShape
from amonite.node import PositionNode
from amonite.utils.utils import CollisionHit

COLLIDER_COLOR: tuple[int, int, int, int] = (0x7F, 0xFF, 0xFF, 0x7F)
SENSOR_COLOR: tuple[int, int, int, int] = (0x7F, 0xFF, 0x7F, 0x7F)

class CollisionType(Enum):
    STATIC = 0
    DYNAMIC = 1

class CollisionMethod(Enum):
    """
    Collision method enumerator:

    Active collisions are the ones driven by velocity, they usually command the parent movement.

    Passive collisions are not driven by velocity, they are usually commanded by parent movement.
    """

    ACTIVE = 0
    PASSIVE = 1

class CollisionNode(PositionNode):
    def __init__(
        self,
        shape: CollisionShape,
        x: float = 0,
        y: float = 0,
        active_tags: list[str] = [],
        passive_tags: list[str] = [],
        collision_type: CollisionType = CollisionType.STATIC,
        collision_method: CollisionMethod = CollisionMethod.ACTIVE,
        sensor: bool = False,
        color: tuple[int, int, int, int] | None = None,
        on_triggered: Callable[[list[str], int, bool], None] | None = None
    ) -> None:
        super().__init__(x, y)

        # Velocity components.
        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0

        self.active_tags: list[str] = active_tags
        self.passive_tags: list[str] = passive_tags
        self.type: CollisionType = collision_type
        self.method: CollisionMethod = collision_method
        self.sensor: bool = sensor
        self.shape: CollisionShape = shape
        self.on_triggered: Callable[[list[str], int, bool], None] | None = on_triggered

        self.collisions: set[CollisionNode] = set[CollisionNode]()
        self.in_collisions: set[CollisionNode] = set[CollisionNode]()
        self.out_collisions: set[CollisionNode] = set[CollisionNode]()

        # Set shape color.
        if color is not None:
            self.shape.set_color(color = color)
        else:
            self.shape.set_color(color = SENSOR_COLOR if sensor else COLLIDER_COLOR)

    def delete(self) -> None:
        if self.shape is not None:
            self.shape.delete()

    def set_position(
        self,
        position: tuple[float, float],
        z: float | None = None
    ) -> None:
        super().set_position(position)

        if self.shape is not None:
            self.shape.set_position(position = position)

    def get_velocity(self) -> tuple[float, float]:
        return (self.velocity_x, self.velocity_y)

    def put_velocity(
        self,
        velocity: tuple[float, float]
    ) -> None:
        """
        Sums the provided velocity to any already there.
        """
        self.velocity_x += velocity[0]
        self.velocity_y += velocity[1]

        if self.shape is not None:
            self.shape.put_velocity(velocity = velocity)

    def set_velocity(
        self,
        velocity: tuple[float, float]
    ) -> None:
        self.velocity_x = velocity[0]
        self.velocity_y = velocity[1]

        if self.shape is not None:
            self.shape.set_velocity(velocity = velocity)

    def collide(self, other) -> CollisionHit | None:
        assert isinstance(other, CollisionNode)

        # Reset collision time.
        collision_hit = None

        # Make sure there's at least one matching tag.
        if bool(set(self.active_tags) & set(other.passive_tags)):

            # Check collision from shape.
            if self.shape is not None:
                collision_hit = self.shape.swept_collide(other.shape)

            if other not in self.collisions and collision_hit is not None:
                # Store the colliding sensor.
                self.collisions.add(other)
                self.in_collisions.add(other)
            elif other in self.collisions and collision_hit is None:
                # Remove if not colliding anymore.
                self.collisions.remove(other)
                self.out_collisions.add(other)

        return collision_hit