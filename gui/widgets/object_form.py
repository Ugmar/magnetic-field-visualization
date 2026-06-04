from PyQt6.QtCore import Qt, QEvent, QLocale, QTimer
from PyQt6.QtGui import (
    QDoubleValidator,
    QKeySequence,
    QShortcut,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTableView,
    QHeaderView,
    QStyledItemDelegate,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QApplication,
)

# Импорты вашего приложения
from gui.controller import Controller
from gui.widgets.canvas import Canvas
from .objectPanel import ObjectCardsPanel
from .types import CircleDirection, LayerType, ObjectType, PointDirection

# Стандартные библиотеки
from typing import List, Tuple, Optional


class FloatDelegate(QStyledItemDelegate):
    """Делегат для валидации чисел в таблице"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setDecimals(3)
        editor.setMinimum(-9999.0)
        editor.setMaximum(9999.0)
        editor.setSingleStep(0.1)
        editor.setLocale(QLocale(QLocale.Language.English))
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        editor.interpretText()
        value = "{:.3f}".format(editor.value()).rstrip('0').rstrip('.') or "0.0"
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class FloatDelegate(QStyledItemDelegate):
    """Делегат для валидации чисел в таблице"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setFrame(False)
        editor.setDecimals(3)
        editor.setMinimum(-9999.0)
        editor.setMaximum(9999.0)
        editor.setSingleStep(0.1)
        editor.setLocale(QLocale(QLocale.Language.English))
        return editor

    def setEditorData(self, editor: QDoubleSpinBox, index):
        model = index.model()
        if model:
            value = model.data(index, Qt.ItemDataRole.EditRole)
        editor.setValue(float(value))

    def setModelData(self, editor: QDoubleSpinBox, model, index):
        editor.interpretText()
        value = "{:.3f}".format(editor.value()).rstrip("0").rstrip(".") or "0.0"
        if model:
            model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        if editor:
            editor.setGeometry(option.rect)


