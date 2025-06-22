from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QPushButton, QFrame, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QSoundEffect
from app.widgets.cell import NotebookCell
from app.storage import save_notebook, load_notebook
import sys
import os


def show_loading_screen(app, window, on_finish):
    loading = QWidget()
    loading.setStyleSheet("background-color: #0d0d0d;")
    layout = QVBoxLayout()
    label = QLabel("<span style='color:#33ff66; font-size:32px; font-family:Courier New,monospace;'>RETRO NOTEBOOK<br>Loading<span id='cursor'>_</span></span>")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    loading.setLayout(layout)
    loading.setWindowTitle("Retro Notebook - Loading")
    loading.resize(500, 300)
    loading.show()

    # Soundeffekt für Startscreen
    sound = QSoundEffect()
    start_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "start.wav")
    sound.setSource(f"file://{os.path.abspath(start_path)}")
    sound.setVolume(1.25)
    sound.play()

    # Blinker für Cursor
    def blink():
        html = label.text()
        if "_</span>" in html:
            label.setText(html.replace("_</span>", "</span>"))
        else:
            label.setText(html.replace("</span>", "_</span>"))
    timer = QTimer()
    timer.timeout.connect(blink)
    timer.start(500)

    def finish():
        timer.stop()
        loading.close()
        on_finish()

    QTimer.singleShot(1800, finish)


def start_app():
    app = QApplication(sys.argv)

    # Retro-Style laden
    with open("assets/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = QWidget()
    window.setWindowTitle("Retro Notebook")

    def show_main():
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
        def add_cell(cell_type="Code", input_text="", output_text=""):
            cell = NotebookCell(cell_type)
            cell.input.setPlainText(input_text)
            if cell_type == "Code" and output_text:
                cell.output.setText(output_text)
            scroll_layout.addWidget(cell)
            cells.append(cell)

        # Erste Zelle automatisch hinzufügen
        add_cell()

        # Button für neue Zelle
        new_cell_button = QPushButton("Neue Zelle")
        new_cell_button.clicked.connect(lambda: add_cell())

        layout.addWidget(new_cell_button)

        # Buttons zum Speichern und Laden des Notebooks
        save_button = QPushButton("Speichern")
        load_button = QPushButton("Laden")

        layout.addWidget(save_button)
        layout.addWidget(load_button)

        # About-Button
        about_button = QPushButton("About")
        def show_about():
            msg = QMessageBox(window)
            msg.setWindowTitle("About Retro Notebook")
            msg.setText(
                """
<pre style='color:#33ff66; background:#0d0d0d; font-family:Courier New,monospace;'>
RETRO NOTEBOOK v1.0
(c) 2025 by Jakob Szarkowicz

A retro-inspired notebook for code, math & learning.

ASCII-Design, Sound, und mehr!

https://github.com/sharkofwitch/retro-notebook
This project is licensed under the MIT License.
</pre>
                """
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
        about_button.clicked.connect(show_about)
        layout.addWidget(about_button)

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
                    cell_type = cell_data.get("type", "Code").capitalize()
                    input_text = cell_data.get("input", "")
                    output_text = cell_data.get("output", "")
                    add_cell(cell_type, input_text, output_text)
            except FileNotFoundError:
                print("Keine gespeicherte Datei gefunden.")

        # Verbinden der Buttons mit den Funktionen
        save_button.clicked.connect(on_save)
        load_button.clicked.connect(on_load)

        # Setzen des Layouts für das Hauptfenster
        window.setLayout(layout)
        window.resize(800, 600)
        window.show()

    show_loading_screen(app, window, show_main)
    sys.exit(app.exec())