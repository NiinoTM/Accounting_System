#libraries
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

#modules
from menu.setup_menu.setup_actions import SetupActions
from menu.transactions_actions import TransactionsActions
from menu.templates_actions import TemplatesActions
from menu.reports_actions import ReportsActions
from menu.ar_ap_menu import ARPActions
from menu.fixed_asset_menu import FixedAssetActions
from menu.recurring_transactions_actions import RecurringTransactionsActions

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_actions = SetupActions(self)
        self.transactions_actions = TransactionsActions(self)
        self.templates_actions = TemplatesActions(self)
        self.ar_ap_actions = ARPActions(self)
        self.reports_actions = ReportsActions(self)
        self.fixed_assets_actions = FixedAssetActions(self)
        self.recurring_transactions = RecurringTransactionsActions(self)

        self.init_ui()
        self.create_menu()
        self.setup_central_widget()


    def init_ui(self):
        self.setWindowTitle("FinTrack")
        self.setMinimumSize(800, 600)

    def create_menu(self):
        menubar = self.menuBar()
        
        # Menu Options
            #SETUP
        setup_menu = menubar.addMenu("Setup")
        self.setup_actions.add_setup_actions_to_menu(setup_menu)

            #TRANSACTIONS
        transactions_menu = self.transactions_actions.transactions_menu
        menubar.addMenu(transactions_menu)

        # --- Recurring Transactions Menu ---
        recurring_menu = self.recurring_transactions.recurring_transactions_menu
        menubar.addMenu(recurring_menu) 


            #TEMPLATES
        templates_menu = self.templates_actions.templates_menu
        menubar.addMenu(templates_menu)

            #ACCOUNTS RECEIVABLES & PAYABLES
        ar_ap_menu = self.ar_ap_actions.ar_ap_menu
        menubar.addMenu(ar_ap_menu)

            # REPORTS
        reports_menu = self.reports_actions.reports_menu  # Get the reports menu
        menubar.addMenu(reports_menu) # Add the created reports menu

        fixed_asset_menu = self.fixed_assets_actions.fixed_asset_menu
        menubar.addMenu(fixed_asset_menu)


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
 
    
    
