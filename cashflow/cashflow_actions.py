# reports/cashflow_actions.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from cashflow.settings import CashflowSettingsWindow  # Import the settings window

class CashflowActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.cashflow_menu = self.create_cashflow_menu()

    def create_cashflow_menu(self):
        cashflow_menu = QMenu("Cash Flow", self.main_window)

        actual_cashflow_action = QAction("Actual Cash Flow", self.main_window)
        # actual_cashflow_action.triggered.connect(self.show_actual_cashflow) # Connect later

        forecast_action = QAction("Cash Flow Forecast", self.main_window)
        # forecast_action.triggered.connect(self.show_forecast) # Connect later

        settings_action = QAction("Settings", self.main_window)
        settings_action.triggered.connect(self.open_settings)  # Connect to open_settings

        cashflow_menu.addAction(actual_cashflow_action)
        cashflow_menu.addAction(forecast_action)
        cashflow_menu.addAction(settings_action)

        return cashflow_menu

    # Placeholder methods (to be implemented later)
    # def show_actual_cashflow(self):
    #     pass

    # def show_forecast(self):
    #     pass

    def open_settings(self):  # NEW
        """Opens the cash flow settings window."""
        self.settings_window = CashflowSettingsWindow(self.main_window)
        self.settings_window.show()