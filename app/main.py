from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.widgets.cell import NotebookCell
import sys

def start_app():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Retro Notebook")

    layout = QVBoxLayout()

    # Scroll-Bereich für die Zellen
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Container-Widget im Scrollbereich
    scroll_content = QFrame()
    scroll_layout = QVBoxLayout()
    scroll_content.setLayout(scroll_layout)

    scroll_area.setWidget(scroll_content)
    layout.addWidget(scroll_area)

    # Liste von Zellen
    cells = []

    def add_cell():
        cell = NotebookCell()
        scroll_layout.addWidget(cell)
        cells.append(cell)

    # Erste Zelle automatisch hinzufügen
    add_cell()

    # Button für neue Zelle
    new_cell_button = QPushButton("Neue Zelle")
    new_cell_button.clicked.connect(add_cell)
    layout.addWidget(new_cell_button)

    window.setLayout(layout)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())