#libraries
import sys
from PySide6.QtWidgets import QApplication

#modules
from data.create_database import create_database
from main_window import MainWindow

if __name__ == "__main__":
    create_db = create_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
