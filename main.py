# libraries
import sys
from PySide6.QtWidgets import QApplication

# modules
from create_database import create_database
from main_window import MainWindow
from process_future_transactions import process_future_transactions # Import

if __name__ == "__main__":
    # Initialize database
    database_init_create = create_database()

    # Start application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # --- Process future transactions ---
    process_future_transactions(window)  # Pass the main window as parent

    sys.exit(app.exec())