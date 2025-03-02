# menu/recurring_transactions_actions.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from recurring_transactions.create_recurring_transaction import CreateRecurringTransactionWindow

class RecurringTransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.recurring_transactions_menu = self.create_recurring_transactions_menu()

    def create_recurring_transactions_menu(self):
        recurring_menu = QMenu("Recurring Transactions", self.main_window)

        create_action = QAction("Create Recurring Transaction", self.main_window)
        create_action.triggered.connect(self.create_recurring_transaction)

        create_from_template_action = QAction("New Recurring Transaction from Template", self.main_window) # new
        # create_from_template_action.triggered.connect(self.create_from_template) # Connect later

        edit_action = QAction("Edit Recurring Transaction", self.main_window)
        # edit_action.triggered.connect(self.edit_recurring_transaction)

        delete_action = QAction("Delete Recurring Transaction", self.main_window)
        # delete_action.triggered.connect(self.delete_recurring_transaction)

        pause_resume_action = QAction("Pause/Resume Recurring Transactions", self.main_window)
        # pause_resume_action.triggered.connect(self.pause_resume_recurring_transactions)

        recurring_menu.addAction(create_action)
        recurring_menu.addAction(create_from_template_action) # added
        recurring_menu.addAction(edit_action)
        recurring_menu.addAction(delete_action)
        recurring_menu.addAction(pause_resume_action)

        return recurring_menu

    # Placeholder methods
    def create_recurring_transaction(self):
        create_recurring_transaction_window = CreateRecurringTransactionWindow(self.main_window)
        create_recurring_transaction_window.show()
        

    # def create_from_template(self):  # NEW placeholder method
    #     pass

    # def edit_recurring_transaction(self):
    #     pass

    # def delete_recurring_transaction(self):
    #     pass

    # def pause_resume_recurring_transactions(self):
    #     pass