from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from app.interpreter import eval_expr

class NotebookCell(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        # Eingabe mehrzeilig
        self.input = QTextEdit()
        self.layout.addWidget(self.input)

        # Ausführen-Button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.execute)
        self.layout.addWidget(self.run_button)

        # Ausgabe (initial leer)
        self.output = QLabel("")
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)

    def execute(self):
        code = self.input.toPlainText()
        result = eval_expr(code)
        self.output.setText(f"Result: {result}")