# ar_ap/record_asset_recovery.py

import sqlite3
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog)
from PySide6.QtCore import QDate
from data.create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name

class RecordAssetRecoveryWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Record Asset Recovery (Inflow)")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "ar_ap_settings.json")
        self.selected_debtor = None
        self.selected_asset = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # Date, Debtor, Asset, Details, Amount, and Save Button setup (same as before)
        date_layout = QHBoxLayout()
        self.date_label = QLabel("Date:")
        self.date_input = QLineEdit()
        self.date_input.setReadOnly(True)
        self.date_button = QPushButton("Select Date")
        self.date_button.clicked.connect(self.select_date)
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(self.date_button)
        layout.addLayout(date_layout)

        debtor_layout = QHBoxLayout()
        self.debtor_label = QLabel("Debtor:")
        self.debtor_input = QLineEdit()
        self.debtor_input.setReadOnly(True)
        self.debtor_button = QPushButton("Select Debtor")
        self.debtor_button.clicked.connect(self.select_debtor)
        debtor_layout.addWidget(self.debtor_label)
        debtor_layout.addWidget(self.debtor_input)
        debtor_layout.addWidget(self.debtor_button)
        layout.addLayout(debtor_layout)

        asset_layout = QHBoxLayout()
        self.asset_label = QLabel("Asset:")
        self.asset_input = QLineEdit()
        self.asset_input.setReadOnly(True)
        self.asset_button = QPushButton("Select Asset")
        self.asset_button.clicked.connect(self.select_asset)
        asset_layout.addWidget(self.asset_label)
        asset_layout.addWidget(self.asset_input)
        asset_layout.addWidget(self.asset_button)
        layout.addLayout(asset_layout)

        details_layout = QHBoxLayout()
        self.details_label = QLabel("Details (Optional):")
        self.details_input = QLineEdit()
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_input)
        layout.addLayout(details_layout)

        amount_layout = QHBoxLayout()
        self.amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        amount_layout.addWidget(self.amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)

        self.save_button = QPushButton("Record")
        self.save_button.clicked.connect(self.record_recovery)
        layout.addWidget(self.save_button)
        self.setLayout(layout)


    def select_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def select_debtor(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor',
            additional_filter="account = '1'"
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_debtor = selected
                self.debtor_input.setText(selected['name'])

    def select_asset(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts',
            additional_filter="type_id IN (1, 2)"
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_asset = selected
                self.asset_input.setText(f"{selected['name']} ({selected['code']})")

    def record_recovery(self):
        # Input Validation (same as before)
        if not self.date_input.text() or not self.selected_debtor or not self.selected_asset:
            QMessageBox.warning(self, "Error", "Please fill in all required fields.")
            return
        try:
            amount = float(self.amount_input.text())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid positive amount.")
            return

        date = self.date_input.text()
        details = self.details_input.text().strip()
        debtor_id = self.selected_debtor['id']
        debtor_name = self.selected_debtor['name']
        asset_id = self.selected_asset['id']
        transaction_type = "Inflow"  # Always "Inflow" for this function

        # Default details if empty
        if not details:
            details = f"{debtor_name}: Inflow"

        try:
            with self.db_manager as db:
                # --- 1. Update debtor_creditor_transactions ---
                db.cursor.execute(
                    """
                    INSERT INTO debtor_creditor_transactions (date, details, amount, debtor_creditor, type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (date, details, amount, debtor_id, transaction_type)  # Include type and debtor_id
                )

                # --- 2. Update debtor_creditor amount (DEDUCT) ---
                db.cursor.execute(
                    "UPDATE debtor_creditor SET amount = amount - ? WHERE id = ?",
                    (amount, debtor_id)
                )

                # --- 3. Load AR account ID from settings ---
                if not os.path.exists(self.settings_file):
                    QMessageBox.critical(self, "Error", "AR/AP settings not found.  Please configure them.")
                    return
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                ar_account_id = settings.get("receivable_account_id")
                if not ar_account_id:
                    QMessageBox.critical(self, "Error", "Accounts Receivable account not set in AR/AP settings.")
                    return

                # --- 4. Insert into transactions table ---
                db.cursor.execute(
                    "INSERT INTO transactions (date, description, debited, credited, amount) VALUES (?, ?, ?, ?, ?)",
                    (date, details, asset_id, ar_account_id, amount)  # Use 'details'
                )

                # --- 5. Update Account Balances ---
                db.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, asset_id))
                db.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, ar_account_id))

                db.commit()
                QMessageBox.information(self, "Success", "Asset recovery recorded successfully!")
                self.close()

        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))