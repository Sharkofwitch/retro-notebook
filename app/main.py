from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.widgets.cell import NotebookCell
from app.storage import save_notebook, load_notebook
import sys

def start_app():
    app = QApplication(sys.argv)

    # Retro-Style laden
    with open("assets/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    # Hauptfenster erstellen
    window = QWidget()
    window.setWindowTitle("Retro Notebook")

    # Layout für das Hauptfenster
    layout = QVBoxLayout()

    # Scroll-Bereich für die Zellen
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Container-Widget im Scrollbereich
    scroll_content = QFrame()
    scroll_layout = QVBoxLayout()
    scroll_content.setLayout(scroll_layout)

    # Setzen des Scroll-Inhalts
    scroll_area.setWidget(scroll_content)
    layout.addWidget(scroll_area)

    # Liste von Zellen
    cells = []

    # Funktion zum Hinzufügen einer neuen Zelle
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

    # Buttons zum Speichern und Laden des Notebooks
    save_button = QPushButton("Speichern")
    load_button = QPushButton("Laden")

    layout.addWidget(save_button)
    layout.addWidget(load_button)

    # Save/Load-Handler
    NOTEBOOK_FILE = "notebooks/auto_save.json"

    # Funktion zum Speichern des Notebooks
    def on_save():
        save_notebook(cells, NOTEBOOK_FILE)

    # Funktion zum Laden des Notebooks
    def on_load():
        try:
            data = load_notebook(NOTEBOOK_FILE)
            # Vorherige Zellen entfernen
            for i in reversed(range(scroll_layout.count())):
                scroll_layout.itemAt(i).widget().setParent(None)
            cells.clear()
            # Neue Zellen anlegen
            for cell_data in data:
                cell = NotebookCell()
                cell.input.setPlainText(cell_data["input"])
                cell.output.setText(cell_data["output"])
                scroll_layout.addWidget(cell)
                cells.append(cell)
        except FileNotFoundError:
            print("Keine gespeicherte Datei gefunden.")

    # Verbinden der Buttons mit den Funktionen
    save_button.clicked.connect(on_save)
    load_button.clicked.connect(on_load)

    # Setzen des Layouts für das Hauptfenster
    window.setLayout(layout)
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())