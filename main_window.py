#libraries
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

#modules
from setup_menu.setup_actions import SetupActions

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_actions = SetupActions(self)
        self.init_ui()
        self.create_menu()
        self.setup_central_widget()


    def init_ui(self):
        self.setWindowTitle("FinTrack")
        self.setMinimumSize(800, 600)

    def create_menu(self):
        menubar = self.menuBar()
        
        # Menu Options
        setup_menu = menubar.addMenu("Setup")
        self.setup_actions.add_setup_actions_to_menu(setup_menu)

        transactions_menu = menubar.addMenu("Transactions")
        templates_menu = menubar.addMenu("Templates")
        reports_menu = menubar.addMenu("Reports")
        assets_menu = menubar.addMenu("Fixed Assets")
        ar_ap_menu = menubar.addMenu("AR/AP") #accounts receivables & payable
        backup_menu = menubar.addMenu("Backups")
        help_menu = menubar.addMenu("Help")

    def setup_central_widget(self):
        """Set up the central widget and main layout."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
            
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
            
        self.dashboard = QLabel("Financial Dashboard")
        self.dashboard.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dashboard)
 
    
    
