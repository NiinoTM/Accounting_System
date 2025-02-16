import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QCalendarWidget, QLabel, QPushButton, QHBoxLayout # Import QDialog
from PySide6.QtCore import QDate

class DateSelectWindow(QDialog):  # Inherit from QDialog
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select Date")
        self.setMinimumSize(300, 250)

        layout = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked[QDate].connect(self.show_selected_date)

        self.label = QLabel("Selected Date: ")

        # Add OK and Cancel buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)  # Connect to built-in accept slot
        self.cancel_button.clicked.connect(self.reject)  # Connect to built-in reject slot
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        

        layout.addWidget(self.calendar)
        layout.addWidget(self.label)
        layout.addLayout(button_layout)  # Add the button layout

        self.setLayout(layout)

    def show_selected_date(self, date):
        self.label.setText(f"Selected Date: {date.toString('yyyy-MM-dd')}")

def main():
    app = QApplication(sys.argv)
    window = DateSelectWindow()
    window.show()  # Keep show() for standalone testing
    sys.exit(app.exec())

if __name__ == "__main__":
    main()