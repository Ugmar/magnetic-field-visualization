import math
from typing import TYPE_CHECKING, Any

import numpy as np
from magpylib import Collection
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap

if TYPE_CHECKING:
    from gui.widgets.canvas import Canvas
else:
    Canvas = Any

from .ObjectManager import (  # convert_object_to_magnetic_objects,
    convert_magnetic_objects_to_magpy,
)

if TYPE_CHECKING:
    from gui.widgets.canvas import Canvas


class FieldManager:
    """Class for heatmap and field direction management"""

    def __init__(self, canvas_instance: "Canvas"):
        self.canvas = canvas_instance
        self.heatmap_resolution = 6
        self.direction_vectors_resolution = 20
        self.B_strengths: None = None
        self.max_B_strength = 0
        self.min_B_strength = 0

    def _reset(self) -> None:
        self.B_strengths = None
        self.max_B_strength = 0
        self.min_B_strength = 0

    def _get_field_data(self, resolution: int) -> dict | None:
        """Calculate array of HeatPoints"""
        if not self.canvas.objects:
            self._reset()
            return

        magpy_objects = convert_magnetic_objects_to_magpy(self.canvas.objects)

        if not magpy_objects:
            self._reset()
            return

        # Creating magpylib-specific collection
        magpy_objects_collection = Collection(magpy_objects)

        # Create x and y probes  for field measures
        x_probes = np.arange(0, self.canvas.width() + resolution, resolution)
        y_probes = np.arange(0, self.canvas.height() + resolution, resolution)
        X_canvas, Y_canvas = np.meshgrid(x_probes, y_probes)

        # Convert to real coordinates
        world_planar_coords = np.array(
            [
                self.canvas.to_world(float(x), float(y))
                for x, y in zip(X_canvas.ravel(), Y_canvas.ravel())
            ]
        )
        world_spacial_points = np.column_stack(
            [world_planar_coords, np.zeros(len(world_planar_coords))]
        )  # adds component z = 0 for magpy proper work

        # Calculate field vectors for all spacial_points
        B_fields = magpy_objects_collection.getB(world_spacial_points)

        strengths = np.linalg.norm(B_fields, axis=1)
        # Нормализация с использованием процентилей

        p5 = np.percentile(strengths, 2)
        p95 = np.percentile(strengths, 97)

        if p5 == p95:
            normalized_strengths = np.zeros_like(strengths)
        else:
            normalized_strengths = np.clip((strengths - p5) / (p95 - p5), 0, 1)

        self.max_B_strength = np.max(strengths)
        self.min_B_strength = np.min(strengths)

        return {
            "points": list(zip(X_canvas.ravel(), Y_canvas.ravel())),
            "vector": B_fields,
            "norm_strengths": normalized_strengths,
        }

    def draw_heatmap(self, pixmap: QPixmap):
        """Отрисовка тепловой карты"""
        heatmap_data = self._get_field_data(self.heatmap_resolution)
        if not heatmap_data:
            return

        points = heatmap_data["points"]
        norm_strengths = heatmap_data["norm_strengths"]
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            for i, (x, y) in enumerate(points):
                intensity = norm_strengths[i]
                color = self._field_strength_to_color(intensity, 255)
                painter.fillRect(
                    x - self.heatmap_resolution // 2,
                    y - self.heatmap_resolution // 2,
                    self.heatmap_resolution,
                    self.heatmap_resolution,
                    color,
                )

    def _field_strength_to_color(self, intensity: float, opacity: int):
        """
        Convert intensity (0.0 to 1.0) to RGB color through the sequence:
        Black (0,0,0) -> Blue (0,0,255) -> Cyan (0,255,255) -> Green (0,255,0) ->
        Yellow (255,255,0) -> Red (255,0,0)
        """
        # Ensure intensity is in [0, 1] range
        intensity = max(0.0, min(1.0, intensity))

        # Define the color transition points
        if intensity <= 0.2:
            # Black (0,0,0) to Blue (0,0,255)
            ratio = intensity / 0.2
            r = 0
            g = 0
            b = int(255 * ratio)
        elif intensity <= 0.4:
            # Blue (0,0,255) to Cyan (0,255,255)
            ratio = (intensity - 0.2) / 0.2
            r = 0
            g = int(255 * ratio)
            b = 255
        elif intensity <= 0.6:
            # Cyan (0,255,255) to Green (0,255,0)
            ratio = (intensity - 0.4) / 0.2
            r = 0
            g = 255
            b = int(255 * (1 - ratio))
        elif intensity <= 0.8:
            # Green (0,255,0) to Yellow (255,255,0)
            ratio = (intensity - 0.6) / 0.2
            r = int(255 * ratio)
            g = 255
            b = 0
        else:
            # Yellow (255,255,0) to Red (255,0,0)
            ratio = (intensity - 0.8) / 0.2
            r = 255
            g = int(255 * (1 - ratio))
            b = 0

        return QColor(r, g, b, opacity)

    def draw_heatmap_legend(
        self,
        pixmap: QPixmap,
        x: int = 10,
        y: int = 30,
        width: int = 200,
        height: int = 20,
    ) -> None:
        with QPainter(pixmap) as painter:
            # Рисуем градиентную полосу
            gradient_steps = width
            for i in range(gradient_steps):
                intensity = i / gradient_steps
                color = self._field_strength_to_color(intensity, 255)
                painter.fillRect(x + i, y, 1, height, color)

            # Рисуем рамку вокруг легенды
            painter.setPen(QPen(QColor("white"), 1))
            painter.drawRect(x, y, width, height)

            fm = painter.fontMetrics()

            # Форматируем значения
            def format_value(val):
                if val == 0:
                    return "0"
                elif abs(val) >= 1:
                    return f"{val:.2f}"
                elif abs(val) >= 0.001:
                    return f"{val:.3f}"
                else:
                    return f"{val:.1e}"

            # Подписи значений
            min_text = format_value(self.min_B_strength)
            max_text = format_value(self.max_B_strength)
            mid_text = format_value((self.max_B_strength + self.min_B_strength) / 2)

            # Рисуем подписи под легендой
            text_y = y + height + fm.height() + 5

            # Минимальное значение (слева)
            painter.drawText(x, text_y, min_text)

            # Среднее значение (по центру)
            mid_x = x + width // 2 - fm.horizontalAdvance(mid_text) // 2
            painter.drawText(mid_x, text_y, mid_text)

            # Максимальное значение (справа)
            max_x = x + width - fm.horizontalAdvance(max_text)
            painter.drawText(max_x, text_y, max_text)

            # Единицы измерения
            unit_text = "Магнитная индукция (Тл)"
            unit_x = x + width // 2 - fm.horizontalAdvance(unit_text) // 2
            unit_y = y - 5
            painter.drawText(unit_x, unit_y, unit_text)

    def draw_field_vectors(self, pixmap: QPixmap):
        field_points = self._get_field_data(self.direction_vectors_resolution)
        if not field_points:
            return

        # Array of dots
        points = field_points["points"]

        # Array of B vectors
        vector = field_points["vector"]

        for i, (x, y) in enumerate(points):
            self.draw_vector(x, y, vector[i], pixmap)

    def draw_vector(
        self, x: float, y: float, vector: tuple[float, float, float], pixmap: QPixmap
    ):
        """Draw vector with appropriate visualization based on direction
        Args:
            x, y: Coordinates
            vector: (x, y, z) components of the vector
            pixmap: Target pixmap to draw on
        """
        vector_x, vector_y, vector_z = vector

        # Case 1: Pure perpendicular vector (only Z component)
        if vector_z != 0 and vector_x == 0 and vector_y == 0:
            self._draw_perpendicular_indicator(x, y, vector_z, pixmap)

        # Case 2: Horizontal vector (X and/or Y components)
        elif vector_x**2 + vector_y**2 > 0:
            self._draw_horizontal_arrow(x, y, vector_x, vector_y, pixmap)

    def _draw_perpendicular_indicator(
        self, x: float, y: float, z_component: float, pixmap: QPixmap
    ):
        """Draw perpendicular vector indicator (circle or cross)"""
        if z_component == 0:
            return

        with QPainter(pixmap) as painter:
            color = QColor("green")
            painter.setPen(QPen(color, 1))

            if z_component > 0:
                # Draw "to us" - circle
                R = 6
                painter.drawEllipse(x - (R // 2), y - (R // 2), R, R)
            else:
                # Draw "from us" - cross
                size = 3
                painter.drawLine(x - size, y - size, x + size, y + size)
                painter.drawLine(x - size, y + size, x + size, y - size)

    def _draw_horizontal_arrow(
        self, x: float, y: float, vector_x: float, vector_y: float, pixmap: QPixmap
    ):
        """Draw horizontal vector as arrow"""
        vector_length = 10
        arrow_tip_length = vector_length / 2

        with QPainter(pixmap) as painter:
            color = QColor("green")
            painter.setPen(QPen(color, 1))
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Calculate direction and normalize
            direction_length = math.sqrt(vector_x**2 + vector_y**2)
            dx = -vector_x / direction_length  # Note: x direction is flipped
            dy = vector_y / direction_length

            # Calculate main vector line
            vector_start = QPointF(x, y)
            vector_end = QPointF(
                x + vector_length * dx,
                y + vector_length * dy,
            )

            # Draw the main line
            painter.drawLine(vector_start, vector_end)

            # Calculate arrow tip
            line_length = math.sqrt(
                (vector_end.x() - vector_start.x()) ** 2
                + (vector_end.y() - vector_start.y()) ** 2
            )
            if line_length > 0:
                # Normalize the direction (recalculate to be precise)
                dx_line = (vector_end.x() - vector_start.x()) / line_length
                dy_line = (vector_end.y() - vector_start.y()) / line_length

                # Calculate perpendicular direction for arrow wings
                perp_dx = -dy_line
                perp_dy = dx_line

                # Calculate arrow tip points
                arrow_tip_base = QPointF(
                    vector_end.x() - dx_line * arrow_tip_length,
                    vector_end.y() - dy_line * arrow_tip_length,
                )

                # Calculate the two arrow wing points
                arrow_wing1 = QPointF(
                    arrow_tip_base.x() + perp_dx * arrow_tip_length * 0.5,
                    arrow_tip_base.y() + perp_dy * arrow_tip_length * 0.5,
                )

                arrow_wing2 = QPointF(
                    arrow_tip_base.x() - perp_dx * arrow_tip_length * 0.5,
                    arrow_tip_base.y() - perp_dy * arrow_tip_length * 0.5,
                )

                # Draw arrow tip lines
                painter.drawLine(vector_end, arrow_wing1)
                painter.drawLine(vector_end, arrow_wing2)
