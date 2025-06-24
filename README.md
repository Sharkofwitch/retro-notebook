# retro-notebook

Ein modernes, retro-inspiriertes Desktop-Notebook für Code, Mathematik, Logik und Minigames.

## Features
- Hochwertige Retro-Optik (CRT-Look, Scanlines, Glow, animierte Pixel, Retro-Icons)
- Zellen für Code (eigener Interpreter) und Markdown
- Eigener Interpreter für mathematische Ausdrücke, Variablen, Listen, Strings, Funktionen, Bedingungen, Schleifen
- Grafikbefehle: Punkte, Linien, Kreise (z.B. zum Plotten von Daten)
- Soundeffekte beim Ausführen und Starten
- Notebook speichern und laden (JSON)
- Fehlerabfang und Endlosschleifen-Schutz
- Minigames: **CodeGrid** (Logikpuzzle, mehrere Spielmodi, Daily Challenge, XP, Highscore, Achievements, Seed-System), **Bit Factory** (Survival Builder)
- Fortschrittssystem: XP, Highscore, Achievements, Daily Challenge
- Animierte, atmosphärische Startseite und Menüs im Retro-Stil
- About-Fenster im Retro-Stil
- Drag & Drop für Zellen
- Mac-kompatibel: Ressourcen-Handling für App-Bundle vorbereitet
- Beispiel-Workflow im Ordner `docs/notebooks/`

## Installation & Start
1. Python 3.10+ installieren
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Starten:
   ```bash
   python run.py
   ```

### Als macOS-App (Bundle)
- Die App ist vorbereitet für PyInstaller, py2app oder Briefcase.
- Alle Ressourcen werden über `resource_path` geladen (funktioniert im Bundle und im Dev-Modus).
- Für ein App-Bundle: Siehe Beispiel-Specfile oder py2app-Setup (nicht im Repo enthalten).

## Sprache & Beispiele
- Variablen und Listen:
  ```
  LET x = 5
  LET arr = [10, 20, 30]
  LET arr[1] = 42
  PRINT arr[1]
  ```
- Schleifen und Bedingungen:
  ```
  LET i = 0
  WHILE i < 5 DO
      PRINT i
      LET i = i + 1
  ENDWHILE
  IF x > 3 THEN
      PRINT "x ist groß"
  ELSE
      PRINT "x ist klein"
  ENDIF
  ```
- Grafikbefehle (alle in einem Block werden gemeinsam angezeigt):
  ```
  LET arr = [20, 34, 29, 40, 32]
  LET i = 0
  WHILE i < len(arr) - 1 DO
      LET x1 = i * 20
      LET y1 = arr[i]
      LET x2 = (i + 1) * 20
      LET y2 = arr[i + 1]
      LINE x1, y1, x2, y2
      LET i = i + 1
  ENDWHILE
  ```
- Eingebaute Funktionen: `len`, `str`, `int`, `float`, `list`, `ord`, `chr`, `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`
- Minigames: Im Hauptmenü auswählbar, Fortschritt wird gespeichert.

## Hinweise
- Alle Grafikbefehle in einer Codezelle werden als ein Bild angezeigt.
- WHILE/ENDWHILE, FOR/NEXT und IF/ELSE/ENDIF unterstützen Blöcke.
- Fehler in Schleifen oder Grafikbefehlen brechen die Ausführung ab.
- Maximal 1000 WHILE-Durchläufe (Schutz vor Endlosschleifen).
- Ressourcen werden immer über `resource_path` geladen (auch im App-Bundle).

## To-Do / Ideen
- Export als HTML/PDF
- Undo/Redo für Zellen
- Farbschema-Auswahl (verschiedene Retro-Themes)
- Virtuelle Statusleiste/LED
- Noch mehr Animationen und Retro-Effekte
- Weitere Minigames und Easter Eggs
- Bessere macOS-Integration (Dock-Icon, Info.plist, App-Icon)

---

(c) 2025 by Jakob Szarkowicz & Contributors
MIT License, siehe LICENSE
