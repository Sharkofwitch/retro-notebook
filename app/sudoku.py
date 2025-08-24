"""Retro-styled Sudoku dialog with uniqueness generator and pencil/notes mode."""
from PySide6.QtWidgets import (
    QDialog, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient, QBrush
import random
import json
import os
import math

SAVE_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'sudoku_save.json')
CFG_PATH = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'sudoku_cfg.json')

GRID = 9
BOX = 3
# smaller cells for a compact layout
CELL_PX = 36
AUTO_SAVE_SECONDS = 30


class SudokuGrid(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.game = parent
        self.setMinimumSize(GRID * CELL_PX, GRID * CELL_PX)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.phase = 0
        # animation state for entry flash
        self.entry_flash = 0.0
        # subtle specks placed near box/grid intersections for a Sudoku feel
        self.particles = []
        # create a small number of specks anchored near box lines/intersections
        for by in range(BOX + 1):
            for bx in range(BOX + 1):
                # place one speck near each box intersection with small random jitter
                x = bx * BOX * CELL_PX + random.uniform(-CELL_PX * 0.2, CELL_PX * 0.2)
                y = by * BOX * CELL_PX + random.uniform(-CELL_PX * 0.2, CELL_PX * 0.2)
                self.particles.append({
                    'x': max(0, min(GRID * CELL_PX, x)),
                    'y': max(0, min(GRID * CELL_PX, y)),
                    'speed': random.uniform(0.04, 0.18),
                    'size': random.uniform(0.9, 1.8),
                    'phase': random.random() * 360,
                })

    def tick_phase(self):
        self.phase = (self.phase + 1) % 360
        # decay entry flash slowly
        if getattr(self, 'entry_flash', 0) > 0:
            self.entry_flash = max(0.0, self.entry_flash - 0.02)
        # gently nudge specks to create a slow breathing motion
        for sp in self.particles:
            # ensure original anchor stored once
            if 'ox' not in sp:
                sp['ox'] = sp['x']
            if 'oy' not in sp:
                sp['oy'] = sp['y']
            sp['phase'] = (sp['phase'] + sp['speed'] * 8) % 360
            # tiny oscillation around anchor point (very small)
            jitter = math.sin(math.radians(sp['phase'])) * (CELL_PX * 0.06)
            sp['x'] = sp['ox'] + jitter * 0.6
            sp['y'] = sp['oy'] + jitter * 0.2
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#060606'))
        phase = getattr(self, 'phase', 0)

        # fonts
        main_font = QFont('Courier', max(12, int(CELL_PX * 0.72)), QFont.Weight.Bold)
        small_font = QFont('Courier', max(8, int(CELL_PX * 0.22)))

        # gentle radial background with a tiny motion (phase-driven) to feel alive
        midx = (GRID * CELL_PX) / 2
        midy = (GRID * CELL_PX) / 2
        # offset the center a bit based on phase for slow motion
        offset_x = math.sin(math.radians(phase * 0.6)) * (CELL_PX * 0.8)
        offset_y = math.cos(math.radians(phase * 0.4)) * (CELL_PX * 0.4)
        grad = QRadialGradient(midx + offset_x, midy + offset_y, GRID * CELL_PX * 0.9)
        grad.setColorAt(0.0, QColor(36, 54, 36, 20))
        grad.setColorAt(0.7, QColor(8, 10, 8, 18))
        grad.setColorAt(1.0, QColor(6, 6, 6, 220))
        p.fillRect(self.rect(), QBrush(grad))

        # subtle static scanlines (very faint)
        p.setPen(QColor(0, 0, 0, 6))
        for sy in range(0, GRID * CELL_PX, 4):
            p.drawLine(0, sy, GRID * CELL_PX, sy)

        # specks anchored to box intersections (steady, tiny)
        p.setPen(Qt.PenStyle.NoPen)
        for sp in self.particles:
            col = QColor(180, 255, 190, 90)
            p.setBrush(col)
            sx = int(sp['x'])
            sy = int(sp['y'])
            s = max(1, int(sp.get('size', 1)))
            p.drawEllipse(sx, sy, s, s)

        # highlight the selected 3x3 box to improve visibility
        selx, sely = self.game.selected
        box_x = (selx // BOX) * BOX * CELL_PX
        box_y = (sely // BOX) * BOX * CELL_PX
        p.fillRect(box_x + 1, box_y + 1, BOX * CELL_PX - 2, BOX * CELL_PX - 2, QColor(12, 60, 60, 28))

        # draw cells and numbers (no per-cell borders to keep it clean)
        for y in range(GRID):
            for x in range(GRID):
                rx = x * CELL_PX
                ry = y * CELL_PX

                # selection background: steady highlight for the focused cell
                if (x, y) == self.game.selected:
                    p.fillRect(rx + 1, ry + 1, CELL_PX - 2, CELL_PX - 2, QColor(6, 46, 46, 40))

                val = self.game.current[y][x]
                is_given = self.game.givens[y][x]

                # pencil candidates
                if val == 0 and len(self.game.candidates[y][x]) > 0:
                    p.setFont(small_font)
                    fm = p.fontMetrics()
                    small_cell = CELL_PX // 3
                    for n in range(1, GRID + 1):
                        col = (n - 1) % 3
                        rown = (n - 1) // 3
                        sx = rx + col * small_cell + 3
                        sy = ry + rown * small_cell + fm.ascent() + 2
                        if n in self.game.candidates[y][x]:
                            p.setPen(QColor('#6df0b0'))
                            p.drawText(sx, sy, str(n))
                    continue

                # draw number
                if val != 0:
                    p.setFont(main_font)
                    fm = p.fontMetrics()
                    txt = str(val)
                    w = fm.horizontalAdvance(txt)
                    h = fm.ascent()
                    if is_given:
                        p.setPen(QColor('#6fbfa0'))
                    else:
                        if self.game._board_conflict(x, y):
                            p.setPen(QColor('#ff6b6b'))
                        else:
                            p.setPen(QColor('#fff4d1'))
                    p.drawText(rx + (CELL_PX - w) // 2, ry + (CELL_PX + h) // 2 - 2, txt)

        # draw grid lines: thin lines and heavier box separators
        for i in range(0, GRID + 1):
            if i % BOX == 0:
                pen = QPen(QColor('#bfbfbf'))
                pen.setWidth(2)
                p.setPen(pen)
                p.drawLine(i * CELL_PX, 0, i * CELL_PX, GRID * CELL_PX)
                p.drawLine(0, i * CELL_PX, GRID * CELL_PX, i * CELL_PX)
            else:
                pen = QPen(QColor('#2a2a2a'))
                pen.setWidth(1)
                p.setPen(pen)
                p.drawLine(i * CELL_PX, 0, i * CELL_PX, GRID * CELL_PX)
                p.drawLine(0, i * CELL_PX, GRID * CELL_PX, i * CELL_PX)

        # subtle vignette overlay
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 28))
        p.drawRect(0, 0, GRID * CELL_PX, GRID * CELL_PX)

        # entry flash overlay (very subtle)
        flash = getattr(self, 'entry_flash', 0.0)
        if flash > 0.01:
            a = int(12 * flash)
            p.fillRect(self.rect(), QColor(255, 255, 255, a))

    def mousePressEvent(self, event):
        x = int(event.position().x()) // CELL_PX
        y = int(event.position().y()) // CELL_PX
        x = max(0, min(GRID - 1, x))
        y = max(0, min(GRID - 1, y))
        self.game.selected = (x, y)
        self.setFocus()
        self.update()

    def keyPressEvent(self, event):
        g = self.game
        x, y = g.selected
        key = event.key()
        mods = event.modifiers()

        # Ctrl-based shortcuts
        if mods & Qt.KeyboardModifier.ControlModifier:
            if key in (Qt.Key.Key_Z, Qt.Key.Key_U):
                g.undo()
                self.update()
                g.update_status()
                return
            if key == Qt.Key.Key_S:
                try:
                    g.save_game()
                except Exception:
                    pass
                return
            if key == Qt.Key.Key_L:
                try:
                    g.load_game()
                except Exception:
                    pass
                return
        if key in (Qt.Key.Key_Left, Qt.Key.Key_A):
            g.selected = (max(0, x - 1), y)
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_D):
            g.selected = (min(GRID - 1, x + 1), y)
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            g.selected = (x, max(0, y - 1))
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            g.selected = (x, min(GRID - 1, y + 1))
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if not g.givens[y][x]:
                g._push_history()
                g.current[y][x] = 0
                g.candidates[y][x].clear()
        elif key == Qt.Key.Key_N:
            # new puzzle
            g.generate_and_apply(difficulty=g.difficulty_menu.currentText())
            return
        elif key == Qt.Key.Key_P:
            # toggle pencil mode
            g.pencil_mode = not g.pencil_mode
            self.update()
            return
        elif key == Qt.Key.Key_H:
            # hint
            g.hint_fill()
            return
        else:
            text = event.text()
            if text.isdigit() and text != '0':
                v = int(text)
                if g.pencil_mode and not g.givens[y][x]:
                    # toggle candidate
                    if v in g.candidates[y][x]:
                        g.candidates[y][x].remove(v)
                    else:
                        g.candidates[y][x].add(v)
                else:
                    if not g.givens[y][x]:
                        g._push_history()
                        g.current[y][x] = v
                        g.candidates[y][x].clear()
        g.update_status()
        self.update()


class SudokuDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Sudoku — Retro')
        self.setStyleSheet('background:#0b0b0b; color:#9fe2c0; font-family:Courier New,monospace;')

        # state
        self.solution = [[0] * GRID for _ in range(GRID)]
        self.puzzle = [[0] * GRID for _ in range(GRID)]
        self.current = [[0] * GRID for _ in range(GRID)]
        self.givens = [[False] * GRID for _ in range(GRID)]
        self.selected = (0, 0)
        self.timer_seconds = 0
        self.history = []
        self.candidates = [[set() for _ in range(GRID)] for _ in range(GRID)]
        self.pencil_mode = False

        # UI - compact layout: status + compact toolbar + grid
        v = QVBoxLayout()
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(6)

        # status line
        status_row = QHBoxLayout()
        self.status = QLabel('')
        self.status.setStyleSheet('color:#9fe2c0; font-family:Courier New,monospace;')
        status_row.addWidget(self.status)
        status_row.addStretch()
        v.addLayout(status_row)

        # compact toolbar under status (keyboard-first, small controls)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.difficulty_menu = QComboBox()
        self.difficulty_menu.addItems(['easy', 'medium', 'hard'])
        self.difficulty_menu.setFixedHeight(28)
        toolbar.addWidget(self.difficulty_menu)

        new_btn = QPushButton('New')
        new_btn.setFixedHeight(28)
        new_btn.clicked.connect(self._on_new)
        toolbar.addWidget(new_btn)

        # Help button kept for information
        help_btn = QPushButton('Help')
        help_btn.setFixedHeight(28)
        help_btn.setToolTip('Help')
        help_btn.clicked.connect(self._show_help)
        toolbar.addWidget(help_btn)

        self.auto_resume_chk = QCheckBox('Auto')
        cfg = self._load_cfg()
        self.auto_resume_chk.setChecked(cfg.get('auto_resume', True))
        self.auto_resume_chk.setToolTip('Auto-resume')
        self.auto_resume_chk.stateChanged.connect(lambda _: self._save_cfg({'auto_resume': bool(self.auto_resume_chk.isChecked())}))
        toolbar.addWidget(self.auto_resume_chk)

        # tighten styles for compact toolbar
        for w in [new_btn, help_btn, self.difficulty_menu]:
            w.setStyleSheet('background:#181c1b; color:#9fe2c0; border:1px solid #2f9; font-family:Courier New; font-size:12px; padding:4px 8px;')

        v.addLayout(toolbar)

        # main grid widget
        self.grid_widget = SudokuGrid(self)
        v.addWidget(self.grid_widget)

        self.setLayout(v)

        # timers
        self.tick = QTimer(self)
        self.tick.timeout.connect(self._tick)
        self.tick.start(1000)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.grid_widget.tick_phase)
        self.anim_timer.start(80)

        # initial puzzle
        if should_auto_resume():
            try:
                self.load_game()
            except Exception:
                self.generate_and_apply(difficulty=self.difficulty_menu.currentText())
        else:
            self.generate_and_apply(difficulty=self.difficulty_menu.currentText())

    # UI callbacks
    def _on_new(self):
        self.generate_and_apply(difficulty=self.difficulty_menu.currentText())

    def _show_help(self):
        text = (
            "How to play Sudoku (Retro)\n\n"
            "- Click a cell or use arrow keys to move the selection.\n"
            "- Type 1-9 to set a number. Backspace/Delete clears a cell.\n"
            "- 'Hint' fills one correct cell for you. 'Undo' reverts recent changes.\n"
            "- Pencil: toggle Pencil and type to toggle candidate notes.\n"
            "- Use the difficulty menu before pressing New to choose puzzle density.\n"
            "- The game autosaves every 30s. Toggle 'Auto-resume' to auto-load on launch.\n\n"
            "Design notes:\nThis interface intentionally omits an on-screen number pad for a clean, keyboard-first experience."
        )
        QMessageBox.information(self, 'Sudoku — Help', text)

    def toggle_pencil(self, checked):
        self.pencil_mode = bool(checked)
        self.grid_widget.update()

    def _board_conflict(self, x, y):
        v = self.current[y][x]
        if v == 0:
            return False
        for ix in range(GRID):
            if ix != x and self.current[y][ix] == v:
                return True
        for iy in range(GRID):
            if iy != y and self.current[iy][x] == v:
                return True
        bx = (x // BOX) * BOX
        by = (y // BOX) * BOX
        for yy in range(by, by + BOX):
            for xx in range(bx, bx + BOX):
                if (xx, yy) != (x, y) and self.current[yy][xx] == v:
                    return True
        return False

    def _push_history(self):
        cur_copy = [row.copy() for row in self.current]
        cand_copy = [[set(c) for c in row] for row in self.candidates]
        self.history.append((cur_copy, cand_copy))
        if len(self.history) > 50:
            self.history.pop(0)

    def undo(self):
        if self.history:
            cur_copy, cand_copy = self.history.pop()
            self.current = cur_copy
            self.candidates = [[set(c) for c in row] for row in cand_copy]
            self.grid_widget.update()
            self.update_status()

    # game actions
    def clear_cell(self):
        x, y = self.selected
        if not self.givens[y][x]:
            self._push_history()
            self.current[y][x] = 0
            self.candidates[y][x].clear()
            self.grid_widget.update()
            self.update_status()

    def hint_fill(self):
        empties = [(x, y) for y in range(GRID) for x in range(GRID) if self.current[y][x] == 0]
        if not empties:
            return
        self._push_history()
        x, y = random.choice(empties)
        self.current[y][x] = self.solution[y][x]
        self.candidates[y][x].clear()
        self.grid_widget.update()
        self.update_status()

    def new_puzzle_dialog(self):
        self.generate_and_apply(difficulty=self.difficulty_menu.currentText())

    # game logic
    def generate_and_apply(self, difficulty='easy'):
        full = self._generate_full_grid()
        self.solution = full
        removals = {'easy': 30, 'medium': 40, 'hard': 50}.get(difficulty, 30)
        puzzle = self._make_unique_puzzle_from_solution(full, removals)
        self.puzzle = puzzle
        self.current = [row.copy() for row in puzzle]
        self.givens = [[bool(cell) for cell in row] for row in puzzle]
        self.timer_seconds = 0
        self.history = []
        self.candidates = [[set() for _ in range(GRID)] for _ in range(GRID)]
        self.update_status()
        self.grid_widget.update()

    def is_conflict(self, x, y):
        val = self.current[y][x]
        if val == 0:
            return False
        if self._board_conflict(x, y):
            return True
        if self.solution and self.solution[y][x] != 0 and self.current[y][x] != self.solution[y][x]:
            return True
        return False

    def _generate_full_grid(self):
        board = [[0] * GRID for _ in range(GRID)]
        nums = list(range(1, GRID + 1))

        def valid(b, r, c, v):
            for i in range(GRID):
                if b[r][i] == v or b[i][c] == v:
                    return False
            br = (r // BOX) * BOX
            bc = (c // BOX) * BOX
            for rr in range(br, br + BOX):
                for cc in range(bc, bc + BOX):
                    if b[rr][cc] == v:
                        return False
            return True

        def solve_cell(pos=0):
            if pos >= GRID * GRID:
                return True
            r = pos // GRID
            c = pos % GRID
            if board[r][c] != 0:
                return solve_cell(pos + 1)
            random.shuffle(nums)
            for v in nums:
                if valid(board, r, c, v):
                    board[r][c] = v
                    if solve_cell(pos + 1):
                        return True
                    board[r][c] = 0
            return False

        solve_cell()
        return board

    def _count_solutions(self, board, limit=2):
        b = [row.copy() for row in board]
        nums = list(range(1, GRID + 1))
        count = 0

        def valid_local(bd, r, c, v):
            for i in range(GRID):
                if bd[r][i] == v or bd[i][c] == v:
                    return False
            br = (r // BOX) * BOX
            bc = (c // BOX) * BOX
            for rr in range(br, br + BOX):
                for cc in range(bc, bc + BOX):
                    if bd[rr][cc] == v:
                        return False
            return True

        def solver(pos=0):
            nonlocal count
            if count >= limit:
                return
            if pos >= GRID * GRID:
                count += 1
                return
            r = pos // GRID
            c = pos % GRID
            if b[r][c] != 0:
                solver(pos + 1)
                return
            for v in nums:
                if valid_local(b, r, c, v):
                    b[r][c] = v
                    solver(pos + 1)
                    b[r][c] = 0
                    if count >= limit:
                        return

        solver(0)
        return count

    def _make_unique_puzzle_from_solution(self, sol, removals):
        puzzle = [row.copy() for row in sol]
        cells = [(x, y) for y in range(GRID) for x in range(GRID)]
        random.shuffle(cells)
        removed = 0
        for x, y in cells:
            if removed >= removals:
                break
            saved = puzzle[y][x]
            puzzle[y][x] = 0
            if self._count_solutions(puzzle, limit=2) != 1:
                puzzle[y][x] = saved
            else:
                removed += 1
        return puzzle

    # autosave / tick
    def _tick(self):
        self.timer_seconds += 1
        if self.timer_seconds > 0 and self.timer_seconds % AUTO_SAVE_SECONDS == 0:
            try:
                self.save_game()
            except Exception:
                pass
        self.update_status()

    def update_status(self):
        solved = all(self.current[y][x] != 0 and not self.is_conflict(x, y) for y in range(GRID) for x in range(GRID))
        state = 'SOLVED' if solved else 'PLAY'
        m, s = divmod(self.timer_seconds, 60)
        time_str = f"{m:02d}:{s:02d}"
        self.status.setText(f"{state} | Time {time_str} | Selected {self.selected[0]+1},{self.selected[1]+1}")

    # hints / utils
    def hint_fill_cell(self, x, y):
        if self.givens[y][x] or self.current[y][x] != 0:
            return False
        self.current[y][x] = self.solution[y][x]
        self.candidates[y][x].clear()
        self.grid_widget.update()
        self.update_status()
        return True

    def save_game(self):
        data = {
            'solution': self.solution,
            'puzzle': self.puzzle,
            'current': self.current,
            'givens': self.givens,
            'timer_seconds': self.timer_seconds
        }
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # save cfg
        self._save_cfg({'auto_resume': bool(self.auto_resume_chk.isChecked())})

    def load_game(self):
        if not os.path.exists(SAVE_PATH):
            return
        with open(SAVE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.solution = data.get('solution', self.solution)
        self.puzzle = data.get('puzzle', self.puzzle)
        self.current = data.get('current', self.current)
        self.givens = data.get('givens', self.givens)
        cand = data.get('candidates', None)
        if cand:
            self.candidates = [[set(cell) for cell in row] for row in cand]
        self.timer_seconds = data.get('timer_seconds', self.timer_seconds)
        self.grid_widget.update()
        self.update_status()

    # validation (kept for completeness)
    def validate_puzzle(self):
        for y in range(GRID):
            for x in range(GRID):
                if self.current[y][x] == 0 or self.is_conflict(x, y):
                    QMessageBox.information(self, 'Sudoku', 'Puzzle is not valid yet.')
                    return False
        QMessageBox.information(self, 'Sudoku', 'Puzzle looks valid!')
        return True

    # config helpers
    def _load_cfg(self):
        try:
            if os.path.exists(CFG_PATH):
                with open(CFG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {'auto_resume': True}

    def _save_cfg(self, cfg: dict):
        try:
            os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
            with open(CFG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def should_auto_resume():
    try:
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f).get('auto_resume', True)
    except Exception:
        pass
    return True


# compatibility alias for the menu
Sudoku = SudokuDialog


if __name__ == '__main__':
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        dlg = SudokuDialog()
        dlg.show()
        print('Sudoku module loaded')
    except Exception as e:
        print('Cannot run smoke test in this environment:', e)
