# libraries
import sys
from PySide6.QtWidgets import QApplication

# modules
from create_database import create_database
from main_window import MainWindow
from process_future_transactions import process_future_transactions
from backup_system import register_app_close_backup  # Import the backup system

if __name__ == "__main__":
    # Initialize database
    database_init_create = create_database()

    # Start application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Process future transactions
    process_future_transactions(window)
    
    # Register backup on application close
    register_app_close_backup(app, window)

    sys.exit(app.exec())