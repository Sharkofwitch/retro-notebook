from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPen

# --- TETRIS: Clean, robust rewrite ---

class TetrisWidget(QWidget):
    def background_anim_tick(self):
        # Animate background for retro effect
        self.bg_anim_phase = getattr(self, 'bg_anim_phase', 0) + 1
        self.update()

    def start_background_anim(self):
        if not hasattr(self, 'bg_anim_timer') or self.bg_anim_timer is None:
            from PySide6.QtCore import QTimer
            self.bg_anim_timer = QTimer(self)
            self.bg_anim_timer.timeout.connect(self.background_anim_tick)
            self.bg_anim_timer.start(60)

    def showEvent(self, event):
        self.start_background_anim()
        super().showEvent(event)
    GRID_W, GRID_H = 10, 20
    CELL_SIZE = 26
    TETROMINOS = [
        [[1, 1, 1, 1]],  # I
        [[1, 1], [1, 1]],  # O
        [[0, 1, 0], [1, 1, 1]],  # T
        [[1, 1, 0], [0, 1, 1]],  # S
        [[0, 1, 1], [1, 1, 0]],  # Z
        [[1, 0, 0], [1, 1, 1]],  # J
        [[0, 0, 1], [1, 1, 1]],  # L
    ]
    COLORS = [QColor('#33ff66'), QColor('#ffe066'), QColor('#ff33cc'), QColor('#00ff99'), QColor('#66ccff'), QColor('#ff3366'), QColor('#ff8800')]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(360, 560)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.x_offset = (self.width() - self.GRID_W * self.CELL_SIZE) // 2
        self.y_offset = (self.height() - self.GRID_H * self.CELL_SIZE) // 2 + 10
        self.gravity_timer = None
        self.line_clear_anim_timer = None
        self.lines_to_clear = []
        self.anim_frame = 0
        self.scanline_offset = 0
        self.reset_game()
        self.start_gravity()

    def start_gravity(self):
        if hasattr(self, 'gravity_timer') and self.gravity_timer:
            self.gravity_timer.stop()
        self.gravity_timer = QTimer(self)
        self.gravity_timer.timeout.connect(self.gravity_tick)
        self.gravity_timer.start(500)

    def gravity_tick(self):
        if self.game_over:
            if self.gravity_timer:
                self.gravity_timer.stop()
            return
        if not self.collides(self.tetro_x, self.tetro_y + 1, self.tetro):
            self.tetro_y += 1
        else:
            self.lock_tetromino()
        self.update()

    def reset_game(self):
        import random
        self.board = [[0 for _ in range(self.GRID_W)] for _ in range(self.GRID_H)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.rng = random.Random()
        self.spawn_tetromino()

    def spawn_tetromino(self):
        idx = self.rng.randint(0, len(self.TETROMINOS)-1)
        self.tetro = [row[:] for row in self.TETROMINOS[idx]]
        self.tetro_color = idx + 1
        self.tetro_x = self.GRID_W // 2 - len(self.tetro[0]) // 2
        self.tetro_y = 0
        if self.collides(self.tetro_x, self.tetro_y, self.tetro):
            self.game_over = True

    def collides(self, x, y, tetro):
        for i, row in enumerate(tetro):
            for j, v in enumerate(row):
                if v:
                    bx, by = x + j, y + i
                    if bx < 0 or bx >= self.GRID_W or by < 0 or by >= self.GRID_H:
                        return True
                    if self.board[by][bx]:
                        return True
        return False

    def paintEvent(self, event):
        qp = QPainter(self)
        # --- Sleeke animierte Retro-Lichtstreifen im Hintergrund ---
        qp.fillRect(self.rect(), QColor('#0d0d0d'))
        phase = getattr(self, 'bg_anim_phase', 0)
        for i in range(8):
            color = QColor(51,255,102, 30 + 20 * (i%2))
            y = int((self.height()/8)*i + (phase*2)%self.height()/8)
            qp.fillRect(0, y, self.width(), 8, color)
        # --- Retro scanlines ---
        for y in range(0, self.height(), 4):
            qp.setPen(QColor(0,0,0,40))
            qp.drawLine(0, y+self.scanline_offset, self.width(), y+self.scanline_offset)
        # Draw grid background with glow
        grid_w_px = self.GRID_W * self.CELL_SIZE
        grid_h_px = self.GRID_H * self.CELL_SIZE
        qp.setBrush(QColor('#181c1b'))
        qp.setPen(QPen(QColor('#33ff66'), 4))
        qp.drawRoundedRect(self.x_offset-10, self.y_offset-10, grid_w_px+20, grid_h_px+20, 14, 14)
        qp.setPen(QColor('#222'))
        # Draw cells (board)
        for y in range(self.GRID_H):
            for x in range(self.GRID_W):
                val = self.board[y][x]
                rx = self.x_offset + x * self.CELL_SIZE
                ry = self.y_offset + y * self.CELL_SIZE
                if y in self.lines_to_clear and self.anim_frame % 2 == 1:
                    # Blinking effect for lines to clear
                    qp.setBrush(QColor('#ffe066'))
                    qp.setPen(QColor('#fff'))
                    qp.drawRect(rx, ry, self.CELL_SIZE-2, self.CELL_SIZE-2)
                elif val:
                    qp.setBrush(self.COLORS[val-1])
                    qp.setPen(QColor('#fff'))
                    qp.drawRect(rx, ry, self.CELL_SIZE-2, self.CELL_SIZE-2)
                else:
                    qp.setBrush(QColor('#23282a'))
                    qp.setPen(QColor('#222'))
                    qp.drawRect(rx, ry, self.CELL_SIZE, self.CELL_SIZE)
        # Draw active tetromino
        if not self.game_over:
            for i, row in enumerate(self.tetro):
                for j, v in enumerate(row):
                    if v:
                        rx = self.x_offset + (self.tetro_x + j) * self.CELL_SIZE
                        ry = self.y_offset + (self.tetro_y + i) * self.CELL_SIZE
                        qp.setBrush(self.COLORS[self.tetro_color-1])
                        qp.setPen(QColor('#fff'))
                        qp.drawRect(rx, ry, self.CELL_SIZE-2, self.CELL_SIZE-2)
        # Draw grid lines
        qp.setPen(QColor('#33ff66'))
        for i in range(self.GRID_W+1):
            qp.drawLine(self.x_offset+i*self.CELL_SIZE, self.y_offset, self.x_offset+i*self.CELL_SIZE, self.y_offset+grid_h_px)
        for i in range(self.GRID_H+1):
            qp.drawLine(self.x_offset, self.y_offset+i*self.CELL_SIZE, self.x_offset+grid_w_px, self.y_offset+i*self.CELL_SIZE)
        # (Score/Level/Lines Anzeige ist jetzt im Dialog, nicht mehr im Spielfeld)

    def keyPressEvent(self, event):
        if self.game_over:
            return
        key = event.key()
        # Use getattr for compatibility with all Qt versions
        KEY_LEFT = getattr(Qt, 'Key_Left', 0x01000012)
        KEY_RIGHT = getattr(Qt, 'Key_Right', 0x01000014)
        KEY_UP = getattr(Qt, 'Key_Up', 0x01000013)
        KEY_DOWN = getattr(Qt, 'Key_Down', 0x01000015)
        KEY_SPACE = getattr(Qt, 'Key_Space', 0x20)
        acted = False
        if key == KEY_LEFT:
            self.try_move(-1, 0)
            acted = True
        elif key == KEY_RIGHT:
            self.try_move(1, 0)
            acted = True
        elif key == KEY_DOWN:
            self.try_move(0, 1)
            acted = True
        elif key == KEY_UP:
            self.try_rotate()
            acted = True
        elif key == KEY_SPACE:
            self.hard_drop()
            acted = True
        if acted:
            self.update()

    def try_rotate(self):
        # Rotate clockwise
        rotated = [list(row) for row in zip(*self.tetro[::-1])]
        if not self.collides(self.tetro_x, self.tetro_y, rotated):
            self.tetro = rotated

    def hard_drop(self):
        # Drop tetromino to the bottom
        while not self.collides(self.tetro_x, self.tetro_y + 1, self.tetro):
            self.tetro_y += 1
        self.lock_tetromino()
        self.update()

    def lock_tetromino(self):
        # Place tetromino on the board
        for i, row in enumerate(self.tetro):
            for j, v in enumerate(row):
                if v:
                    bx, by = self.tetro_x + j, self.tetro_y + i
                    if 0 <= bx < self.GRID_W and 0 <= by < self.GRID_H:
                        self.board[by][bx] = self.tetro_color
        # Find lines to clear
        self.lines_to_clear = [y for y, row in enumerate(self.board) if all(cell != 0 for cell in row)]
        if self.lines_to_clear:
            self.animating = True
            self.anim_frame = 0
            self.line_clear_anim_timer = QTimer(self)
            self.line_clear_anim_timer.timeout.connect(self.animate_line_clear)
            self.line_clear_anim_timer.start(80)
        else:
            self.animating = False
            # WICHTIG: Gravity-Tick nach Zeilenlöschung sofort auslösen, damit der neue Block korrekt "fällt"
            self.spawn_tetromino()
            if self.collides(self.tetro_x, self.tetro_y, self.tetro):
                self.game_over = True
            self.update()
            # Gravity sofort triggern, damit der neue Block nicht "hängt"
            if self.gravity_timer:
                self.gravity_timer.stop()
            self.gravity_tick()

    def animate_line_clear(self):
        self.anim_frame += 1
        self.scanline_offset = (self.scanline_offset + 1) % 4
        if self.anim_frame >= 6:
            if self.line_clear_anim_timer:
                self.line_clear_anim_timer.stop()
            # 1. Zeilen löschen und Board aktualisieren
            lines_cleared = len(self.lines_to_clear)
            if lines_cleared > 0:
                new_board = [row for y, row in enumerate(self.board) if y not in self.lines_to_clear]
                for _ in range(lines_cleared):
                    new_board.insert(0, [0 for _ in range(self.GRID_W)])
                self.board = new_board
                self.lines += lines_cleared
                self.score += 100 * lines_cleared
            self.lines_to_clear = []
            # 2. Jetzt EINEN neuen Block spawnen und Gravity sofort triggern
            self.animating = False
            self.spawn_tetromino()
            if self.collides(self.tetro_x, self.tetro_y, self.tetro):
                self.game_over = True
            self.update()
            # Gravity sofort triggern, damit der neue Block nicht "hängt"
            if self.gravity_timer:
                self.gravity_timer.stop()
            self.gravity_tick()
        else:
            self.update()
    def gravity_tick(self):
        if self.game_over:
            if self.gravity_timer:
                self.gravity_timer.stop()
            return
        if not self.collides(self.tetro_x, self.tetro_y + 1, self.tetro):
            self.tetro_y += 1
        else:
            self.lock_tetromino()
        self.update()

    def clear_lines(self):
        # Remove full lines and add empty ones at the top
        # (Diese Methode wird nicht mehr direkt nach lock_tetromino verwendet)
        pass

    def keyReleaseEvent(self, event):
        pass

    def try_move(self, dx, dy):
        nx, ny = self.tetro_x + dx, self.tetro_y + dy
        if not self.collides(nx, ny, self.tetro):
            self.tetro_x, self.tetro_y = nx, ny

class TetrisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RETRO TETRIS")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        vbox = QVBoxLayout()
        self.tetris = TetrisWidget(self)
        # Info-Panel oben
        info_hbox = QHBoxLayout()
        self.score_label = QPushButton()
        self.score_label.setEnabled(False)
        self.score_label.setStyleSheet('background:#111;color:#ffe066;font-size:18px;font-family:Courier New;border:2px solid #ffe066;border-radius:8px;padding:6px 18px;')
        info_hbox.addWidget(self.score_label)
        self.lines_label = QPushButton()
        self.lines_label.setEnabled(False)
        self.lines_label.setStyleSheet('background:#111;color:#33ff66;font-size:18px;font-family:Courier New;border:2px solid #33ff66;border-radius:8px;padding:6px 18px;')
        info_hbox.addWidget(self.lines_label)
        self.level_label = QPushButton()
        self.level_label.setEnabled(False)
        self.level_label.setStyleSheet('background:#111;color:#ff33cc;font-size:18px;font-family:Courier New;border:2px solid #ff33cc;border-radius:8px;padding:6px 18px;')
        info_hbox.addWidget(self.level_label)
        vbox.addLayout(info_hbox)
        vbox.addWidget(self.tetris)
        hbox = QHBoxLayout()
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self.restart_game)
        hbox.addWidget(self.restart_btn)
        self.menu_btn = QPushButton("Back to Menu")
        self.menu_btn.clicked.connect(self.accept)
        hbox.addWidget(self.menu_btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        # Timer für Info-Panel
        self.info_timer = QTimer(self)
        self.info_timer.timeout.connect(self.update_info)
        self.info_timer.start(100)

    def update_info(self):
        self.score_label.setText(f'SCORE: {self.tetris.score:06d}')
        self.lines_label.setText(f'LINES: {self.tetris.lines:03d}')
        self.level_label.setText(f'LEVEL: {self.tetris.level:02d}')

    def restart_game(self):
        self.tetris.reset_game()
        self.tetris.start_gravity()

def show_tetris(parent=None):
    dlg = TetrisDialog(parent)
    dlg.exec()
