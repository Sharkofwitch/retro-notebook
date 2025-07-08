from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollArea,
    QPushButton, QFrame, QLabel, QMessageBox, QHBoxLayout, QDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from app.widgets.cell import NotebookCell
from app.storage import save_notebook, load_notebook
from PySide6.QtGui import QCursor, QKeyEvent
import sys
import os
import random
from app.minigame import show_minigame


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def show_loading_screen(app, window, on_finish):
    loading = QWidget()
    loading.setStyleSheet("background-color: #0d0d0d;")
    layout = QVBoxLayout()
    label = QLabel("<span style='color:#33ff66; font-size:32px; font-family:Courier New,monospace;'>RETRO NOTEBOOK<br>Loading<span id='cursor'>_</span></span>")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    loading.setLayout(layout)
    loading.setWindowTitle("Retro Notebook - Loading")
    loading.resize(500, 300)
    loading.show()

    # Soundeffekt für Startscreen mit QMediaPlayer
    loading.player = QMediaPlayer()
    loading.audio_output = QAudioOutput()
    loading.player.setAudioOutput(loading.audio_output)
    start_path = resource_path("assets/start.mp3")
    loading.player.setSource(f"file://{os.path.abspath(start_path)}")
    loading.audio_output.setVolume(0.25)
    loading.player.play()

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

    QTimer.singleShot(3000, finish)


