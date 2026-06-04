from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.objects import (
    ArbitraryFigure,
    CircleDirection,
    MagneticObject,
    PointDirection,
    PointWire,
    Ring,
    StraightWire,
)

# from gui.controller import Controller


class ObjectCard(QFrame):
    """Custom widget for information about objects on a canvas"""

    # Signal emitted when delete button is clicked, carrying the index
    delete_clicked = pyqtSignal(int)
    remove_temp_object = pyqtSignal()
    set_temp_object = pyqtSignal(MagneticObject)

    def __init__(self, object: MagneticObject, index: int, parent=None):
        super().__init__(parent)
        self.payload = object
        self.index = index

        self.setup_ui()
        self.reset_styles()

    def setup_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        # Text content layout (left side)
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(4)

        # Title label
        self.title_label = QLabel(f"<b>{self.payload.name}</b>")
        self.title_label.setStyleSheet("font-size: 14px;")

        # Content label with rich text support - show detailed properties
        content_text = self._generate_content_text()
        self.content_label = QLabel(content_text)
        self.content_label.setTextFormat(Qt.TextFormat.RichText)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("font-size: 12px;")

        self.text_layout.addWidget(self.title_label)
        self.text_layout.addWidget(self.content_label)

        self.delete_btn = QPushButton("×")  # Using multiplication sign as close icon
        self.delete_btn.hide()  # Initially hidden
        self.delete_btn.clicked.connect(self.on_delete_clicked)

        # Add layouts to main layout
        main_layout.addLayout(self.text_layout, 1)  # Text takes most space
        main_layout.addWidget(
            self.delete_btn,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignHCenter,
        )

    def _generate_content_text(self) -> str:
        """Generate formatted content text based on object type"""
        obj = self.payload

        if isinstance(obj, StraightWire):
            return self._format_straight_wire_content(obj)
        elif isinstance(obj, Ring):
            return self._format_ring_content(obj)
        elif isinstance(obj, PointWire):
            return self._format_point_wire_content(obj)
        elif isinstance(obj, ArbitraryFigure):
            # у меня не получилось это релизнуть
            return self._format_arbitrary_figure_content(obj)
        else:
            return f"Тип: {type(obj).__name__}<br>Ток: {obj.current} A"

    def _format_straight_wire_content(self, wire: StraightWire) -> str:
        """Format content for StraightWire"""
        return f"""
        <b>Тип:</b> Прямой провод<br>
        <b>Ток:</b> {wire.current} А<br>
        <b>Точка 1:</b> ({wire.x1:.2f}, {wire.y1:.2f})<br>
        <b>Точка 2:</b> ({wire.x2:.2f}, {wire.y2:.2f})<br>
        """

    def _format_ring_content(self, ring: Ring) -> str:
        """Format content for Ring"""
        direction_text = (
            "По часовой"
            if ring.direction == str(CircleDirection.CLOCKWISE)
            else "Против часовой"
        )
        return f"""
        <b>Тип:</b> Кольцо<br>
        <b>Ток:</b> {ring.current} А<br>
        <b>Центр:</b> ({ring.x:.2f}, {ring.y:.2f})<br>
        <b>Радиус:</b> {ring.r:.2f}<br>
        <b>Направление:</b> {direction_text}<br>
        """

    def _format_point_wire_content(self, point: PointWire) -> str:
        """Format content for PointWire"""
        direction_text = (
            "К нам" if point.direction == str(PointDirection.TO_US) else "От нас"
        )
        return f"""
        <b>Тип:</b> Перпендикуляр<br>
        <b>Ток:</b> {point.current} А<br>
        <b>Положение:</b> ({point.x:.2f}, {point.y:.2f})<br>
        <b>Направление:</b> {direction_text}<br>
        """

    def _format_arbitrary_figure_content(self, arbitrary: ArbitraryFigure) -> str:
        # Я пытался но у меня не получилось
        """Format content for ArbitraryFigure"""
        direction_text = (
            "По часовой"
            if arbitrary.direction == str(CircleDirection.CLOCKWISE)
            else "Против часовой"
        )
        return f"""
        <b>Тип:</b> Произвольная фигура<br>
        <b>Ток:</b> {arbitrary.current} А<br>
        <b>Направление:</b> {direction_text}<br>
        """

    def calculate_button_size(self):
        """Calculate button size based on card height"""
        card_height = self.height()
        button_size = min(card_height - 25, 40)
        return button_size

    def update_button_size(self):
        """Update the button size based on current card height"""
        button_size = self.calculate_button_size()
        self.delete_btn.setFixedSize(button_size, button_size)

        radius = button_size // 4
        self.delete_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0);
                color: red;
                border: 4px solid rgba(255, 0, 0, 1);
                border-radius: {radius}px;
                font-weight: bold;
                font-size: {button_size}px;
            }}
            QPushButton:hover {{
                background-color: #ff6666;
            }}
            QPushButton:pressed {{
                background-color: #cc3333;
            }}
        """
        )

    def resizeEvent(self, event):
        """Handle resize events to update button size"""
        super().resizeEvent(event)
        if self.delete_btn.isVisible():
            self.update_button_size()

    def on_delete_clicked(self):
        """Handle delete button click - emit signal with index"""
        self.delete_clicked.emit(self.index)
        self.remove_temp_object.emit()

    def reset_styles(self):
        self.setStyleSheet(
            """
            ObjectCard {
                background-color: rgba(0, 0, 0, 0.0);
                border: 2px solid rgba(124, 124, 124, 1.0);
                border-radius: 10px;
                margin: 2px;
            }
        """
        )
        self.delete_btn.hide()

    def enterEvent(self, event):
        """Handle hover enter"""
        self.set_temp_object.emit(self.payload)
        self.setStyleSheet(
            """
            ObjectCard {
                background-color: rgba(124, 124, 124, 1.0);
                border: 4px solid rgba(0, 0, 255, 1.0);
                border-radius: 10px;
                margin: 0px;
            }
        """
        )
        # Update button size before showing
        self.update_button_size()
        self.delete_btn.show()  # Show button on hover
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle hover leave"""
        self.remove_temp_object.emit()
        self.reset_styles()
        super().leaveEvent(event)


class ObjectCardsPanel(QWidget):
    """Scrollable panel containing object cards"""

    def __init__(self, objects_list: list[MagneticObject], parent=None):
        super().__init__(parent)
        self.objects_list = objects_list
        self.controller = None

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Container for scroll area content
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

    def update(self):
        """Remove all ObjectCard widgets and recreate still existing"""
        # Remove all existing cards from the layout
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child:
                widget = child.widget()
                if widget:
                    widget.deleteLater()

        # Add new cards for each object
        for index, obj in enumerate(self.objects_list):
            card = ObjectCard(obj, index)

            # Connect the card's delete signal to our handler
            if self.controller:
                card.delete_clicked.connect(self.controller.remove_object)
                card.set_temp_object.connect(self.controller.set_temporary_object)
                card.remove_temp_object.connect(self.controller.remove_temporary_object)

            self.scroll_layout.addWidget(card)

        super().update()
