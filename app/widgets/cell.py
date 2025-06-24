from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QInputDialog, QHBoxLayout  # QHBoxLayout ergänzt
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.interpreter import RetroInterpreter
import markdown2
import os
import sys
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient
import math

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

class NotebookCell(QWidget):
    def __init__(self, cell_type="Code"):
        super().__init__()

        self.layout = QVBoxLayout()
        self.setProperty('dragged', False)  # Für visuelles Feedback

        # Drag-Handle (Griff) hinzufügen
        self.outer_layout = QHBoxLayout()
        self.drag_handle = QLabel("≡")
        self.drag_handle.setFixedWidth(24)
        self.drag_handle.setAlignment(Qt.AlignCenter)
        self.drag_handle.setStyleSheet('color: #888; font-size: 22px; padding: 0 4px;')
        self.outer_layout.addWidget(self.drag_handle)
        self.inner_layout = QVBoxLayout()

        # Zellentyp-Auswahl
        self.cell_type = QComboBox()
        self.cell_type.addItems(["Code", "Markdown"])
        self.cell_type.setCurrentText(cell_type)
        self.inner_layout.addWidget(self.cell_type)

        # Eingabe mehrzeilig
        self.input = QTextEdit()
        self.inner_layout.addWidget(self.input)

        # Ausführen-Button (immer sichtbar)
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.execute)
        self.inner_layout.addWidget(self.run_button)

        # Ausgabe (initial leer)
        self.output = QLabel("")
        self.inner_layout.addWidget(self.output)

        self.outer_layout.addLayout(self.inner_layout)
        self.layout.addLayout(self.outer_layout)
        self.setLayout(self.layout)
        self.interpreter = RetroInterpreter()

        # Soundeffekt vorbereiten
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        beep_path = resource_path("assets/beep.wav")
        self.player.setSource(f"file://{os.path.abspath(beep_path)}")
        self.audio_output.setVolume(0.25)

        # Retro-Animation: Rahmen, Scanlines, Icons
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update)
        self.anim_timer.start(60)
        self.anim_phase = 0

    def execute(self):
        # Status auf "Läuft..." setzen, falls möglich
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'set_status'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'set_status'):
            main_window.set_status('#ffff00', 'Läuft...')
        self.player.stop()  # Falls noch ein Sound läuft
        self.player.play()
        if self.cell_type.currentText() == "Markdown":
            md = self.input.toPlainText()
            html = markdown2.markdown(md)
            self.output.setText(html)
            if main_window and hasattr(main_window, 'set_status'):
                main_window.set_status('#33ff66', 'Bereit')
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
            error_found = False
            for result in flat_results:
                if isinstance(result, dict) and 'graphics' in result:
                    graphics.extend(result['graphics'])
                elif isinstance(result, str) and result.startswith('Error'):
                    text_results.append(result)
                    error_found = True
                elif result:
                    text_results.append(str(result))
            self.output.setText("\n".join(text_results))
            if graphics:
                self.show_graphics(graphics)
            # Status nach Ausführung setzen
            if main_window and hasattr(main_window, 'set_status'):
                if error_found:
                    main_window.set_status('#ff3333', 'Fehler beim Ausführen')
                else:
                    main_window.set_status('#33ff66', 'Bereit')

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

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Glow-Rahmen
        for i in range(1, 4):
            qp.setPen(QPen(QColor(51,255,102, 18//i), 6+2*i))
            qp.drawRoundedRect(2-i, 2-i, w-4+2*i, h-4+2*i, 12+i, 12+i)
        qp.setPen(QPen(QColor('#33ff66'), 2))
        qp.drawRoundedRect(2, 2, w-4, h-4, 12, 12)
        # Scanlines
        for y in range(8, h-8, 4):
            y_off = y + (self.anim_phase % 8)
            color = QColor(30,30,30,60)
            if y%16==0:
                color = QColor('#33ff66') if (y//16)%2==0 else QColor('#ffe066')
                color.setAlpha(40)
            qp.setPen(QPen(color, 1))
            qp.drawLine(8, y_off, w-8, y_off)
        # CRT-Vignette (korrekt mit QLinearGradient)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(0,0,0,80))
        grad.setColorAt(0.5, QColor(0,0,0,0))
        grad.setColorAt(1, QColor(0,0,0,80))
        qp.setBrush(grad)
        qp.setPen(Qt.PenStyle.NoPen)
        qp.drawRoundedRect(2, 2, w-4, h-4, 12, 12)
        # Disketten-Icon (unten rechts)
        t = self.anim_phase
        dx = int(w-36+math.sin(t/11)*2)
        dy = int(h-36+math.cos(t/13)*2)
        qp.setBrush(QColor('#33ff66'))
        qp.setPen(QPen(QColor('#222'), 2))
        qp.drawRect(dx, dy, 18, 18)
        qp.setBrush(QColor('#ffe066'))
        qp.drawRect(dx+6, dy+9, 6, 6)
        # Cursor-Icon (oben links, blinkt)
        if (self.anim_phase//10)%2 == 0:
            qp.setPen(QPen(QColor('#ff33cc'), 2))
            qp.drawLine(12, 12, 22, 22)
            qp.drawLine(22, 22, 18, 22)
            qp.drawLine(22, 22, 22, 18)
        self.anim_phase += 1
        qp.end()