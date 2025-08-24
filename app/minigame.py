from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPen
import random
import math

from app.codegrid import show_codegrid
from app.tetris import show_tetris

# Sudoku is imported lazily in start_sudoku() to avoid import-time failures


class MinigameMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RETRO NOTEBOOK – Minispiele")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")

        vbox = QVBoxLayout()
        vbox.setContentsMargins(24, 24, 24, 24)

        # Animated retro frame widget
        class RetroFrame(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setMinimumHeight(260)
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update)
                self.timer.start(50)
                self.phase = 0

            def paintEvent(self, event):
                qp = QPainter(self)
                qp.setRenderHint(QPainter.RenderHint.Antialiasing)
                # Glow border
                for i in range(1, 6):
                    qp.setPen(QPen(QColor(51, 255, 102, 22 // i), 8 + 2 * i))
                    qp.drawRoundedRect(
                        8 - i * 2, 8 - i * 2, self.width() - 16 + i * 4, self.height() - 16 + i * 4, 18 + i * 2, 18 + i * 2
                    )
                qp.setBrush(QColor('#181c1b'))
                qp.setPen(QPen(QColor('#33ff66'), 3))
                qp.drawRoundedRect(8, 8, self.width() - 16, self.height() - 16, 18, 18)
                # Scanlines
                for y in range(16, self.height() - 16, 4):
                    y_off = y + (self.phase % 8)
                    color = QColor(30, 30, 30, 80)
                    if y % 16 == 0:
                        color = QColor('#33ff66') if (y // 16) % 2 == 0 else QColor('#ffe066')
                        color.setAlpha(60)
                    qp.setPen(QPen(color, 2))
                    qp.drawLine(16, y_off, self.width() - 16, y_off)
                # Disk icon
                t = self.phase
                dx = int(self.width() - 60 + math.sin(t / 11) * 2)
                dy = int(self.height() - 60 + math.cos(t / 13) * 2)
                qp.setBrush(QColor('#33ff66'))
                qp.setPen(QPen(QColor('#222'), 2))
                qp.drawRect(dx, dy, 24, 24)
                qp.setBrush(QColor('#ffe066'))
                qp.drawRect(dx + 8, dy + 12, 8, 8)
                # Cursor blink
                if (self.phase // 10) % 2 == 0:
                    qp.setPen(QPen(QColor('#ff33cc'), 3))
                    qp.drawLine(40, 40, 52, 52)
                    qp.drawLine(52, 52, 48, 52)
                    qp.drawLine(52, 52, 52, 48)
                # Subtle glitch
                if self.phase % 23 == 0:
                    qp.setOpacity(0.13)
                    qp.setBrush(QColor('#ff33cc'))
                    qp.drawRect(8, 8, self.width() - 16, self.height() - 16)
                    qp.setOpacity(1.0)
                self.phase += 1

        retro_frame = RetroFrame()
        retro_layout = QVBoxLayout(retro_frame)
        retro_layout.setContentsMargins(32, 32, 32, 32)

        # Title with glitch effect
        title = QLabel("RETRO NOTEBOOK – Minispiele")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet('font-size:28px; color:#33ff66;')

        def title_glitch():
            txt = "RETRO NOTEBOOK – Minispiele"
            if random.random() < 0.15:
                idx = random.randint(0, len(txt) - 1)
                glitched = txt[:idx] + '<span style="color:#ffe066;">' + txt[idx] + '</span>' + txt[idx + 1 :]
                title.setText(glitched)
            else:
                title.setText(txt)

        glitch_timer = QTimer()
        glitch_timer.timeout.connect(title_glitch)
        glitch_timer.start(400)
        retro_layout.addWidget(title)

        # Buttons
        btn_codegrid = QPushButton("CodeGrid – Logikpuzzle")
        btn_codegrid.setStyleSheet(
            'font-size:22px; padding:18px; background:#181c1b; color:#33ff66; border:2px solid #33ff66; border-radius:8px;'
        )
        btn_tetris = QPushButton("Tetris – Retro Klassiker")
        btn_tetris.setStyleSheet(
            'font-size:22px; padding:18px; background:#181c1b; color:#ff668c; border:2px solid #ff668c; border-radius:8px;'
        )
        btn_sudoku = QPushButton("Sudoku – Retro")
        btn_sudoku.setStyleSheet(
            'font-size:22px; padding:18px; background:#181c1b; color:#9fe2c0; border:2px solid #9fe2c0; border-radius:8px;'
        )
        help_btn = QPushButton("Was ist das?")
        help_btn.setStyleSheet(
            'font-size:18px; padding:10px; background:#181c1b; color:#ff33cc; border:2px solid #ff33cc; border-radius:8px;'
        )

        btns = [btn_codegrid, btn_tetris, btn_sudoku, help_btn]

        def btn_flicker(btn, base_color):
            c = QColor(base_color)
            c = c.lighter(random.randint(90, 120))
            btn.setStyleSheet(
                f"font-size:22px; padding:18px; background:#181c1b; color:{c.name()}; border:2px solid {c.name()}; border-radius:8px;"
            )

        btn_timer = QTimer()

        def update_btns():
            btn_flicker(btn_codegrid, '#33ff66')
            btn_flicker(btn_tetris, '#ff668c')
            btn_flicker(btn_sudoku, '#9fe2c0')
            btn_flicker(help_btn, '#ff33cc')

        btn_timer.timeout.connect(update_btns)
        btn_timer.start(180)

        retro_layout.addWidget(btn_codegrid)
        retro_layout.addWidget(btn_tetris)
        retro_layout.addWidget(btn_sudoku)
        retro_layout.addWidget(help_btn)
        retro_layout.addStretch()

        vbox.addWidget(retro_frame)
        self.setLayout(vbox)

        # Connect buttons
        btn_codegrid.clicked.connect(self.start_codegrid)
        btn_tetris.clicked.connect(self.start_tetris)
        btn_sudoku.clicked.connect(self.start_sudoku)
        help_btn.clicked.connect(self.show_help)

    def start_codegrid(self):
        self.accept()
        show_codegrid(self.parent())

    def start_tetris(self):
        self.accept()
        show_tetris(self.parent())

    def show_help(self):
        msg = QDialog(self)
        msg.setWindowTitle("Minispiele – Hilfe")
        v = QVBoxLayout()
        l = QLabel(
            "<b>CodeGrid – Logikpuzzle</b><br>"
            "Ziel: Mache das linke Grid identisch zum rechten Zielmuster.\n"
            "Nutze die Buttons, um Zeilen/Spalten zu verschieben, zu flippen oder zu tauschen.\n"
            "Jedes Level wird schwerer. Löse das Puzzle in möglichst wenigen Zügen!<br><br>"
            "<b>Bit Factory – Survival Builder</b><br>"
            "Baue eine funktionierende Retro-Fabrik auf einem Grid.\n"
            "Platziere Generatoren (Energie), Förderbänder (Transport), Speicher (lagern), Assembler (verarbeiten).\n"
            "Produziere Ressourcen, optimiere deine Fabrik und speichere deinen Fortschritt.\n"
            "Entspanntes Aufbauspiel ohne Zeitdruck – experimentiere und finde clevere Lösungen!<br><br>"
            "<b>Tetris – Retro Klassiker</b><br>"
            "Das beliebte Tetris-Spiel im Retro-Stil.\n"
            "Steuere die fallenden Blöcke, um vollständige Linien zu bilden und Punkte zu sammeln.\n"
            "Einfach zu lernen, aber schwer zu meistern! Wer erreichte die höchste Punktzahl?"
        )
        l.setWordWrap(True)
        l.setStyleSheet('font-size:18px; color:#ffe066;')
        v.addWidget(l)
        ok = QPushButton("OK")
        ok.clicked.connect(msg.accept)
        v.addWidget(ok)
        msg.setLayout(v)
        msg.exec()

    def start_sudoku(self):
        # lazy import to avoid breaking the menu if Sudoku has an import error
        try:
            from app.sudoku import Sudoku, should_auto_resume
        except Exception:
            dlg = QDialog(self)
            dlg.setWindowTitle('Sudoku nicht verfügbar')
            v = QVBoxLayout()
            v.addWidget(QLabel('Sudoku-Modul konnte nicht geladen werden.'))
            btn = QPushButton('OK')
            btn.clicked.connect(dlg.accept)
            v.addWidget(btn)
            dlg.setLayout(v)
            dlg.exec()
            return

        self.accept()
        dlg = Sudoku(self.parent())
        # load saved Sudoku only if user has auto-resume enabled
        try:
            if callable(getattr(should_auto_resume, '__call__', None)):
                auto = should_auto_resume()
            else:
                auto = True
            if auto:
                dlg.load_game()
        except Exception:
            # ignore load errors (file may not exist or be malformed)
            pass
        dlg.exec()


def show_minigame(parent):
    dlg = MinigameMenu(parent)
    dlg.exec()
