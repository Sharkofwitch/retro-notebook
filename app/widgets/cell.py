from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QInputDialog
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
            results = self.interpreter.run_block(lines)
            # Ergebnisse flatten
            def flatten(items):
                for item in items:
                    if isinstance(item, list):
                        yield from flatten(item)
                    else:
                        yield item
            flat_results = list(flatten(results))
            graphics = []
            text_results = []
            for result in flat_results:
                if isinstance(result, dict) and 'graphics' in result:
                    graphics.extend(result['graphics'])
                elif result:
                    text_results.append(str(result))
            self.output.setText("\n".join(text_results))
            if graphics:
                self.show_graphics(graphics)

    def show_animation(self, frames):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt, QTimer
        size = 300
        dlg = QDialog(self)
        dlg.setWindowTitle("Animation")
        vbox = QVBoxLayout()
        label = QLabel()
        vbox.addWidget(label)
        dlg.setLayout(vbox)
        dlg.resize(size, size)
        pixmaps = []
        for graphics in frames:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.black)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(QColor('#33ff66'))
            for item in graphics:
                if item['type'] == 'point':
                    x = int(item['x'] * size / 100)
                    y = int(item['y'] * size / 100)
                    painter.drawEllipse(x-2, y-2, 4, 4)
                elif item['type'] == 'line':
                    x1 = int(item['x1'] * size / 100)
                    y1 = int(item['y1'] * size / 100)
                    x2 = int(item['x2'] * size / 100)
                    y2 = int(item['y2'] * size / 100)
                    painter.drawLine(x1, y1, x2, y2)
                elif item['type'] == 'circle':
                    x = int(item['x'] * size / 100)
                    y = int(item['y'] * size / 100)
                    r = int(item['r'] * size / 100)
                    painter.drawEllipse(x - r, y - r, 2*r, 2*r)
            painter.end()
            pixmaps.append(pixmap)
        # Animation abspielen
        idx = [0]
        def next_frame():
            label.setPixmap(pixmaps[idx[0]])
            idx[0] = (idx[0] + 1) % len(pixmaps)
        timer = QTimer()
        timer.timeout.connect(next_frame)
        timer.start(300)  # 300 ms pro Frame
        dlg.exec()
        timer.stop()

    def show_graphics(self, graphics):
        # Einfache Zeichenfläche als neues Fenster
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt
        size = 300
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.black)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor('#33ff66'))
        for item in graphics:
            if item['type'] == 'point':
                x = int(item['x'] * size / 100)
                y = int(item['y'] * size / 100)
                painter.drawEllipse(x-2, y-2, 4, 4)
            elif item['type'] == 'line':
                x1 = int(item['x1'] * size / 100)
                y1 = int(item['y1'] * size / 100)
                x2 = int(item['x2'] * size / 100)
                y2 = int(item['y2'] * size / 100)
                painter.drawLine(x1, y1, x2, y2)
            elif item['type'] == 'circle':
                x = int(item['x'] * size / 100)
                y = int(item['y'] * size / 100)
                r = int(item['r'] * size / 100)
                painter.drawEllipse(x - r, y - r, 2*r, 2*r)
        painter.end()
        dlg = QDialog(self)
        dlg.setWindowTitle("Grafik")
        vbox = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        vbox.addWidget(label)
        dlg.setLayout(vbox)
        dlg.exec()