# delete_recurring_transactions.py

import sqlite3
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout) # Changed QWidget to QDialog
from data.create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog

class DeleteRecurringTransactionWindow(QDialog): # Changed QWidget to QDialog
    def __init__(self, main_window):
        super().__init__(parent=main_window) # Updated super().__init__ to include parent
        self.main_window = main_window
        self.setWindowTitle("Delete Recurring Transaction")
        self.db_manager = DatabaseManager()
        self.selected_recurring_transaction_id = None
        self.selected_recurring_transaction_description = None # Store description for confirmation
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Select Recurring Transaction
        select_recurring_layout = QHBoxLayout()
        self.select_recurring_label = QLabel("Recurring Transaction to Delete:")
        self.select_recurring_input = QLineEdit()
        self.select_recurring_input.setReadOnly(True)
        self.select_recurring_button = QPushButton("Select Recurring Transaction")
        self.select_recurring_button.clicked.connect(self.select_recurring_transaction)
        select_recurring_layout.addWidget(self.select_recurring_label)
        select_recurring_layout.addWidget(self.select_recurring_input)
        select_recurring_layout.addWidget(self.select_recurring_button)
        layout.addLayout(select_recurring_layout)

        # Confirmation Label (initially empty)
        self.confirmation_label = QLabel("")
        layout.addWidget(self.confirmation_label)

        # Delete Button (initially disabled)
        self.delete_button = QPushButton("Delete Recurring Transaction")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_recurring_transaction)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def select_recurring_transaction(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='recurring_transactions'
        )
        if search_dialog.exec() == QDialog.Accepted: # QDialog uses .exec()
            selected_transaction = search_dialog.get_selected_item()
            if selected_transaction:
                self.selected_recurring_transaction_id = selected_transaction['id']
                self.selected_recurring_transaction_description = selected_transaction['description'] # Store description
                self.select_recurring_input.setText(f"Recurring Transaction ID: {self.selected_recurring_transaction_id}")
                self.confirmation_label.setText(f"Confirm deletion of recurring transaction: '{self.selected_recurring_transaction_description}'?") # Use description in confirmation
                self.delete_button.setEnabled(True) # Enable delete button

    def delete_recurring_transaction(self):
        if self.selected_recurring_transaction_id is None:
            QMessageBox.warning(self, "Error", "No recurring transaction selected for deletion.")
            return

        try:
            with self.db_manager as db:
                # Fetch debited, credited, and description to delete future transactions
                db.cursor.execute("SELECT debited, credited, description FROM recurring_transactions WHERE id = ?", (self.selected_recurring_transaction_id,))
                transaction_details = db.cursor.fetchone()
                if transaction_details:
                    debited_id = transaction_details['debited']
                    credited_id = transaction_details['credited']
                    description = transaction_details['description']

                    # Delete future transactions first
                    db.cursor.execute(
                        "DELETE FROM future_transactions WHERE debited = ? AND credited = ? AND description = ?",
                        (debited_id, credited_id, description)
                    )

                    # Delete the recurring transaction
                    delete_query = "DELETE FROM recurring_transactions WHERE id = ?"
                    db.cursor.execute(delete_query, (self.selected_recurring_transaction_id,))

                    db.commit()
                    QMessageBox.information(self, "Success",
                                            f"Recurring transaction '{self.selected_recurring_transaction_description}' and associated future transactions deleted successfully!") # Use stored description
                    self.close() # close the dialog

                else:
                    QMessageBox.warning(self, "Error", "Recurring transaction not found in database.")
                    return

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))