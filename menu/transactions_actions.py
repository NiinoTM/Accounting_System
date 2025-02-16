#libraries
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud.generic_crud import GenericCRUD

class TransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.transactions_menu = self.create_transactions_actions()
        self.crud = GenericCRUD("transactions")

    def create_transactions_actions(self):
    # Add CRUD actions to the transactionss menu
        transactions_menu = QMenu("Transactions", self.main_window)

        # Create CRUD actions
        create_transactions = QAction("Create Transaction", self.main_window)
        read_transactions = QAction("View Transactions", self.main_window)
        update_transactions = QAction("Update Transaction", self.main_window)
        delete_transactions = QAction("Delete Transaction", self.main_window)

        # Connect actions to their respective methods
        create_transactions.triggered.connect(self.create_transactions)
        read_transactions.triggered.connect(self.read_transactions)
        update_transactions.triggered.connect(self.update_transactions)
        delete_transactions.triggered.connect(self.delete_transactions)

        # Add CRUD actions to the transactionss menu
        transactions_menu.addAction(create_transactions)
        transactions_menu.addAction(read_transactions)
        transactions_menu.addAction(update_transactions)
        transactions_menu.addAction(delete_transactions)

        return transactions_menu

    def create_transactions(self):
        self.crud.create(self.main_window)

    def read_transactions(self):
        self.crud.read(self.main_window)

    def update_transactions(self):
        self.crud.edit(self.main_window)

    def delete_transactions(self):
        self.crud.delete(self.main_window)
