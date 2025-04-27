# menu/transactions_actions.py
import sqlite3
from PySide6.QtWidgets import QMenu, QHBoxLayout, QMessageBox, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QDialogButtonBox, QAbstractItemView
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView  # Import QHeaderView
from utils.crud.transactions_crud import TransactionsCRUD
from utils.crud.template_transactions_crud import TemplateTransactionCRUD
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
# Import the new filter dialog
from utils.crud.transaction_filter_dialog import TransactionFilterDialog
from utils.formatters import format_table_name  # Import the formatter


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
        # Connect to the new method that opens the filter dialog
        self.view_transactions_action.triggered.connect(self.show_transaction_filter)

        self.edit_transaction_action = self.transactions_menu.addAction("Edit Transaction")
        self.edit_transaction_action.triggered.connect(self.edit_transaction)

        self.delete_transaction_action = self.transactions_menu.addAction("Delete Transaction")
        self.delete_transaction_action.triggered.connect(self.delete_transaction)

    def add_transaction(self):
        self.transactions_crud.create(self.main_window)

    def show_transaction_filter(self): # Renamed from view_transactions
        """Opens the filter dialog and then displays transactions."""
        dialog = TransactionFilterDialog(self.main_window)
        if dialog.exec() == QDialog.Accepted:
            filters = dialog.get_filters()
            if filters: # Ensure filters are valid
                # Call the CRUD read method with the filters
                self.transactions_crud.read(self.main_window, filters=filters)

    def view_transactions(self):
        # This method is now effectively replaced by show_transaction_filter
        # You can keep it if you want an unfiltered view option elsewhere,
        # or remove it if show_transaction_filter is the only way to view.
        # For now, let's call the filter dialog from here too for consistency if triggered elsewhere.
        self.show_transaction_filter()

    def edit_transaction(self):
        self.transactions_crud.edit(self.main_window)

    def delete_transaction(self):
        self.transactions_crud.delete(self.main_window)

    def add_transaction_from_template(self):
        """Handles adding transactions from a selected template."""
        # --- Step 1: Show Template List using AdvancedSearchDialog ---
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self.main_window,
            db_path=self.transactions_crud.db_path,  # Use the transactions CRUD's db_path
            table_name='transaction_templates'  # Specify the table for templates
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_template = search_dialog.get_selected_item()
            if selected_template:
                # --- Proceed with the selected template ---
                self._show_transaction_edit_dialog(selected_template['id'])


    def _show_transaction_edit_dialog(self, template_id):
        """Displays a dialog to edit transaction amounts from the selected template."""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Edit Transaction Amounts")
        dialog.setMinimumSize(800, 400)  # Set a reasonable minimum size!
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Initially not editable
        layout.addWidget(table)

        # --- CRITICAL FIX: Set row_factory here, before the execute call ---
        self.template_crud.conn.row_factory = sqlite3.Row
        self.template_crud.cursor = self.template_crud.conn.cursor()  # Ensure we have a fresh cursor


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

        # --- Column Sizing ---
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Description stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Debited Account
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Credited Account
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) #amount
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Edit button - fixed size
        header.setSectionResizeMode(5, QHeaderView.Fixed) #empty label
        header.resizeSection(4, 80)   # Set a reasonable width for the Edit button
        header.resizeSection(5, 20)

        self.transaction_data_for_creation = []  # Store prepared transactions

        for row_idx, trans in enumerate(transactions):
            # Store all necessary data.  Now trans is an sqlite3.Row object.
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
        """Allows editing ALL fields of a single transaction."""
        transaction = self.transaction_data_for_creation[row]

        # Create a dialog for editing
        dialog = QDialog()
        dialog.setWindowTitle("Edit Transaction")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # --- 1. Description ---
        layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit(transaction['description'])
        layout.addWidget(description_input)

        # --- 2. Debited Account ---
        layout.addWidget(QLabel("Debited Account:"))
        debited_display = QLineEdit(transaction['debit_name'] + " (" + transaction['debit_code'] + ")")
        debited_display.setReadOnly(True)
        debited_search_button = QPushButton("Search")
        debited_layout = QHBoxLayout()
        debited_layout.addWidget(debited_display)
        debited_layout.addWidget(debited_search_button)
        layout.addLayout(debited_layout)
        debited_account_id = transaction['debited']  # Store current ID

        def handle_debited_search():
            nonlocal debited_account_id  # Access and modify the outer variable
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=dialog, db_path=self.transactions_crud.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected:
                    debited_display.setText(f"{selected['name']} ({selected['code']})")
                    debited_account_id = selected['id']  # Update the ID

        debited_search_button.clicked.connect(handle_debited_search)


        # --- 3. Credited Account ---
        layout.addWidget(QLabel("Credited Account:"))
        credited_display = QLineEdit(transaction['credit_name'] + " (" + transaction['credit_code'] + ")")
        credited_display.setReadOnly(True)
        credited_search_button = QPushButton("Search")
        credited_layout = QHBoxLayout()
        credited_layout.addWidget(credited_display)
        credited_layout.addWidget(credited_search_button)
        layout.addLayout(credited_layout)
        credited_account_id = transaction['credited']  # Store current ID

        def handle_credited_search():
            nonlocal credited_account_id
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=dialog, db_path=self.transactions_crud.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected:
                    credited_display.setText(f"{selected['name']} ({selected['code']})")
                    credited_account_id = selected['id']  # Update the ID
        credited_search_button.clicked.connect(handle_credited_search)

        # --- 4. Amount ---
        layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit(transaction['amount'])
        layout.addWidget(amount_input)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._update_transaction_and_table(
            row, description_input.text(), debited_account_id, debited_display.text(),
            credited_account_id, credited_display.text(), amount_input.text(), table, dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()


    def _update_transaction_and_table(self, row, new_description, new_debited_id, new_debited_display,
                                      new_credited_id, new_credited_display, new_amount, table, dialog):
        """Updates the transaction data and the table."""
        try:
            float(new_amount)  # Validate amount
            transaction = self.transaction_data_for_creation[row]
            transaction['description'] = new_description
            transaction['debited'] = new_debited_id
            transaction['credited'] = new_credited_id
            transaction['amount'] = new_amount
            #  Update display names/codes (very important!)
            transaction['debit_name'] = new_debited_display.split(" (")[0]  # Extract name
            transaction['debit_code'] = new_debited_display.split(" (")[1][:-1]  # Extract code
            transaction['credit_name'] = new_credited_display.split(" (")[0]
            transaction['credit_code'] = new_credited_display.split(" (")[1][:-1]


            # Update the table
            table.setItem(row, 0, QTableWidgetItem(new_description))
            table.setItem(row, 1, QTableWidgetItem(new_debited_display))
            table.setItem(row, 2, QTableWidgetItem(new_credited_display))
            table.setItem(row, 3, QTableWidgetItem(new_amount))

            dialog.accept()
        except ValueError:
            QMessageBox.warning(dialog, "Invalid Amount", "Please enter a valid number for the amount.")


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