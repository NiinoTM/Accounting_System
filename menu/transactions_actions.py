# --- START OF FILE transactions_actions.py ---

# menu/transactions_actions.py
import sqlite3
from PySide6.QtWidgets import QMenu, QMessageBox, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QDialogButtonBox, QAbstractItemView
from PySide6.QtCore import Qt
from utils.crud.transactions_crud import TransactionsCRUD
from utils.crud.template_transactions_crud import TemplateTransactionCRUD  # Import for template listing
from utils.crud.date_select import DateSelectWindow #import DateSelectWindow

class TransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.transactions_menu = QMenu("Transactions", self.main_window)
        self.transactions_crud = TransactionsCRUD()  # Create instance
        self.template_crud = TemplateTransactionCRUD() # Instance for template
        self.create_actions()

    def create_actions(self):
        self.add_transaction_action = self.transactions_menu.addAction("Add Transaction")
        self.add_transaction_action.triggered.connect(self.add_transaction)

        self.add_from_template_action = self.transactions_menu.addAction("Add Transaction from Template")
        self.add_from_template_action.triggered.connect(self.add_transaction_from_template)

        self.view_transactions_action = self.transactions_menu.addAction("View Transactions")
        self.view_transactions_action.triggered.connect(self.view_transactions)

        self.edit_transaction_action = self.transactions_menu.addAction("Edit Transaction")
        self.edit_transaction_action.triggered.connect(self.edit_transaction)

        self.delete_transaction_action = self.transactions_menu.addAction("Delete Transaction")
        self.delete_transaction_action.triggered.connect(self.delete_transaction)




    def add_transaction(self):
        self.transactions_crud.create(self.main_window)

    def view_transactions(self):
        self.transactions_crud.read(self.main_window)

    def edit_transaction(self):
        self.transactions_crud.edit(self.main_window)

    def delete_transaction(self):
        self.transactions_crud.delete(self.main_window)

    def add_transaction_from_template(self):
        """Handles adding transactions from a selected template."""
        # --- Step 1:  Show Template List ---
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Select Transaction Template")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        table = QTableWidget()
        layout.addWidget(table)

        # Fetch and display templates
        self.template_crud.conn.row_factory = sqlite3.Row # ensure row factory
        self.template_crud.cursor = self.template_crud.conn.cursor()
        self.template_crud.cursor.execute("SELECT * FROM transaction_templates")
        templates = self.template_crud.cursor.fetchall()

        table.setRowCount(len(templates))
        table.setColumnCount(3)  # ID, Name, Actions
        table.setHorizontalHeaderLabels(["ID", "Template Name", "Actions"])

        for row_idx, template in enumerate(templates):
            table.setItem(row_idx, 0, QTableWidgetItem(str(template['id'])))
            table.setItem(row_idx, 1, QTableWidgetItem(template['name']))

            # --- View Details Button ---
            view_details_button = QPushButton("View Details")
            view_details_button.clicked.connect(lambda checked, tid=template['id']: self.template_crud.show_template_details(self.main_window, str(tid)))
            table.setCellWidget(row_idx, 2, view_details_button)

        # --- Confirm Selection and Proceed ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._confirm_template_selection(dialog, table))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _confirm_template_selection(self, dialog, table):
        """Handles confirming the template and showing the transaction editing dialog."""
        selected_row = table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(dialog, "No Template Selected", "Please select a template.")
            return

        template_id = table.item(selected_row, 0).text()
        dialog.accept()  # Close the template selection dialog
        self._show_transaction_edit_dialog(template_id)

    def _show_transaction_edit_dialog(self, template_id):
        """Displays a dialog to edit transaction amounts from the selected template."""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Edit Transaction Amounts")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Initially not editable
        layout.addWidget(table)
        # Fetch template transactions and details, using debited/credited
        self.template_crud.cursor.execute("""
            SELECT tt.description, ttd.debited, ttd.credited, ttd.amount,
                   da.name AS debit_name, da.code AS debit_code,
                   ca.name AS credit_name, ca.code AS credit_code,
                   ttd.id AS transaction_detail_id
            FROM template_transactions tt
            JOIN template_transaction_details ttd ON tt.id = ttd.template_transaction_id
            JOIN accounts da ON ttd.debited = da.id  -- debited
            JOIN accounts ca ON ttd.credited = ca.id  -- credited
            WHERE tt.template_id = ?
        """, (template_id,))
        transactions = self.template_crud.cursor.fetchall()

        table.setRowCount(len(transactions))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Description", "Debited Account", "Credited Account", "Amount", "", ""])  # Edit/Delete

        self.transaction_data_for_creation = []  # Store prepared transactions

        for row_idx, trans in enumerate(transactions):
            # Store all necessary data.
            transaction_data = {
                'description': trans['description'],
                'debited': trans['debited'],
                'credited': trans['credited'],
                'amount': str(trans['amount']),  # Keep as string for editing
                'debit_name': trans['debit_name'],
                'debit_code': trans['debit_code'],
                'credit_name': trans['credit_name'],
                'credit_code': trans['credit_code'],
                'transaction_detail_id': trans['transaction_detail_id']
            }
            self.transaction_data_for_creation.append(transaction_data)


            table.setItem(row_idx, 0, QTableWidgetItem(trans['description']))
            table.setItem(row_idx, 1, QTableWidgetItem(f"{trans['debit_name']} ({trans['debit_code']})"))  # Display name/code
            table.setItem(row_idx, 2, QTableWidgetItem(f"{trans['credit_name']} ({trans['credit_code']})"))  # Display name/code
            table.setItem(row_idx, 3, QTableWidgetItem(str(trans['amount'])))

            # Edit Button
            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, row=row_idx: self._edit_transaction_amount(table, row))
            table.setCellWidget(row_idx, 4, edit_button)

            # Delete not needed, so an empty button
            table.setCellWidget(row_idx, 5, QLabel())

        # Proceed to Date Selection
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._select_date_and_create_transactions(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _edit_transaction_amount(self, table, row):
        """Allows editing the amount of a single transaction in the table."""
        transaction = self.transaction_data_for_creation[row]

        # Create a small dialog for editing the amount
        dialog = QDialog()
        dialog.setWindowTitle("Edit Amount")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        amount_label = QLabel("Amount:")
        amount_input = QLineEdit(transaction['amount'])  # Pre-fill with current amount
        layout.addWidget(amount_label)
        layout.addWidget(amount_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._update_amount_and_table(transaction, amount_input.text(), table, row, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _update_amount_and_table(self, transaction, new_amount, table, row, dialog):
        """Updates the transaction data and the table with the new amount."""
        try:
            float(new_amount)  # Validate amount
            transaction['amount'] = new_amount
            table.setItem(row, 3, QTableWidgetItem(new_amount))  # Update the table
            dialog.accept()
        except ValueError:
            QMessageBox.warning(dialog, "Invalid Amount", "Please enter a valid number for the amount.")

    def _select_date_and_create_transactions(self, dialog):
        """Opens the date selection dialog and then creates the transactions."""
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
            dialog.accept()  # Close the amount editing dialog
            self._create_transactions_with_date(selected_date)
        # else the operation is cancelled, no need for action

    def _create_transactions_with_date(self, selected_date):
        """Creates the transactions in the database with the selected date."""
        try:
            self.transactions_crud.cursor.execute("BEGIN")
            for transaction in self.transaction_data_for_creation:

                # Prepare the data for insertion.  We're *not* using
                # the _create_input_fields method of the CRUD class here,
                # because we already have the data.
                data = {
                    'date': selected_date,
                    'description': transaction['description'],
                    'debited': transaction['debited'],
                    'credited': transaction['credited'],
                    'amount': float(transaction['amount'])  # Now it's safe to convert
                }

                # Insert the transaction
                self.transactions_crud.cursor.execute(
                    """INSERT INTO transactions (date, description, debited, credited, amount)
                       VALUES (:date, :description, :debited, :credited, :amount)""",
                    data
                )

                # Update account balances
                self.transactions_crud._update_account_balance(data['debited'], data['amount'], 'add')
                self.transactions_crud._update_account_balance(data['credited'], data['amount'], 'subtract')


            self.transactions_crud.conn.commit()
            QMessageBox.information(self.main_window, "Success", "Transactions created successfully!")

        except (sqlite3.Error, ValueError) as e:
            self.transactions_crud.conn.rollback()
            QMessageBox.critical(self.main_window, "Error", f"Failed to create transactions: {str(e)}")