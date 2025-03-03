# cashflow/settings.py

import json
import os
import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QLineEdit, QDialog,
                               QTableWidget, QTableWidgetItem, QAbstractItemView, QDialogButtonBox)
from PySide6.QtCore import Qt
from create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog

class CashflowSettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Cash Flow Settings")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "cashflow_accounts.json")
        self.accounts_data = []  # List to store selected accounts
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Cash Flow Accounts Table ---
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(3)  # Account, Edit, Delete
        self.accounts_table.setHorizontalHeaderLabels(["Account", "", ""])  # Remove 'Amount'
        self.accounts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.accounts_table)

        add_account_button = QPushButton("Add Account")
        add_account_button.clicked.connect(self.add_account)
        layout.addWidget(add_account_button)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def add_account(self):
        """Opens a dialog to select a cash flow account."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Cash Flow Account")
        layout = QVBoxLayout(dialog)

        # Account selection
        account_layout = QHBoxLayout()
        account_label = QLabel("Account:")
        account_input = QLineEdit()
        account_input.setReadOnly(True)
        account_button = QPushButton("Select Account")
        account_layout.addWidget(account_label)
        account_layout.addWidget(account_input)
        account_layout.addWidget(account_button)
        layout.addLayout(account_layout)
        selected_account_info = {}  # Store account info here


        def select_account():
            search_dialog = AdvancedSearchDialog(
                field_type='generic',
                parent=dialog,
                db_path=self.db_manager.db_path,
                table_name='accounts',
                additional_filter="type_id = 1"  # <<-- CRITICAL: Filter for Current Assets
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected:
                    account_input.setText(f"{selected['name']} ({selected['code']})")
                    selected_account_info['account'] = selected # keeps the selected account


        account_button.clicked.connect(select_account)

        #OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.add_account_to_table(selected_account_info.get('account'), dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def add_account_to_table(self, account, dialog):  # Removed amount_text
        """Adds the selected account to the accounts_data and updates the table."""
        if not account:
            QMessageBox.warning(self, "Error", "Please select an account.")
            return

        # Check if the account is already in the list.  Important!
        for existing_account in self.accounts_data:
            if existing_account['id'] == account['id']:
                QMessageBox.warning(self, "Error", "This account has already been added.")
                return

        self.accounts_data.append(account)  # Just add the account
        self.update_accounts_table()
        dialog.accept()

    def update_accounts_table(self):
        """Refreshes the QTableWidget with the current account data."""
        self.accounts_table.setRowCount(len(self.accounts_data))
        for row, account in enumerate(self.accounts_data):
            self.accounts_table.setItem(row, 0, QTableWidgetItem(f"{account['name']} ({account['code']})"))

            # No Edit button

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_account(r))
            self.accounts_table.setCellWidget(row, 2, delete_button)  # Column 2 for Delete

    def delete_account(self, row):
        """Deletes an account from the accounts_data and updates the table."""
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to remove this account?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.accounts_data[row]
            self.update_accounts_table()

    def load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    account_ids = json.load(f)  # Load a list of IDs

                # Fetch account details from the database
                with self.db_manager as db:
                    for account_id in account_ids:
                        db.cursor.execute("SELECT id, name, code FROM accounts WHERE id = ?", (account_id,))
                        account = db.cursor.fetchone()
                        if account:  # Check if account exists
                            self.accounts_data.append(account)
                self.update_accounts_table()  # Update the table after loading

            except (json.JSONDecodeError, FileNotFoundError):
                QMessageBox.critical(self, "Error", "Invalid settings file.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", str(e))

    def save_settings(self):
        """Saves settings to the JSON file."""
        account_ids = [account['id'] for account in self.accounts_data]  # Extract IDs
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump(account_ids, f, indent=4)  # Save the list of IDs
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")