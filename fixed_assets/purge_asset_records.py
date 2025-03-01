# fixed_assets/purge_asset_records.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QDialog)
from data.create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog

class PurgeAssetRecordsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Purge Asset Records")
        self.db_manager = DatabaseManager()
        self.selected_asset = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Asset Selection
        self.select_button = QPushButton("Select Asset")
        self.select_button.clicked.connect(self.select_asset)
        layout.addWidget(self.select_button)

        # Asset Display (Read-only)
        self.asset_label = QLabel("Selected Asset: None")
        layout.addWidget(self.asset_label)

        # Delete Button (Initially disabled)
        self.delete_button = QPushButton("Delete All Data")
        self.delete_button.clicked.connect(self.purge_asset)
        self.delete_button.setEnabled(False)  # Disabled until an asset is selected
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def select_asset(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='fixed_assets'  # Search in fixed_assets
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_asset = selected
                self.asset_label.setText(f"Selected Asset: {selected['asset_name']} (ID: {selected['asset_id']})")
                self.delete_button.setEnabled(True)

    def purge_asset(self):
        if not self.selected_asset:
            return

        confirm = QMessageBox.question(
            self, "Confirm Purge",
            "Are you sure you want to PERMANENTLY DELETE ALL data related to this asset?  This action CANNOT be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        asset_id = self.selected_asset['asset_id']
        account_id = self.selected_asset['account_id']

        try:
            with self.db_manager as db:
                # --- 1. Find and Reverse Transactions ---
                db.cursor.execute("SELECT id, debited, credited, amount FROM transactions WHERE description LIKE ?",(f"%{self.selected_asset['asset_name']}%",)) # LIKE query
                transactions = db.cursor.fetchall()
                for trans in transactions:
                    # Reverse the transaction's effect on account balances
                    db.cursor.execute(
                        "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                        (trans['amount'], trans['debited'])
                    )
                    db.cursor.execute(
                        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                        (trans['amount'], trans['credited'])
                    )

                    # Delete the transaction
                    db.cursor.execute("DELETE FROM transactions WHERE id = ?", (trans['id'],))

                # --- 2. Delete from depreciation_schedule ---
                db.cursor.execute("DELETE FROM depreciation_schedule WHERE asset_id = ?", (asset_id,))

                # --- 3. Delete from fixed_assets ---
                db.cursor.execute("DELETE FROM fixed_assets WHERE asset_id = ?", (asset_id,))

                 # --- 4. Check Account Balance and Delete (if zero) ---
                db.cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
                account_balance = db.cursor.fetchone()['balance']

                if float(account_balance) == 0.0:
                    db.cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
                else:
                    QMessageBox.critical(self, "Error", f"Account balance is not zero ({account_balance}). Cannot delete account.")
                    db.conn.rollback()  # Rollback changes!
                    return

                db.commit()
                QMessageBox.information(self, "Success", "Asset records purged successfully!")
                self.close()

        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))