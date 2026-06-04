from enum import Enum, auto


class ObjectType(Enum):
    WIRE = auto()  # Прямой провод
    POINT_WIRE = auto()  # Провод-точка
    RING = auto()  # Кольцо
    ARBITRARY_FIGURE = auto()  # Произвольная фигура

    def __str__(self):
        return {
            ObjectType.WIRE: "Прямой провод",
            ObjectType.POINT_WIRE: "Провод-точка",
            ObjectType.RING: "Кольцо",
            ObjectType.ARBITRARY_FIGURE: "Произвольная фигура",
        }[self]


class CircleDirection(Enum):
    CLOCKWISE = auto()
    COUNTERCLOCKWISE = auto()

    def __str__(self):
        return {
            CircleDirection.CLOCKWISE: "По часовой",
            CircleDirection.COUNTERCLOCKWISE: "Против часовой",
        }[self]


class PointDirection(Enum):
    TO_US = auto()
    FROM_US = auto()

    def __str__(self):
        return {
            PointDirection.TO_US: "К нам (•)",
            PointDirection.FROM_US: "От нас (×)",
        }[self]


class LayerType(Enum):
    # Layers are painted in order specified here
    HEATMAP = auto()
    GRID = auto()
    AXES = auto()
    DIRECTIONS = auto()
    OBJECTS = auto()
    HIGHLIGHT = auto()
    HEATMAP_LEGEND = auto()
    MOUSE_POSITION_BAR = auto()

    def default_visibility(self) -> bool:
        return {
            LayerType.HEATMAP: True,
            LayerType.GRID: False,
            LayerType.AXES: True,
            LayerType.DIRECTIONS: True,
            LayerType.OBJECTS: True,
            LayerType.HIGHLIGHT: True,
            LayerType.HEATMAP_LEGEND: True,
            LayerType.MOUSE_POSITION_BAR: True,
        }[self]
