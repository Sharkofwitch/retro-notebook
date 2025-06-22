from PySide6.QtWidgets import QApplication, QWidget, QBoxLayout, QLineEdit, QPushButton, QLabel
import sys

def start_app():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Retro Notebook")

    layout = QBoxLayout()

    input_field = QLineEdit()
    layout.addWidget(input_field)

    run_button = QPushButton("Run")
    layout.addWidget(run_button)

    output_label = QLabel("")
    layout.addWidget(output_label)

    def on_run():
        text = input_field.text()
        output_label.setText(f"Output: {text}")

    run_button.clicked.connect(on_run)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())
