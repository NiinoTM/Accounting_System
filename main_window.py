#libraries
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_menu()

    def init_ui(self):
        self.setWindowTitle("FinTrack")
        self.setMinimumSize(800, 600)

    def create_menu(self):
        menubar = self.menuBar()
        
        # Menu Options
        setup_menu = menubar.addMenu("Setup")
        transactions_menu = menubar.addMenu("Transactions")
        templates_menu = menubar.addMenu("Templates")
        reports_menu = menubar.addMenu("Reports")
        assets_menu = menubar.addMenu("Assets")
        ar_ap_menu = menubar.addMenu("AR/AP") #accounts receivables & payable
        backup_menu = menubar.addMenu("Backups")
        help_menu = menubar.addMenu("Help")

    
    
