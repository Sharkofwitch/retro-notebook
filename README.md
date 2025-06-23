# retro-notebook

Ein retro-inspiriertes Desktop-Notebook für Code, Mathematik und Lernen.

## Features
- Retro-Optik (schwarz/grün, Pixel-Look, ASCII-Design)
- Zellen für Code und Markdown
- Eigener Interpreter für mathematische Ausdrücke, Variablen, Listen, Strings, Funktionen, Bedingungen, Schleifen
- Grafikbefehle: Punkte, Linien, Kreise (z.B. zum Plotten von Daten)
- Soundeffekte beim Ausführen und Starten
- About-Fenster im Retro-Stil
- Notebook speichern und laden (JSON)
- Fehlerabfang und Endlosschleifen-Schutz
- Beispiel-Workflow im Ordner `docs/notebooks/`

## Installation
1. Python 3.10+ installieren
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Starten:
   ```bash
   python run.py
   ```

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

## Hinweise
- Alle Grafikbefehle in einer Codezelle werden als ein Bild angezeigt.
- WHILE/ENDWHILE und FOR/NEXT unterstützen Blöcke.
- Fehler in Schleifen oder Grafikbefehlen brechen die Ausführung ab.
- Maximal 1000 WHILE-Durchläufe (Schutz vor Endlosschleifen).

## To-Do / Ideen
- Export als HTML/PDF
- Drag & Drop für Zellen
- Undo/Redo
- Farbschema-Auswahl (verschiedene Retro-Themes)
- Virtuelle Statusleiste/LED
- Animationen und WAIT-Befehl
- Easter Eggs (z.B. Minispiel)

---

(c) 2025 by Jakob Szarkowicz & Contributors
MIT License, siehe LICENSE