class ObjectForm(QWidget):
    def __init__(self, canvas_instance: Canvas, parent=None):
        super().__init__(parent)
        self.llayout = QVBoxLayout()
        self.setLayout(self.llayout)
        self.objectsPanel = ObjectCardsPanel(canvas_instance.objects, self)
        self.controller = Controller(canvas_instance, self.objectsPanel)

        # --- object type choice ---
        self.object_type_combobox = QComboBox()
        for obj_type in ObjectType:
            self.object_type_combobox.addItem(str(obj_type), obj_type)
        self.object_type_combobox.currentTextChanged.connect(self.update_form)
        self.object_type_combobox.currentIndexChanged.connect(
            self.on_object_type_changed
        )

        # --- object parameters form ---
        self.form_layout = QFormLayout()

        # --- set fixed size ---
        self.setMinimumWidth(320)
        self.setMaximumWidth(420)

        # --- Object creation button ---
        self.create_btn = QPushButton("Добавить объект")
        self.create_btn.clicked.connect(self.create_object_wrapper)
        # Create shortcut that works regardless of focus
        self.enter_shortcut = QShortcut(QKeySequence("Return"), self)
        self.enter_shortcut.activated.connect(self.create_btn.click)
        # Optional: Also capture numpad Enter
        self.numpad_enter_shortcut = QShortcut(QKeySequence("Enter"), self)
        self.numpad_enter_shortcut.activated.connect(self.create_btn.click)

        # --- Clear canvas button ---
        self.clear_canvas_btn = QPushButton("Очистить окно")
        self.clear_canvas_btn.clicked.connect(self.controller.clear_objects)

        # --- Layers visibility checkboxes ---
        self.field_visibility_checkbox = QCheckBox("Показать магнитные линии")
        self.field_visibility_checkbox.setChecked(
            LayerType.DIRECTIONS.default_visibility()
        )
        self.field_visibility_checkbox.stateChanged.connect(
            lambda signal_arg: self.controller.set_layer_visibility(
                signal_arg, LayerType.DIRECTIONS
            )
        )

        self.heatmap_visibility_checkbox = QCheckBox("Показать тепловую карту")
        self.heatmap_visibility_checkbox.setChecked(
            LayerType.HEATMAP.default_visibility()
        )
        self.heatmap_visibility_checkbox.stateChanged.connect(
            lambda signal_arg: self.controller.set_layer_visibility(
                signal_arg, LayerType.HEATMAP
            )
        )

        self.grid_visibility_checkbox = QCheckBox("Показать сетку")
        self.grid_visibility_checkbox.setChecked(LayerType.GRID.default_visibility())
        self.grid_visibility_checkbox.stateChanged.connect(
            lambda signal_arg: self.controller.set_layer_visibility(
                signal_arg, LayerType.GRID
            )
        )

        # --- Layout compilation ---
        self.llayout.addWidget(self.object_type_combobox)
        self.llayout.addLayout(self.form_layout)

        self.llayout.addWidget(self.objectsPanel)

        self.llayout.addWidget(self.field_visibility_checkbox)
        self.llayout.addWidget(self.heatmap_visibility_checkbox)
        self.llayout.addWidget(self.grid_visibility_checkbox)
        self.llayout.addWidget(self.create_btn)
        self.llayout.addWidget(self.clear_canvas_btn)

        self.update_form()

    # ------------------------------------------------------------------
    # Создание числового поля с ограничением
    # ------------------------------------------------------------------
    def _create_float_input(self, min_value=-9999.0, max_value=9999.0):
        # Создание числового поля с ограничением (по умолчанию разрешены отрицательные).
        line = QLineEdit()
        validator = QDoubleValidator(min_value, max_value, 3)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        validator.setLocale(QLocale(QLocale.Language.English))
        line.setValidator(validator)
        line.installEventFilter(self)
        return line

    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.Type.MouseButtonPress:
            # Let the mouse press event complete first, then select text
            result = super().eventFilter(obj, event)  # Let normal processing happen
            QTimer.singleShot(0, obj.selectAll)  # Select after click is processed
            return result
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Обновление формы при выборе типа объекта
    # ------------------------------------------------------------------
    def update_form(self):
        # Очистка предыдущих ресурсов для ARBITRARY_FIGURE
        if hasattr(self, "points_model"):
            self.points_model.deleteLater()
            del self.points_model
        if hasattr(self, "points_table"):
            self.points_table.setModel(None)  # Отвязываем модель
            del self.points_table
        if hasattr(self, "points_counter"):
            del self.points_counter

        # Очистка основного layout
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        obj_type = self.object_type_combobox.currentData()

        # общее поле силы тока
        self.current_input = self._create_float_input(0.0)
        self.current_input.setText("1.0")
        self.form_layout.addRow("Сила тока (A):", self.current_input)

        if obj_type == ObjectType.WIRE:
            self.x1_input = self._create_float_input()
            self.y1_input = self._create_float_input()
            self.x2_input = self._create_float_input()
            self.y2_input = self._create_float_input()

            self.x1_input.setText("0.0")
            self.y1_input.setText("0.0")
            self.x2_input.setText("1.0")  # TODO remove hardcode
            self.y2_input.setText("1.0")

            self.form_layout.addRow("x₁:", self.x1_input)
            self.form_layout.addRow("y₁:", self.y1_input)
            self.form_layout.addRow("x₂:", self.x2_input)
            self.form_layout.addRow("y₂:", self.y2_input)

        elif obj_type == ObjectType.POINT_WIRE:
            self.x_input = self._create_float_input()
            self.y_input = self._create_float_input()

            self.x_input.setText("1.0")
            self.y_input.setText("1.0")

            self.direction_input = QComboBox()
            self.direction_input.addItems([str(i) for i in PointDirection])

            self.form_layout.addRow("x:", self.x_input)
            self.form_layout.addRow("y:", self.y_input)
            self.form_layout.addRow("Направление:", self.direction_input)

        elif obj_type == ObjectType.RING:
            self.x_input = self._create_float_input()
            self.y_input = self._create_float_input()
            self.radius_input = self._create_float_input(0.0)
            self.x_input.setText("1.0")
            self.y_input.setText("1.0")
            self.radius_input.setText("3.0")

            self.direction_input = QComboBox()
            self.direction_input.addItems([str(i) for i in CircleDirection])

            self.form_layout.addRow("x центра:", self.x_input)
            self.form_layout.addRow("y центра:", self.y_input)
            self.form_layout.addRow("Радиус:", self.radius_input)
            self.form_layout.addRow("Направление:", self.direction_input)

        elif obj_type == ObjectType.ARBITRARY_FIGURE:
            # --- Определение цветовой схемы ---
            self.direction_input = QComboBox()
            self.direction_input.addItems([str(i) for i in CircleDirection])
            self.form_layout.addRow("Направление:", self.direction_input)

            palette = QApplication.palette()
            is_dark_theme = palette.base().color().lightness() < 128

            # --- Стили для светлой/тёмной темы ---
            if is_dark_theme:
                table_style = """
                    QTableView {
                        border: 1px solid #555555;
                        gridline-color: #444444;
                        selection-background-color: #1e64c8;
                        background-color: #2d2d2d;
                        color: #ffffff;
                    }
                    QHeaderView::section {
                        background-color: #3a3a3a;
                        color: #e0e0e0;
                        padding: 4px;
                        border: 1px solid #555555;
                        font-weight: bold;
                    }
                    QHeaderView::section:checked {
                        background-color: #254a86;
                    }
                    QTableView::item {
                        padding: 4px;
                    }
                """
                counter_style = "font-weight: bold; color: #64b5f6;"
                add_btn_style = (
                    "font-weight: bold; background-color: #2e7d32; color:"
                    " white; border-radius: 4px; padding: 3px 8px;"
                )
                remove_btn_style = (
                    "font-weight: bold; background-color: #c62828; color:"
                    " white; border-radius: 4px; padding: 3px 8px;"
                )
            else:
                table_style = """
                    QTableView {
                        border: 1px solid #c0c0c0;
                        gridline-color: #e0e0e0;
                        selection-background-color: #d6e9ff;
                        background-color: white;
                        color: #333333;
                    }
                    QHeaderView::section {
                        background-color: #f0f5ff;
                        color: #2c3e50;
                        padding: 4px;
                        border: 1px solid #d0d0d0;
                        font-weight: bold;
                    }
                    QHeaderView::section:checked {
                        background-color: #bbdefb;
                    }
                    QTableView::item {
                        padding: 4px;
                    }
                """
                counter_style = "font-weight: bold; color: #2c3e50;"
                add_btn_style = (
                    "font-weight: bold; background-color: #27ae60; color:"
                    " white; border-radius: 4px; padding: 3px 8px;"
                )
                remove_btn_style = (
                    "font-weight: bold; background-color: #c0392b; color: "
                    "white; border-radius: 4px; padding: 3px 8px;"
                )

            # --- Таблица точек ---
            self.points_table = QTableView()
            self.points_table.setStyleSheet(table_style)
            self.points_table.setAlternatingRowColors(True)

            # Включаем вертикальный заголовок для номеров точек
            vertical_header = self.points_table.verticalHeader()
            if vertical_header:
                vertical_header.setVisible(True)
                vertical_header.setFixedWidth(30)
                vertical_header.setStyleSheet(
                    """
                    QHeaderView::section {
                        padding: 4px;
                        font-weight: bold;
                        background-color: #4a4a4a;
                        color: #ffffff;
                        border: none;
                    }
                """
                    if is_dark_theme
                    else """
                    QHeaderView::section {
                        padding: 4px;
                        font-weight: bold;
                        background-color: #e3f2fd;
                        color: #1a237e;
                        border: none;
                    }
                """
                )

            self.points_table.setEditTriggers(QTableView.EditTrigger.DoubleClicked)
            self.points_table.setSelectionBehavior(
                QTableView.SelectionBehavior.SelectRows
            )
            self.points_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
            self.points_table.setMinimumHeight(200)  # Минимальная высота для удобства

            # --- Модель данных ---
            self.points_model = QStandardItemModel(3, 2)  # 3 строки, 2 колонки (x, y)
            self.points_model.setHorizontalHeaderLabels(["x", "y"])

            # Заполняем начальные значения
            for row in range(3):
                self._set_table_item(row, 0, str(row * 2) + ".0")
                self._set_table_item(row, 1, str(row * row) + ".0")

            # Устанавливаем модель и обновляем заголовки
            self.points_table.setModel(self.points_model)
            self._update_row_headers()

            # Ширина колонок
            header = self.points_table.horizontalHeader()
            if header:
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

            # --- Кнопки управления ---
            btns_widget = QWidget()
            btns_layout = QHBoxLayout(btns_widget)
            btns_layout.setContentsMargins(0, 0, 0, 0)

            add_btn = QPushButton("✚ Добавить точку")
            add_btn.setStyleSheet(add_btn_style)
            remove_btn = QPushButton("✖ Удалить выбранную")
            remove_btn.setStyleSheet(remove_btn_style)

            # Счётчик точек
            self.points_counter = QLabel("Точек: 3")
            self.points_counter.setStyleSheet(counter_style)

            btns_layout.addWidget(self.points_counter)
            btns_layout.addWidget(add_btn)
            btns_layout.addWidget(remove_btn)
            btns_layout.addStretch()

            # --- Сборка ---
            self.form_layout.addRow("Координаты вершин:", self.points_table)
            self.form_layout.addRow(btns_widget)

            # --- События ---
            add_btn.clicked.connect(self._add_table_row)
            remove_btn.clicked.connect(self._remove_selected_row)

            # Автообновление при изменении модели
            self.points_model.rowsInserted.connect(
                lambda *args: self._on_rows_changed()
            )
            self.points_model.rowsRemoved.connect(lambda *args: self._on_rows_changed())

            # Обработка выделения
            selection_model = self.points_table.selectionModel()
            if selection_model:
                selection_model.selectionChanged.connect(
                    lambda: remove_btn.setEnabled(
                        len(self.points_table.selectedIndexes()) > 0
                    )
                )

            # Начальное состояние кнопки удаления
            remove_btn.setEnabled(False)

    def _add_table_row(self):
        """Добавляет новую строку в конец таблицы"""
        row_count = self.points_model.rowCount()
        self.points_model.insertRow(row_count)
        self._set_table_item(row_count, 0, "0.0")
        self._set_table_item(row_count, 1, "0.0")

    def _update_row_headers(self):
        """Обновляет нумерацию строк в вертикальном заголовке"""
        for row in range(self.points_model.rowCount()):
            # Устанавливаем номер точки (начиная с 1)
            self.points_model.setVerticalHeaderItem(row, QStandardItem(f"{row + 1}"))

    def _on_rows_changed(self):
        """Обработчик изменений в таблице (добавление/удаление строк)"""
        self._update_row_headers()
        self._update_table_counter()

        # Автоматически выделяем новую строку при добавлении
        if self.points_model.rowCount() > 3:
            last_row = self.points_model.rowCount() - 1
            self.points_table.selectRow(last_row)
            self.points_table.scrollTo(self.points_model.index(last_row, 0))

    def _set_table_item(self, row: int, column: int, value: str):
        """Создаёт элемент таблицы с валидацией"""
        item = QStandardItem(value)
        item.setData(
            QLocale(QLocale.Language.English), Qt.ItemDataRole.UserRole
        )  # Для валидации
        font = item.font()
        font.setPointSize(9)
        item.setFont(font)

        # Применяем валидатор через делегат
        self.points_table.setItemDelegateForColumn(column, FloatDelegate(self))

        self.points_model.setItem(row, column, item)

    def _remove_selected_row(self):
        """Удаляет выбранную строку"""
        indexes = self.points_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите точку для удаления!")
            return

        row = indexes[0].row()
        if self.points_model.rowCount() <= 3:
            QMessageBox.warning(self, "Ошибка", "Минимум 3 точки для замкнутой фигуры!")
            return

        self.points_model.removeRow(row)

    def _update_table_counter(self):
        """Обновляет счётчик точек"""
        count = self.points_model.rowCount()
        self.points_counter.setText(f"Точек: {count}")

    # ------------------------------------------------------------------
    # Проверка корректности данных
    # ------------------------------------------------------------------
    def validate_form(self):
        obj_type = self.object_type_combobox.currentData()

        def check_fields(*fields):
            for f in fields:
                if not f.text().strip():
                    QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
                    return False
            return True

        # --- Проверяем силу тока ---
        if not self.current_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите силу тока!")
            return False
        try:
            current = float(self.current_input.text())
            if current < 0:
                QMessageBox.warning(self, "Ошибка", "Сила тока должна быть больше 0 А!")
                return False
        except ValueError:
            QMessageBox.warning(
                self, "Ошибка", "Введите корректное числовое значение силы тока!"
            )
            return False

        # --- Проверяем остальные поля ---
        if obj_type == ObjectType.WIRE:
            if not check_fields(
                self.x1_input, self.y1_input, self.x2_input, self.y2_input
            ):
                return False
            try:
                x1 = float(self.x1_input.text())
                y1 = float(self.y1_input.text())
                x2 = float(self.x2_input.text())
                y2 = float(self.y2_input.text())
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите корректные координаты!")
                return False
            if x1 == x2 and y1 == y2:
                QMessageBox.warning(
                    self, "Ошибка", "Начальная и конечная точки совпадают!"
                )
                return False

        elif obj_type == ObjectType.POINT_WIRE:
            if not check_fields(self.x_input, self.y_input):
                return False

        elif obj_type == ObjectType.RING:
            if not check_fields(self.x_input, self.y_input, self.radius_input):
                return False
            try:
                r = float(self.radius_input.text())
                if r <= 0:
                    QMessageBox.warning(self, "Ошибка", "Радиус должен быть больше 0!")
                    return False
            except ValueError:
                QMessageBox.warning(
                    self, "Ошибка", "Введите корректное значение радиуса!"
                )
                return False

        elif obj_type == ObjectType.ARBITRARY_FIGURE:
            if not hasattr(self, "points_model"):
                QMessageBox.warning(
                    self, "Ошибка", "Не инициализирована таблица точек!"
                )
                return False

            row_count = self.points_model.rowCount()
            if row_count < 3:
                QMessageBox.warning(self, "Ошибка", "Нужно минимум 3 точки!")
                return False

            for row in range(row_count):
                for col in range(2):  # x и y
                    item = self.points_model.item(row, col)
                    if not item or not item.text().strip():
                        QMessageBox.warning(
                            self,
                            "Ошибка",
                            f"Пустое значение в точке {row+1}, координата {
                                'x' if col == 0 else 'y'}",
                        )
                        return False

                    try:
                        float(item.text())
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Ошибка",
                            f"Некорректное число в точке {row+1}, координата {
                                'x' if col == 0 else 'y'}:\n'{item.text()}'",
                        )
                        return False

        return True

    # ------------------------------------------------------------------
    # Создание объекта
    # ------------------------------------------------------------------
    def create_object_wrapper(self):
        if not self.validate_form():
            return

        self.add_object_by_input(self.object_type_combobox.currentData())

    def on_object_type_changed(self, index: int) -> None:
        """Реакция на смену выбранного типа объекта в форме."""
        if index < 0:
            return

        obj_type = self.object_type_combobox.itemData(index)
        if obj_type is None:
            return

        self.controller.canvas.set_object_type(obj_type)

    def add_object_by_input(self, obj_type):
        params = {}

        try:
            current = float(self.current_input.text())

            if obj_type == ObjectType.WIRE:
                params = dict(
                    current=current,
                    x1=float(self.x1_input.text()),
                    y1=float(self.y1_input.text()),
                    x2=float(self.x2_input.text()),
                    y2=float(self.y2_input.text()),
                )

            elif obj_type == ObjectType.POINT_WIRE:
                params = dict(
                    current=current,
                    x=float(self.x_input.text()),
                    y=float(self.y_input.text()),
                    direction=self.direction_input.currentText(),
                )

            elif obj_type == ObjectType.RING:
                params = dict(
                    current=current,
                    x=float(self.x_input.text()),
                    y=float(self.y_input.text()),
                    r=float(self.radius_input.text()),
                    direction=self.direction_input.currentText(),
                )

            elif obj_type == ObjectType.ARBITRARY_FIGURE:
                points = []
                for row in range(self.points_model.rowCount()):
                    x_item = self.points_model.item(row, 0)
                    y_item = self.points_model.item(row, 1)
                    if x_item and y_item:
                        points.append((float(x_item.text()), float(y_item.text())))

                params = dict(
                    current=current,
                    points=points,
                    direction=self.direction_input.currentText(),
                )

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числовые значения!")
            return

        self.controller.add_object(obj_type, params)
