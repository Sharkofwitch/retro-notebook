from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.interpreter import RetroInterpreter
import markdown2
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

class NotebookCell(QWidget):
    def __init__(self, cell_type="Code"):
        super().__init__()

        self.layout = QVBoxLayout()

        # Zellentyp-Auswahl
        self.cell_type = QComboBox()
        self.cell_type.addItems(["Code", "Markdown"])
        self.cell_type.setCurrentText(cell_type)
        self.layout.addWidget(self.cell_type)

        # Eingabe mehrzeilig
        self.input = QTextEdit()
        self.layout.addWidget(self.input)

        # Ausführen-Button (immer sichtbar)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.execute)
        self.layout.addWidget(self.run_button)

        # Ausgabe (initial leer)
        self.output = QLabel("")
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)
        self.interpreter = RetroInterpreter()

        # Soundeffekt vorbereiten
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        beep_path = resource_path("assets/beep.wav")
        self.player.setSource(f"file://{os.path.abspath(beep_path)}")
        self.audio_output.setVolume(0.25)

    def execute(self):
        self.player.stop()  # Falls noch ein Sound läuft
        self.player.play()
        if self.cell_type.currentText() == "Markdown":
            md = self.input.toPlainText()
            html = markdown2.markdown(md)
            self.output.setText(html)
        else:
            code = self.input.toPlainText()
            lines = code.splitlines()
            results = [self.interpreter.run_line(line) for line in lines]
            self.output.setText("\n".join(f"→ {r}" for r in results if r))