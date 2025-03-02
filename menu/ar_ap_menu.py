# menu/ar_ap_menu.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

from ar_ap.settings import ARAPSettingsWindow

from ar_ap.new_ar_ap import NewDebtorCreditorWindow
from ar_ap.edit_ar_ap import EditDebtorCreditorWindow
from ar_ap.delete_ar_ap import DeleteDebtorCreditorWindow

from ar_ap.register_asset_transfer_outflow import RegisterAssetTransferOutflowWindow
from ar_ap.record_asset_recovery import RecordAssetRecoveryWindow
from ar_ap.adjust_receivable import AdjustReceivableWindow
from ar_ap.write_off_receivable import WriteOffReceivableWindow

from ar_ap.register_asset_transfer_inflow import RegisterAssetTransferInflowWindow
from ar_ap.record_liability_settlement import RecordLiabilitySettlementWindow
from ar_ap.adjust_payable import AdjustPayableWindow
from ar_ap.cancel_payable import CancelPayableWindow

from ar_ap.view_outstanding_balance import OutstandingBalanceWindow

class ARPActions:  # Renamed for clarity, as it handles both AR and AP
    def __init__(self, main_window):
        self.main_window = main_window
        self.ar_ap_menu = self.create_ar_ap_menu()
        

    def create_ar_ap_menu(self):
        ar_ap_menu = QMenu("AR/AP", self.main_window)

        # --- View Submenu ---
        view_outstanding_balances_action = QAction("View Outstanding Balances", ar_ap_menu)
        view_outstanding_balances_action.triggered.connect(self.view_outstanding_balance)
        ar_ap_menu.addAction(view_outstanding_balances_action)

        # --- Debtor Creditor Management Submenu ---
        debtor_creditor_management_menu = QMenu("Debtor/Creditor Management", ar_ap_menu)

        new_debtor_creditor_action = QAction("New Debtor/Creditor", self.main_window)
        new_debtor_creditor_action.triggered.connect(self.open_new_debtor_creditor)

        edit_debtor_creditor_action = QAction("Edit Debtor/Creditor", self.main_window)
        edit_debtor_creditor_action.triggered.connect(self.open_edit_debtor_creditor)

        delete_debtor_creditor_action = QAction("Delete Debtor/Creditor", self.main_window)
        delete_debtor_creditor_action.triggered.connect(self.open_delete_debtor_creditor)
        debtor_creditor_management_menu.addAction(new_debtor_creditor_action)
        debtor_creditor_management_menu.addAction(edit_debtor_creditor_action)
        debtor_creditor_management_menu.addAction(delete_debtor_creditor_action)
        ar_ap_menu.addMenu(debtor_creditor_management_menu)
        


        # --- Debtor Transactions Submenu ---
        debtor_transactions_menu = QMenu("Debtor Transactions", ar_ap_menu)

        register_asset_transfer_out_action = QAction("Register Asset Transfer (Outflow)", self.main_window)
        register_asset_transfer_out_action.triggered.connect(self.open_register_asset_transfer_outflow)
        
        record_asset_recovery_action = QAction("Record Asset Recovery (Inflow)", self.main_window)
        record_asset_recovery_action.triggered.connect(self.open_record_asset_recovery)

        adjust_receivable_action = QAction("Adjust Receivable", self.main_window)
        adjust_receivable_action.triggered.connect(self.open_adjust_receivable)

        write_off_receivable_action = QAction("Write-Off Receivable", self.main_window)
        write_off_receivable_action.triggered.connect(self.open_write_off_receivable)

        debtor_transactions_menu.addAction(register_asset_transfer_out_action)
        debtor_transactions_menu.addAction(record_asset_recovery_action)
        debtor_transactions_menu.addAction(adjust_receivable_action)
        debtor_transactions_menu.addAction(write_off_receivable_action)
        ar_ap_menu.addMenu(debtor_transactions_menu)

        # --- Creditor Transactions Submenu ---
        creditor_transactions_menu = QMenu("Creditor Transactions", ar_ap_menu)

        register_asset_transfer_in_action = QAction("Register Asset Transfer (Inflow)", self.main_window)
        register_asset_transfer_in_action.triggered.connect(self.open_register_asset_transfer_inflow)

        record_liability_settlement_action = QAction("Record Liability Settlement (Outflow)", self.main_window)
        record_liability_settlement_action.triggered.connect(self.open_record_liability_settlement)

        adjust_payable_action = QAction("Adjust Payable", self.main_window)
        adjust_payable_action.triggered.connect(self.open_adjust_payable)

        cancel_payable_action = QAction("Cancel Payable", self.main_window)
        cancel_payable_action.triggered.connect(self.open_cancel_payable)

        creditor_transactions_menu.addAction(register_asset_transfer_in_action)
        creditor_transactions_menu.addAction(record_liability_settlement_action)
        creditor_transactions_menu.addAction(adjust_payable_action)
        creditor_transactions_menu.addAction(cancel_payable_action)

        ar_ap_menu.addMenu(creditor_transactions_menu)

        # --- Settings Submenu ---
        settings_action = QAction("Settings", ar_ap_menu)
        settings_action.triggered.connect(self.open_settings)
        ar_ap_menu.addAction(settings_action)

        return ar_ap_menu
    
    def open_settings(self):
        """Opens the AR/AP settings window."""
        self.settings_window = ARAPSettingsWindow(self.main_window)
        self.settings_window.show()

    def open_new_debtor_creditor(self):
        """Opens the new debtor/creditor window."""
        self.new_dc_window = NewDebtorCreditorWindow(self.main_window)
        self.new_dc_window.show()

    def open_edit_debtor_creditor(self):
        """Opens the edit debtor/creditor window."""
        self.edit_dc_window = EditDebtorCreditorWindow(self.main_window)
        self.edit_dc_window.show()

    def open_delete_debtor_creditor(self):
        """Opens the delete debtor/creditor window."""
        self.delete_dc_window = DeleteDebtorCreditorWindow(self.main_window)
        self.delete_dc_window.show()

    def open_register_asset_transfer_outflow(self):  # New method
        """Opens the register asset transfer outflow window."""
        self.register_outflow_window = RegisterAssetTransferOutflowWindow(self.main_window)
        self.register_outflow_window.show()

    def open_record_asset_recovery(self):
        """Opens the record asset recovery inflow window."""
        self.record_asset_recovery_window = RecordAssetRecoveryWindow(self.main_window)
        self.record_asset_recovery_window.show()

    def open_adjust_receivable(self):
        """Opens the adjust receivable window"""
        self.adjust_receivable_window = AdjustReceivableWindow(self.main_window)
        self.adjust_receivable_window.show()

    def open_write_off_receivable(self):
        """Opens the write-off receivable window."""
        self.write_off_receivable_window = WriteOffReceivableWindow(self.main_window)
        self.write_off_receivable_window.show()

    def open_register_asset_transfer_inflow(self):
        """Opens the register asset transfer inflow window."""
        self.register_inflow_window = RegisterAssetTransferInflowWindow(self.main_window)
        self.register_inflow_window.show()

    def open_record_liability_settlement(self):  # New method
        """Opens the record liability settlement window."""
        self.record_settlement_window = RecordLiabilitySettlementWindow(self.main_window)
        self.record_settlement_window.show()

    def open_adjust_payable(self):  # New method
        """Opens the adjust payable window."""
        self.adjust_payable_window = AdjustPayableWindow(self.main_window)
        self.adjust_payable_window.show()

    def open_cancel_payable(self):  # New method
        """Opens the cancel payable window."""
        self.cancel_payable_window = CancelPayableWindow(self.main_window)
        self.cancel_payable_window.show()

    def view_outstanding_balance(self):  # New method
        self.view_outstanding_balance_window = OutstandingBalanceWindow(self.main_window)
        self.view_outstanding_balance_window.show()