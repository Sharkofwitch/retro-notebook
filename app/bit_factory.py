from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QComboBox, QFileDialog, QSizePolicy, QListWidget, QListWidgetItem, QTextBrowser
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont
from enum import Enum
from random import randint, choice
import json, os

FACTORY_SAVE_PATH = os.path.join(os.path.dirname(__file__), '../notebooks/bit_factory_save.json')

BELT_DIRECTIONS = ['right', 'down', 'left', 'up']
BELT_SYMBOLS = {'right': '→', 'down': '↓', 'left': '←', 'up': '↑'}
BELT_COLORS = {'right': '#33ff66', 'down': '#33ff66', 'left': '#33ff66', 'up': '#33ff66'}

class ModuleType(Enum):
    EMPTY = 0
    GENERATOR = 1  # Erzeugt Energie
    BELT = 2       # Transportiert
    STORAGE = 3    # Speichert & verteilt
    ASSEMBLER = 4  # Wandelt um
    GARDEN = 5     # Verwandelt überschüssige Energie in Bit-Pflanzen
    RECYCLER = 6   # Wandelt alte Module in Energie um

class ResourceType(Enum):
    ENERGY = "energy"
    MODULES = "modules"
    PLANTS = "plants"
    HARMONY = "harmony"  # Neue "Zen"-Ressource

