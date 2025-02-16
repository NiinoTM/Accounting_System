# libraries
import sys
from PySide6.QtWidgets import QApplication

# modules
from data.create_database import create_database
from main_window import MainWindow

if __name__ == "__main__":
    # Initialize database
    database_init_create = create_database()

    # Start application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())