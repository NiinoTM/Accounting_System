# menu/reports_actions.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction  # Corrected import
from reports.income_statement_interface import IncomeStatementWindow
from reports.balance_sheet_interface import BalanceSheetWindow
from cashflow.cashflow_actions import CashflowActions  # Import


class ReportsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.reports_menu = QMenu("Reports", main_window)
        self.cashflow_actions = CashflowActions(main_window)  # Create instance *here*
        self.create_actions()

    def create_actions(self):
        self.income_statement_action = self.reports_menu.addAction("Income Statement")
        self.income_statement_action.triggered.connect(self.show_income_statement)

        self.balance_sheet_action = self.reports_menu.addAction("Balance Sheet")
        self.balance_sheet_action.triggered.connect(self.show_balance_sheet)

        # --- Add Cash Flow Menu as a SUBMENU ---
        cashflow_menu = self.cashflow_actions.cashflow_menu  # Get the menu
        self.reports_menu.addMenu(cashflow_menu)  # Add as submenu


    def show_income_statement(self):
        income_statement_widget = IncomeStatementWindow(self.main_window)
        income_statement_widget.show()

    def show_balance_sheet(self):
        balance_sheet_widget = BalanceSheetWindow(self.main_window)
        balance_sheet_widget.show()