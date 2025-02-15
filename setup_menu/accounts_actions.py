# account_actions.py
from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud import CRUD

class AccountsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.accounts_menu = self.create_account_actions()

    def create_account_actions(self):
        # Create the main Accounts menu
        accounts_menu = QMenu("Accounts", self.main_window)

        # Create CRUD actions
        create_account = QAction("Create Account", self.main_window)
        read_accounts = QAction("View Accounts", self.main_window)
        update_account = QAction("Update Account", self.main_window)
        delete_account = QAction("Delete Account", self.main_window)

        # Connect actions to their respective methods
        create_account.triggered.connect(self.create_account)
        read_accounts.triggered.connect(self.read_accounts)
        update_account.triggered.connect(self.update_account)
        delete_account.triggered.connect(self.delete_account)

        # Add CRUD actions to the Accounts menu
        accounts_menu.addAction(create_account)
        accounts_menu.addAction(read_accounts)
        accounts_menu.addAction(update_account)
        accounts_menu.addAction(delete_account)

        return accounts_menu

    def create_account(self):
        crud = CRUD("accounts")
        crud.create(self.main_window)

    def read_accounts(self):
        crud = CRUD("accounts")
        crud.read(self.main_window)

    def update_account(self):
        crud = CRUD("accounts")
        crud.edit(self.main_window)

    def delete_account(self):
        crud = CRUD("accounts")
        crud.delete(self.main_window)