class BitFactory(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bit Garden – Zen Factory")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        self.grid_size = 8
        self.story_shown = False
        self.tick_interval = 2000
        self.paused = False
        self.harmony_goal = 10  # Ziel für nächsten Level
        self.init_game()
        self.init_ui()
        self.load_factory()
        self.update_status()
        self.init_timer()

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.tick_interval)

    def init_game(self):
        self.grid = [[{
            'type': ModuleType.EMPTY,
            'dir': 'right',
            'energy': 0,
            'modules': 0,
            'plants': 0,
            'active': False
        } for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        self.resources = {
            "energy": 0,
            "modules": 0,
            "plants": 0,
            "harmony": 0  # Now an integer
        }
        self.ticks = 0
        self.level = 1
        self.selected_module = ModuleType.GENERATOR

    def init_ui(self):
        vbox = QVBoxLayout()
        vbox.setContentsMargins(32, 32, 32, 32)
        # Statuszeile
        status_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.status_label.setStyleSheet('font-size:18px; color:#33ff66;')
        status_row.addWidget(self.status_label)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet('font-size:16px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px; padding:6px 18px;')
        self.pause_btn.clicked.connect(self.toggle_pause)
        status_row.addWidget(self.pause_btn)
        self.tick_btn = QPushButton("+1 Tick")
        self.tick_btn.setStyleSheet('font-size:16px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px; padding:6px 18px;')
        self.tick_btn.clicked.connect(self.manual_tick)
        status_row.addWidget(self.tick_btn)
        vbox.addLayout(status_row)
        # Story/Hilfe-Button
        self.story_label = QLabel()
        self.story_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.story_label.setStyleSheet('font-size:16px; color:#ffe066; margin:8px;')
        vbox.addWidget(self.story_label)
        # Grid
        self.grid_widget = BitFactoryGrid(self)
        vbox.addWidget(self.grid_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        # Modulauswahl
        hbox = QHBoxLayout()
        self.module_combo = QComboBox()
        self.module_combo.addItems(["Generator", "Förderband", "Speicher", "Assembler", "Entfernen"])
        self.module_combo.setStyleSheet('font-size:18px; background:#111; color:#33ff66; border:2px solid #33ff66; border-radius:6px; min-width:120px;')
        self.module_combo.currentTextChanged.connect(self.select_module)
        hbox.addWidget(QLabel("Modul:"))
        hbox.addWidget(self.module_combo)
        self.save_btn = QPushButton("Speichern")
        self.save_btn.setStyleSheet('font-size:16px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px; padding:6px 18px;')
        self.save_btn.clicked.connect(self.save_factory)
        hbox.addWidget(self.save_btn)
        self.load_btn = QPushButton("Laden")
        self.load_btn.setStyleSheet('font-size:16px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px; padding:6px 18px;')
        self.load_btn.clicked.connect(self.load_factory)
        hbox.addWidget(self.load_btn)
        self.help_btn = QPushButton("Hilfe/Story")
        self.help_btn.setStyleSheet('font-size:16px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:6px 18px;')
        self.help_btn.clicked.connect(self.show_story)
        hbox.addWidget(self.help_btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
            self.pause_btn.setText("Fortsetzen")
        else:
            self.timer.start(self.tick_interval)
            self.pause_btn.setText("Pause")

    def manual_tick(self):
        self.tick()

    def select_module(self, name):
        if name == "Generator":
            self.selected_module = ModuleType.GENERATOR
        elif name == "Förderband":
            self.selected_module = ModuleType.BELT
        elif name == "Speicher":
            self.selected_module = ModuleType.STORAGE
        elif name == "Assembler":
            self.selected_module = ModuleType.ASSEMBLER
        else:
            self.selected_module = ModuleType.EMPTY

    def tick(self):
        if self.paused:
            return

        # Phase 1: Generator-Produktion
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                cell = self.grid[y][x]
                if cell['type'] == ModuleType.GENERATOR:
                    cell['energy'] = min(cell['energy'] + 1, 5)  # Max 5 Energie pro Generator
                    cell['active'] = True

        # Phase 2: Transport (Förderbänder)
        self.process_belts()

        # Phase 3: Verarbeitung
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                cell = self.grid[y][x]
                
                if cell['type'] == ModuleType.STORAGE:
                    # Speicher verteilt Energie gleichmäßig
                    if cell['energy'] > 0:
                        self.distribute_energy(x, y)
                        cell['active'] = True
                
                elif cell['type'] == ModuleType.ASSEMBLER:
                    # Assembler wandelt Energie in Module um
                    if cell['energy'] >= 2:
                        cell['energy'] -= 2
                        cell['modules'] += 1
                        cell['active'] = True
                
                elif cell['type'] == ModuleType.GARDEN:
                    # Garten wandelt überschüssige Energie in Pflanzen
                    if cell['energy'] >= 3:
                        cell['energy'] -= 3
                        cell['plants'] += 1
                        self.resources['harmony'] += 0.1
                        cell['active'] = True
                
                elif cell['type'] == ModuleType.RECYCLER:
                    # Recycler wandelt alte Module zurück in Energie
                    if cell['modules'] >= 1:
                        cell['modules'] -= 1
                        cell['energy'] += 3
                        cell['active'] = True

        # Phase 4: Ressourcen sammeln und Harmonie berechnen
        self.collect_resources()
        self.check_harmony()
        
        self.ticks += 1
        self.update_status()
        
        # Visuelles Feedback zurücksetzen
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                self.grid[y][x]['active'] = False

    def process_belts(self):
        # Förderbänder transportieren Ressourcen in ihre Richtung
        moved = True
        while moved:  # Mehrere Durchgänge, bis nichts mehr bewegt wird
            moved = False
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    cell = self.grid[y][x]
                    if cell['type'] == ModuleType.BELT and (cell['energy'] > 0 or cell['modules'] > 0):
                        next_x, next_y = self.get_next_position(x, y, cell['dir'])
                        if self.is_valid_position(next_x, next_y):
                            target = self.grid[next_y][next_x]
                            if self.can_accept_resources(target):
                                self.move_resources(cell, target)
                                moved = True
                                cell['active'] = True

    def distribute_energy(self, x, y):
        # Speicher verteilt Energie an benachbarte Module
        directions = [(0,1), (1,0), (0,-1), (-1,0)]
        neighbors = []
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                target = self.grid[ny][nx]
                if target['type'] in [ModuleType.ASSEMBLER, ModuleType.GARDEN]:
                    neighbors.append(target)
        
        if neighbors:
            energy_per_neighbor = min(1, self.grid[y][x]['energy'] / len(neighbors))
            for neighbor in neighbors:
                if energy_per_neighbor >= 1:
                    self.grid[y][x]['energy'] -= 1
                    neighbor['energy'] += 1

    def check_harmony(self):
        # Prüfe, ob genug Harmonie für den nächsten Level erreicht wurde
        if self.resources['harmony'] >= self.harmony_goal:
            self.level_up()

    def level_up(self):
        # Level aufsteigen, neue Ziele setzen
        self.level += 1
        self.harmony_goal *= 1.5
        self.show_level_up_message()

    def show_level_up_message(self):
        msg = QDialog(self)
        msg.setWindowTitle("Level Up!")
        msg.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout()
        text = f"""
        <div style='text-align:center;'>
        <h2 style='color:#ffe066;'>Level {self.level} erreicht!</h2>
        <p>Deine Bit-Fabrik wächst in Harmonie.</p>
        <p>Neues Ziel: {self.harmony_goal:.1f} Harmonie</p>
        </div>
        """
        label = QLabel(text)
        layout.addWidget(label)
        ok_btn = QPushButton("Weiter")
        ok_btn.clicked.connect(msg.accept)
        layout.addWidget(ok_btn)
        msg.setLayout(layout)
        msg.exec()

    def update_status(self):
        self.status_label.setText(
            f"Level: {self.level} | "
            f"Harmonie: {self.resources['harmony']:.1f}/{self.harmony_goal:.1f} | "
            f"Energie: {self.resources['energy']} | "
            f"Module: {self.resources['modules']} | "
            f"Pflanzen: {self.resources['plants']}"
        )
        self.grid_widget.update()

    def show_story(self):
        dlg = BitFactoryHelp(self)
        dlg.exec()

    def mousePressEvent(self, event):
        self.story_label.setText("")
        self.story_shown = False

    def save_factory(self):
        data = {
            "grid": self.grid,
            "resources": self.resources,
            "ticks": self.ticks
        }
        with open(FACTORY_SAVE_PATH, 'w') as f:
            json.dump(data, f)
        self.story_label.setText("Fabrik gespeichert!")

    def load_factory(self):
        if os.path.exists(FACTORY_SAVE_PATH):
            with open(FACTORY_SAVE_PATH, 'r') as f:
                data = json.load(f)
            loaded_grid = data.get("grid", self.grid)
            # Ensure all cells are valid dicts with required fields
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    cell = None
                    try:
                        cell = loaded_grid[y][x]
                    except Exception:
                        pass
                    if not isinstance(cell, dict):
                        # Replace None or invalid with default
                        loaded_grid[y][x] = {
                            'type': ModuleType.EMPTY,
                            'dir': 'right',
                            'energy': 0,
                            'modules': 0,
                            'plants': 0,
                            'active': False
                        }
                    else:
                        # Ensure all required fields exist
                        for k, v in {
                            'type': ModuleType.EMPTY,
                            'dir': 'right',
                            'energy': 0,
                            'modules': 0,
                            'plants': 0,
                            'active': False
                        }.items():
                            if k not in loaded_grid[y][x]:
                                loaded_grid[y][x][k] = v
                        # Convert 'type' from int/string to ModuleType if needed
                        if not isinstance(loaded_grid[y][x]['type'], ModuleType):
                            try:
                                loaded_grid[y][x]['type'] = ModuleType(loaded_grid[y][x]['type'])
                            except Exception:
                                loaded_grid[y][x]['type'] = ModuleType.EMPTY
            self.grid = loaded_grid
            self.resources = data.get("resources", self.resources)
            self.ticks = data.get("ticks", 0)
            # Fehlende Felder ergänzen (z.B. harmony)
            if 'harmony' not in self.resources:
                self.resources['harmony'] = 0
            if 'plants' not in self.resources:
                self.resources['plants'] = 0
            self.story_label.setText("Fabrik geladen!")
        else:
            self.story_label.setText("")
        self.update_status()

    def is_valid_position(self, x, y):
        return 0 <= x < self.grid_size and 0 <= y < self.grid_size

    def can_accept_resources(self, cell):
        return (cell['type'] != ModuleType.GENERATOR and 
                cell['type'] != ModuleType.EMPTY and
                cell['energy'] < 5)  # Max 5 Energie pro Zelle

    def move_resources(self, source, target):
        # Bewegt Ressourcen von einer Zelle zur anderen
        if source['energy'] > 0 and target['energy'] < 5:
            target['energy'] += 1
            source['energy'] -= 1
        if source['modules'] > 0:
            target['modules'] += 1
            source['modules'] -= 1

    def collect_resources(self):
        # Sammelt Ressourcen aus allen Zellen
        total_energy = 0
        total_modules = 0
        total_plants = 0
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                cell = self.grid[y][x]
                total_energy += cell['energy']
                total_modules += cell['modules']
                total_plants += cell['plants']
                
        self.resources['energy'] = total_energy
        self.resources['modules'] = total_modules
        self.resources['plants'] = total_plants

    def get_next_position(self, x, y, direction):
        if direction == 'right':
            return x + 1, y
        elif direction == 'down':
            return x, y + 1
        elif direction == 'left':
            return x - 1, y
        else:  # up
            return x, y - 1

class BitFactoryGrid(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.game = parent
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    def mousePressEvent(self, event):
        cell_size = self.width() // self.game.grid_size
        x = event.x() // cell_size
        y = event.y() // cell_size
        if 0 <= x < self.game.grid_size and 0 <= y < self.game.grid_size:
            cell = self.game.grid[y][x]
            if self.game.selected_module == ModuleType.BELT:
                # Drehe Richtung, wenn bereits Belt
                if cell['type'] == ModuleType.BELT:
                    idx = BELT_DIRECTIONS.index(cell['dir'])
                    cell['dir'] = BELT_DIRECTIONS[(idx+1)%4]
                else:
                    cell['type'] = ModuleType.BELT
                    cell['dir'] = self.game.selected_belt_dir
            elif self.game.selected_module == ModuleType.EMPTY:
                cell['type'] = ModuleType.EMPTY
            else:
                cell['type'] = self.game.selected_module
            self.game.update_status()
    def paintEvent(self, event):
        qp = QPainter(self)
        grid_size = self.game.grid_size
        w = self.width() // grid_size
        h = self.height() // grid_size
        for y in range(grid_size):
            for x in range(grid_size):
                cell = self.game.grid[y][x]
                mtype = cell['type']
                if mtype == ModuleType.GENERATOR:
                    qp.setPen(QColor('#ffe066'))
                    qp.setFont(QFont('Courier New', 24, QFont.Weight.Bold))
                    qp.drawText(x*w+8, y*h+32, '⚡')
                elif mtype == ModuleType.BELT:
                    qp.setPen(QColor(BELT_COLORS[cell['dir']]))
                    qp.setFont(QFont('Courier New', 24, QFont.Weight.Bold))
                    qp.drawText(x*w+8, y*h+32, BELT_SYMBOLS[cell['dir']])
                elif mtype == ModuleType.STORAGE:
                    qp.setPen(QColor('#66ccff'))
                    qp.setFont(QFont('Courier New', 24, QFont.Weight.Bold))
                    qp.drawText(x*w+8, y*h+32, '□')
                elif mtype == ModuleType.ASSEMBLER:
                    qp.setPen(QColor('#ff3366'))
                    qp.setFont(QFont('Courier New', 24, QFont.Weight.Bold))
                    qp.drawText(x*w+8, y*h+32, '✚')
                qp.setPen(QColor('#444'))
                qp.drawRect(x*w, y*h, w, h)

class BitFactoryHelp(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bit Factory – Hilfe & Story")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        self.resize(600, 480)
        layout = QHBoxLayout()
        self.menu = QListWidget()
        self.menu.setStyleSheet('font-size:20px; background:#111; color:#33ff66; border:none;')
        self.menu.setFixedWidth(210)
        self.menu.addItem(QListWidgetItem("Über das Spiel"))
        self.menu.addItem(QListWidgetItem("Story"))
        self.menu.addItem(QListWidgetItem("Module & Symbole"))
        self.menu.addItem(QListWidgetItem("Tipps & Strategie"))
        self.menu.currentRowChanged.connect(self.show_section)
        layout.addWidget(self.menu)
        self.text = QTextBrowser()
        self.text.setStyleSheet('font-size:18px; background:#181818; color:#ffe066; border:none; padding:18px;')
        layout.addWidget(self.text)
        self.setLayout(layout)
        self.menu.setCurrentRow(0)
        close_btn = QPushButton("Schließen")
        close_btn.setStyleSheet('font-size:18px; padding:10px; background:#222; color:#33ff66; border:2px solid #33ff66; border-radius:8px;')
        close_btn.clicked.connect(self.accept)
        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addWidget(close_btn)
        self.setLayout(vbox)

    def show_section(self, idx):
        if idx == 0:
            self.text.setHtml(
                """
<h2 style='color:#33ff66;'>Bit Factory – Das entspannte Retro-Aufbauspiel</h2>
<hr style='border:1px solid #33ff66;'>
<p>Baue auf einem digitalen Grid eine funktionierende Bit-Fabrik.<br>
Produziere Energie, Module und optimiere deine Produktion.<br>
Keine Gegner, kein Zeitdruck – nur du, deine Fabrik und der Flow!</p>
<p style='color:#66ccff;'><b>Wähle links ein Thema für Details!</b></p>
"""
            )
        elif idx == 1:
            self.text.setHtml(
                """
<h2 style='color:#33ff66;'>Story</h2>
<hr style='border:1px solid #33ff66;'>
<p>Im Daten-Nirvana, einer vergessenen Retro-Welt, liegt eine alte Bit-Fabrik brach.<br>
Du bist der neue Operator! Deine Aufgabe: Die Fabrik wieder zum Laufen bringen, Energie und Module produzieren, neue Technologien freischalten und das digitale Ödland in eine blühende Bit-Oase verwandeln.<br>
Mit jedem Fortschritt schaltest du neue Module, Upgrades und Story-Events frei.<br>
</p>
<div style='color:#ffe066; background:#222; border-radius:6px; padding:8px; margin-top:12px;'>
<b>Dein Ziel:</b> Baue, optimiere, experimentiere – und bring die Retro-Fabrik zum Blühen!</div>
"""
            )
        elif idx == 2:
            self.text.setHtml(
                """
<h2 style='color:#33ff66;'>Module & Symbole</h2>
<hr style='border:1px solid #33ff66;'>
<ul style='font-size:18px;'>
<li><span style='color:#ffe066;'>⚡ <b>Generator</b></span>: Erzeugt Energie pro Tick.</li>
<li><span style='color:#33ff66;'>→ <b>Förderband</b></span>: (später) Transportiert Ressourcen.</li>
<li><span style='color:#66ccff;'>□ <b>Speicher</b></span>: (später) Lagert Ressourcen.</li>
<li><span style='color:#ff3366;'>✚ <b>Assembler</b></span>: Wandelt Energie in Module um.</li>
</ul>
<p><b>Bedienung:</b><br>
- Modul auswählen, auf das Grid klicken zum Platzieren.<br>
- Mit "Entfernen" löschst du Module.<br>
- "Speichern"/"Laden" sichern deinen Fortschritt.</p>
"""
            )
        elif idx == 3:
            self.text.setHtml(
                """
<h2 style='color:#33ff66;'>Tipps & Strategie</h2>
<hr style='border:1px solid #33ff66;'>
<ul style='font-size:18px;'>
<li>Starte mit Generatoren, um Energie zu erzeugen.</li>
<li>Setze Assembler, um Energie in Module zu verwandeln.</li>
<li>Experimentiere mit der Anordnung für maximale Effizienz.</li>
<li>Später kannst du Förderbänder und Speicher nutzen, um komplexere Fabriken zu bauen.</li>
<li>Es gibt keine Zeitlimits – optimiere in deinem Tempo!</li>
</ul>
<div style='color:#ffe066; background:#222; border-radius:6px; padding:8px; margin-top:12px;'>
<b>Tipp:</b> Speichere regelmäßig, damit deine Fabrik nicht verloren geht!</div>
"""
            )
