import json

def save_notebook(cells, filename):
    data = []
    for cell in cells:
        data.append({
            "input": cell.input.toPlainText(),
            "output": cell.output.text()
        })
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_notebook(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)  # gibt eine Liste von Zellen zurück