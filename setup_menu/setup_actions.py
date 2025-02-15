# libraries
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QAction

#modules
from .categories_action import CategoriesAction
from .accounts_action import AccountsAction
from .accounting_periods_action import AccountingPeriodsAction

class SetupActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_actions = {}
        self.action_handlers = {
            'categories': CategoriesAction(main_window),
            'accounts': AccountsAction(main_window),
            'accounting_periods': AccountingPeriodsAction(main_window)
        }
        self.create_setup_actions()

    def create_setup_actions(self):
        # Categories
        self.setup_actions['categories'] = QAction("Categories", self.main_window)
        self.setup_actions['categories'].triggered.connect(
            self.action_handlers['categories'].execute
        )
        
        # Accounts
        self.setup_actions['accounts'] = QAction("Accounts", self.main_window)
        self.setup_actions['accounts'].triggered.connect(
            self.action_handlers['accounts'].execute
        )
        
        # Accounting Periods
        self.setup_actions['accounting_periods'] = QAction("Accounting Periods", self.main_window)
        self.setup_actions['accounting_periods'].triggered.connect(
            self.action_handlers['accounting_periods'].execute
        )

    def add_setup_actions_to_menu(self, setup_menu):
        """Add all setup actions to the setup menu"""
        for action in self.setup_actions.values():
            setup_menu.addAction(action)