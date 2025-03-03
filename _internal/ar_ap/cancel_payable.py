# ar_ap/cancel_payable.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog)
from create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog

class CancelPayableWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Cancel Payable")
        self.db_manager = DatabaseManager()
        self.selected_creditor = None
        self.selected_transaction = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

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

        # Transaction Selection (initially disabled)
        transaction_layout = QHBoxLayout()
        self.transaction_label = QLabel("Transaction:")
        self.transaction_input = QLineEdit()
        self.transaction_input.setReadOnly(True)
        self.transaction_button = QPushButton("Select Transaction")
        self.transaction_button.clicked.connect(self.select_transaction)
        self.transaction_button.setEnabled(False)
        transaction_layout.addWidget(self.transaction_label)
        transaction_layout.addWidget(self.transaction_input)
        transaction_layout.addWidget(self.transaction_button)
        layout.addLayout(transaction_layout)

        # Date (read-only)
        date_layout = QHBoxLayout()
        self.date_label = QLabel("Date:")
        self.date_input = QLineEdit()
        self.date_input.setReadOnly(True)
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)

        # Details (read-only)
        details_layout = QHBoxLayout()
        self.details_label = QLabel("Details:")
        self.details_input = QLineEdit()
        self.details_input.setReadOnly(True)
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_input)
        layout.addLayout(details_layout)

        # Amount (read-only)
        amount_layout = QHBoxLayout()
        self.amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        self.amount_input.setReadOnly(True)
        amount_layout.addWidget(self.amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)

        # Cancel Button (initially disabled)
        self.cancel_button = QPushButton("Cancel Payable")  # Changed button text
        self.cancel_button.clicked.connect(self.cancel_payable)
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

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
                self.transaction_button.setEnabled(True)
                # Reset transaction if new creditor selected
                self.selected_transaction = None
                self.transaction_input.clear()
                self.clear_fields()

    def select_transaction(self):
        if not self.selected_creditor:
            return

        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor_transactions',
            additional_filter=f"debtor_creditor = '{self.selected_creditor['id']}'"
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_transaction = selected
                self.transaction_input.setText(f"ID: {selected['id']}, Date: {selected['date']}")
                self.populate_fields()
                self.cancel_button.setEnabled(True)

    def populate_fields(self):
        if self.selected_transaction:
            self.date_input.setText(self.selected_transaction['date'])
            self.details_input.setText(self.selected_transaction['details'])
            self.amount_input.setText(str(self.selected_transaction['amount']))

    def clear_fields(self):
        """Clears the input fields and disables the cancel button."""
        self.date_input.clear()
        self.details_input.clear()
        self.amount_input.clear()
        self.cancel_button.setEnabled(False)

    def cancel_payable(self):
        if not self.selected_transaction:
            return

        confirm = QMessageBox.question(
            self, "Confirm Cancel",
            "Are you sure you want to cancel this payable?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        transaction_id = self.selected_transaction['id']
        creditor_id = self.selected_creditor['id']
        amount = float(self.selected_transaction['amount'])
        transaction_type = self.selected_transaction['type']

        try:
            with self.db_manager as db:
                # --- 1. Find corresponding transaction in 'transactions' table ---
                db.cursor.execute("SELECT * FROM transactions WHERE description = ? AND date = ?", (self.selected_transaction['details'], self.selected_transaction['date']))
                transaction = db.cursor.fetchone()
                if not transaction:
                    QMessageBox.critical(self, "Error", "Could not find corresponding transaction in 'transactions' table.")
                    return

                transaction_id_trans = transaction['id']
                debited_account_id = transaction['debited']
                credited_account_id = transaction['credited']

                # --- 2. Delete from debtor_creditor_transactions ---
                db.cursor.execute(
                    "DELETE FROM debtor_creditor_transactions WHERE id = ?",
                    (transaction_id,)
                )

                # --- 3. Update debtor_creditor amount ---
                if transaction_type == "Inflow":  # If it was originally an inflow, we *add* it back
                    db.cursor.execute(
                        "UPDATE debtor_creditor SET amount = amount + ? WHERE id = ?",
                        (amount, creditor_id)
                    )
                elif transaction_type == "Outflow": # If it was a payment (outflow), we *subtract*
                    db.cursor.execute(
                        "UPDATE debtor_creditor SET amount = amount - ? WHERE id = ?",
                        (amount, creditor_id)
                    )
                else:
                    QMessageBox.critical(self, "Error", f"Invalid transaction type: {transaction_type}")
                    return

                # --- 4. Delete from transactions table ---
                db.cursor.execute(
                    "DELETE FROM transactions WHERE id = ?",
                    (transaction_id_trans,)
                )

                # --- 5. Update Account Balances ---
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (amount, debited_account_id)
                )
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (amount, credited_account_id)
                )

                db.commit()
                QMessageBox.information(self, "Success", "Payable canceled successfully!")
                self.close()

        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))