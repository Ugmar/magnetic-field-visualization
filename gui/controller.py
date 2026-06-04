from typing import Any, Optional, List, Tuple

# Импортируем классы объектов
from core.objects import MagneticObject, PointWire, Ring, StraightWire, ArbitraryFigure
from gui.widgets.types import LayerType

from .widgets.canvas import Canvas
from .widgets.objectPanel import ObjectCardsPanel
from .widgets.types import CircleDirection, ObjectType, PointDirection

from PyQt6.QtWidgets import QMessageBox


class Controller:
    def __init__(self, canvas: Canvas, objectsPanel: ObjectCardsPanel) -> None:
        self.canvas = canvas
        self.objectsPanel = objectsPanel
        self.objectsPanel.controller = self  # type: ignore

        # List is syncronised between canvas, controller and other stuff that "store"
        # the link to the list so they actually use shared list.
        self.objects = self.canvas.objects

    def set_layer_visibility(self, checked: bool, layer_type: LayerType) -> None:
        self.canvas.layers_visibility[layer_type] = checked
        self.canvas.mark_layer_dirty(layer_type)
        self.canvas.update()

    # ------------------------------------------------------------------
    # Фабрика по созданию MagneticObject
    # ------------------------------------------------------------------
    def create_magnetic_object(
        self, obj_type: ObjectType, params: dict[str, Any]
    ) -> Optional[MagneticObject]:
        """Создаёт объект нужного класса по типу."""
        try:
            color = params.get("color", "#FFFFFF")
            current = float(params.get("current", 0))

            if obj_type == ObjectType.WIRE:
                return StraightWire(
                    name=obj_type,
                    current=current,
                    x1=float(params.get("x1", 0)),
                    y1=float(params.get("y1", 0)),
                    x2=float(params.get("x2", 0)),
                    y2=float(params.get("y2", 1)),
                    color=color,
                )

            elif obj_type == ObjectType.RING:
                return Ring(
                    name=obj_type,
                    current=current,
                    x=float(params.get("x", 0)),
                    y=float(params.get("y", 0)),
                    r=float(params.get("r", 1)),
                    direction=params.get("direction", CircleDirection.CLOCKWISE),
                    color=color,
                )

            elif obj_type == ObjectType.POINT_WIRE:
                return PointWire(
                    name=obj_type,
                    current=current,
                    x=float(params.get("x", 0)),
                    y=float(params.get("y", 0)),
                    direction=params.get("direction", PointDirection.TO_US),
                    color=color,
                )

            elif obj_type == ObjectType.ARBITRARY_FIGURE:
                points = params.get("points", [])

                # Валидация точек
                if not isinstance(points, list) or len(points) < 3:
                    raise ValueError(
                        f"Для произвольной фигуры необходимо минимум 3 точки, получено:"
                        f"{len(points)}"
                    )

                # Проверяем формат каждой точки
                validated_points: List[Tuple[float, float]] = []
                for i, point in enumerate(points):
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        raise ValueError(
                            f"Некорректный формат точки {i+1}. Ожидается [x, y],"
                            f" получено: {point}"
                        )
                    x, y = point
                    validated_points.append((float(x), float(y)))

                return ArbitraryFigure(
                    name=obj_type,
                    current=current,
                    points=validated_points,
                    color=color,
                    direction=params.get("direction", CircleDirection.CLOCKWISE),
                )

            else:
                print(f"[WARN] Неизвестный тип объекта: {obj_type}")
                return None

        except Exception as e:
            print(f"[ERROR] Ошибка при создании объекта {obj_type}: {e}")
            # Показываем ошибку пользователю через QMessageBox
            QMessageBox.critical(
                None,
                "Ошибка создания объекта",
                f"Не удалось создать объект '{obj_type}':\n{str(e)}",
            )
            return None

    def add_object(self, obj_type: ObjectType, params: dict[str, Any]) -> None:
        """Creates MagneticObject by type and adds to canvas"""
        obj = self.create_magnetic_object(obj_type, params)
        if obj is not None:
            self.objects.append(obj)
            self.objectsPanel.update()
            self.canvas.mark_layer_dirty(LayerType.OBJECTS)
            self.canvas.update()

    def clear_objects(self):
        self.objects.clear()
        self.objectsPanel.update()
        self.canvas.mark_layer_dirty(LayerType.OBJECTS)
        self.canvas.update()

    def remove_object(self, index: int):
        # Remove the object from the list
        if 0 <= index < len(self.objects):
            self.objects.pop(index)
            # Update the panel to reflect the changes
            self.canvas.mark_layer_dirty(LayerType.OBJECTS)
            self.canvas.update()
            self.objectsPanel.update()

    def set_temporary_object(self, obj: MagneticObject):
        self.canvas.temporary_object = obj
        self.canvas.mark_layer_dirty(LayerType.HIGHLIGHT)
        self.canvas.update()

    def remove_temporary_object(self):
        self.canvas.temporary_object = None
        self.canvas.mark_layer_dirty(LayerType.HIGHLIGHT)
        self.canvas.update()
