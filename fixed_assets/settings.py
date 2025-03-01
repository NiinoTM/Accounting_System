# fixed_assets/settings.py
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QLineEdit, QDialog)
from utils.crud.search_dialog import AdvancedSearchDialog
from data.create_database import DatabaseManager

class FixedAssetSettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Fixed Asset Settings")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "owner_equity_account.json")
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
        self.equity_search_button.clicked.connect(self.open_account_search)
        equity_layout.addWidget(self.equity_label)
        equity_layout.addWidget(self.equity_display)
        equity_layout.addWidget(self.equity_search_button)
        layout.addLayout(equity_layout)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def open_account_search(self):
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
                self.equity_display.setText(display_text)
                self.selected_equity_account = selected

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    account_id = data.get("owner_equity_account_id")
                    if account_id:
                        self.load_account_details(account_id)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid settings file.")

    def load_account_details(self, account_id):
        try:
            with self.db_manager as db:
                db.cursor.execute("SELECT name, code FROM accounts WHERE id = ?", (account_id,))
                account = db.cursor.fetchone()
                if account:
                    display_text = f"{account['name']} ({account['code']})"
                    self.equity_display.setText(display_text)
                    self.selected_equity_account = {'id': account_id, 'name': account['name'], 'code': account['code']}
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def save_settings(self):
        data = {}
        if hasattr(self, 'selected_equity_account') and self.selected_equity_account:
            data["owner_equity_account_id"] = self.selected_equity_account['id']

        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")