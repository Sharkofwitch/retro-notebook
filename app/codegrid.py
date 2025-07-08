from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QWidget, QSizePolicy, QMessageBox, QInputDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush
import random, copy, json, os

CODEGRID_SAVE_PATH = os.path.join(os.path.dirname(__file__), '../notebooks/codegrid_save.json')

class CodeGridMinimal(QDialog):
    def __init__(self, parent=None, mode='classic', fixed_seed=None):
        super().__init__(parent)
        self.setWindowTitle("CODEGRID – Retro Logic Puzzle")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        self.level = 1
        self.highscore = 0
        self.xp = 0
        self.achievements = set()
        self.daily_challenge = self.generate_daily_challenge()
        self.load_progress()
        self.mode = mode
        self.fixed_seed = fixed_seed
        self.init_level()
        self.init_ui()
        self.update_status()

    def generate_daily_challenge(self):
        # Erzeuge eine Challenge basierend auf Tagesdatum
        import datetime, hashlib
        today = datetime.date.today().isoformat()
        h = int(hashlib.sha256(today.encode()).hexdigest(), 16)
        size = 4 + (h % 5)  # 4-8
        moves = 8 + (h % 6)
        return {'size': size, 'moves': moves, 'seed': h % 100000}

    def init_ui(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QPainter, QPen, QColor
        vbox = QVBoxLayout()
        vbox.setContentsMargins(32, 32, 32, 32)
        # Menü-Button oben rechts
        menu_hbox = QHBoxLayout()
        menu_hbox.addStretch()
        self.back_btn = QPushButton("Zurück zum Hauptmenü")
        self.back_btn.setStyleSheet('font-size:16px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:6px 18px;')
        self.back_btn.clicked.connect(self.close)
        menu_hbox.addWidget(self.back_btn)
        vbox.addLayout(menu_hbox)
        # Status
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.status_label.setStyleSheet('font-size:22px; color:#33ff66;')
        vbox.addWidget(self.status_label)
        vbox.addSpacing(12)
        # Animierter Rahmen/Scanlines
        class AnimatedFrame(QWidget):
            def __init__(self, grid_size, cell_size, parent=None):
                super().__init__(parent)
                self.setMinimumHeight(2*(grid_size*cell_size+64))
                self.grid_size = grid_size
                self.cell_size = cell_size
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update)
                self.timer.start(50)
                self.phase = 0
            def paintEvent(self, event):
                qp = QPainter(self)
                qp.setRenderHint(QPainter.RenderHint.Antialiasing)
                # Glow-Rahmen
                for i in range(1, 6):
                    qp.setPen(QPen(QColor(51,255,102, 22//i), 8+2*i))
                    qp.drawRoundedRect(8-i*2, 8-i*2, self.width()-16+i*4, self.height()-16+i*4, 18+i*2, 18+i*2)
                # Spielfeld-Hintergrund besonders hervorheben
                grid_w = self.grid_size*self.cell_size
                grid_h = self.grid_size*self.cell_size
                grid_x = (self.width()-grid_w)//2
                grid_y = (self.height()-grid_h)//2
                qp.setBrush(QColor('#222'))
                qp.setPen(QPen(QColor('#ffe066'), 4))
                qp.drawRoundedRect(grid_x-12, grid_y-12, grid_w+24, grid_h+24, 18, 18)
                qp.setBrush(QColor('#181c1b'))
                qp.setPen(QPen(QColor('#33ff66'), 3))
                qp.drawRoundedRect(8, 8, self.width()-16, self.height()-16, 18, 18)
                # Scanlines
                for y in range(16, self.height()-16, 4):
                    y_off = y + (self.phase % 8)
                    color = QColor(30,30,30,80)
                    if y%16==0:
                        color = QColor('#33ff66') if (y//16)%2==0 else QColor('#ffe066')
                        color.setAlpha(60)
                    qp.setPen(QPen(color, 2))
                    qp.drawLine(16, y_off, self.width()-16, y_off)
                # Glitch-Overlay (subtil)
                if self.phase%23==0:
                    qp.setOpacity(0.13)
                    qp.setBrush(QColor('#ff33cc'))
                    qp.drawRect(8, 8, self.width()-16, self.height()-16)
                    qp.setOpacity(1.0)
                self.phase += 1
        frame = AnimatedFrame(self.grid_size, self.cell_size, self)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(32, 32, 32, 32)
        hbox_grids = QHBoxLayout()
        self.grid_widget = GridWidget(self)
        self.target_widget = TargetGridWidget(self)
        hbox_grids.addStretch(1)
        hbox_grids.addWidget(self.grid_widget)
        hbox_grids.addSpacing(32)
        hbox_grids.addWidget(self.target_widget)
        hbox_grids.addStretch(1)
        frame_layout.addLayout(hbox_grids)
        vbox.addWidget(frame)
        vbox.addSpacing(12)
        # Steuerung mit Labels
        hbox = QHBoxLayout()
        label_action = QLabel("Aktion:")
        label_action.setStyleSheet('font-size:18px; color:#ffe066;')
        hbox.addWidget(label_action)
        self.cmd_combo = QComboBox()
        self.cmd_combo.setStyleSheet('font-size:20px; min-width:110px;')
        hbox.addWidget(self.cmd_combo)
        self.idx1_combo = QComboBox()
        self.idx1_combo.setStyleSheet('font-size:20px; min-width:60px;')
        hbox.addWidget(self.idx1_combo)
        self.idx2_combo = QComboBox()
        self.idx2_combo.setStyleSheet('font-size:20px; min-width:60px;')
        hbox.addWidget(self.idx2_combo)
        self.exec_btn = QPushButton("OK")
        self.exec_btn.setStyleSheet('font-size:20px; min-width:60px;')
        hbox.addWidget(self.exec_btn)
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setStyleSheet('font-size:20px; min-width:60px;')
        hbox.addWidget(self.undo_btn)
        # Button für Daily Challenge
        self.daily_btn = QPushButton("Tägliche Challenge")
        self.daily_btn.setStyleSheet('font-size:16px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:6px 18px;')
        self.daily_btn.clicked.connect(self.show_daily_challenge)
        hbox.addWidget(self.daily_btn)
        vbox.addLayout(hbox)
        # Animierte Buttons (Flicker)
        def btn_flicker(btn, base_color):
            c = QColor(base_color)
            c = c.lighter(random.randint(90,120))
            btn.setStyleSheet(f"font-size:20px; min-width:60px; background:#181c1b; color:{c.name()}; border:2px solid {c.name()}; border-radius:8px; padding:6px 18px;")
        btns = [self.exec_btn, self.undo_btn, self.daily_btn, self.back_btn]
        btn_timer = QTimer(self)
        def update_btns():
            btn_flicker(self.exec_btn, '#33ff66')
            btn_flicker(self.undo_btn, '#ffe066')
            btn_flicker(self.daily_btn, '#ff33cc')
            btn_flicker(self.back_btn, '#ffe066')
        btn_timer.timeout.connect(update_btns)
        btn_timer.start(180)
        # Hilfetext
        self.setLayout(vbox)
        self.exec_btn.clicked.connect(self.execute_command)
        self.undo_btn.clicked.connect(self.undo)
        self.cmd_combo.currentIndexChanged.connect(self.update_cmd_visibility)
        self.update_cmds()

    def init_level(self, seed=None):
        import hashlib
        # Seed-Handling je nach Modus
        if self.mode in ('zen', 'custom', 'daily'):
            if self.fixed_seed is not None:
                # Seed ist jetzt abhängig von Level, damit jedes Level eindeutig reproduzierbar ist
                seed = f"{self.fixed_seed}-L{self.level}"
            else:
                seed = str(random.randint(0, 99999999))
        else:  # classic
            if seed is None:
                seed = str(random.randint(0, 99999999))
        self.current_seed = seed
        rnd = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2**32))
        self.grid_size = min(3 + self.level // 2, 8)
        self.cell_size = 48
        self.moves_left = max(5 + self.level, int(self.grid_size*1.7))
        self.locked = set()
        self.board = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.target = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        if self.level < 4:
            for _ in range(rnd.randint(2, self.grid_size)):
                x, y = rnd.randint(0, self.grid_size-1), rnd.randint(0, self.grid_size-1)
                self.target[y][x] = 1
        elif self.level < 7:
            for _ in range(rnd.randint(2, self.grid_size)):
                x, y = rnd.randint(0, self.grid_size-1), rnd.randint(0, self.grid_size-1)
                self.target[y][x] = 1
                self.target[y][self.grid_size-1-x] = 1
        else:
            for _ in range(rnd.randint(self.grid_size, self.grid_size*2)):
                x, y = rnd.randint(0, self.grid_size-1), rnd.randint(0, self.grid_size-1)
                self.target[y][x] = 1
            for _ in range(rnd.randint(1, self.grid_size//2)):
                x, y = rnd.randint(0, self.grid_size-1), rnd.randint(0, self.grid_size-1)
                self.target[y][x] = 0
        if self.level >= 5:
            for _ in range(rnd.randint(1, self.grid_size//2)):
                x, y = rnd.randint(0, self.grid_size-1), rnd.randint(0, self.grid_size-1)
                self.locked.add((x, y))
        temp = copy.deepcopy(self.target)
        cmds = ["MOVE ROW", "MOVE COL"]
        if self.level >= 3:
            cmds += ["FLIP ROW", "FLIP COL"]
        if self.level >= 6:
            cmds += ["SWAP ROWS", "SWAP COLS"]
        if self.level >= 9:
            cmds += ["INVERT ALL"]
        if self.level >= 12:
            cmds += ["RANDOMIZE ROW"]
        if self.level >= 15:
            cmds += ["MIRROR ROW", "MIRROR COL"]
        for _ in range(2 + self.level):
            cmd = rnd.choice(cmds)
            idx1 = rnd.randint(0, self.grid_size-1)
            idx2 = rnd.randint(0, self.grid_size-1)
            if cmd == "MOVE ROW":
                temp[idx1] = temp[idx1][-1:] + temp[idx1][:-1]
            elif cmd == "MOVE COL":
                col = [temp[y][idx1] for y in range(self.grid_size)]
                col = col[-1:] + col[:-1]
                for y in range(self.grid_size):
                    temp[y][idx1] = col[y]
            elif cmd == "FLIP ROW":
                temp[idx1] = temp[idx1][::-1]
            elif cmd == "FLIP COL":
                col = [temp[y][idx1] for y in range(self.grid_size)]
                for y in range(self.grid_size):
                    temp[y][idx1] = col[self.grid_size-1-y]
            elif cmd == "SWAP ROWS":
                temp[idx1], temp[idx2] = temp[idx2], temp[idx1]
            elif cmd == "SWAP COLS":
                for y in range(self.grid_size):
                    temp[y][idx1], temp[y][idx2] = temp[y][idx2], temp[y][idx1]
            elif cmd == "INVERT ALL":
                for y in range(self.grid_size):
                    temp[y] = [1-v for v in temp[y]]
            elif cmd == "RANDOMIZE ROW":
                temp[idx1] = rnd.sample(temp[idx1], len(temp[idx1]))
            elif cmd == "MIRROR ROW":
                row = temp[idx1]
                mid = len(row)//2
                for i in range(mid):
                    row[-(i+1)] = row[i]
            elif cmd == "MIRROR COL":
                col = [temp[y][idx1] for y in range(self.grid_size)]
                mid = len(col)//2
                for i in range(mid):
                    col[-(i+1)] = col[i]
                for y in range(self.grid_size):
                    temp[y][idx1] = col[y]
        self.board = temp
        self.undo_stack = []
        # Widgets anpassen
        if hasattr(self, 'grid_widget'):
            self.grid_widget.setMinimumSize(self.grid_size*self.cell_size+64, self.grid_size*self.cell_size+64)
            self.grid_widget.update()
        if hasattr(self, 'target_widget'):
            self.target_widget.setMinimumSize(self.grid_size*self.cell_size+64, self.grid_size*self.cell_size+64)
            self.target_widget.update()
        self.resize(max(2*(self.grid_size*self.cell_size+96), 700), max(self.grid_size*self.cell_size+260, 540))
        # Feedback für neue Aktionen
        self.new_action_message = None
        if self.level in [3,6,9,12,15]:
            if self.level == 3:
                self.new_action_message = "Neu: Flip Row/Col freigeschaltet!"
            elif self.level == 6:
                self.new_action_message = "Neu: Swap Rows/Cols freigeschaltet!"
            elif self.level == 9:
                self.new_action_message = "Neu: Invert All freigeschaltet!"
            elif self.level == 12:
                self.new_action_message = "Neu: Randomize Row freigeschaltet!"
            elif self.level == 15:
                self.new_action_message = "Neu: Mirror Row/Col freigeschaltet!"

    def update_status(self):
        ach = f" | Achievements: {len(self.achievements)}" if self.achievements else ""
        self.status_label.setText(f"Level: {self.level}   XP: {self.xp}   Moves: {self.moves_left}   Highscore: {self.highscore}{ach}")
        if hasattr(self, 'grid_widget'):
            self.grid_widget.update()
        if hasattr(self, 'target_widget'):
            self.target_widget.update()

    def update_cmds(self):
        cmds = ["MOVE ROW", "MOVE COL"]
        if self.level >= 3:
            cmds += ["FLIP ROW", "FLIP COL"]
        if self.level >= 6:
            cmds += ["SWAP ROWS", "SWAP COLS"]
        if self.level >= 9:
            cmds += ["INVERT ALL"]
        if self.level >= 12:
            cmds += ["RANDOMIZE ROW"]
        if self.level >= 15:
            cmds += ["MIRROR ROW", "MIRROR COL"]
        self.cmd_combo.clear()
        self.cmd_combo.addItems(cmds)
        self.idx1_combo.clear()
        self.idx2_combo.clear()
        for i in range(self.grid_size):
            self.idx1_combo.addItem(str(i+1))
            self.idx2_combo.addItem(str(i+1))
        self.update_cmd_visibility()

    def update_cmd_visibility(self):
        cmd = self.cmd_combo.currentText()
        self.idx1_combo.setVisible(True)
        self.idx2_combo.setVisible(cmd.startswith("SWAP"))

    def execute_command(self):
        cmd = self.cmd_combo.currentText()
        idx1 = int(self.idx1_combo.currentText())-1 if self.idx1_combo.count() > 0 else 0
        idx2 = int(self.idx2_combo.currentText())-1 if self.idx2_combo.count() > 0 else 0
        self.undo_stack.append((copy.deepcopy(self.board), self.moves_left))
        # Gesperrte Felder: Nur erlauben, wenn nicht betroffen
        if cmd in ["MOVE ROW", "FLIP ROW", "RANDOMIZE ROW", "MIRROR ROW"] and self.level >= 5:
            if any((x, idx1) in self.locked for x in range(self.grid_size)):
                self.status_label.setText("<span style='color:#ff3366'>Fehler: Zeile enthält gesperrte Felder!</span>")
                return
        if cmd in ["MOVE COL", "FLIP COL", "MIRROR COL"] and self.level >= 5:
            if any((idx1, y) in self.locked for y in range(self.grid_size)):
                self.status_label.setText("<span style='color:#ff3366'>Fehler: Spalte enthält gesperrte Felder!</span>")
                return
        if cmd == "MOVE ROW":
            self.board[idx1] = self.board[idx1][-1:] + self.board[idx1][:-1]
        elif cmd == "MOVE COL":
            col = [self.board[y][idx1] for y in range(self.grid_size)]
            col = col[-1:] + col[:-1]
            for y in range(self.grid_size):
                self.board[y][idx1] = col[y]
        elif cmd == "FLIP ROW":
            self.board[idx1] = self.board[idx1][::-1]
        elif cmd == "FLIP COL":
            col = [self.board[y][idx1] for y in range(self.grid_size)]
            for y in range(self.grid_size):
                self.board[y][idx1] = col[self.grid_size-1-y]
        elif cmd == "SWAP ROWS":
            self.board[idx1], self.board[idx2] = self.board[idx2], self.board[idx1]
        elif cmd == "SWAP COLS":
            for y in range(self.grid_size):
                self.board[y][idx1], self.board[y][idx2] = self.board[y][idx2], self.board[y][idx1]
        elif cmd == "INVERT ALL":
            for y in range(self.grid_size):
                self.board[y] = [1-v for v in self.board[y]]
        elif cmd == "RANDOMIZE ROW":
            self.board[idx1] = random.sample(self.board[idx1], len(self.board[idx1]))
        elif cmd == "MIRROR ROW":
            row = self.board[idx1]
            mid = len(row)//2
            for i in range(mid):
                row[-(i+1)] = row[i]
        elif cmd == "MIRROR COL":
            col = [self.board[y][idx1] for y in range(self.grid_size)]
            mid = len(col)//2
            for i in range(mid):
                col[-(i+1)] = col[i]
            for y in range(self.grid_size):
                self.board[y][idx1] = col[y]
        self.moves_left -= 1
        self.update_status()
        # Feedback für neue Aktionen
        if hasattr(self, 'new_action_message') and self.new_action_message:
            self.status_label.setText(self.status_label.text() + f"  <span style='color:#ffe066'>{self.new_action_message}</span>")
            self.new_action_message = None
        if self.check_win():
            self.level += 1
            self.highscore = max(self.highscore, self.level-1)
            self.init_level()
            self.update_cmds()
            self.update_status()
        elif self.moves_left == 0:
            self.level = 1
            self.init_level()
            self.update_cmds()
            self.update_status()

    def undo(self):
        if self.undo_stack:
            self.board, self.moves_left = self.undo_stack.pop()
            self.update_status()

    def check_win(self):
        if self.board == self.target:
            # XP und Achievements vergeben
            self.xp += 10 + max(0, self.moves_left)
            if self.moves_left >= self.grid_size:
                self.achievements.add("Effizienz-Profi")
            if self.level == 10:
                self.achievements.add("Level 10 erreicht")
            if self.level == 1 and self.moves_left > 5:
                self.achievements.add("Perfekter Start")
            if self.level == 5 and len(self.locked) > 0:
                self.achievements.add("Locked Master")
            self.save_progress()
            return True
        return False

    def show_daily_challenge(self):
        from PySide6.QtWidgets import QMessageBox
        c = self.daily_challenge
        msg = QMessageBox(self)
        msg.setWindowTitle("Tägliche Challenge")
        msg.setText(f"<b>Daily Challenge:</b><br>Grid: {c['size']}x{c['size']}<br>Moves: {c['moves']}<br>Seed: {c['seed']}<br><br>Klicke OK, um die Challenge zu starten.")
        if msg.exec() == 1024:  # QMessageBox.Ok == 1024
            self.level = 1
            self.daily_mode = True
            self.init_level(seed=str(c['seed']))
            self.update_cmds()
            self.update_status()
            self.daily_mode = False

    def show_seed_dialog(self):
        seed, ok = QInputDialog.getText(self, "Seed eingeben", "Seed für Puzzle (Zahl oder Text):")
        if ok and seed:
            self.init_level(seed=seed)
            self.update_cmds()
            self.update_status()

    def show_current_seed(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Puzzle-Seed")
        msg.setText(f"Seed für dieses Puzzle: <b>{self.current_seed}</b>")
        msg.exec()

    def save_progress(self):
        data = {
            "highscore": self.highscore,
            "xp": self.xp,
            "achievements": list(self.achievements)
        }
        with open(CODEGRID_SAVE_PATH, 'w') as f:
            json.dump(data, f)

    def load_progress(self):
        if os.path.exists(CODEGRID_SAVE_PATH):
            with open(CODEGRID_SAVE_PATH, 'r') as f:
                data = json.load(f)
            self.highscore = data.get("highscore", 0)
            self.xp = data.get("xp", 0)
            self.achievements = set(data.get("achievements", []))

class GridWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.game = parent
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    def paintEvent(self, event):
        qp = QPainter(self)
        grid_size = self.game.grid_size
        cell_size = self.game.cell_size
        locked = getattr(self.game, 'locked', set())
        # Hintergrund für das gesamte Grid
        qp.setBrush(QColor('#111'))
        qp.setPen(QPen(Qt.PenStyle.NoPen))
        qp.drawRect(32, 32, grid_size*cell_size, grid_size*cell_size)
        for y in range(grid_size):
            for x in range(grid_size):
                val = self.game.board[y][x]
                rect = (32+x*cell_size, 32+y*cell_size, cell_size, cell_size)
                if (x, y) in locked:
                    qp.setPen(QColor('#ff3366'))
                    qp.setBrush(QColor(60,0,0,180))
                    qp.drawRect(*rect)
                elif not val:
                    # Leere Felder klar hervorheben
                    qp.setPen(QColor('#222'))
                    qp.setBrush(QColor('#222'))
                    qp.drawRect(*rect)
                else:
                    qp.setPen(QColor('#33ff66'))
                    qp.setBrush(QColor('#33ff66'))
                    qp.drawRect(*rect)
                # Text/Icon
                qp.setPen(QColor('#0d0d0d') if val else QColor('#888'))
                qp.setFont(QFont('Courier New', 36, QFont.Weight.Bold))
                qp.drawText(rect[0], rect[1]+40, '█' if val else '·')
        # Gitterlinien
        qp.setPen(QColor('#222'))
        for i in range(grid_size+1):
            qp.drawLine(32, 32+i*cell_size, 32+grid_size*cell_size, 32+i*cell_size)
            qp.drawLine(32+i*cell_size, 32, 32+i*cell_size, 32+grid_size*cell_size)
        # Rahmen
        qp.setPen(QColor('#33ff66'))
        qp.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        qp.drawRect(30, 30, grid_size*cell_size+4, grid_size*cell_size+4)

class TargetGridWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.game = parent
        self.setMinimumSize(320, 320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    def paintEvent(self, event):
        qp = QPainter(self)
        grid_size = self.game.grid_size
        cell_size = self.game.cell_size
        # Hintergrund für das gesamte Grid
        qp.setBrush(QColor('#111'))
        qp.setPen(QPen(Qt.PenStyle.NoPen))
        qp.drawRect(32, 32, grid_size*cell_size, grid_size*cell_size)
        for y in range(grid_size):
            for x in range(grid_size):
                val = self.game.target[y][x]
                rect = (32+x*cell_size, 32+y*cell_size, cell_size, cell_size)
                if val:
                    qp.setPen(QColor('#ffe066'))
                    qp.setBrush(QColor('#ffe066'))
                    qp.drawRect(*rect)
                else:
                    qp.setPen(QColor('#222'))
                    qp.setBrush(QColor('#222'))
                    qp.drawRect(*rect)
                qp.setPen(QColor('#0d0d0d') if val else QColor('#888'))
                qp.setFont(QFont('Courier New', 36, QFont.Weight.Bold))
                qp.drawText(rect[0], rect[1]+40, '█' if val else '·')
        # Gitterlinien
        qp.setPen(QColor('#222'))
        for i in range(grid_size+1):
            qp.drawLine(32, 32+i*cell_size, 32+grid_size*cell_size, 32+i*cell_size)
            qp.drawLine(32+i*cell_size, 32, 32+i*cell_size, 32+grid_size*cell_size)
        # Rahmen
        qp.setPen(QColor('#ffe066'))
        qp.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        qp.drawRect(30, 30, grid_size*cell_size+4, grid_size*cell_size+4)

class CodeGridMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CodeGrid – Modus wählen")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        self.resize(420, 340)
        vbox = QVBoxLayout()
        title = QLabel("<span style='font-size:32px; color:#33ff66;'>CodeGrid</span>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)
        vbox.addSpacing(12)
        btn_classic = QPushButton("Classic Modus")
        btn_classic.setStyleSheet('font-size:22px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px; padding:10px 24px;')
        btn_zen = QPushButton("Zen Modus")
        btn_zen.setStyleSheet('font-size:22px; background:#222; color:#66ccff; border:2px solid #66ccff; border-radius:8px; padding:10px 24px;')
        btn_custom = QPushButton("Custom Modus (Seed)")
        btn_custom.setStyleSheet('font-size:22px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:10px 24px;')
        btn_daily = QPushButton("Daily Challenge")
        btn_daily.setStyleSheet('font-size:22px; background:#222; color:#ff33cc; border:2px solid #ff33cc; border-radius:8px; padding:10px 24px;')
        vbox.addWidget(btn_classic)
        vbox.addWidget(btn_zen)
        vbox.addWidget(btn_custom)
        vbox.addWidget(btn_daily)
        vbox.addSpacing(18)
        info = QLabel("<span style='color:#888; font-size:15px;'>Classic: Level für Level, mit Zuglimit<br>Zen: Ohne Zuglimit, entspannend<br>Custom: Puzzle nach Seed<br>Daily: Tägliches, für alle gleiches Puzzle</span>")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(info)
        self.setLayout(vbox)
        self.mode = None
        btn_classic.clicked.connect(lambda: self.select_mode('classic'))
        btn_zen.clicked.connect(lambda: self.select_mode('zen'))
        btn_custom.clicked.connect(lambda: self.select_mode('custom'))
        btn_daily.clicked.connect(lambda: self.select_mode('daily'))
    def select_mode(self, mode):
        self.mode = mode
        self.accept()

def show_codegrid(parent=None):
    menu = CodeGridMenu(parent)
    if not menu.exec():
        return
    mode = menu.mode
    if mode == 'classic':
        dlg = CodeGridMinimal(parent, mode='classic')
        dlg.setWindowTitle("CodeGrid – Classic Modus")
        dlg.exec()
    elif mode == 'zen':
        dlg = CodeGridMinimal(parent, mode='zen', fixed_seed=str(random.randint(0,99999999)))
        dlg.setWindowTitle("CodeGrid – Zen Modus")
        dlg.moves_left = 9999
        dlg.update_status()
        dlg.exec()
    elif mode == 'custom':
        seed, ok = QInputDialog.getText(parent, "Custom Seed", "Seed für Puzzle (Zahl oder Text):")
        if ok and seed:
            dlg = CodeGridMinimal(parent, mode='custom', fixed_seed=seed)
            dlg.setWindowTitle(f"CodeGrid – Custom Modus (Seed: {seed})")
            dlg.init_level()
            dlg.update_cmds()
            dlg.update_status()
            dlg.exec()
    elif mode == 'daily':
        cseed = CodeGridMinimal(parent).daily_challenge['seed']
        dlg = CodeGridMinimal(parent, mode='daily', fixed_seed=str(cseed))
        dlg.setWindowTitle("CodeGrid – Daily Challenge")
        dlg.init_level()
        dlg.update_cmds()
        dlg.update_status()
        dlg.exec()

# Am Ende der Datei (oder im Minigame-Menü) aufrufbar machen:
# from app.codegrid import show_codegrid
# show_codegrid(parent)
