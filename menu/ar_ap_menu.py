# menu/ar_ap_menu.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from ar_ap.settings import ARAPSettingsWindow


class ARPActions:  # Renamed for clarity, as it handles both AR and AP
    def __init__(self, main_window):
        self.main_window = main_window
        self.ar_ap_menu = self.create_ar_ap_menu()

    def create_ar_ap_menu(self):
        ar_ap_menu = QMenu("AR/AP", self.main_window)

        # --- View Submenu ---
        view_outstanding_balances_action = QAction("View Outstanding Balances", ar_ap_menu)
        ar_ap_menu.addAction(view_outstanding_balances_action)

        # --- Settings Submenu ---
        settings_action = QAction("Settings", ar_ap_menu)
        settings_action.triggered.connect(self.open_settings)
        ar_ap_menu.addAction(settings_action)

        # --- Debtor Creditor Management Submenu ---
        debtor_creditor_management_menu = QMenu("Debtor/Creditor Management", ar_ap_menu)
        new_debtor_creditor_action = QAction("New Debtor/Creditor", self.main_window)
        edit_debtor_creditor_action = QAction("Edit Debtor/Creditor", self.main_window)
        delete_debtor_creditor_action = QAction("Delete Debtor/Creditor", self.main_window)
        debtor_creditor_management_menu.addAction(new_debtor_creditor_action)
        debtor_creditor_management_menu.addAction(edit_debtor_creditor_action)
        debtor_creditor_management_menu.addAction(delete_debtor_creditor_action)
        ar_ap_menu.addMenu(debtor_creditor_management_menu)
        


        # --- Debtor Transactions Submenu ---
        debtor_transactions_menu = QMenu("Debtor Transactions", ar_ap_menu)

        register_asset_transfer_out_action = QAction("Register Asset Transfer (Outflow)", self.main_window)
        record_asset_recovery_action = QAction("Record Asset Recovery (Inflow)", self.main_window)
        adjust_receivable_action = QAction("Adjust Receivable", self.main_window)
        write_off_receivable_action = QAction("Write-Off Receivable", self.main_window)

        debtor_transactions_menu.addAction(register_asset_transfer_out_action)
        debtor_transactions_menu.addAction(record_asset_recovery_action)
        debtor_transactions_menu.addAction(adjust_receivable_action)
        debtor_transactions_menu.addAction(write_off_receivable_action)
        ar_ap_menu.addMenu(debtor_transactions_menu)

        # --- Creditor Transactions Submenu ---
        creditor_transactions_menu = QMenu("Creditor Transactions", ar_ap_menu)
        register_asset_transfer_in_action = QAction("Register Asset Transfer (Inflow)", self.main_window)
        record_liability_settlement_action = QAction("Record Liability Settlement (Outflow)", self.main_window)
        adjust_payable_action = QAction("Adjust Payable", self.main_window)
        cancel_payable_action = QAction("Cancel Payable", self.main_window)

        creditor_transactions_menu.addAction(register_asset_transfer_in_action)
        creditor_transactions_menu.addAction(record_liability_settlement_action)
        creditor_transactions_menu.addAction(adjust_payable_action)
        creditor_transactions_menu.addAction(cancel_payable_action)

        ar_ap_menu.addMenu(creditor_transactions_menu)

        return ar_ap_menu
    
    def open_settings(self):
        """Opens the AR/AP settings window."""
        self.settings_window = ARAPSettingsWindow(self.main_window)
        self.settings_window.show()