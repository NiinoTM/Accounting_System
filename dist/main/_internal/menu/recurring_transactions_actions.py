# recurring_transactions_actions.py (ensure correct connection)
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from recurring_transactions.create_recurring_transaction import CreateRecurringTransactionWindow
from recurring_transactions.create_recurring_transaction_from_template import CreateRecurringTransactionFromTemplateWindow
from recurring_transactions.edit_recurring_transactions import EditRecurringTransactionWindow
from recurring_transactions.delete_recurring_transactions import DeleteRecurringTransactionWindow # Import Delete Window

class RecurringTransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.recurring_transactions_menu = self.create_recurring_transactions_menu()

    def create_recurring_transactions_menu(self):
        recurring_menu = QMenu("Recurring Transactions", self.main_window)

        create_action = QAction("Create Recurring Transaction", self.main_window)
        create_action.triggered.connect(self.create_recurring_transaction)

        create_from_template_action = QAction("New Recurring Transaction from Template", self.main_window)
        create_from_template_action.triggered.connect(self.create_from_template)

        edit_action = QAction("Edit Recurring Transaction", self.main_window)
        edit_action.triggered.connect(self.edit_recurring_transaction)

        delete_action = QAction("Delete Recurring Transaction", self.main_window)
        delete_action.triggered.connect(self.delete_recurring_transaction_action) # Connect Delete action

        recurring_menu.addAction(create_action)
        recurring_menu.addAction(create_from_template_action)
        recurring_menu.addAction(edit_action)
        recurring_menu.addAction(delete_action)

        return recurring_menu

    def create_recurring_transaction(self):
        create_recurring_transaction_window = CreateRecurringTransactionWindow(self.main_window)
        create_recurring_transaction_window.show()

    def create_from_template(self):
        create_from_template_window = CreateRecurringTransactionFromTemplateWindow(self.main_window)
        create_from_template_window.show()

    def edit_recurring_transaction(self):
        edit_recurring_transaction_window = EditRecurringTransactionWindow(self.main_window)
        edit_recurring_transaction_window.show()

    def delete_recurring_transaction_action(self): # Method to show Delete Window
        delete_recurring_transaction_window = DeleteRecurringTransactionWindow(self.main_window)
        delete_recurring_transaction_window.show()