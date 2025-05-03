# --- START OF FILE transactions_actions.py ---

# menu/transactions_actions.py
import sqlite3
from PySide6.QtWidgets import (QMenu, QHBoxLayout, QMessageBox, QDialog, QVBoxLayout,
                              QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
                              QLabel, QDialogButtonBox, QAbstractItemView, QHeaderView) # Added QHeaderView
from PySide6.QtCore import Qt, QLocale # Added QLocale
from utils.crud.transactions_crud import TransactionsCRUD
from utils.crud.template_transactions_crud import TemplateTransactionCRUD
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
# Import the new filter dialog
from utils.crud.transaction_filter_dialog import TransactionFilterDialog
# from utils.formatters import format_table_name # Import formatter if needed directly


class TransactionsActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.transactions_menu = QMenu("Transactions", self.main_window)
        # Initialize CRUD instances - TransactionsCRUD now includes source_type checks
        self.transactions_crud = TransactionsCRUD()
        self.template_crud = TemplateTransactionCRUD()
        self.transaction_data_for_creation = [] # Initialize temporary storage for template transactions
        self.create_actions()

    def create_actions(self):
        """Creates the menu actions and connects them to methods."""
        self.add_transaction_action = self.transactions_menu.addAction("Add Transaction")
        self.add_transaction_action.triggered.connect(self.add_transaction) # Calls CRUD.create

        self.add_from_template_action = self.transactions_menu.addAction("Add Transaction from Template")
        self.add_from_template_action.triggered.connect(self.add_transaction_from_template) # Calls template logic

        self.view_transactions_action = self.transactions_menu.addAction("View Transactions")
        self.view_transactions_action.triggered.connect(self.show_transaction_filter) # Opens filter dialog

        self.edit_transaction_action = self.transactions_menu.addAction("Edit Transaction")
        self.edit_transaction_action.triggered.connect(self.edit_transaction) # Calls CRUD.edit (with source_type check)

        self.delete_transaction_action = self.transactions_menu.addAction("Delete Transaction")
        self.delete_transaction_action.triggered.connect(self.delete_transaction) # Calls CRUD.delete (with source_type check)

    def add_transaction(self):
        """Opens the standard transaction creation dialog via CRUD."""
        # CRUD's _save_record handles setting source_type='GENERAL' for new records
        self.transactions_crud.create(self.main_window)

    def show_transaction_filter(self):
        """Opens the filter dialog and then displays transactions based on filters."""
        dialog = TransactionFilterDialog(self.main_window)
        if dialog.exec() == QDialog.Accepted:
            filters = dialog.get_filters()
            # Proceed even if filters is empty dict, read handles defaults
            self.transactions_crud.read(self.main_window, filters=filters)
        # else: User cancelled filter dialog

    def view_transactions(self):
        """Legacy method - now consistently opens the filter dialog."""
        # If an unfiltered view is needed, it can be triggered by the filter
        # dialog with default/empty settings (e.g., empty dates, no account, default limit).
        self.show_transaction_filter()

    def edit_transaction(self):
        """Initiates the edit process via CRUD (which includes source_type check)."""
        # The CRUD edit method now contains the logic to check source_type
        # and prevent editing if not 'GENERAL'.
        self.transactions_crud.edit(self.main_window)

    def delete_transaction(self):
        """Initiates the delete process via CRUD (which includes source_type check)."""
        # The CRUD delete method now contains the logic to check source_type
        # and prevent deletion if not 'GENERAL'.
        self.transactions_crud.delete(self.main_window)

    # --- Template Transaction Logic ---

    def add_transaction_from_template(self):
        """Handles adding transactions starting from selecting a template."""
        # Step 1: Select the template using a search dialog
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self.main_window,
            db_path=self.transactions_crud.db_path, # Use consistent DB path from transactions CRUD
            table_name='transaction_templates'
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_template = search_dialog.get_selected_item()
            if selected_template and 'id' in selected_template:
                # Step 2: Show the dialog for reviewing and editing template details
                self._show_transaction_edit_dialog(selected_template['id'])
            elif selected_template:
                QMessageBox.warning(self.main_window, "Selection Error", "Selected template is missing a valid ID.")
            # else: User cancelled template selection

    def _show_transaction_edit_dialog(self, template_id):
        """Displays a dialog to review and edit transaction details fetched from the selected template."""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Review & Edit Template Transactions")
        dialog.setMinimumSize(850, 450) # Provide ample space
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Prevent direct editing in the table cells
        table.setSelectionBehavior(QAbstractItemView.SelectRows) # Select whole rows
        table.setSelectionMode(QAbstractItemView.SingleSelection) # Select one row at a time
        layout.addWidget(table)

        try:
            # Ensure the template CRUD connection uses sqlite3.Row factory
            if not isinstance(self.template_crud.conn.row_factory, type(sqlite3.Row)):
                 self.template_crud.conn.row_factory = sqlite3.Row
                 self.template_crud.cursor = self.template_crud.conn.cursor() # Recreate cursor if needed

            # Fetch transaction details associated with the selected template
            self.template_crud.cursor.execute("""
                SELECT tt.description, ttd.debited, ttd.credited, ttd.amount,
                       da.name AS debit_name, da.code AS debit_code,
                       ca.name AS credit_name, ca.code AS credit_code,
                       ttd.id AS transaction_detail_id -- Original detail ID from template_transaction_details
                FROM template_transactions tt
                JOIN template_transaction_details ttd ON tt.id = ttd.template_transaction_id
                JOIN accounts da ON ttd.debited = da.id
                JOIN accounts ca ON ttd.credited = ca.id
                WHERE tt.template_id = ?
            """, (template_id,))
            transactions_from_db = self.template_crud.cursor.fetchall()

            if not transactions_from_db:
                QMessageBox.information(dialog, "Empty Template", "This transaction template has no details defined.")
                dialog.reject() # Close the dialog if the template is empty
                return

            # Setup table columns
            table.setRowCount(len(transactions_from_db))
            table.setColumnCount(6) # Description, Debited Acct, Credited Acct, Amount, Edit Btn, Spacer
            table.setHorizontalHeaderLabels(["Description", "Debited Account", "Credited Account", "Amount", "Edit", ""])

            # Configure Column Sizing
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)         # Description stretches
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Debited Account fits content
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Credited Account fits content
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Amount fits content
            header.setSectionResizeMode(4, QHeaderView.Fixed)            # Edit Button fixed width
            header.setSectionResizeMode(5, QHeaderView.Fixed)            # Spacer fixed width
            header.resizeSection(4, 80) # Set width for Edit button column
            header.resizeSection(5, 10) # Set width for spacer column

            self.transaction_data_for_creation = [] # Reset/clear temporary storage list

            # Populate the temporary storage and the table
            for row_idx, trans_row in enumerate(transactions_from_db):
                # Store all necessary data in our temporary list of dictionaries
                transaction_data = {
                    'description': trans_row['description'],
                    'debited': trans_row['debited'],
                    'credited': trans_row['credited'],
                    'amount': str(trans_row['amount']), # Store amount as string initially for editing
                    'debit_name': trans_row['debit_name'],
                    'debit_code': trans_row['debit_code'],
                    'credit_name': trans_row['credit_name'],
                    'credit_code': trans_row['credit_code'],
                    'transaction_detail_id': trans_row['transaction_detail_id'] # Preserve original template detail ID if needed later
                }
                self.transaction_data_for_creation.append(transaction_data)

                # Populate the visual table row
                table.setItem(row_idx, 0, QTableWidgetItem(trans_row['description']))
                table.setItem(row_idx, 1, QTableWidgetItem(f"{trans_row['debit_name']} ({trans_row['debit_code']})"))
                table.setItem(row_idx, 2, QTableWidgetItem(f"{trans_row['credit_name']} ({trans_row['credit_code']})"))

                # Format amount nicely for display in the table
                try: amount_display_str = "{:,.2f}".format(float(trans_row['amount']))
                except (ValueError, TypeError): amount_display_str = str(trans_row['amount'] or '0.00') # Fallback
                amount_item_display = QTableWidgetItem(amount_display_str)
                amount_item_display.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Align amount right
                table.setItem(row_idx, 3, amount_item_display)

                # Add an 'Edit' button to each row
                edit_button = QPushButton("Edit")
                # Use lambda with default argument capture to pass the correct row index and table instance
                edit_button.clicked.connect(lambda checked=False, row=row_idx, tbl=table: self._edit_single_template_transaction(tbl, row))
                table.setCellWidget(row_idx, 4, edit_button)

                # Add a small spacer widget (e.g., an empty QLabel) in the last column
                table.setCellWidget(row_idx, 5, QLabel())

            table.resizeRowsToContents() # Adjust row heights

            # Dialog buttons: Proceed to Date Selection or Cancel
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.button(QDialogButtonBox.Ok).setText("Proceed to Select Date") # Custom text for OK
            # Connect OK to the date selection step, passing the current dialog instance
            button_box.accepted.connect(lambda current_dialog=dialog: self._select_date_and_create_transactions(current_dialog))
            button_box.rejected.connect(dialog.reject) # Cancel closes the dialog
            layout.addWidget(button_box)

            dialog.exec() # Show the modal dialog

        except sqlite3.Error as e:
            QMessageBox.critical(self.main_window, "Database Error", f"Failed to load template transaction details: {str(e)}")
        except Exception as e:
             QMessageBox.critical(self.main_window, "Error", f"An unexpected error occurred while preparing template view: {str(e)}")

    def _edit_single_template_transaction(self, table, row):
        """Opens a dialog to edit all fields of a single transaction *before* it's created."""
        # Basic bounds check
        if not (0 <= row < len(self.transaction_data_for_creation)):
            QMessageBox.warning(table.parent(), "Error", "Invalid row index selected for editing.")
            return

        transaction_to_edit = self.transaction_data_for_creation[row]

        # Create a dedicated dialog for editing this single item
        edit_dialog = QDialog(table.parent()) # Parent to the previous review dialog
        edit_dialog.setWindowTitle(f"Edit Transaction Detail (Row {row + 1})")
        edit_layout = QVBoxLayout()
        edit_dialog.setLayout(edit_layout)
        edit_dialog.setMinimumWidth(450)

        # --- 1. Description Field ---
        edit_layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit(transaction_to_edit['description'])
        edit_layout.addWidget(description_input)

        # --- 2. Debited Account Field ---
        edit_layout.addWidget(QLabel("Debited Account:"))
        debited_display = QLineEdit(f"{transaction_to_edit['debit_name']} ({transaction_to_edit['debit_code']})")
        debited_display.setReadOnly(True) # Display only, changed via search
        debited_search_button = QPushButton("Search")
        debited_layout = QHBoxLayout()
        debited_layout.addWidget(debited_display)
        debited_layout.addWidget(debited_search_button)
        edit_layout.addLayout(debited_layout)
        # Use a temporary dictionary to hold potentially changed account info during the edit dialog session
        temp_edit_data = {
            'debited_id': transaction_to_edit['debited'],
            'debited_display': debited_display.text()
        }

        def handle_debited_search():
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=self.transactions_crud.db_path,
                table_name='accounts', additional_filter='is_active = 1' # Only show active accounts
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected and 'id' in selected and 'name' in selected:
                    code = selected.get('code', '?') # Handle missing code gracefully
                    display_text = f"{selected['name']} ({code})"
                    debited_display.setText(display_text)
                    # Update the temporary dictionary holding the selection
                    temp_edit_data['debited_id'] = selected['id']
                    temp_edit_data['debited_display'] = display_text
                elif selected:
                     QMessageBox.warning(edit_dialog, "Selection Error", "Invalid account selected (missing ID or name).")

        debited_search_button.clicked.connect(handle_debited_search)

        # --- 3. Credited Account Field ---
        edit_layout.addWidget(QLabel("Credited Account:"))
        credited_display = QLineEdit(f"{transaction_to_edit['credit_name']} ({transaction_to_edit['credit_code']})")
        credited_display.setReadOnly(True) # Display only
        credited_search_button = QPushButton("Search")
        credited_layout = QHBoxLayout()
        credited_layout.addWidget(credited_display)
        credited_layout.addWidget(credited_search_button)
        edit_layout.addLayout(credited_layout)
        # Initialize credited info in the temporary dictionary
        temp_edit_data['credited_id'] = transaction_to_edit['credited']
        temp_edit_data['credited_display'] = credited_display.text()

        def handle_credited_search():
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=self.transactions_crud.db_path,
                table_name='accounts', additional_filter='is_active = 1' # Only active accounts
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected and 'id' in selected and 'name' in selected:
                    code = selected.get('code', '?')
                    display_text = f"{selected['name']} ({code})"
                    credited_display.setText(display_text)
                    # Update the temporary dictionary
                    temp_edit_data['credited_id'] = selected['id']
                    temp_edit_data['credited_display'] = display_text
                elif selected:
                     QMessageBox.warning(edit_dialog, "Selection Error", "Invalid account selected (missing ID or name).")

        credited_search_button.clicked.connect(handle_credited_search)

        # --- 4. Amount Field ---
        edit_layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit(transaction_to_edit['amount']) # Edit the stored string amount
        amount_input.setLocale(QLocale.C) # Crucial: Use '.' as decimal separator internally for float conversion
        # Optional: Add a validator for immediate feedback, but final validation happens on save.
        # from PySide6.QtGui import QDoubleValidator
        # validator = QDoubleValidator(0.01, 999999999.99, 2, edit_dialog) # Positive amounts only
        # validator.setNotation(QDoubleValidator.StandardNotation)
        # amount_input.setValidator(validator)
        edit_layout.addWidget(amount_input)

        # --- Dialog Buttons (OK/Cancel) ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Connect OK button to a function that validates the inputs and updates the main list/table
        button_box.accepted.connect(lambda: self._update_template_transaction_data(
            row, description_input.text(), # Get current text from input fields
            temp_edit_data.get('debited_id'), temp_edit_data.get('debited_display'), # Get potentially updated values from temp dict
            temp_edit_data.get('credited_id'), temp_edit_data.get('credited_display'),
            amount_input.text(), # Get current text from amount input
            table, # Pass the main review table to update it
            edit_dialog # Pass the current edit dialog to close it on success
        ))
        button_box.rejected.connect(edit_dialog.reject) # Cancel closes this edit dialog
        edit_layout.addWidget(button_box)

        edit_dialog.exec() # Show the modal edit dialog for this single transaction detail

    def _update_template_transaction_data(self, row, new_description, new_debited_id, new_debited_display,
                                           new_credited_id, new_credited_display, new_amount_str, table, dialog):
        """Validates the edited data and updates the specific item in the temporary list and the review table row."""
        try:
            # --- Validation ---
            if not new_description: # Basic check for description
                 raise ValueError("Description cannot be empty.")

            # Validate amount string can be converted to a positive float
            new_amount_float = float(new_amount_str) # This will raise ValueError if invalid format
            if new_amount_float <= 0:
                raise ValueError("Amount must be a positive number.")

            # Validate Account IDs
            if new_debited_id is None or new_credited_id is None:
                 raise ValueError("Both Debited and Credited accounts must be selected.")
            if new_debited_id == new_credited_id:
                raise ValueError("Debited and Credited accounts cannot be the same.")
            if not new_debited_display or not new_credited_display: # Check if display text is present
                 raise ValueError("Account display information is missing.")


            # --- Update the master list holding the data for final creation ---
            transaction = self.transaction_data_for_creation[row]
            transaction['description'] = new_description
            transaction['debited'] = new_debited_id
            transaction['credited'] = new_credited_id
            transaction['amount'] = new_amount_str # Store the validated string amount back

            # Safely parse display text back to names/codes for storage, handling potential errors
            try: transaction['debit_name'] = new_debited_display.split(" (")[0]
            except IndexError: transaction['debit_name'] = new_debited_display # Fallback if format issue
            try: transaction['debit_code'] = new_debited_display.split(" (")[1][:-1] # Extract code inside parentheses
            except IndexError: transaction['debit_code'] = "?" # Fallback code

            try: transaction['credit_name'] = new_credited_display.split(" (")[0]
            except IndexError: transaction['credit_name'] = new_credited_display
            try: transaction['credit_code'] = new_credited_display.split(" (")[1][:-1]
            except IndexError: transaction['credit_code'] = "?"


            # --- Update the visual table row in the review dialog ---
            table.setItem(row, 0, QTableWidgetItem(new_description))
            table.setItem(row, 1, QTableWidgetItem(new_debited_display))
            table.setItem(row, 2, QTableWidgetItem(new_credited_display))

            # Format amount for display in the table again
            amount_display_item = QTableWidgetItem("{:,.2f}".format(new_amount_float))
            amount_display_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 3, amount_display_item)

            dialog.accept() # Close the single-item edit dialog successfully

        except ValueError as e:
            # Show validation errors to the user in the edit dialog
            QMessageBox.warning(dialog, "Invalid Input", str(e))
        except Exception as e:
             # Catch unexpected errors during update
             QMessageBox.critical(dialog, "Error", f"An unexpected error occurred while updating: {str(e)}")

    def _select_date_and_create_transactions(self, calling_dialog):
        """Opens the date selection dialog, then triggers the final transaction creation process."""
        date_dialog = DateSelectWindow()
        # Optional: Pre-select a date (e.g., today, last used)
        # date_dialog.calendar.setSelectedDate(QDate.currentDate())
        if date_dialog.exec() == QDialog.Accepted:
            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
            calling_dialog.accept() # Close the template review dialog as we are proceeding
            self._create_transactions_with_date(selected_date)
        # else: User cancelled the date selection, the review dialog remains open or closes depending on prior state

    def _create_transactions_with_date(self, selected_date):
        """Creates the actual transactions in the database using the prepared data."""
        # Check if there's anything to create
        if not self.transaction_data_for_creation:
            QMessageBox.information(self.main_window, "No Transactions", "There are no prepared transaction details to create.")
            return

        conn = None # Ensure conn is defined for potential rollback in finally block
        try:
            # Use the transactions_crud connection and cursor for atomicity and helper methods
            conn = self.transactions_crud.conn
            cursor = conn.cursor() # Get cursor from the connection

            cursor.execute("BEGIN") # Start a database transaction

            created_count = 0
            # Iterate through the prepared data stored in the instance list
            for transaction_data in self.transaction_data_for_creation:
                try:
                    # Final validation just before insertion (redundant but safe)
                    amount_float = float(transaction_data['amount'])
                    if amount_float <= 0:
                        raise ValueError(f"Invalid amount ({amount_float}) in final data for '{transaction_data.get('description', 'N/A')}'.")
                    if not transaction_data.get('debited') or not transaction_data.get('credited'):
                         raise ValueError(f"Missing account ID in final data for '{transaction_data.get('description', 'N/A')}'.")

                    # Prepare the final data dictionary for the SQL INSERT statement
                    data_to_insert = {
                        'date': selected_date,
                        'description': transaction_data['description'],
                        'debited': transaction_data['debited'],
                        'credited': transaction_data['credited'],
                        'amount': amount_float,
                        'source_type': 'GENERAL' # <<< Explicitly set source type to 'GENERAL' for template transactions
                    }

                    # Execute the INSERT statement
                    cursor.execute(
                        """INSERT INTO transactions (date, description, debited, credited, amount, source_type)
                           VALUES (:date, :description, :debited, :credited, :amount, :source_type)""",
                        data_to_insert
                    )
                    # last_inserted_id = cursor.lastrowid # Optional: Get the ID if needed

                    # Update account balances using the reliable CRUD helper method
                    self.transactions_crud._update_account_balance(data_to_insert['debited'], data_to_insert['amount'], 'add')
                    self.transactions_crud._update_account_balance(data_to_insert['credited'], data_to_insert['amount'], 'subtract')
                    created_count += 1

                except (ValueError, TypeError, KeyError) as item_error:
                    # If an error occurs processing any single item, raise it to trigger a rollback of the entire batch
                    raise ValueError(f"Error processing transaction item '{transaction_data.get('description', 'N/A')}': {item_error}") from item_error


            # If the loop completes without raising an exception, commit the transaction
            conn.commit()
            QMessageBox.information(self.main_window, "Success", f"{created_count} transaction(s) created successfully from template!")
            self.transaction_data_for_creation = [] # Clear the temporary data list after successful creation

        except (sqlite3.Error, ValueError, TypeError) as e:
            # Catch database errors or value errors from processing/validation
            if conn: # Check if connection was established before trying to rollback
                conn.rollback() # Rollback the entire transaction on any error
            error_msg = f"Failed to create transactions from template: {str(e)}"
            print(f"ERROR: {error_msg}") # Log detailed error for debugging
            QMessageBox.critical(self.main_window, "Transaction Creation Error", error_msg)
        finally:
             # Optional cleanup: Ensure the cursor/connection state is managed appropriately,
             # though usually handled by the context manager or CRUD class destructor if applicable.
             pass

# --- END OF FILE transactions_actions.py ---