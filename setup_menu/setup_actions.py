# setup_actions.py
from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtGui import QAction

# modules
from setup_menu.accounts_actions import AccountsActions  # Import the new AccountActions class
from setup_menu.accounting_periods_actions import AccountingPeriodsActions
from setup_menu.categories_actions import CategoriesActions

class SetupActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_actions = {}
        self.action_handlers = {
            'accounts': AccountsActions(main_window),
            'accounting_periods': AccountingPeriodsActions(main_window),
            'categories': CategoriesActions(main_window)
        }
        self.accounts_actions = AccountsActions(main_window)  # Initialize AccountActions
        self.accounting_periods_actions = AccountingPeriodsActions(main_window)  # Initialize AccountActions
        self.categories_actions = CategoriesActions(main_window)  # Initialize AccountActions
        self.create_setup_actions()

    def create_setup_actions(self):
        # Accounts
        self.setup_actions['accounts'] = self.accounts_actions.accounts_menu

        # Accounting Period
        self.setup_actions['accounting_periods'] = self.accounting_periods_actions.accounting_periods_menu

        # Categories
        self.setup_actions['categories'] = self.categories_actions.categories_menu


    def add_setup_actions_to_menu(self, setup_menu):
        """Add all setup actions to the setup menu"""
        for action in self.setup_actions.values():
            if isinstance(action, QMenu):
                setup_menu.addMenu(action)
            else:
                setup_menu.addAction(action)