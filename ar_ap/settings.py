# ar_ap/settings.py
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QLineEdit, QDialog)
from utils.crud.search_dialog import AdvancedSearchDialog
from data.create_database import DatabaseManager

class ARAPSettingsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("AR/AP Settings")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "ar_ap_settings.json")  # Correct path
        self.init_ui()
        self.load_settings()


    def init_ui(self):
        layout = QVBoxLayout(self)

        # Accounts Receivable Selection
        ar_layout = QHBoxLayout()
        self.ar_label = QLabel("Select your version of Accounts Receivables:")
        self.ar_display = QLineEdit()
        self.ar_display.setReadOnly(True)
        self.ar_search_button = QPushButton("Search")
        self.ar_search_button.clicked.connect(lambda: self.open_account_search("receivable"))
        ar_layout.addWidget(self.ar_label)
        ar_layout.addWidget(self.ar_display)
        ar_layout.addWidget(self.ar_search_button)
        layout.addLayout(ar_layout)


        # Accounts Payable Selection
        ap_layout = QHBoxLayout()
        self.ap_label = QLabel("Select your version of Accounts Payables:")
        self.ap_display = QLineEdit()
        self.ap_display.setReadOnly(True)
        self.ap_search_button = QPushButton("Search")
        self.ap_search_button.clicked.connect(lambda: self.open_account_search("payable"))
        ap_layout.addWidget(self.ap_label)
        ap_layout.addWidget(self.ap_display)
        ap_layout.addWidget(self.ap_search_button)
        layout.addLayout(ap_layout)

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
            db_path=self.db_manager.db_path,  # Use db_manager for path
            table_name='accounts'
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                display_text = f"{selected.get('name', '')} ({selected.get('code', '')})"
                if account_type == "receivable":
                    self.ar_display.setText(display_text)
                    self.selected_ar_account = selected
                elif account_type == "payable":
                    self.ap_display.setText(display_text)
                    self.selected_ap_account = selected

    def load_settings(self):
        """Loads settings from the JSON file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
                    ar_id = data.get("receivable_account_id")
                    ap_id = data.get("payable_account_id")

                    if ar_id:
                        self.load_account_details("receivable", ar_id)
                    if ap_id:
                        self.load_account_details("payable", ap_id)


            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid settings file.")
        #No else needed, starts with empty file if not exists

    def load_account_details(self, account_type, account_id):
        """Loads and displays account details from the database."""
        try:
            with self.db_manager as db:
                db.cursor.execute("SELECT name, code FROM accounts WHERE id = ?", (account_id,))
                account = db.cursor.fetchone()
                if account:
                    display_text = f"{account['name']} ({account['code']})"
                    if account_type == "receivable":
                        self.ar_display.setText(display_text)
                        self.selected_ar_account = {'id': account_id, 'name': account['name'], 'code': account['code']}
                    elif account_type == "payable":
                        self.ap_display.setText(display_text)
                        self.selected_ap_account = {'id': account_id, 'name': account['name'], 'code': account['code']}

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def save_settings(self):
        """Saves settings to the JSON file."""
        data = {}
        if hasattr(self, 'selected_ar_account') and self.selected_ar_account:
             data["receivable_account_id"] = self.selected_ar_account['id']
        if hasattr(self, 'selected_ap_account') and self.selected_ap_account:
            data["payable_account_id"] = self.selected_ap_account['id']

        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True) # Ensure directory
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")