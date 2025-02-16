# menu/transactions_actions.py

from PySide6.QtWidgets import QMenu, QMessageBox
from utils.crud.transactions_crud import TransactionsCRUD #Important

class TransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.transactions_menu = QMenu("Transactions", self.main_window)
        self.transactions_crud = TransactionsCRUD() # Create instance
        self.create_actions()

    def create_actions(self):
        self.add_transaction_action = self.transactions_menu.addAction("Add Transaction")
        self.add_transaction_action.triggered.connect(self.add_transaction)
        self.view_transactions_action = self.transactions_menu.addAction("View Transactions")
        self.view_transactions_action.triggered.connect(self.view_transactions)
        self.edit_transaction_action = self.transactions_menu.addAction("Edit Transaction")
        self.edit_transaction_action.triggered.connect(self.edit_transaction)

        self.delete_transaction_action = self.transactions_menu.addAction("Delete Transaction")
        self.delete_transaction_action.triggered.connect(self.delete_transaction)

    def add_transaction(self):
        self.transactions_crud.create(self.main_window)

    def view_transactions(self):
        self.transactions_crud.read(self.main_window)

    def edit_transaction(self):
        self.transactions_crud.edit(self.main_window)

    def delete_transaction(self):
        self.transactions_crud.delete(self.main_window)