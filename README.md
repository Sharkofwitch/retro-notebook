# retro-notebook

Ein retro-inspiriertes Desktop-Notebook für Code, Mathematik und Lernen.

## Features
- Retro-Optik (schwarz/grün, Pixel-Look, ASCII-Design)
- Zellen für Code und Markdown
- Eigener Interpreter für mathematische Ausdrücke, Variablen, Funktionen, Schleifen, Bedingungen
- Soundeffekte beim Ausführen und Starten
- About-Fenster im Retro-Stil
- Notebook speichern und laden (JSON)
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

## Beispiel-Workflow
- Neue Zelle anlegen, mathematischen Ausdruck eingeben (z.B. `LET x = 2+2`)
- Auf "Run" klicken, Ergebnis erscheint darunter
- Variablen, eigene Funktionen, Bedingungen und Schleifen möglich:
  ```
  LET x = 5
  PRINT sqrt(x)
  DEF f(a) = a^2 + 1
  PRINT f(3)
  FOR i = 1 TO 3
      PRINT i
  NEXT
  ```
- Notebook kann gespeichert und wieder geladen werden

## To-Do / Ideen
- Export als HTML/PDF
- Drag & Drop für Zellen
- Undo/Redo
- Farbschema-Auswahl (verschiedene Retro-Themes)
- Virtuelle Statusleiste/LED
- Easter Eggs (z.B. Minispiel)

---

(c) 2025 by Jakob Szarkowicz & Contributors
MIT License, siehe LICENSE
