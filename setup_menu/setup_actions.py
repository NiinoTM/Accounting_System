# setup_actions.py
from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtGui import QAction

# modules
from setup_menu.categories_actions import CategoriesActions
from setup_menu.accounting_periods_actions import AccountingPeriodsActions
from setup_menu.accounts_actions import AccountsActions  # Import the new AccountActions class

class SetupActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_actions = {}
        self.action_handlers = {
            'accounts': AccountsActions(main_window),
            'accounting_periods': AccountingPeriodsActions(main_window),
            'categories': CategoriesActions(main_window)
        }
        self.account_actions = AccountsActions(main_window)  # Initialize AccountActions
        self.create_setup_actions()

    def create_setup_actions(self):
        # Add the Accounts menu from AccountActions
        self.setup_actions['accounts'] = self.account_actions.accounts_menu

        # Accounting Periods
        self.setup_actions['accounting_periods'] = QAction("Accounting Periods", self.main_window)
        self.setup_actions['accounting_periods'].triggered.connect(
            self.action_handlers['accounting_periods'].execute
        )

        # Categories
        self.setup_actions['categories'] = QAction("Categories", self.main_window)
        self.setup_actions['categories'].triggered.connect(
            self.action_handlers['categories'].execute
        )

    def add_setup_actions_to_menu(self, setup_menu):
        """Add all setup actions to the setup menu"""
        for action in self.setup_actions.values():
            if isinstance(action, QMenu):
                setup_menu.addMenu(action)
            else:
                setup_menu.addAction(action)