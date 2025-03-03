# ar_ap/record_liability_settlement.py

import sqlite3
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog)
from PySide6.QtCore import QDate
from create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name

class RecordLiabilitySettlementWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Record Liability Settlement (Outflow)")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "ar_ap_settings.json")
        self.selected_creditor = None
        self.selected_asset = None  # We'll use an asset to settle the liability
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Date Selection
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

        # Creditor Selection
        creditor_layout = QHBoxLayout()
        self.creditor_label = QLabel("Creditor:")
        self.creditor_input = QLineEdit()
        self.creditor_input.setReadOnly(True)
        self.creditor_button = QPushButton("Select Creditor")
        self.creditor_button.clicked.connect(self.select_creditor)
        creditor_layout.addWidget(self.creditor_label)
        creditor_layout.addWidget(self.creditor_input)
        creditor_layout.addWidget(self.creditor_button)
        layout.addLayout(creditor_layout)

        # Asset Selection (for payment)
        asset_layout = QHBoxLayout()
        self.asset_label = QLabel("Asset (Payment):")  # Clarified label
        self.asset_input = QLineEdit()
        self.asset_input.setReadOnly(True)
        self.asset_button = QPushButton("Select Asset")
        self.asset_button.clicked.connect(self.select_asset)
        asset_layout.addWidget(self.asset_label)
        asset_layout.addWidget(self.asset_input)
        asset_layout.addWidget(self.asset_button)
        layout.addLayout(asset_layout)

        # Details Input
        details_layout = QHBoxLayout()
        self.details_label = QLabel("Details (Optional):")
        self.details_input = QLineEdit()
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_input)
        layout.addLayout(details_layout)

        # Amount Input
        amount_layout = QHBoxLayout()
        self.amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        amount_layout.addWidget(self.amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)

        # Save Button
        self.save_button = QPushButton("Record Settlement")  # Changed button text
        self.save_button.clicked.connect(self.record_settlement)  # Changed method name
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def select_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def select_creditor(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor',
            additional_filter="account = '2'"  # Filter for creditors
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_creditor = selected
                self.creditor_input.setText(selected['name'])

    def select_asset(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts',
            additional_filter="type_id IN (1, 2)"  # Filter for assets
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_asset = selected
                self.asset_input.setText(f"{selected['name']} ({selected['code']})")

    def record_settlement(self):  # Changed method name
        # Input Validation
        if not self.date_input.text() or not self.selected_creditor or not self.selected_asset:
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
        creditor_id = self.selected_creditor['id']
        creditor_name = self.selected_creditor['name']
        asset_id = self.selected_asset['id']
        transaction_type = "Outflow"  #  "Outflow" for liability settlement

        # Default details
        if not details:
            details = f"{creditor_name}: Liability Settlement"

        try:
            with self.db_manager as db:
                # --- 1. Insert into debtor_creditor_transactions ---
                db.cursor.execute(
                    """
                    INSERT INTO debtor_creditor_transactions (date, details, amount, debtor_creditor, type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (date, details, amount, creditor_id, transaction_type)
                )

                # --- 2. Update debtor_creditor amount (Add) ---
                db.cursor.execute(
                    "UPDATE debtor_creditor SET amount = amount + ? WHERE id = ?",  # ADD for outflow
                    (amount, creditor_id)
                )

                # --- 3. Load AP account ID from settings ---
                if not os.path.exists(self.settings_file):
                    QMessageBox.critical(self, "Error", "AR/AP settings not found.  Please configure them.")
                    return
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                ap_account_id = settings.get("payable_account_id")
                if not ap_account_id:
                    QMessageBox.critical(self, "Error", "Accounts Payable account not set in AR/AP settings.")
                    return

                # --- 4. Insert into transactions table ---
                db.cursor.execute(
                    "INSERT INTO transactions (date, description, debited, credited, amount) VALUES (?, ?, ?, ?, ?)",
                    (date, details, ap_account_id, asset_id, amount)  # AP is debited, Asset is credited
                )

                # --- 5. Update Account Balances ---
                db.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, ap_account_id))  # Increase AP
                db.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, asset_id))  # Decrease Asset

                db.commit()
                QMessageBox.information(self, "Success", "Liability settled successfully!")
                self.close()

        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))