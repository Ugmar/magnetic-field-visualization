from __future__ import annotations  # Делает все аннотации строками по умолчанию

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Tuple

import magpylib as magpy
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap

from gui.widgets.types import CircleDirection, ObjectType, PointDirection

if TYPE_CHECKING:
    from gui.widgets.canvas import Canvas


@dataclass(kw_only=True)
class MagneticObject:
    """Базовый объект магнитной сцены."""

    current: float  # Electric current in this object
    name: ObjectType  # Name of this object
    color: str = "#000000"

    def draw(self, pixmap: QPixmap, canvas: "Canvas", color: QColor | None = None):
        """Виртуальный метод для отрисовки."""
        raise NotImplementedError

    def to_magpy(self):
        """Конвертация в объект magpylib."""
        raise NotImplementedError


# === Прямой провод ===
@dataclass
class StraightWire(MagneticObject):
    x1: float
    y1: float
    x2: float
    y2: float

    def draw(self, pixmap: QPixmap, canvas: Canvas, color: QColor | None = None):
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if not color:
                color = QColor(self.color)
            painter.setPen(QPen(color, 2))

            # --- экранные координаты ---
            p1 = canvas.to_canvas(self.x1, self.y1)
            p2 = canvas.to_canvas(self.x2, self.y2)

            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            norm = (dx**2 + dy**2) ** 0.5
            if norm == 0:
                return
            dx /= norm
            dy /= norm

            # --- бесконечная линия ---
            max_len = max(canvas.width(), canvas.height()) * 1.5
            start = QPointF(p1.x() - dx * max_len, p1.y() - dy * max_len)
            end = QPointF(p1.x() + dx * max_len, p1.y() + dy * max_len)
            painter.drawLine(start, end)

            # --- стрелка направления ---
            vx, vy = self.x2 - self.x1, self.y2 - self.y1
            norm_v = (vx**2 + vy**2) ** 0.5
            if norm_v == 0:
                return
            vx /= norm_v
            vy /= norm_v

            # проекция (0,0) на прямую
            t_proj = -(self.x1 * vx + self.y1 * vy)
            x_arrow = self.x1 + vx * t_proj
            y_arrow = self.y1 + vy * t_proj
            pos_arrow = canvas.to_canvas(x_arrow, y_arrow)

            arrow_len = 10
            angle = math.atan2(dy, dx)
            left = QPointF(
                pos_arrow.x() - arrow_len * math.cos(angle - math.pi / 6),
                pos_arrow.y() - arrow_len * math.sin(angle - math.pi / 6),
            )
            right = QPointF(
                pos_arrow.x() - arrow_len * math.cos(angle + math.pi / 6),
                pos_arrow.y() - arrow_len * math.sin(angle + math.pi / 6),
            )
            painter.drawLine(pos_arrow, left)
            painter.drawLine(pos_arrow, right)

    def to_magpy(self):
        """Создание проводника через magpylib 5.2.0 API."""
        try:
            dx, dy = self.x2 - self.x1, self.y2 - self.y1
            length = (dx**2 + dy**2) ** 0.5

            # Нормализуем направление
            dx, dy = dx / length, dy / length

            wire_length = 100000
            # Используем Polyline для прямого провода
            start = [
                self.x1 - dx * wire_length,
                self.y1 - dy * wire_length,
                0,
            ]
            end = [
                self.x1 + dx * wire_length,
                self.y1 + dy * wire_length,
                0,
            ]

            return magpy.current.Polyline(
                current=self.current * 100, vertices=[start, end]
            )
        except Exception as e:
            print(f"[WARN] Ошибка при создании StraightWire magpylib: {e}")
            return None


# === Кольцевой ток ===
@dataclass
class Ring(MagneticObject):
    x: float
    y: float
    r: float
    direction: CircleDirection

    def draw(self, pixmap: QPixmap, canvas: "Canvas", color: QColor | None = None):
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if not color:
                color = QColor(self.color)
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # --- контур кольца ---
            center = canvas.to_canvas(self.x, self.y)
            radius = self.r * canvas.axes_marks_scale
            painter.drawEllipse(center, radius, radius)

            # --- стрелка направления ---
            x0, y0 = self.x, self.y
            dx, dy = -x0, -y0
            dist = math.hypot(dx, dy)

            # если центр в (0,0) → рисуем стрелку сверху
            if dist == 0:
                dx, dy = 0, -1
            else:
                dx /= dist
                dy /= dist

            # точка на окружности ближе к (0,0)
            x_arrow = x0 + dx * self.r
            y_arrow = y0 + dy * self.r
            pos_arrow = canvas.to_canvas(x_arrow, y_arrow)

            # касательная в этой точке
            tangent_angle = math.atan2(dy, dx)
            if self.direction == str(CircleDirection.CLOCKWISE):
                tangent_angle -= math.pi / 2
            else:
                tangent_angle += math.pi / 2

            arrow_len = 10
            tip = QPointF(
                pos_arrow.x() + arrow_len * math.cos(tangent_angle),
                pos_arrow.y() - arrow_len * math.sin(tangent_angle),
            )
            left = QPointF(
                tip.x() - arrow_len * math.cos(tangent_angle - math.pi / 6),
                tip.y() + arrow_len * math.sin(tangent_angle - math.pi / 6),
            )
            right = QPointF(
                tip.x() - arrow_len * math.cos(tangent_angle + math.pi / 6),
                tip.y() + arrow_len * math.sin(tangent_angle + math.pi / 6),
            )
            painter.drawLine(tip, left)
            painter.drawLine(tip, right)

    def to_magpy(self):
        """Создание кольца через magpylib 5.2.0 API."""
        try:
            # Вычисление модулей B происходит 2 раза за 1 добавление обьекта
            # (при отрисовке направлений и тепловой карты) =>
            # self.current *= -1 не работает =>
            # либо менять структуру вызова подсчета heat-map, либо оставлять так
            if self.direction == str(CircleDirection.CLOCKWISE):
                self.current = -abs(self.current)
            else:
                self.current = abs(self.current)

            # Используем Circle для кольца
            return magpy.current.Circle(
                current=self.current * 100,
                diameter=self.r * 2,
                position=(self.x, self.y, 0),
            )
        except Exception as e:
            print(f"[WARN] Ошибка при создании Ring magpylib: {e}")
            return None