def show_homepage(app, window, on_start_notebook):
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGraphicsOpacityEffect
    from PySide6.QtCore import Qt, QTimer, QPropertyAnimation
    from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPixmap, QLinearGradient
    import random, math
    class RetroNotebookWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setFixedSize(600, 200)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update)
            self.timer.start(40)
            self.phase = 0
            self.scanline_offset = 0
            self.pixels = [[random.randint(40, 560), random.randint(40, 180), random.choice(['#33ff66','#ffe066','#ff33cc','#00ff99'])] for _ in range(32)]
        def paintEvent(self, event):
            qp = QPainter(self)
            qp.setRenderHint(QPainter.RenderHint.Antialiasing)
            # CRT-Verzerrung (leichtes Wellenmuster)
            for y in range(20, 180, 2):
                offset = int(4*math.sin(self.phase/13 + y/18))
                qp.setPen(QPen(QColor('#0d0d0d'), 2))
                qp.drawLine(30+offset, y, 570-offset, y)
            # Retro-Notebook-Rahmen mit Glow
            for i in range(1, 7):
                qp.setPen(QPen(QColor(51,255,102, 22//i), 10+2*i))
                qp.drawRoundedRect(30-i*2, 20-i*2, 540+i*4, 160+i*4, 24+i*2, 24+i*2)
            qp.setBrush(QColor('#181c1b'))
            qp.setPen(QPen(QColor('#33ff66'), 4))
            qp.drawRoundedRect(30, 20, 540, 160, 24, 24)
            # Animierte Tabs oben
            for i, color in enumerate(['#33ff66','#ffe066','#ff33cc']):
                glow = QColor(color).lighter(100+int(20*math.sin(self.phase/7+i)))
                qp.setBrush(glow)
                qp.setPen(Qt.PenStyle.NoPen)
                qp.drawRoundedRect(60+60*i, 8, 48, 18, 6, 6)
            # Farbige, wandernde Scanlines
            for y in range(24, 180, 4):
                y_off = y + (self.phase % 8)
                color = QColor(30,30,30,80)
                if y%16==0:
                    color = QColor('#33ff66') if (y//16)%2==0 else QColor('#ffe066')
                    color.setAlpha(60)
                qp.setPen(QPen(color, 2))
                qp.drawLine(32, y_off, 568, y_off)
            # Animierte Pixel (Notebook-Glitch)
            for i, (x, y, c) in enumerate(self.pixels):
                px = int(x + 4*math.sin(self.phase/8 + i))
                py = int(y + 2*math.cos(self.phase/11 + i))
                qp.setPen(QPen(QColor(c), 1))
                qp.setBrush(QColor(c))
                qp.drawEllipse(px, py, 6, 6)
            # Pixel-Notizbuchseiten (animiert)
            for i in range(4):
                y = 44 + i*28 + int(2*math.sin(self.phase/7+i))
                qp.setBrush(QColor('#222'))
                qp.setPen(QPen(QColor('#ffe066'), 2))
                qp.drawRoundedRect(90, y, 320, 18, 4, 4)
                qp.setPen(QPen(QColor('#33ff66'), 1))
                for lx in range(0, 320, 32):
                    qp.drawLine(90+lx, y+4, 90+lx, y+14)
            # Disketten-Icon (animiert)
            t = self.phase
            dx = int(480+math.sin(t/11)*2)
            dy = int(120+math.cos(t/13)*2)
            qp.setBrush(QColor('#33ff66'))
            qp.setPen(QPen(QColor('#222'), 2))
            qp.drawRect(dx, dy, 24, 24)
            qp.setBrush(QColor('#ffe066'))
            qp.drawRect(dx+8, dy+12, 8, 8)
            # Cursor-Icon (blinkt)
            if (self.phase//10)%2 == 0:
                qp.setPen(QPen(QColor('#ff33cc'), 3))
                qp.drawLine(320, 60, 332, 72)
                qp.drawLine(332, 72, 328, 72)
                qp.drawLine(332, 72, 332, 68)
            # Stern-Icon
            qp.setPen(QColor('#ffe066'))
            for i in range(5):
                angle = i * 2 * math.pi / 5
                x1 = int(540 + 12 * math.cos(angle))
                y1 = int(40 + 12 * math.sin(angle))
                x2 = int(540 + 5 * math.cos(angle + math.pi/5))
                y2 = int(40 + 5 * math.sin(angle + math.pi/5))
                qp.drawLine(540, 40, x1, y1)
                qp.drawLine(540, 40, x2, y2)
            # Glitch-Overlay (subtil)
            if self.phase%23==0:
                qp.setOpacity(0.18)
                qp.setBrush(QColor('#ff33cc'))
                qp.drawRect(30, 20, 540, 160)
                qp.setOpacity(1.0)
            # CRT-Vignette
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0, QColor(0,0,0,120))
            grad.setColorAt(0.5, QColor(0,0,0,0))
            grad.setColorAt(1, QColor(0,0,0,120))
            qp.setBrush(QBrush(grad))
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRoundedRect(30, 20, 540, 160, 24, 24)
            # Notebook-Glow
            qp.setOpacity(0.10)
            qp.setBrush(QColor(255,255,255,80))
            qp.drawEllipse(120, 30, 360, 30)
            qp.setOpacity(1.0)
            self.phase += 1
    homepage = QWidget()
    homepage.setStyleSheet("background-color: #0d0d0d;")
    layout = QVBoxLayout()
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # Header mit animiertem Farbverlauf und Glitch
    header = QLabel("RETRO NOTEBOOK")
    header.setStyleSheet("color:#33ff66; font-size:54px; font-family:Courier New,monospace; text-shadow: 0 0 16px #33ff66;")
    header.setAlignment(Qt.AlignmentFlag.AlignCenter)
    effect = QGraphicsOpacityEffect()
    header.setGraphicsEffect(effect)
    anim_logo = QPropertyAnimation(effect, b"opacity")
    anim_logo.setDuration(1200)
    anim_logo.setStartValue(0)
    anim_logo.setEndValue(1)
    anim_logo.start()
    def header_glitch():
        txt = "RETRO NOTEBOOK"
        if random.random() < 0.18:
            idx = random.randint(0, len(txt)-1)
            glitched = txt[:idx] + '<span style="color:#ffe066;">'+txt[idx]+'</span>' + txt[idx+1:]
            header.setText(glitched)
        else:
            header.setText(txt)
    glitch_timer = QTimer()
    glitch_timer.timeout.connect(header_glitch)
    glitch_timer.start(400)
    layout.addWidget(header)
    # Animiertes Retro-Notebook
    retro_notebook = RetroNotebookWidget()
    layout.addWidget(retro_notebook)
    # "Press Start" animiert + Flackern
    press_start = QLabel("<span style='color:#ffe066; font-size:22px; font-family:Courier New;'>Press Start</span>")
    press_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(press_start)
    def blink():
        if press_start.isVisible():
            press_start.setVisible(False)
        else:
            press_start.setVisible(True)
    blink_timer = QTimer()
    blink_timer.timeout.connect(blink)
    blink_timer.start(600)
    # Buttons mit Fade-In + Flackern
    start_btn = QPushButton("Start")
    start_btn.setStyleSheet("background:#262626; color:#33ff66; font-size:22px; padding:12px 32px; border:2px solid #33ff66; border-radius:8px;")
    minigame_btn = QPushButton("Minigame")
    minigame_btn.setStyleSheet("background:#262626; color:#00ff99; font-size:18px; padding:8px 24px; border:2px solid #00ff99; border-radius:8px;")
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_row.addWidget(start_btn)
    btn_row.addSpacing(24)
    btn_row.addWidget(minigame_btn)
    btn_row.addStretch()
    def btn_flicker(btn, base_color):
        c = QColor(base_color)
        c = c.lighter(random.randint(90,120))
        btn.setStyleSheet(f"background:#262626; color:{c.name()}; font-size:22px; padding:12px 32px; border:2px solid {c.name()}; border-radius:8px;")
    btn_timer = QTimer()
    def update_btns():
        btn_flicker(start_btn, '#33ff66')
        btn_flicker(minigame_btn, '#00ff99')
    btn_timer.timeout.connect(update_btns)
    btn_timer.start(180)
    for btn in [start_btn, minigame_btn]:
        eff = QGraphicsOpacityEffect()
        btn.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(1200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()
    layout.addLayout(btn_row)
    credits = QLabel("<span style='color:#888;font-size:14px;'>by Jakob Szarkowicz · 2025</span>")
    credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(credits)
    homepage.setLayout(layout)
    homepage.setWindowTitle("Retro Notebook - Home")
    homepage.resize(600, 440)
    homepage.show()
    def start():
        homepage.close()
        on_start_notebook()
    start_btn.clicked.connect(start)
    homepage.keyPressEvent = lambda e: start()
    homepage.mousePressEvent = lambda e: start()
    minigame_btn.clicked.connect(lambda: show_minigame(homepage))


def start_app():
    app = QApplication(sys.argv)

    # Retro-Style laden
    with open(resource_path("assets/style.qss"), "r") as f:
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
RETRO NOTEBOOK v1.2
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

        # Zurück-zum-Menü-Button
        back_button = QPushButton("Zurück zum Hauptmenü")
        back_button.setStyleSheet('font-size:18px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:8px 24px;')
        def go_home():
            window.close()
            show_homepage(app, window, show_main)
        back_button.clicked.connect(go_home)
        layout.addWidget(back_button)

        # Statusleiste/LED unten hinzufügen
        status_layout = QHBoxLayout()
        status_led = QLabel()
        status_led.setFixedSize(16, 16)
        status_led.setStyleSheet('background: #33ff66; border-radius: 8px; border: 2px solid #222;')
        status_text = QLabel('Bereit')
        status_text.setStyleSheet('color: #33ff66; font-family: Courier New, monospace; font-size: 16px;')
        status_layout.addWidget(status_led)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Methode zum Setzen des Status
        def set_status(color, text):
            status_led.setStyleSheet(f'background: {color}; border-radius: 8px; border: 2px solid #222;')
            status_text.setText(text)

        # Status-Setter global verfügbar machen
        window.set_status = set_status

        # Beispiel: Status bei Start
        set_status('#33ff66', 'Bereit')

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

        # Drag & Drop für Zellen aktivieren
        scroll_content.setAcceptDrops(True)
        class DraggableCell(NotebookCell):
            def __init__(self, cell_type="Code"):
                super().__init__(cell_type)
                self.drag_handle.setObjectName("drag_handle")
                self.drag_handle.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
                self.drag_handle.mousePressEvent = self.handle_mouse_press
                self.drag_handle.mouseMoveEvent = self.handle_mouse_move
                self.drag_handle.mouseReleaseEvent = self.handle_mouse_release
                self._drag_active = False
                self.drag_start_pos = None
            def handle_mouse_press(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_start_pos = event.pos()
                    self.drag_handle.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            def handle_mouse_move(self, event):
                if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos:
                    if (event.pos() - self.drag_start_pos).manhattanLength() > 10:
                        from PySide6.QtGui import QDrag, QPixmap
                        from PySide6.QtCore import QMimeData
                        drag = QDrag(self)
                        mime = QMimeData()
                        mime.setText('cell')
                        drag.setMimeData(mime)
                        pixmap = QPixmap(self.size())
                        self.setProperty('dragged', True)
                        self.style().unpolish(self)
                        self.style().polish(self)
                        self.render(pixmap)
                        drag.setPixmap(pixmap)
                        drag.exec()
                        self.setProperty('dragged', False)
                        self.style().unpolish(self)
                        self.style().polish(self)
            def handle_mouse_release(self, event):
                self.drag_handle.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            def mousePressEvent(self, event):
                super().mousePressEvent(event)
            def mouseMoveEvent(self, event):
                super().mouseMoveEvent(event)
        def add_cell(cell_type="Code", input_text="", output_text=""):
            cell = DraggableCell(cell_type)
            cell.input.setPlainText(input_text)
            if cell_type == "Code" and output_text:
                cell.output.setText(output_text)
            scroll_layout.addWidget(cell)
            cells.append(cell)
        # Drag & Drop Handler für das Scroll-Content
        def move_cell(from_idx, to_idx):
            if from_idx == to_idx or from_idx < 0 or to_idx < 0 or from_idx >= len(cells) or to_idx >= len(cells):
                return
            cell = cells.pop(from_idx)
            cells.insert(to_idx, cell)
            scroll_layout.insertWidget(to_idx, cell)
        # Einfüge-Indikator
        insert_line = QLabel()
        insert_line.setFixedHeight(4)
        insert_line.setStyleSheet('background: #33ff66; border-radius: 2px;')
        insert_line.hide()
        scroll_content.insert_line = insert_line
        scroll_layout.addWidget(insert_line)
        def show_insert_line(pos):
            insert_line.hide()
            for idx, cell in enumerate(cells):
                if cell.geometry().contains(pos):
                    scroll_layout.insertWidget(idx, insert_line)
                    insert_line.show()
                    return idx
            insert_line.hide()
            return None
        scroll_content.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasText() else e.ignore()
        def dragMoveEvent(e):
            pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
            show_insert_line(pos)
            e.accept()
        scroll_content.dragMoveEvent = dragMoveEvent
        scroll_content.dropEvent = lambda e: handle_drop(e)
        def handle_drop(e):
            pos = e.position().toPoint() if hasattr(e, 'position') else e.pos()
            to_idx = show_insert_line(pos)
            insert_line.hide()
            for idx, cell in enumerate(cells):
                if cell.geometry().contains(pos):
                    from_idx = cells.index(e.source())
                    if to_idx is not None:
                        move_cell(from_idx, to_idx)
                    break
            e.accept()

        # Setzen des Layouts für das Hauptfenster
        window.setLayout(layout)
        window.resize(800, 600)
        window.show()

    def show_home():
        show_homepage(app, window, show_main)
    show_loading_screen(app, window, show_home)
    sys.exit(app.exec())