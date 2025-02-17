# utils/crud/template_transactions_crud.py
import sqlite3
from PySide6.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QLineEdit,
                              QPushButton, QLabel, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QDialogButtonBox, QAbstractItemView)
from PySide6.QtCore import Qt
from .generic_crud import GenericCRUD
from .search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name, normalize_text


class TemplateTransactionCRUD(GenericCRUD):
    def __init__(self):
        super().__init__('transaction_templates')
        self.transaction_data = []  # List of transaction dictionaries

    def create_template(self, main_window):
        dialog = QDialog(main_window)
        dialog.setWindowTitle("Create New Transaction Template")
        dialog.setMinimumSize(800, 600)  # Set a reasonable minimum size
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(QLabel("Template Name:"))
        template_name_input = QLineEdit()
        layout.addWidget(template_name_input)

        # --- Transactions Table ---
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(6)  # Description, Debit, Credit, Amount, Edit, Delete
        self.transactions_table.setHorizontalHeaderLabels(
            ["Description", "Debited Account", "Credited Account", "Amount", "", ""] # changed labels
        )
        self.transactions_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # not editable by double click.
        layout.addWidget(self.transactions_table)
        self.transaction_data = []  # Reset transaction data


        add_transaction_button = QPushButton("Add Transaction")
        add_transaction_button.clicked.connect(lambda: self._add_transaction_dialog(dialog))
        layout.addWidget(add_transaction_button)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._save_template(dialog, template_name_input.text()))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.finished.connect(lambda result: self._handle_dialog_close(dialog, result, template_name_input.text()))

        dialog.exec()

    def _handle_dialog_close(self, dialog, result, template_name):
        """Handles saving or discarding data when the dialog is closed."""
        if result == QDialog.Rejected:  # User clicked Cancel or closed the window
            if template_name.strip() or any(self.transaction_data):  # Check for any entered data
                confirm = QMessageBox.question(
                    dialog, "Confirm Discard",
                    "Do you want to discard the template?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.No:
                    dialog.show()  # re-open the dialog.

    def _add_transaction_dialog(self, parent_dialog):
        """Opens a dialog to add a single transaction."""
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle("Add Transaction")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        inputs = {}

        layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit()
        layout.addWidget(description_input)
        inputs['description'] = description_input

        # Changed field names to debited and credited, and account_type to generic
        for field, account_type in [('debited', 'generic'), ('credited', 'generic')]:
            layout.addWidget(QLabel(f"{format_table_name(field)} Account:"))  # Added "Account" for clarity
            display_field = QLineEdit()
            display_field.setReadOnly(True)
            search_button = QPushButton("Search")
            field_layout = QHBoxLayout()
            field_layout.addWidget(display_field)
            field_layout.addWidget(search_button)
            layout.addLayout(field_layout)
            inputs[field] = {'display': display_field, 'value': None, 'button': search_button}

            def create_search_handler(field_name, display, input_dict):
                def handle_search():
                    # Now searching all accounts, so we use 'generic' and the 'accounts' table.
                    search_dialog = AdvancedSearchDialog(field_type=account_type, parent=dialog, db_path=self.db_path, table_name='accounts')
                    if search_dialog.exec() == QDialog.Accepted:
                        selected = search_dialog.get_selected_item()
                        if selected:
                            display_text = f"{selected.get('name', '')} ({selected.get('code', '')})"
                            display.setText(display_text)
                            input_dict[field_name]['value'] = selected['id']
                return handle_search
            search_button.clicked.connect(create_search_handler(field, display_field, inputs))

        layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit()
        layout.addWidget(amount_input)
        inputs['amount'] = amount_input

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._add_transaction_to_table(inputs, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.exec()

    def _add_transaction_to_table(self, inputs, dialog):
        """Adds a transaction to the table and updates self.transaction_data."""
        transaction = {
            'description': inputs['description'].text(),
            'debited': inputs['debited']['value'],  # Use 'debited'
            'credited': inputs['credited']['value'],  # Use 'credited'
            'amount': inputs['amount'].text(),
            'debited_display': inputs['debited']['display'].text(),  # For display
            'credited_display': inputs['credited']['display'].text(), # For display
        }

        if not self._validate_transaction_data(transaction):
            return  # Validation failed

        self.transaction_data.append(transaction)
        self._update_transactions_table()
        dialog.accept()

    def _update_transactions_table(self):
        """Refreshes the QTableWidget with the current transaction data."""
        self.transactions_table.setRowCount(len(self.transaction_data))
        for row, transaction in enumerate(self.transaction_data):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(transaction['description']))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(transaction['debited_display'])) # changed
            self.transactions_table.setItem(row, 2, QTableWidgetItem(transaction['credited_display'])) # changed
            self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction['amount']))

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, r=row: self._edit_transaction(r))
            self.transactions_table.setCellWidget(row, 4, edit_button)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda checked, r=row: self._delete_transaction(r))
            self.transactions_table.setCellWidget(row, 5, delete_button)


    def _edit_transaction(self, row):
        """Opens the add transaction dialog to edit an existing transaction."""
        transaction = self.transaction_data[row]

        # Create and populate the dialog with the existing data.
        dialog = QDialog()
        dialog.setWindowTitle("Edit Transaction")
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        inputs = {}

        # Description
        layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit(transaction['description'])
        layout.addWidget(description_input)
        inputs['description'] = description_input

        # Debited and Credited Accounts (reusing search logic)
        #  Changed field names to debited and credited
        for field, account_type in [('debited', 'generic'), ('credited', 'generic')]:
            layout.addWidget(QLabel(f"{format_table_name(field)} Account:"))
            display_field = QLineEdit(transaction[f'{field}_display'])  # Pre-fill display
            display_field.setReadOnly(True)
            search_button = QPushButton("Search")
            field_layout = QHBoxLayout()
            field_layout.addWidget(display_field)
            field_layout.addWidget(search_button)
            layout.addLayout(field_layout)
            inputs[field] = {'display': display_field, 'value': transaction[field], 'button': search_button}

            def create_search_handler(field_name, display, input_dict):
                def handle_search():
                    # search all accounts.
                    search_dialog = AdvancedSearchDialog(field_type=account_type, parent=dialog, db_path=self.db_path, table_name='accounts')
                    if search_dialog.exec() == QDialog.Accepted:
                        selected = search_dialog.get_selected_item()
                        if selected:
                            display_text = f"{selected.get('name', '')} ({selected.get('code', '')})"
                            display.setText(display_text)
                            input_dict[field_name]['value'] = selected['id']
                return handle_search

            search_button.clicked.connect(create_search_handler(field, display_field, inputs))

        # Amount
        layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit(transaction['amount'])
        layout.addWidget(amount_input)
        inputs['amount'] = amount_input

        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._update_transaction(row, inputs, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _update_transaction(self, row, inputs, dialog):
        # changed debited and credited
        updated_transaction = {
            'description': inputs['description'].text(),
            'debited': inputs['debited']['value'],
            'credited': inputs['credited']['value'],
            'amount': inputs['amount'].text(),
            'debited_display': inputs['debited']['display'].text(),  # Update display
            'credited_display': inputs['credited']['display'].text(), # Update display
        }
        if self._validate_transaction_data(updated_transaction):
            self.transaction_data[row] = updated_transaction
            self._update_transactions_table()
            dialog.accept()

    def _delete_transaction(self, row):
        """Deletes a transaction from the table and updates self.transaction_data."""
        confirm = QMessageBox.question(
            None, "Confirm Delete",
            "Are you sure you want to delete this transaction?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.transaction_data[row]
            self._update_transactions_table()

    def _validate_transaction_data(self, transaction):
        """Validates a single transaction's data."""
        if not transaction['description'].strip():
            QMessageBox.warning(None, "Error", "Description cannot be empty.")
            return False
        if transaction['debited'] is None:  # Use 'debited'
            QMessageBox.warning(None, "Error", "Debited account must be selected.")
            return False
        if transaction['credited'] is None:  # Use 'credited'
            QMessageBox.warning(None, "Error", "Credited account must be selected.")
            return False
        if not transaction['amount'].strip():
            QMessageBox.warning(None, "Error", "Amount cannot be empty.")
            return False
        try:
            float(transaction['amount'])  # Check if amount is a valid number
        except ValueError:
            QMessageBox.warning(None, "Error", "Invalid amount format.")
            return False
        return True

    def _save_template_changes(self, dialog, template_id, new_template_name):
        """Save changes to the template and its transactions."""
        if not new_template_name.strip():
            QMessageBox.warning(dialog, "Error", "Template name cannot be empty.")
            return
        if not self.transaction_data:
            QMessageBox.warning(dialog, "Error", "At least one transaction is required.")
            return

        try:
            self.cursor.execute("BEGIN")
            
            # Update template name
            normalized_template_name = normalize_text(new_template_name)
            self.cursor.execute(
                "UPDATE transaction_templates SET name = ?, normalized_name = ? WHERE id = ?",
                (new_template_name, normalized_template_name, template_id)
            )

            # Delete existing transactions and details
            self.cursor.execute(
                "DELETE FROM template_transactions WHERE template_id = ?",
                (template_id,)
            )

            # Insert updated transactions
            for transaction in self.transaction_data:
                self.cursor.execute(
                    "INSERT INTO template_transactions (template_id, description) VALUES (?, ?)",
                    (template_id, transaction['description'])
                )
                template_transaction_id = self.cursor.lastrowid
                
                self.cursor.execute(
                    """INSERT INTO template_transaction_details 
                    (template_transaction_id, debited, credited, amount) 
                    VALUES (?, ?, ?, ?)""",
                    (template_transaction_id, transaction['debited'], 
                    transaction['credited'], float(transaction['amount']))
                )

            self.conn.commit()
            QMessageBox.information(dialog, "Success", "Template updated successfully!")
            dialog.accept()

        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.critical(dialog, "Database Error", str(e))

    def read(self, main_window):
        """Displays the list of templates. Double-clicking shows details."""
        # Ensure we're using Row factory for this connection
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("SELECT * FROM transaction_templates")
        templates = self.cursor.fetchall()

        table = QTableWidget(main_window)
        table.setRowCount(len(templates))
        table.setColumnCount(2)  # ID and Name
        table.setHorizontalHeaderLabels(["ID", "Template Name"])

        for row_idx, template in enumerate(templates):
            table.setItem(row_idx, 0, QTableWidgetItem(str(template['id'])))
            table.setItem(row_idx, 1, QTableWidgetItem(template['name']))

        table.cellDoubleClicked.connect(lambda row, col: self.show_template_details(main_window, table.item(row, 0).text()))
        main_window.setCentralWidget(table)

    def show_template_details(self, main_window, template_id):
        """Shows the details (transactions) of a selected template."""
        dialog = QDialog(main_window)
        dialog.setWindowTitle("Template Details")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        table = QTableWidget()
        layout.addWidget(table)

        # Fetch template transactions and details, using debited/credited
        self.cursor.execute("""
            SELECT tt.description, ttd.debited, ttd.credited, ttd.amount,
                   da.name AS debit_name, da.code AS debit_code,
                   ca.name AS credit_name, ca.code AS credit_code
            FROM template_transactions tt
            JOIN template_transaction_details ttd ON tt.id = ttd.template_transaction_id
            JOIN accounts da ON ttd.debited = da.id  -- debited
            JOIN accounts ca ON ttd.credited = ca.id  -- credited
            WHERE tt.template_id = ?
        """, (template_id,))
        transactions = self.cursor.fetchall()

        table.setRowCount(len(transactions))
        table.setColumnCount(5)  # Desc, Debited, Credited, Amount, Debit Name/Code, Credit Name/Code
        table.setHorizontalHeaderLabels(["Description", "Debited Account", "Credited Account", "Amount", "Debit Name/Code", "Credit Name/Code"])

        for row_idx, trans in enumerate(transactions):
            table.setItem(row_idx, 0, QTableWidgetItem(trans['description']))
            table.setItem(row_idx, 1, QTableWidgetItem(str(trans['debited']))) # changed
            table.setItem(row_idx, 2, QTableWidgetItem(str(trans['credited']))) # changed
            table.setItem(row_idx, 3, QTableWidgetItem(str(trans['amount'])))
            table.setItem(row_idx, 4, QTableWidgetItem(f"{trans['debit_name']} ({trans['debit_code']})"))
            table.setItem(row_idx, 5, QTableWidgetItem(f"{trans['credit_name']} ({trans['credit_code']})"))

        dialog.exec()

    def edit(self, main_window):
        """Edit an existing template and its transactions."""
        # Ensure we're using Row factory for this connection
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Use advanced search to select template to edit
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_template = search_dialog.get_selected_item()
            if not selected_template:
                return

            template_id = selected_template['id']
            
            # Create edit dialog
            dialog = QDialog(main_window)
            dialog.setWindowTitle("Edit Transaction Template")
            dialog.setMinimumSize(800, 600)
            layout = QVBoxLayout()
            dialog.setLayout(layout)

            # Template name field
            layout.addWidget(QLabel("Template Name:"))
            template_name_input = QLineEdit(selected_template['name'])
            layout.addWidget(template_name_input)

            # Initialize transaction table
            self.transactions_table = QTableWidget()
            self.transactions_table.setColumnCount(6)  # Description, Debit, Credit, Amount, Edit, Delete
            self.transactions_table.setHorizontalHeaderLabels(
                ["Description", "Debited Account", "Credited Account", "Amount", "", ""]
            )
            self.transactions_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            layout.addWidget(self.transactions_table)

            # Load existing transactions
            self.transaction_data = []
            self.cursor.execute("""
                SELECT tt.id, tt.description, ttd.debited, ttd.credited, ttd.amount,
                    da.name AS debit_name, da.code AS debit_code,
                    ca.name AS credit_name, ca.code AS credit_code
                FROM template_transactions tt
                JOIN template_transaction_details ttd ON tt.id = ttd.template_transaction_id
                JOIN accounts da ON ttd.debited = da.id
                JOIN accounts ca ON ttd.credited = ca.id
                WHERE tt.template_id = ?
            """, (template_id,))
            
            existing_transactions = self.cursor.fetchall()
            
            for trans in existing_transactions:
                transaction = {
                    'id': trans['id'],
                    'description': trans['description'],
                    'debited': trans['debited'],
                    'credited': trans['credited'],
                    'amount': str(trans['amount']),
                    'debited_display': f"{trans['debit_name']} ({trans['debit_code']})",
                    'credited_display': f"{trans['credit_name']} ({trans['credit_code']})"
                }
                self.transaction_data.append(transaction)
            
            self._update_transactions_table()

            # Add transaction button
            add_transaction_button = QPushButton("Add Transaction")
            add_transaction_button.clicked.connect(lambda: self._add_transaction_dialog(dialog))
            layout.addWidget(add_transaction_button)

            # Save and Cancel buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            button_box.accepted.connect(
                lambda: self._save_template_changes(dialog, template_id, template_name_input.text())
            )
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.exec()

    def delete(self, main_window):
        """Deletes a template and all associated transactions (with confirmation)."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name= self.table_name
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item:
                return

            template_id = selected_item['id']
            confirm = QMessageBox.question(
                main_window, "Confirm Delete",
                f"Are you sure you want to delete the template '{selected_item['name']}' and ALL its transactions?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                try:
                    # Use a transaction for atomicity (all or nothing)
                    self.cursor.execute("BEGIN")
                    # The ON DELETE CASCADE in the database schema will handle deleting
                    # related records in template_transactions and template_transaction_details.
                    self.cursor.execute("DELETE FROM transaction_templates WHERE id = ?", (template_id,))
                    self.conn.commit()
                    QMessageBox.information(main_window, "Success", "Template and transactions deleted successfully!")
                except sqlite3.Error as e:
                    self.conn.rollback()
                    QMessageBox.critical(main_window, "Database Error", str(e))