# === Точечный источник ===
@dataclass
class PointWire(MagneticObject):
    x: float
    y: float
    direction: PointDirection

    def draw(self, pixmap: QPixmap, canvas: "Canvas", color: QColor | None = None):
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if not color:
                color = QColor(self.color)
            painter.setPen(QPen(color, 2))
            pos = canvas.to_canvas(self.x, self.y)
            painter.drawEllipse(pos, 10, 10)

            painter.setBrush(QColor(color))
            if self.direction == str(PointDirection.TO_US):
                painter.drawEllipse(pos, 4, 4)
            else:
                size = 5
                p1 = QPointF(pos.x() - size, pos.y() - size)
                p2 = QPointF(pos.x() + size, pos.y() + size)
                p3 = QPointF(pos.x() - size, pos.y() + size)
                p4 = QPointF(pos.x() + size, pos.y() - size)
                painter.drawLine(p1, p2)
                painter.drawLine(p3, p4)

    def to_magpy(self):
        """Создание проводника через magpylib 5.2.0 API."""
        try:
            self.moment = 1
            if self.direction == str(PointDirection.TO_US):
                self.moment = -1
            wire_length = 10000
            # Используем Polyline для прямого провода
            start = [self.x, self.y, -self.moment * wire_length]
            end = [self.x, self.y, self.moment * wire_length]

            return magpy.current.Polyline(
                current=self.current * 100, vertices=[start, end]
            )
        except Exception as e:
            print(f"[WARN] Ошибка при создании PointWire magpylib: {e}")
            return None


# === Произвольная фигура ===
@dataclass
class ArbitraryFigure(MagneticObject):
    """Произвольная замкнутая фигура, заданная списком точек."""

    points: List[Tuple[float, float]]  # Список (x, y) координат вершин
    direction: CircleDirection

    def __post_init__(self):
        """Проверяет, что передано не менее 3 точек."""
        if len(self.points) < 3:
            raise ValueError(
                "Для создания ArbitraryFigure необходимо указать не менее 3 точек."
            )

    def draw(self, pixmap: QPixmap, canvas: "Canvas", color: QColor | None = None):
        """Отрисовывает замкнутую ломаную линию с указанием направления тока."""
        if len(self.points) < 3:
            return

        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if color is None:
                color = QColor(self.color)
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Преобразуем точки в экранные координаты
            qpoints = [canvas.to_canvas(x, y) for x, y in self.points]

            # Рисуем все сегменты
            for i in range(len(qpoints)):
                p1 = qpoints[i]
                p2 = qpoints[(i + 1) % len(qpoints)]
                painter.drawLine(p1, p2)

            # --- Рисуем стрелку направления на первом сегменте ---
            # Берём первый сегмент: от точки 0 к точке 1
            p_start = qpoints[0]
            p_end = qpoints[1]

            # Вектор сегмента
            dx = p_end.x() - p_start.x()
            dy = p_end.y() - p_start.y()
            seg_len = math.hypot(dx, dy)

            if seg_len == 0:
                return  # Сегмент вырожден

            # Нормализуем направление
            dx /= seg_len
            dy /= seg_len

            # Точка для стрелки: на 1/3 длины сегмента от начала
            arrow_pos = QPointF(
                p_start.x() + dx * seg_len / 3,
                p_start.y() + dy * seg_len / 3,
            )

            # Длина стрелки (в пикселях)
            arrow_len = 8
            arrow_angle = math.atan2(dy, dx)

            # Если направление "по часовой", то ток идёт в обратную сторону
            if self.direction == str(CircleDirection.CLOCKWISE):
                arrow_angle += math.pi  # разворачиваем стрелку на 180°

            # Кончик стрелки
            tip = QPointF(
                arrow_pos.x() + arrow_len * math.cos(arrow_angle),
                arrow_pos.y() + arrow_len * math.sin(arrow_angle),
            )

            # Крылья стрелки
            wing_angle = math.pi / 6  # 30 градусов
            left_wing = QPointF(
                tip.x() - arrow_len * math.cos(arrow_angle - wing_angle),
                tip.y() - arrow_len * math.sin(arrow_angle - wing_angle),
            )
            right_wing = QPointF(
                tip.x() - arrow_len * math.cos(arrow_angle + wing_angle),
                tip.y() - arrow_len * math.sin(arrow_angle + wing_angle),
            )

            # Рисуем стрелку
            painter.drawLine(tip, left_wing)
            painter.drawLine(tip, right_wing)

    def to_magpy(self):
        """Конвертирует фигуру в список объектов magpylib Polyline."""
        # raise NotImplemented
        if len(self.points) < 3:
            # Проверка на всякий случай
            return None

        try:
            segments = []
            sign_current = self.current

            if self.direction == str(CircleDirection.CLOCKWISE):
                sign_current *= -1

            vertices = [[x, y, 0] for x, y in self.points]
            # Замыкаем фигуру, добавляя первую точку в конец
            vertices.append(vertices[0])

            return magpy.current.Polyline(current=sign_current * 100, vertices=vertices)

            # Возвращаем список отрезков
            return segments
        except Exception as e:
            print(f"[WARN] Ошибка при создании ArbitraryFigure magpylib: {e}")
            return None
