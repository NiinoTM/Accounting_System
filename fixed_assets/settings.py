# fixed_assets/settings.py
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QLineEdit, QDialog)
from utils.crud.search_dialog import AdvancedSearchDialog
from create_database import DatabaseManager

class FixedAssetSettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Fixed Asset Settings")
        self.db_manager = DatabaseManager()
        self.equity_settings_file = os.path.join("data", "owner_equity_account.json")  # Equity setting
        self.depreciation_settings_file = os.path.join("data", "depreciation_account.json")  # Depreciation setting
        self.init_ui()
        self.load_settings()


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Owner's Equity Account Selection
        equity_layout = QHBoxLayout()
        self.equity_label = QLabel("Select Owner's Equity Account:")
        self.equity_display = QLineEdit()
        self.equity_display.setReadOnly(True)
        self.equity_search_button = QPushButton("Search")
        self.equity_search_button.clicked.connect(lambda: self.open_account_search("equity"))
        equity_layout.addWidget(self.equity_label)
        equity_layout.addWidget(self.equity_display)
        equity_layout.addWidget(self.equity_search_button)
        layout.addLayout(equity_layout)


        # Depreciation Account Selection
        depreciation_layout = QHBoxLayout()
        self.depreciation_label = QLabel("Select Depreciation Expense Account:")
        self.depreciation_display = QLineEdit()
        self.depreciation_display.setReadOnly(True)
        self.depreciation_search_button = QPushButton("Search")
        self.depreciation_search_button.clicked.connect(lambda: self.open_account_search("depreciation"))
        depreciation_layout.addWidget(self.depreciation_label)
        depreciation_layout.addWidget(self.depreciation_display)
        depreciation_layout.addWidget(self.depreciation_search_button)
        layout.addLayout(depreciation_layout)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

        self.setLayout(layout)


    def open_account_search(self, account_type):
        """Opens the search dialog for selecting accounts."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts'
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                display_text = f"{selected.get('name', '')} ({selected.get('code', '')})"
                if account_type == "equity":
                    self.equity_display.setText(display_text)
                    self.selected_equity_account = selected
                elif account_type == "depreciation":
                    self.depreciation_display.setText(display_text)
                    self.selected_depreciation_account = selected

    def load_settings(self):
        """Loads settings from the JSON files."""
        # Load Owner's Equity Account
        if os.path.exists(self.equity_settings_file):
            try:
                with open(self.equity_settings_file, "r") as f:
                    data = json.load(f)
                    equity_id = data.get("owner_equity_account_id")
                    if equity_id:
                        self.load_account_details("equity", equity_id)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid equity settings file.")

        # Load Depreciation Account
        if os.path.exists(self.depreciation_settings_file):
            try:
                with open(self.depreciation_settings_file, "r") as f:
                    data = json.load(f)
                    depreciation_id = data.get("depreciation_account_id")
                    if depreciation_id:
                        self.load_account_details("depreciation", depreciation_id)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid depreciation settings file.")


    def load_account_details(self, account_type, account_id):
        """Loads and displays account details from the database."""
        try:
            with self.db_manager as db:
                db.cursor.execute("SELECT name, code FROM accounts WHERE id = ?", (account_id,))
                account = db.cursor.fetchone()
                if account:
                    display_text = f"{account['name']} ({account['code']})"
                    if account_type == "equity":
                        self.equity_display.setText(display_text)
                        self.selected_equity_account = {'id': account_id, 'name': account['name'], 'code': account['code']}
                    elif account_type == "depreciation":
                        self.depreciation_display.setText(display_text)
                        self.selected_depreciation_account = {'id': account_id, 'name': account['name'], 'code': account['code']}
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def save_settings(self):
        """Saves settings to the JSON files."""
        # Save Owner's Equity Account
        equity_data = {}
        if hasattr(self, 'selected_equity_account') and self.selected_equity_account:
            equity_data["owner_equity_account_id"] = self.selected_equity_account['id']

        try:
            os.makedirs(os.path.dirname(self.equity_settings_file), exist_ok=True)
            with open(self.equity_settings_file, "w") as f:
                json.dump(equity_data, f, indent=4)
            #QMessageBox.information(self, "Success", "Equity settings saved successfully!") #not needed
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save equity settings: {e}")
            return # if this fails, it should stop

        # Save Depreciation Account
        depreciation_data = {}
        if hasattr(self, 'selected_depreciation_account') and self.selected_depreciation_account:
            depreciation_data["depreciation_account_id"] = self.selected_depreciation_account['id']

        try:
            os.makedirs(os.path.dirname(self.depreciation_settings_file), exist_ok=True)
            with open(self.depreciation_settings_file, "w") as f:
                json.dump(depreciation_data, f, indent=4)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save depreciation settings: {e}")