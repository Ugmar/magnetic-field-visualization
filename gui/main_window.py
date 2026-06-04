import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

# Импортируем собственные модули
from gui.widgets.canvas import Canvas
from gui.widgets.object_form import ObjectForm

# from gui.controller import Controller


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Визуализация магнитного поля — прототип GUI")
        self.resize(1100, 700)

        # === Центральный виджет ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # === Основной layout ===
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # === Левая часть — холст ===
        self.canvas = Canvas()
        p = self.canvas.palette()
        p.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.canvas.setPalette(p)
        layout.addWidget(self.canvas, stretch=3)

        # === Правая часть — форма ===
        self.form = ObjectForm(self.canvas)
        layout.addWidget(self.form, stretch=1, alignment=Qt.AlignmentFlag.AlignRight)

        # === Контроллер ===

        # self.form.controller = self.controller  # привязка контроллера к форме


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
