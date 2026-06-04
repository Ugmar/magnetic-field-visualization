from typing import Optional

import numpy as np
from magpylib import Collection
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PyQt6.QtWidgets import QWidget

from core.FieldManager import FieldManager
from core.ObjectManager import (  # convert_object_to_magnetic_objects,
    convert_magnetic_objects_to_magpy,
)
from core.objects import MagneticObject
from gui.widgets.types import LayerType, ObjectType


class Canvas(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.objects: list[MagneticObject] = []
        self.temporary_object: MagneticObject | None = None
        self.current_type: Optional[ObjectType] = None
        self.axes_marks_scale: float = 40.0  # scale (1 unit = marks_scale pixels)
        self.grid_pitch: float = 0.5  # scale (1 grid pitch = grid_pitch world units)
        self.mouse_pos: tuple[float, float] | None = (
            None  # current mouse position in world coordinates
        )
        self.layers: dict[LayerType, QPixmap] = {}
        self.layers_visibility: dict[LayerType, bool] = {}
        self.dirty_layers = set(LayerType)
        self.layer_order: list[LayerType] = list(LayerType)
        self.field_manager = FieldManager(self)

        self.setMinimumSize(600, 600)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self.init_layers()

    def init_layers(self):
        # Initialize all layers
        for layer_name in self.layer_order:
            self.layers_visibility[layer_name] = layer_name.default_visibility()
        self.dirty_layers = set(self.layer_order)

    def mark_layer_dirty(self, layer_type: LayerType):
        """Mark a specific layer as needing repaint"""
        self.dirty_layers.add(layer_type)
        self.update()

    def regenerate_layer(self, layer_type):
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(0, 0, 0, 0))

        if layer_type == LayerType.AXES:
            if self.layers_visibility[layer_type]:
                self.draw_axes(pixmap)

        elif layer_type == LayerType.HEATMAP:
            if self.layers_visibility[layer_type]:
                self.field_manager.draw_heatmap(pixmap)
            self.mark_layer_dirty(LayerType.HEATMAP_LEGEND)

        elif layer_type == LayerType.OBJECTS:
            if self.layers_visibility[layer_type]:
                for obj in self.objects:
                    obj.draw(pixmap, self)
            self.mark_layer_dirty(LayerType.HEATMAP)
            self.mark_layer_dirty(LayerType.DIRECTIONS)

        elif layer_type == LayerType.HEATMAP_LEGEND:
            if self.layers_visibility[layer_type]:
                self.field_manager.draw_heatmap_legend(pixmap)

        elif layer_type == LayerType.MOUSE_POSITION_BAR:
            if self.layers_visibility[layer_type]:
                self.draw_cursor_properties(pixmap)

        elif layer_type == LayerType.DIRECTIONS:
            if self.layers_visibility[layer_type]:
                self.field_manager.draw_field_vectors(pixmap)
        elif layer_type == LayerType.GRID:
            if self.layers_visibility[layer_type]:
                self.draw_grid(pixmap)
        elif layer_type == LayerType.HIGHLIGHT:
            if self.layers_visibility[layer_type]:
                if self.temporary_object:
                    self.temporary_object.draw(pixmap, self, QColor("#000000"))
        else:
            raise NotImplementedError

        self.layers[layer_type] = pixmap
        self.dirty_layers.discard(layer_type)

    # ===========================================================
    # Получение типа объекта из Controller
    # ===========================================================
    def set_object_type(self, obj_type: ObjectType) -> None:
        self.current_type = obj_type

    # ===========================================================
    # Преобразование координат
    # ===========================================================
    def to_canvas(self, x: float, y: float) -> QPointF:
        cx, cy = self.width() / 2, self.height() / 2
        return QPointF(cx + x * self.axes_marks_scale, cy - y * self.axes_marks_scale)

    def to_world(self, x: float, y: float) -> tuple[float, float]:
        cx, cy = self.width() / 2, self.height() / 2
        return (x - cx) / self.axes_marks_scale, (cy - y) / self.axes_marks_scale

    # ===========================================================
    # Отрисовка
    # ===========================================================
    def paintEvent(self, event: QPaintEvent):
        for layer_type in list(self.dirty_layers):
            self.regenerate_layer(layer_type)

        # Composite layers in defined order
        painter = QPainter(self)
        for layer_type in self.layer_order:
            if self.layers[layer_type]:
                painter.drawPixmap(0, 0, self.layers[layer_type])
        painter.end()

    # ===========================================================
    # Оси
    # ===========================================================
    def draw_axes(self, pixmap: QPixmap):

        cx, cy = int(self.width() / 2), int(self.height() / 2)
        pen = QPen(QColor("white"), 2)

        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(pen)

            # горизонтальная и вертикальная оси
            painter.drawLine(0, cy, self.width(), cy)
            painter.drawLine(cx, 0, cx, self.height())

            fm = painter.fontMetrics()
            # Подпись осей
            painter.drawText(self.width() - 40, cy - 15 + int(fm.ascent() / 3), "X, см")
            painter.drawText(cx - 50, 15 + int(fm.ascent() / 3), "Y, см")

            # засечки и подписи
            for i in range(
                -int(cx // self.axes_marks_scale), int(cx // self.axes_marks_scale) + 1
            ):
                x = int(cx + i * self.axes_marks_scale)
                painter.drawLine(x, cy - 5, x, cy + 5)
                if i != 0:
                    painter.drawText(x - 10, cy + 20, str(i))

            for j in range(
                -int(cy // self.axes_marks_scale), int(cy // self.axes_marks_scale) + 1
            ):
                y = int(cy - j * self.axes_marks_scale)
                painter.drawLine(cx - 5, y, cx + 5, y)
                if j != 0:
                    painter.drawText(cx + 10, int(y + fm.ascent() / 2), str(j))

    def draw_cursor_properties(self, pixmap: QPixmap) -> None:
        with QPainter(pixmap) as painter:
            if not self.mouse_pos:
                return
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("white")))

            # Get mouse position in world coordinates
            wx, wy = self.mouse_pos

            # Calculate magnetic field at cursor position
            field_value = self._get_field_at_cursor(wx, wy)

            fm = painter.fontMetrics()
            margin = 5
            line_height = fm.height()

            # Format the texts
            coords_text = f"x={wx:.2f}, y={wy:.2f}"

            if field_value is not None:
                # Format the field value nicely
                field_str = self._format_field_value(field_value)
                field_text = f"B={field_str} Тл"

                # Calculate positions for each line independently
                field_text_width = fm.horizontalAdvance(field_text)
                coords_text_width = fm.horizontalAdvance(coords_text)

                # Draw field value on top line (right-aligned)
                field_x = self.width() - field_text_width - margin
                field_y = self.height() - margin - line_height
                painter.drawText(field_x, field_y, field_text)

                # Draw coordinates on bottom line (right-aligned)
                coords_x = self.width() - coords_text_width - margin
                coords_y = self.height() - margin
                painter.drawText(coords_x, coords_y, coords_text)
            else:
                # Only draw coordinates if no field value (right-aligned)
                coords_x = self.width() - fm.horizontalAdvance(coords_text) - margin
                coords_y = self.height() - margin
                painter.drawText(coords_x, coords_y, coords_text)

    def _get_field_at_cursor(self, wx: float, wy: float) -> float | None:
        """Calculate magnetic field strength at specified world coordinates"""
        if not self.objects:
            return None

        try:
            # Convert magnetic objects to magpylib format
            magpy_objects = convert_magnetic_objects_to_magpy(self.objects)
            if not magpy_objects:
                return None

            # Create magpylib collection
            magpy_objects_collection = Collection(magpy_objects)

            # Create point in 3D space (z=0 for 2D projection)
            world_point = np.array([[wx, wy, 0]])

            # Calculate magnetic field at the point
            B_field = magpy_objects_collection.getB(world_point)

            # Calculate field strength (magnitude of B vector)
            field_strength = np.linalg.norm(B_field)
            return float(field_strength)

        except Exception:
            # Return None if calculation fails
            return None

    def _format_field_value(self, value: float) -> str:
        """Format field value for display with appropriate precision"""
        if value == 0:
            return "0"
        elif abs(value) >= 1:
            return f"{value:.2f}"
        elif abs(value) >= 0.001:
            return f"{value:.3f}"
        else:
            return f"{value:.1e}"

    def draw_grid(self, pixmap: QPixmap):
        """Draw a grid with specified pitch in world coordinates"""

        cx, cy = int(self.width() / 2), int(self.height() / 2)

        with QPainter(pixmap) as painter:
            # Use a subtle color for grid lines
            grid_pen = QPen(QColor(100, 100, 100, 200))  # Semi-transparent gray
            grid_pen.setWidth(1)
            painter.setPen(grid_pen)

            # Calculate grid spacing in pixels
            grid_spacing_px = self.grid_pitch * self.axes_marks_scale

            # Draw vertical grid lines
            x = cx
            while x < self.width():
                painter.drawLine(int(x), 0, int(x), self.height())
                x += grid_spacing_px

            x = cx - grid_spacing_px
            while x >= 0:
                painter.drawLine(int(x), 0, int(x), self.height())
                x -= grid_spacing_px

            # Draw horizontal grid lines
            y = cy
            while y < self.height():
                painter.drawLine(0, int(y), self.width(), int(y))
                y += grid_spacing_px

            y = cy - grid_spacing_px
            while y >= 0:
                painter.drawLine(0, int(y), self.width(), int(y))
                y -= grid_spacing_px

    # ===========================================================
    # События мыши
    # ===========================================================
    def mouseMoveEvent(self, event: QMouseEvent):
        wx, wy = self.to_world(event.position().x(), event.position().y())
        self.mouse_pos = (wx, wy)
        self.mark_layer_dirty(LayerType.MOUSE_POSITION_BAR)

        # # динамический предпросмотр
        # if self.start_point and self.temp_object_type in (
        #     ObjectType.WIRE,
        #     ObjectType.RING,
        # ):
        #     x1, y1 = self.start_point
        #     if self.temp_object_type == ObjectType.WIRE:
        #         self.temporary_object = {
        #             "type": ObjectType.WIRE,
        #             "params": {"x1": x1, "y1": y1, "x2": wx, "y2": wy},
        #         }
        #     elif self.temp_object_type == ObjectType.RING:
        #         r = math.hypot(wx - x1, wy - y1)
        #         self.temporary_object = {
        #             "type": ObjectType.RING,
        #             "params": {"x": x1, "y": y1, "r": r, "direction": "По часовой"},
        #         }
        self.update()

    def leaveEvent(self, event):
        self.mouse_pos = None
        self.mark_layer_dirty(LayerType.MOUSE_POSITION_BAR)
        self.update()

    def resizeEvent(self, event: QResizeEvent):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        for member in LayerType:
            self.dirty_layers.add(member)  # Add all layers for redraw
        self.update()
