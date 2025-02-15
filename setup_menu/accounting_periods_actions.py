from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud import CRUD

class AccountingPeriodsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.accounting_periods_menu = self.create_accounting_periods_actions()

    def create_accounting_periods_actions(self):
        # Create the main accounting_periodss menu
        accounting_periods_menu = QMenu("Accounting Periods", self.main_window)

        # Create CRUD actions
        create_accounting_periods = QAction("Create Accounting Periods", self.main_window)
        read_accounting_periods = QAction("View Accounting Periods", self.main_window)
        update_accounting_periods = QAction("Update Accounting Periods", self.main_window)
        delete_accounting_periods = QAction("Delete Accounting Periods", self.main_window)

        # Connect actions to their respective methods
        create_accounting_periods.triggered.connect(self.create_accounting_periods)
        read_accounting_periods.triggered.connect(self.read_accounting_periods)
        update_accounting_periods.triggered.connect(self.update_accounting_periods)
        delete_accounting_periods.triggered.connect(self.delete_accounting_periods)

        # Add CRUD actions to the accounting_periodss menu
        accounting_periods_menu.addAction(create_accounting_periods)
        accounting_periods_menu.addAction(read_accounting_periods)
        accounting_periods_menu.addAction(update_accounting_periods)
        accounting_periods_menu.addAction(delete_accounting_periods)

        return accounting_periods_menu

    def create_accounting_periods(self):
        crud = CRUD("accounting_periods")
        crud.create(self.main_window)

    def read_accounting_periods(self):
        crud = CRUD("accounting_periods")
        crud.read(self.main_window)

    def update_accounting_periods(self):
        crud = CRUD("accounting_periods")
        crud.edit(self.main_window)

    def delete_accounting_periods(self):
        crud = CRUD("accounting_periods")
        crud.delete(self.main_window)
