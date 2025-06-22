import json

def save_notebook(cells, filename):
    data = []
    for cell in cells:
        cell_type = cell.cell_type.currentText()
        entry = {
            "type": cell_type.lower(),
            "input": cell.input.toPlainText()
        }
        if cell_type == "Code":
            entry["output"] = cell.output.text()
        data.append(entry)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_notebook(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)  # gibt eine Liste von Zellen zurück