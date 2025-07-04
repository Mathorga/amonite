from amonite.node import PositionNode


class ShapeNode(PositionNode):
    __slots__ = (
        "color"
    )

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        color: tuple[int, int, int, int] = (0x00, 0x00, 0x00, 0x7F)
    ) -> None:
        super().__init__(
            x = x,
            y = y,
            z = z
        )

        self.color = color

    def set_color(self, color: tuple[int, int, int]) -> None:
        self.color = (color[0], color[1], color[2], 0x7F)