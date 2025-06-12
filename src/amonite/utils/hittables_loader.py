import os
import json
from typing import Any
import pyglet

from amonite import controllers
from amonite.node import PositionNode
from amonite.collision.collision_node import CollisionNode
from amonite.collision.collision_node import CollisionType
from amonite.collision.collision_node import CollisionNode
from amonite.collision.collision_shape import CollisionRect

class HittableNode(PositionNode):
    """
    Generic hittable node.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        width: int = 8,
        height: int = 8,
        sensor: bool = False,
        color: tuple[int, int, int, int] = (0xFF, 0x7F, 0x7F, 0x7F),
        tags: list[str] | None = None,
        batch: pyglet.graphics.Batch | None = None
    ) -> None:
        super().__init__(
            x = x,
            y = y,
            z = z
        )

        self.tags: list[str] = tags if tags is not None else []
        self.width: int = width
        self.height: int = height
        self.sensor: bool = sensor

        # Collider.
        self.__collider: CollisionNode = CollisionNode(
            collision_type = CollisionType.STATIC,
            passive_tags = self.tags,
            sensor = sensor,
            color = color,
            shape = CollisionRect(
                width = width,
                height = height,
                batch = batch
            )
        )
        self.add_component(self.__collider)
        controllers.COLLISION_CONTROLLER.add_collider(self.__collider)

class HittablesLoader:
    @staticmethod
    def fetch(
        source: str,
        batch: pyglet.graphics.Batch | None = None
    ) -> list[HittableNode]:
        """
        Reads and returns the list of walls from the file provided in [source].
        """

        walls_list: list[HittableNode] = []

        abs_path: str = os.path.join(pyglet.resource.path[0], source)

        # Return an empty list if the source file is not found.
        if not os.path.exists(abs_path):
            return []

        print(f"Loading hittables {abs_path}")

        data: dict[str, Any]

        # Load the json file.
        with open(file = abs_path, mode = "r", encoding = "UTF8") as source_file:
            data = json.load(source_file)

        # Just return if no data is read.
        if len(data) <= 0:
            return []

        # Loop through defined wall types.
        for element in data["elements"]:
            positions: list[str] = element["positions"]
            sizes: list[str] = element["sizes"]

            assert len(positions) == len(sizes)

            # Loop through single walls.
            for i in range(len(positions)):
                position_string: str = positions[i]
                size_string: str = sizes[i]

                position: list[int] = list(map(lambda item: int(item), position_string.split(",")))
                size: list[int] = list(map(lambda item: int(item), size_string.split(",")))

                assert len(position) == 2 and len(size) == 2

                # Create a new wall node and add it to the result.
                walls_list.append(HittableNode(
                    x = position[0],
                    y = position[1],
                    width = int(size[0]),
                    height = size[1],
                    sensor = element["sensor"] if "sensor" in element.keys() else False,
                    tags = element["tags"],
                    batch = batch
                ))

        return walls_list

    @staticmethod
    def store(
        dest: str,
        hittables: list[HittableNode]
    ) -> None:
        """
        Saves a hittablemap file to store all provided hittables.
        Hittables are internally sorted by tags.
        """

        # Group hittables by tags and sensority.
        hittables_data: dict[tuple[str, bool], list[HittableNode]] = {}
        for hittable in hittables:
            key: tuple[str, bool] = (",".join(hittable.tags), hittable.sensor)
            if not key in hittables_data:
                hittables_data[key] = [hittable]
            else:
                hittables_data[key].append(hittable)

        # Prepare hittables data for storage.
        result: list[dict[str, Any]] = []
        for key, value in hittables_data.items():
            element: dict[str, Any] = {
                "tags": key[0].split(","),
                "sensor": key[1],
                "positions": list(map(lambda w: f"{int(w.x)},{int(w.y)}", value)),
                "sizes": list(map(lambda w: f"{int(w.width)},{int(w.height)}", value)),
            }
            result.append(element)

        # Write to dest file.
        with open(file = dest, mode = "w", encoding = "UTF8") as dest_file:
            dest_file.write(
                json.dumps(
                    {
                        "elements": result
                    },
                    indent = 4
                )
            )