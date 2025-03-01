# ar_ap/adjust_receivable.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog)
from PySide6.QtCore import QDate
from data.create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name

class AdjustReceivableWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Adjust Receivable")
        self.db_manager = DatabaseManager()
        self.selected_debtor = None
        self.selected_transaction = None
        self.original_amount = 0  # Store the original amount
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Debtor Selection
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

        # Transaction Selection (initially disabled)
        transaction_layout = QHBoxLayout()
        self.transaction_label = QLabel("Transaction:")
        self.transaction_input = QLineEdit()
        self.transaction_input.setReadOnly(True)
        self.transaction_button = QPushButton("Select Transaction")
        self.transaction_button.clicked.connect(self.select_transaction)
        self.transaction_button.setEnabled(False)  # Disable until a debtor is selected
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

        # Details
        details_layout = QHBoxLayout()
        self.details_label = QLabel("Details:")
        self.details_input = QLineEdit()
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_input)
        layout.addLayout(details_layout)

        # Amount
        amount_layout = QHBoxLayout()
        self.amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        amount_layout.addWidget(self.amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)

        # Adjust Button (initially disabled)
        self.adjust_button = QPushButton("Adjust")
        self.adjust_button.clicked.connect(self.adjust_receivable)
        self.adjust_button.setEnabled(False)  # Disable until a transaction is selected
        layout.addWidget(self.adjust_button)

        self.setLayout(layout)

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
                self.transaction_button.setEnabled(True)  # Enable transaction selection
                # Reset transaction selection if a new debtor is chosen
                self.selected_transaction = None
                self.transaction_input.clear()
                self.clear_fields()


    def select_transaction(self):
        if not self.selected_debtor:
            return  # Should not happen, but check for safety

        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor_transactions',
            additional_filter=f"debtor_creditor = '{self.selected_debtor['id']}'"  # Filter by debtor ID
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_transaction = selected
                self.transaction_input.setText(f"ID: {selected['id']}, Date: {selected['date']}")  # Show ID and date
                self.populate_fields()
                self.adjust_button.setEnabled(True)  # Enable adjust button

    def populate_fields(self):
        if self.selected_transaction:
            self.date_input.setText(self.selected_transaction['date'])
            self.details_input.setText(self.selected_transaction['details'])
            self.amount_input.setText(str(self.selected_transaction['amount']))
            self.original_amount = float(self.selected_transaction['amount'])  # Store original

    def clear_fields(self):
        """Clears the input fields."""
        self.date_input.clear()
        self.details_input.clear()
        self.amount_input.clear()
        self.original_amount = 0
        self.adjust_button.setEnabled(False)

    def adjust_receivable(self):
      if not self.selected_transaction:
          return  # Should not happen

      try:
          new_amount = float(self.amount_input.text())
          if new_amount <=0:
            raise ValueError("Amount must be positive.")
      except ValueError:
          QMessageBox.warning(self, "Error", "Please enter a valid positive amount.")
          return

      new_details = self.details_input.text().strip()
      transaction_id = self.selected_transaction['id']
      debtor_id = self.selected_debtor['id']
      amount_difference = new_amount - self.original_amount

      try:
          with self.db_manager as db:
              # --- 1. Update debtor_creditor_transactions ---
              db.cursor.execute(
                  """
                  UPDATE debtor_creditor_transactions
                  SET details = ?, amount = ?
                  WHERE id = ?
                  """,
                  (new_details, new_amount, transaction_id)
              )

              # --- 2. Update debtor_creditor amount ---
              db.cursor.execute(
                  "UPDATE debtor_creditor SET amount = amount + ? WHERE id = ?",
                  (amount_difference, debtor_id)  # Use the *difference*
              )

              # --- 3. Find corresponding transaction in 'transactions' table ---
              db.cursor.execute("SELECT * FROM transactions WHERE description = ? AND date = ?", (self.selected_transaction['details'], self.selected_transaction['date']))
              transaction = db.cursor.fetchone()


              if transaction:  # Check if transaction was found
                transaction_id_trans = transaction['id']
                debited_account_id = transaction['debited']
                credited_account_id = transaction['credited']

                # --- 4. Update the 'transactions' table ---
                db.cursor.execute(
                    """
                    UPDATE transactions
                    SET description = ?, amount = ?
                    WHERE id = ?
                    """,
                    (new_details, new_amount, transaction_id_trans)
                )

                # --- 5. Update Account Balances ---
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (amount_difference, debited_account_id)  # Add the *difference*
                )
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (amount_difference, credited_account_id)  # Subtract the *difference*
                )
              else:
                QMessageBox.warning(self, "Error", "Couldnt find transaction id in transaction table")

              db.commit()
              QMessageBox.information(self, "Success", "Receivable adjusted successfully!")
              self.close()

      except (sqlite3.Error, Exception) as e:
          db.conn.rollback()
          QMessageBox.critical(self, "Error", str(e))