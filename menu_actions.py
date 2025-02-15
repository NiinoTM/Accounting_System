from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QAction

class MenuActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_actions = {}
        self.create_setup_actions()

    def create_setup_actions(self):
        # Company Information
        self.setup_actions['company_info'] = QAction("Company Information", self.main_window)
        self.setup_actions['company_info'].triggered.connect(self.company_info_action)
        
        # Chart of Accounts
        self.setup_actions['chart_accounts'] = QAction("Chart of Accounts", self.main_window)
        self.setup_actions['chart_accounts'].triggered.connect(self.chart_accounts_action)
        
        # Financial Years
        self.setup_actions['financial_years'] = QAction("Financial Years", self.main_window)
        self.setup_actions['financial_years'].triggered.connect(self.financial_years_action)
        
        # Tax Settings
        self.setup_actions['tax_settings'] = QAction("Tax Settings", self.main_window)
        self.setup_actions['tax_settings'].triggered.connect(self.tax_settings_action)
        
        # User Management
        self.setup_actions['user_management'] = QAction("User Management", self.main_window)
        self.setup_actions['user_management'].triggered.connect(self.user_management_action)

    def add_setup_actions_to_menu(self, setup_menu):
        """Add all setup actions to the setup menu"""
        for action in self.setup_actions.values():
            setup_menu.addAction(action)

    # Action handlers
    def company_info_action(self):
        QMessageBox.information(self.main_window, "Company Info", "Company Information dialog will be shown here")

    def chart_accounts_action(self):
        QMessageBox.information(self.main_window, "Chart of Accounts", "Chart of Accounts dialog will be shown here")

    def financial_years_action(self):
        QMessageBox.information(self.main_window, "Financial Years", "Financial Years dialog will be shown here")

    def tax_settings_action(self):
        QMessageBox.information(self.main_window, "Tax Settings", "Tax Settings dialog will be shown here")

    def user_management_action(self):
        QMessageBox.information(self.main_window, "User Management", "User Management dialog will be shown here")