from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QComboBox, QListWidget, QListWidgetItem, QTextBrowser, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap
from enum import Enum
import random, json, os

FACTORY_SAVE_PATH = os.path.join(os.path.dirname(__file__), '../notebooks/bit_factory_save.json')

class TileType(Enum):
    EMPTY = 0
    FIELD = 1
    PLANT = 2
    HOUSE = 3
    FACTORY = 4
    ROAD = 5
    NPC = 6
    WATER = 7
    TREE = 8

class ResourceType(Enum):
    COINS = 'coins'
    FOOD = 'food'
    SEEDS = 'seeds'
    XP = 'xp'
    ENERGY = 'energy'

class NPC:
    def __init__(self, name, quest=None):
        self.name = name
        self.quest = quest or {}
        self.x = 0
        self.y = 0
        self.active = True

class BitFactory(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bit Valley – Retro Farm & City")
        self.setStyleSheet("background:#0d0d0d; color:#33ff66; font-family:Courier New,monospace;")
        self.grid_size = 12
        self.tick_interval = 4000  # Noch langsamer
        self.day = 1
        self.hour = 6
        self.is_night = False
        self.resources = {r.value: 0 for r in ResourceType}
        self.resources['coins'] = 5
        self.resources['seeds'] = 1
        self.resources['food'] = 0
        self.resources['xp'] = 0
        self.resources['energy'] = 5
        self.unlocked = {'FIELD': True, 'PLANT': True, 'HOUSE': False, 'ROAD': False, 'TREE': False, 'WATER': False}
        self.npcs = []
        self.tutorial_shown = False
        self.init_game()
        self.init_ui()
        self.init_timer()
        self.show_tutorial()
        self.endless_quest_counter = 0
        self.max_npcs = 3
        self.crafting_recipes = {
            'HOUSE': {'food': 3, 'coins': 10},
            'ROAD': {'coins': 2},
            'TREE': {'coins': 1},
            'WATER': {'coins': 3},
        }

    def show_tutorial(self):
        if self.tutorial_shown:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Tutorial – Bit Valley")
        v = QVBoxLayout()
        l = QLabel(
            "<b>Willkommen in Bit Valley!</b><br><br>"
            "Ziel: Baue eine kleine Farm, sammle Ressourcen und erfülle Quests.<br>"
            "<ul>"
            "<li><b>Feld pflanzen:</b> Wähle 'Feld pflanzen', klicke auf ein gelbes Feld.</li>"
            "<li><b>Ernten:</b> Wähle 'Ernten', klicke auf eine reife Pflanze (grün).</li>"
            "<li><b>Haus/Straße/Baum/Wasser:</b> Wähle die Aktion, klicke auf ein leeres Feld.</li>"
            "<li><b>NPCs:</b> Klicke auf '@', um Quests zu sehen und Belohnungen zu erhalten.</li>"
            "<li><b>Tag beenden:</b> Klick auf 'Tag beenden', um Zeit zu überspringen.</li>"
            "</ul>"
            "<b>Tipp:</b> Ressourcen und Aktionen werden oben angezeigt. Alles ist rückgängig machbar – einfach ausprobieren!"
        )
        l.setWordWrap(True)
        l.setStyleSheet('font-size:16px; color:#ffe066;')
        v.addWidget(l)
        ok = QPushButton("Los geht's!")
        ok.clicked.connect(dlg.accept)
        v.addWidget(ok)
        dlg.setLayout(v)
        dlg.exec()
        self.tutorial_shown = True

    def show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Hilfe & Erklärung – Bit Valley")
        v = QVBoxLayout()
        l = QLabel(
            "<b>Bit Valley – Das entspannte Retro-Aufbauspiel</b><br><br>"
            "<b>Spielprinzip:</b> Baue Felder, ernte Pflanzen, baue Häuser und erfülle Quests für NPCs.<br>"
            "<ul>"
            "<li>Jede Aktion kostet Ressourcen (Coins, Seeds, Energie).</li>"
            "<li>Pflanzen wachsen über mehrere Ticks (Stufen: . → i → Y → Ψ).</li>"
            "<li>NPCs geben Aufgaben und Belohnungen.</li>"
            "<li>Mit XP schaltest du neue Aktionen frei.</li>"
            "<li>Das Spiel ist rundenbasiert, kein Zeitdruck.</li>"
            "</ul>"
            "<b>Steuerung:</b> Aktion wählen, dann auf das Grid klicken.<br>"
            "<b>Alles ist logisch und einfach gehalten – probiere es aus!</b>"
        )
        l.setWordWrap(True)
        l.setStyleSheet('font-size:16px; color:#33ff66;')
        v.addWidget(l)
        ok = QPushButton("Schließen")
        ok.clicked.connect(dlg.accept)
        v.addWidget(ok)
        dlg.setLayout(v)
        dlg.exec()

    def generate_map(self):
        # Leere Map
        self.grid = [[{'type': TileType.EMPTY, 'growth': 0, 'owner': None} for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        # Ein Startfeld in der Mitte
        mid = self.grid_size // 2
        self.grid[mid][mid]['type'] = TileType.FIELD
        # Start-NPC
        npc = NPC("Bitty", quest={'goal': 'Ernte 1 Pflanze', 'progress': 0, 'target': 1, 'reward': {'coins': 5, 'seeds': 1, 'unlock': 'HOUSE'}, 'type': 'food'})
        npc.x, npc.y = mid, mid-1
        self.npcs = [npc]

    def init_game(self):
        self.generate_map()

    def init_ui(self):
        vbox = QVBoxLayout()
        self.status_label = QLabel()
        self.status_label.setStyleSheet('font-size:16px; color:#33ff66;')
        vbox.addWidget(self.status_label)
        self.grid_widget = BitFactoryGrid(self)
        vbox.addWidget(self.grid_widget)
        hbox = QHBoxLayout()
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Feld pflanzen", "Ernten", "Haus bauen", "Straße bauen", "Baum pflanzen", "Wasser", "Nichts"])
        hbox.addWidget(self.action_combo)
        self.help_btn = QPushButton("Hilfe/Erklärung")
        self.help_btn.clicked.connect(self.show_help)
        hbox.addWidget(self.help_btn)
        self.end_day_btn = QPushButton("Tag beenden")
        self.end_day_btn.clicked.connect(self.end_day)
        hbox.addWidget(self.end_day_btn)
        # Zurück-zum-Menü-Button
        self.back_btn = QPushButton("Zurück zum Hauptmenü")
        self.back_btn.setStyleSheet('font-size:16px; background:#222; color:#ffe066; border:2px solid #ffe066; border-radius:8px; padding:6px 18px;')
        self.back_btn.clicked.connect(self.close)
        hbox.addWidget(self.back_btn)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.update_status()

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(self.tick_interval)

    def tick(self):
        self.hour += 1
        if self.hour == 18:
            self.is_night = True
        if self.hour == 6:
            self.is_night = False
        if self.hour >= 24:
            self.hour = 6
            self.day += 1
            self.resources['energy'] = min(self.resources['energy'] + 3, 10)
            if len(self.npcs) < self.max_npcs:
                self.spawn_npc()
        # Pflanzen wachsen nur am Tag
        if not self.is_night:
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    cell = self.grid[y][x]
                    if cell['type'] == TileType.PLANT and cell['growth'] < 3:
                        cell['growth'] += 1
        # Quests prüfen und Fortschritt updaten
        for npc in self.npcs:
            if npc.active and 'type' in npc.quest:
                if npc.quest['type'] == 'food':
                    npc.quest['progress'] = self.resources['food']
                elif npc.quest['type'] == 'fields':
                    npc.quest['progress'] = sum(1 for row in self.grid for c in row if c['type'] == TileType.FIELD)
                elif npc.quest['type'] == 'trees':
                    npc.quest['progress'] = sum(1 for row in self.grid for c in row if c['type'] == TileType.TREE)
        self.update_status()
        self.grid_widget.update()

    def spawn_npc(self):
        # Endlos generierte Quests
        self.endless_quest_counter += 1
        quest_types = [
            ('Ernte', 'food', random.randint(2, 6), {'coins': random.randint(5, 15), 'xp': random.randint(2, 8)}),
            ('Baue Felder', 'fields', random.randint(2, 5), {'coins': random.randint(4, 10), 'xp': random.randint(2, 6)}),
            ('Pflanze Bäume', 'trees', random.randint(1, 4), {'coins': random.randint(3, 8), 'xp': random.randint(1, 5)})
        ]
        q = random.choice(quest_types)
        quest = {'goal': f'{q[0]} {q[2]}', 'progress': 0, 'target': q[2], 'reward': q[3], 'type': q[1]}
        npc = NPC(f"Bitty-{self.endless_quest_counter}", quest=quest)
        # Zufällige freie Position
        while True:
            x, y = random.randint(0, self.grid_size-1), random.randint(0, self.grid_size-1)
            if self.grid[y][x]['type'] == TileType.EMPTY:
                npc.x, npc.y = x, y
                break
        self.npcs.append(npc)

    def end_day(self):
        self.hour = 6
        self.day += 1
        self.resources['energy'] = min(self.resources['energy'] + 5, 20)
        self.update_status()
        self.grid_widget.update()

    def update_status(self):
        self.status_label.setText(f"Tag: {self.day} | Uhrzeit: {self.hour}:00 | Coins: {self.resources['coins']} | Seeds: {self.resources['seeds']} | Food: {self.resources['food']} | XP: {self.resources['xp']} | Energy: {self.resources['energy']}")

    def unlock(self, name):
        self.unlocked[name] = True
        self.update_status()
        self.grid_widget.update()

    def interact_npc(self, npc):
        msg = QDialog(self)
        msg.setWindowTitle(f"NPC: {npc.name}")
        v = QVBoxLayout()
        l = QLabel(f"Quest: {npc.quest['goal']}<br>Fortschritt: {npc.quest['progress']}/{npc.quest['target']}")
        l.setStyleSheet('font-size:16px; color:#ffe066;')
        v.addWidget(l)
        if npc.quest['progress'] >= npc.quest['target']:
            btn = QPushButton("Belohnung abholen!")
            def claim():
                for k, v_ in npc.quest['reward'].items():
                    if k == 'unlock':
                        self.unlock(v_)
                    else:
                        self.resources[k] += v_
                npc.active = False
                msg.accept()
                self.update_status()
            btn.clicked.connect(claim)
            v.addWidget(btn)
        # Crafting-Button
        if self.unlocked.get('HOUSE') and not self.unlocked.get('ROAD'):
            craft_btn = QPushButton("Straße freischalten (2 Coins)")
            def craft():
                if self.resources['coins'] >= 2:
                    self.resources['coins'] -= 2
                    self.unlock('ROAD')
                    msg.accept()
                    self.update_status()
            craft_btn.clicked.connect(craft)
            v.addWidget(craft_btn)
        ok = QPushButton("OK")
        ok.clicked.connect(msg.accept)
        v.addWidget(ok)
        msg.setLayout(v)
        msg.exec()

class BitFactoryGrid(QWidget):
    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.setMinimumSize(600, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)
        self.setUpdatesEnabled(True)
        # Unicode/ASCII Icons als Fallback
        self.ascii_icons = {
            'FIELD': '▦',
            'PLANT0': '.',
            'PLANT1': 'i',
            'PLANT2': 'Y',
            'PLANT3': 'Ψ',
            'HOUSE': '⌂',
            'ROAD': '=',
            'TREE': '♣',
            'WATER': '~',
            'NPC': '@',
        }

    def paintEvent(self, event):
        self.setUpdatesEnabled(False)
        qp = QPainter(self)
        grid_size = self.game.grid_size
        w = self.width() // grid_size
        h = self.height() // grid_size
        # Tag/Nacht-Visualisierung
        if self.game.is_night:
            qp.fillRect(0, 0, self.width(), self.height(), QColor(10, 10, 30, 220))
        for y in range(grid_size):
            for x in range(grid_size):
                cell = self.game.grid[y][x]
                t = cell['type']
                qp.setPen(QColor('#222'))
                qp.setBrush(QColor('#0d0d0d'))
                qp.drawRect(x*w, y*h, w, h)
                # Unicode/ASCII-Icons zeichnen
                if t == TileType.FIELD:
                    qp.setPen(QColor('#ffe066'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons['FIELD'])
                elif t == TileType.PLANT:
                    g = cell.get('growth', 0)
                    qp.setPen(QColor('#33ff66'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons[f'PLANT{min(g,3)}'])
                elif t == TileType.HOUSE:
                    qp.setPen(QColor('#66ccff'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons['HOUSE'])
                elif t == TileType.ROAD:
                    qp.setPen(QColor('#888'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons['ROAD'])
                elif t == TileType.TREE:
                    qp.setPen(QColor('#00ff99'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons['TREE'])
                elif t == TileType.WATER:
                    qp.setPen(QColor('#3399ff'))
                    qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                    qp.drawText(x*w+w//4, y*h+int(h*0.75), self.ascii_icons['WATER'])
        # NPCs
        for npc in self.game.npcs:
            if npc.active:
                qp.setPen(QColor('#ff33cc'))
                qp.setFont(QFont('Courier New', int(h*0.7), QFont.Weight.Bold))
                qp.drawText(npc.x*w+w//4, npc.y*h+int(h*0.75), self.ascii_icons['NPC'])
        qp.end()
        self.setUpdatesEnabled(True)

    def mousePressEvent(self, event):
        grid_size = self.game.grid_size
        w = self.width() // grid_size
        h = self.height() // grid_size
        x = event.x() // w
        y = event.y() // h
        if 0 <= x < grid_size and 0 <= y < grid_size:
            action = self.game.action_combo.currentText()
            cell = self.game.grid[y][x]
            # Nur erlaubte Aktionen
            if action == "Feld pflanzen" and self.game.unlocked['FIELD'] and self.game.resources['seeds'] > 0 and cell['type'] == TileType.FIELD:
                cell['type'] = TileType.PLANT
                cell['growth'] = 0
                self.game.resources['seeds'] -= 1
            elif action == "Ernten" and cell['type'] == TileType.PLANT and cell['growth'] >= 3:
                cell['type'] = TileType.FIELD
                cell['growth'] = 0
                self.game.resources['food'] += 1
            elif action == "Straße bauen" and self.game.unlocked['ROAD'] and self.game.resources['coins'] >= 2 and cell['type'] == TileType.EMPTY:
                cell['type'] = TileType.ROAD
                self.game.resources['coins'] -= 2
            elif action == "Haus bauen" and self.game.unlocked['HOUSE'] and self.game.resources['food'] >= 3 and self.game.resources['coins'] >= 10 and cell['type'] == TileType.EMPTY:
                cell['type'] = TileType.HOUSE
                self.game.resources['food'] -= 3
                self.game.resources['coins'] -= 10
            elif action == "Baum pflanzen" and self.game.unlocked['TREE'] and self.game.resources['coins'] >= 1 and cell['type'] == TileType.EMPTY:
                cell['type'] = TileType.TREE
                self.game.resources['coins'] -= 1
            elif action == "Wasser" and self.game.unlocked['WATER'] and self.game.resources['coins'] >= 3 and cell['type'] == TileType.EMPTY:
                cell['type'] = TileType.WATER
                self.game.resources['coins'] -= 3
            self.game.update_status()
            self.update()
        # NPC-Interaktion
        for npc in self.game.npcs:
            if npc.active and npc.x == x and npc.y == y:
                self.game.interact_npc(npc)

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
