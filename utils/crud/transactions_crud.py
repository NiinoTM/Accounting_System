# --- START OF FILE transactions_crud.py ---

# utils/crud/transactions_crud.py

import sqlite3
from PySide6.QtWidgets import (QMessageBox, QComboBox, QDialog, QHBoxLayout,
                              QVBoxLayout, QLineEdit, QPushButton, QLabel,
                              QTableWidget, QTableWidgetItem, QHeaderView) # Keep HeaderView
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator # Moved import to top
from .generic_crud import GenericCRUD
from .search_dialog import AdvancedSearchDialog
from .date_select import DateSelectWindow # Moved import to top
from utils.formatters import format_table_name, normalize_text

class TransactionsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__('transactions')
        # Set row factory for the connection used by this instance
        # This makes cursor.fetchone() and fetchall() return Row objects
        # which allow access by column name (like a dictionary) and index.
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor() # Ensure cursor uses the row factory

    def read(self, main_window, filters=None):
        """Read and display transactions, optionally filtered, with improved layout."""
        base_query = """
            SELECT
                t.id,
                t.date,
                t.description,
                da.name AS debited_account_name,
                ca.name AS credited_account_name,
                t.amount
            FROM transactions t
            JOIN accounts da ON t.debited = da.id
            JOIN accounts ca ON t.credited = ca.id
        """
        where_clauses = []
        params = []

        # --- Filter processing ---
        if filters:
            # Add date range filters if provided
            if filters.get('start_date'):
                where_clauses.append("t.date >= ?")
                params.append(filters['start_date'])
            if filters.get('end_date'):
                where_clauses.append("t.date <= ?")
                params.append(filters['end_date'])

            # Add account ID filter if provided
            if filters.get('account_ids'):
                account_ids = filters['account_ids']
                if account_ids: # Only add clause if list is not empty or None
                    placeholders = ', '.join('?' * len(account_ids))
                    # Check if the transaction involves any of the selected accounts
                    # either as the debited or credited account.
                    where_clauses.append(f"(t.debited IN ({placeholders}) OR t.credited IN ({placeholders}))")
                    # Need to add account_ids twice for the placeholders
                    params.extend(account_ids)
                    params.extend(account_ids)
                # If account_ids is an empty list, we effectively ignore this filter.

            # Get limit, defaulting to 15
            limit = filters.get('limit', 15)
            if not isinstance(limit, int) or limit <= 0:
                limit = 1 # Ensure limit is a positive integer
        else:
            # Default limit if no filters object is passed
            limit = 15

        # Construct WHERE clause if any filters exist
        if where_clauses:
            query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
        else:
            query = base_query

        # Add ORDER BY and LIMIT clauses
        query += " ORDER BY t.date DESC, t.id DESC" # Most recent first
        query += " LIMIT ?"
        params.append(limit)
        # --- End of Filter processing ---

        try:
            # Set a timeout to reduce "database is locked" errors in concurrent scenarios
            self.cursor.execute("PRAGMA busy_timeout = 5000;") # 5 seconds
            # Execute the final query
            self.cursor.execute(query, params)
            records = self.cursor.fetchall() # Fetch all matching records as Row objects

            # --- Display in Table ---
            table = QTableWidget(main_window)
            table.setObjectName("transactionsViewTable") # For potential styling/lookup
            columns = ["ID", "Date", "Description", "Debited Account", "Credited Account", "Amount"]
            table.setRowCount(len(records))
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            table.setEditTriggers(QTableWidget.NoEditTriggers) # Read-only table
            table.setSortingEnabled(False) # Disable during population for performance
            table.verticalHeader().setVisible(False) # Hide default row numbers
            table.setAlternatingRowColors(True) # Improve readability

            # === Key Changes for Layout ===
            table.setWordWrap(True) # Allow text wrapping within cells
            # Allow rows to resize vertically to fit wrapped content
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            # === End of Key Changes ===

            # Populate the table widget row by row
            for row_idx, record_row in enumerate(records):
                 # ID Column (Index 0) - Centered
                 id_item = QTableWidgetItem(str(record_row['id']))
                 id_item.setTextAlignment(Qt.AlignCenter)
                 table.setItem(row_idx, 0, id_item)

                 # Date Column (Index 1)
                 table.setItem(row_idx, 1, QTableWidgetItem(str(record_row['date'])))

                 # Description Column (Index 2) - Handle None
                 table.setItem(row_idx, 2, QTableWidgetItem(str(record_row['description'] or '')))

                 # Debited Account Column (Index 3)
                 table.setItem(row_idx, 3, QTableWidgetItem(str(record_row['debited_account_name'])))

                 # Credited Account Column (Index 4)
                 table.setItem(row_idx, 4, QTableWidgetItem(str(record_row['credited_account_name'])))

                 # Amount Column (Index 5) - Centered and Formatted
                 try:
                     amount_str = "{:,.2f}".format(float(record_row['amount']))
                 except (ValueError, TypeError):
                     amount_str = str(record_row['amount'] or '0.00') # Fallback
                 amount_item = QTableWidgetItem(amount_str)
                 amount_item.setTextAlignment(Qt.AlignCenter)
                 table.setItem(row_idx, 5, amount_item)


            # --- Column Sizing Strategy (Apply AFTER populating) ---
            header = table.horizontalHeader()

            # Start with all columns interactive (user can resize)
            for i in range(table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)

            # Resize columns initially based on content
            table.resizeColumnsToContents()

            # Fine-tune specific columns after initial resize for better defaults
            if table.columnWidth(0) < 60: table.setColumnWidth(0, 60)   # ID Min Width
            if table.columnWidth(1) < 90: table.setColumnWidth(1, 90)   # Date Min Width
            if table.columnWidth(5) < 100: table.setColumnWidth(5, 100) # Amount Min Width
            if table.columnWidth(2) < 200: table.setColumnWidth(2, 200) # Description Min Width
            if table.columnWidth(3) < 150: table.setColumnWidth(3, 150) # Debited Acc Min Width
            if table.columnWidth(4) < 150: table.setColumnWidth(4, 150) # Credited Acc Min Width

            # Optional: Make a specific column stretch (e.g., Description)
            # header.setSectionResizeMode(2, QHeaderView.Stretch)

            # Resize rows to content AFTER setting column widths/modes.
            # This ensures rows expand correctly for wrapped text.
            table.resizeRowsToContents()

            # Re-enable sorting after setup is complete
            table.setSortingEnabled(True)

            # Display the table
            main_window.setCentralWidget(table)
            main_window.setWindowTitle("FinTrack - View Transactions")

        except sqlite3.Error as e:
            QMessageBox.critical(main_window, "Database Error", f"Failed to fetch transactions: {str(e)}")
        except Exception as e: # Catch other potential errors during table setup
             QMessageBox.critical(main_window, "Display Error", f"An error occurred displaying transactions: {str(e)}")


    # --- _create_input_fields method ---
    def _create_input_fields(self, columns, dialog, record=None):
        """Creates input fields for the add/edit dialog, pre-filling if 'record' is provided."""
        inputs = {} # Dictionary to store references to input widgets/data
        layout = dialog.layout() # Get the dialog's layout to add widgets

        # --- Fetch Full Details for Editing ---
        # If editing ('record' is provided), fetch comprehensive data including account names/codes.
        # This avoids needing multiple queries later.
        record_data = None # Will hold the sqlite3.Row object with all necessary data
        record_id_for_fetch = None
        if record: # 'record' should be a sqlite3.Row object from the initial selection/fetch in edit()
            try:
                record_id_for_fetch = record['id']
            except (KeyError, TypeError):
                 print("Warning: 'id' key not found or invalid record object passed to _create_input_fields.")

            if record_id_for_fetch is not None:
                try:
                    # Use a temporary cursor with Row factory for this specific fetch
                    temp_cursor = self.conn.cursor()
                    temp_cursor.row_factory = sqlite3.Row # Ensure dict-like rows
                    temp_cursor.execute("""
                        SELECT
                            t.id, t.date, t.description, t.amount,
                            t.debited as debited_id, t.credited as credited_id,
                            da.name as debit_name, da.code as debit_code,
                            ca.name as credit_name, ca.code as credit_code
                        FROM transactions t
                        LEFT JOIN accounts da ON t.debited = da.id
                        LEFT JOIN accounts ca ON t.credited = ca.id
                        WHERE t.id = ?""", (record_id_for_fetch,))
                    record_data = temp_cursor.fetchone() # Assign the fetched Row object
                except sqlite3.Error as e:
                    print(f"Error fetching full details for edit (ID: {record_id_for_fetch}): {e}")
                    # Fallback: use the potentially incomplete 'record' object if fetch fails
                    record_data = record # Might still be None or lack joined details

        # --- Create Input Widgets for Each Column ---
        for idx, column in enumerate(columns):
            col_lower = column.lower()
            # Skip columns not meant for user input in this dialog
            if col_lower in ['id', 'created_at', 'updated_at', 'status']:
                continue

            # Create a label for the input field
            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            # Determine the pre-fill value using the fetched 'record_data'
            current_value = None
            if record_data:
                 try:
                     # Access Row object using keys (defined in the SELECT query)
                     if col_lower == 'debited': current_value = record_data['debited_id']
                     elif col_lower == 'credited': current_value = record_data['credited_id']
                     else: current_value = record_data[col_lower] # Assumes key matches column name
                 except KeyError:
                     print(f"Warning: Key '{col_lower}' not found in fetched record_data for pre-filling.")
                     current_value = None

            # --- Widget Creation Logic ---

            # Account Selection (Debited/Credited)
            if col_lower in ['debited', 'credited']:
                display_field = QLineEdit() # Read-only field to show selection
                display_field.setReadOnly(True)
                search_button = QPushButton("Search") # Button to open account search

                field_id_value = None # To store the actual selected account ID
                # Pre-fill using the comprehensive 'record_data'
                if record_data:
                    if col_lower == 'debited':
                         # Use square brackets for sqlite3.Row access
                         field_id_value = record_data['debited_id']
                         debit_name = record_data['debit_name']
                         debit_code = record_data['debit_code']
                         if debit_name:
                              display_field.setText(f"{debit_name} ({debit_code or '?'})")
                         elif field_id_value is not None:
                              display_field.setText(f"Account ID: {field_id_value}") # Fallback
                    elif col_lower == 'credited':
                         # Use square brackets for sqlite3.Row access
                         field_id_value = record_data['credited_id']
                         credit_name = record_data['credit_name']
                         credit_code = record_data['credit_code']
                         if credit_name:
                              display_field.setText(f"{credit_name} ({credit_code or '?'})")
                         elif field_id_value is not None:
                              display_field.setText(f"Account ID: {field_id_value}") # Fallback
                # Fallback if 'record_data' fetch failed but 'current_value' (ID) was available
                elif current_value is not None:
                    field_id_value = current_value
                    display_field.setText(f"Account ID: {current_value}")

                # Store references in the 'inputs' dictionary
                inputs[column] = {
                    'display': display_field, # The QLineEdit widget
                    'value': field_id_value,  # The actual ID value
                    'button': search_button   # The QPushButton widget
                }
                # Layout for display field and button
                field_layout = QHBoxLayout()
                field_layout.addWidget(display_field)
                field_layout.addWidget(search_button)
                layout.addLayout(field_layout)

                # --- Search Button Handler (Closure) ---
                # Create a closure to capture loop variables correctly for the lambda/slot
                def create_search_handler(col_name_closure, display_widget_closure, input_dict_closure):
                    def handle_search():
                        # Open the account search dialog
                        search_dialog = AdvancedSearchDialog(
                            field_type='generic',
                            table_name='accounts', # Target accounts table
                            parent=dialog, # Modal to the edit/add dialog
                            db_path=self.db_path,
                            additional_filter='is_active = 1' # Only show active accounts
                        )
                        if search_dialog.exec() == QDialog.Accepted:
                            selected = search_dialog.get_selected_item() # Returns dict or None
                            if selected:
                                # Update display field and stored value
                                display_text = self._format_display_text(selected, col_name_closure)
                                display_widget_closure.setText(display_text)
                                try:
                                    # Store the selected ID (as int)
                                    input_dict_closure[col_name_closure]['value'] = int(selected['id'])
                                except (ValueError, KeyError, TypeError):
                                     QMessageBox.warning(dialog, "Selection Error", "Invalid account selected (missing or invalid ID).")
                                     input_dict_closure[col_name_closure]['value'] = None # Reset on error
                    return handle_search

                search_button.clicked.connect(create_search_handler(column, display_field, inputs))

            # Date Selection
            elif col_lower.endswith('_date') or col_lower == 'date':
                date_input = QLineEdit() # Read-only display for date
                date_input.setPlaceholderText("YYYY-MM-DD")
                date_input.setReadOnly(True)
                date_button = QPushButton("Select Date") # Button for calendar popup

                current_date_val = None # Store date as 'YYYY-MM-DD' string
                if current_value is not None:
                    current_date_val = str(current_value)
                    date_input.setText(current_date_val)

                # Store references
                inputs[column] = {
                    'display': date_input,
                    'value': current_date_val, # Store the 'YYYY-MM-DD' string
                    'button': date_button
                }
                # Layout for date field and button
                field_layout = QHBoxLayout()
                field_layout.addWidget(date_input)
                field_layout.addWidget(date_button)
                layout.addLayout(field_layout)

                # --- Date Button Handler (Closure) ---
                def create_date_handler(col_name_closure, display_widget_closure, input_dict_closure):
                    def handle_date_select():
                        # Open the date selection window
                        date_dialog = DateSelectWindow() # No parent needed based on prior fix
                        # Get current date value from stored input data
                        current_date_str = input_dict_closure[col_name_closure]['value'] # Access directly

                        # Pre-select date in calendar
                        initial_date = QDate.currentDate() # Default to today
                        if current_date_str:
                             parsed_date = QDate.fromString(current_date_str, 'yyyy-MM-dd')
                             if parsed_date.isValid():
                                 initial_date = parsed_date # Use valid stored date

                        date_dialog.calendar.setSelectedDate(initial_date)

                        # Show dialog and process result
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget_closure.setText(selected_date)
                            # Update the stored value
                            if col_name_closure in input_dict_closure:
                                input_dict_closure[col_name_closure]['value'] = selected_date
                            else:
                                print(f"Error: Input dictionary key '{col_name_closure}' not found for date.")
                    return handle_date_select

                date_button.clicked.connect(create_date_handler(column, date_input, inputs))

            # General Text/Number Input (Description, Amount)
            else:
                current_text_val = ""
                if current_value is not None:
                     # Format amount specifically
                     if col_lower == 'amount':
                         try:
                             current_text_val = "{:.2f}".format(float(current_value))
                         except (ValueError, TypeError):
                             current_text_val = str(current_value or '') # Fallback
                     else: # Description or other fields
                         current_text_val = str(current_value or '')

                input_field = QLineEdit(current_text_val)

                # Add validator for amount
                if col_lower == 'amount':
                     validator = QDoubleValidator(-999999999.99, 999999999.99, 2) # Allows negatives initially
                     validator.setNotation(QDoubleValidator.StandardNotation)
                     input_field.setValidator(validator)
                elif col_lower == 'description':
                    input_field.setMaxLength(255) # Example length limit

                # Store the QLineEdit widget directly
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs # Return dictionary of input controls


    # --- _get_search_type method ---
    def _get_search_type(self, column_name):
        """Determines search type (mostly for generic CRUD patterns)."""
        if column_name.lower() in ['debited', 'credited']:
            return 'generic' # Use generic search configured for accounts
        return 'generic' # Default


    # --- _format_display_text method ---
    def _format_display_text(self, selected, column_name):
        """Formats text for display after search selection."""
        if column_name.lower() in ['debited', 'credited']:
             # Use .get for safety as 'selected' is a standard dict from search dialog
             code = selected.get('code', 'N/A') or 'N/A' # Handle None or empty string
             name = selected.get('name', 'N/A')
             return f"{name} ({code})"
        # Default for other searches (e.g., searching transactions directly)
        return selected.get('description', selected.get('name', 'N/A')) # Fallback


    # --- _update_account_balance method ---
    def _update_account_balance(self, account_id, amount, operation):
        """Updates account balance within a transaction."""
        if account_id is None:
             print("Error: Cannot update balance for None account ID.")
             raise ValueError("Cannot update balance for a missing account ID.")
        try:
            amount_float = float(amount)
        except (ValueError, TypeError) as e:
             print(f"Error: Invalid amount '{amount}' for balance update. {e}")
             raise ValueError(f"Invalid amount format for balance update: {amount}")

        if operation == 'add': adjustment = amount_float
        elif operation == 'subtract': adjustment = -amount_float
        else: raise ValueError(f"Invalid balance update operation: {operation}")

        try:
            self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adjustment, account_id))
            print(f"Balance update: Account {account_id}, Operation: {operation}, Amount: {amount_float}, Adjustment: {adjustment}")
        except sqlite3.Error as e:
            print(f"DB Error updating account balance for ID {account_id}: {e}")
            raise # Re-raise to trigger rollback
        except Exception as e:
             print(f"Unexpected error during balance update for ID {account_id}: {e}")
             raise # Re-raise


    # --- _save_record method ---
    def _save_record(self, dialog, inputs, update=False, record_id=None):
        """Saves a transaction record (insert or update) and updates account balances within a DB transaction."""
        columns = [] # List to hold column names for the SQL query
        values = []  # List to hold corresponding values for the SQL query
        debited_account_id = None
        credited_account_id = None
        amount = None
        transaction_date = None # Store date for validation

        # Define which fields are mandatory
        required_fields = ['date', 'debited', 'credited', 'amount']

        # --- 1. Data Extraction and Initial Validation ---
        for column, input_widget in inputs.items():
            col_lower = column.lower()
            value = None

            # Extract value based on input widget type
            if isinstance(input_widget, dict): # For fields with search/date buttons
                value = input_widget['value'] # Get the stored ID or date string (use direct access)
                # Special handling for account IDs: ensure they are integers if not None
                if col_lower in ['debited', 'credited'] and value is not None:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                         QMessageBox.warning(dialog, "Input Error", f"Invalid Account ID for '{format_table_name(column)}'. Selection might be corrupted.")
                         return False # Stop saving process
            elif isinstance(input_widget, QComboBox):
                 idx = input_widget.currentIndex()
                 if idx >= 0: value = input_widget.itemData(idx)
                 else: value = None
            elif isinstance(input_widget, QLineEdit):
                value = input_widget.text().strip()
                # Treat empty string as None for non-required text fields (like description)
                if col_lower not in required_fields and value == "": value = None
            else:
                value = None; print(f"Warning: Unexpected input widget type for column '{column}'")

            # --- 2. Centralized Check for Required Fields ---
            if col_lower in required_fields and (value is None or str(value).strip() == ""):
                 QMessageBox.warning(dialog, "Input Error", f"'{format_table_name(column)}' is required.")
                 return False

            # --- 3. Specific Value Assignment and Validation ---
            if col_lower == 'debited': debited_account_id = value
            elif col_lower == 'credited': credited_account_id = value
            elif col_lower == 'date':
                transaction_date = value
                parsed_date = QDate.fromString(str(value), 'yyyy-MM-dd')
                if not parsed_date.isValid():
                    QMessageBox.warning(dialog, "Input Error", f"Invalid date format for '{format_table_name(column)}'. Use YYYY-MM-DD.")
                    return False
            elif col_lower == 'amount':
                 try:
                     amount = float(value)
                     if amount <= 0:
                         QMessageBox.warning(dialog, "Input Error", "Amount must be a positive number (greater than 0).")
                         return False
                     value = amount # Use the validated float
                 except (ValueError, TypeError):
                     QMessageBox.warning(dialog, "Input Error", f"Invalid amount format: '{value}'. Please enter a valid positive number.")
                     return False
            elif col_lower == 'description' and value is not None:
                 value = normalize_text(value) # Returns None if result is empty/whitespace

            columns.append(column)
            values.append(value)

        # --- 4. Final Logic Checks Before Database Operations ---
        if debited_account_id is None or credited_account_id is None or amount is None or transaction_date is None:
             QMessageBox.warning(dialog, "Input Error", "Date, Debited Account, Credited Account, and Amount are all required.")
             return False
        if debited_account_id == credited_account_id:
             QMessageBox.warning(dialog, "Input Error", "Debited and Credited accounts cannot be the same.")
             return False

        # --- 5. Database Transaction ---
        query = ""
        final_values = []
        try:
            self.cursor.execute("BEGIN")

            original_debited = None
            original_credited = None
            original_amount = None

            # Get actual DB column names to check for timestamp columns existence
            db_column_names = self.get_columns() # Base class method returning list of names
            db_cols_lower_set = {name.lower() for name in db_column_names} # Set for efficient lookup

            # --- UPDATE Logic ---
            if update and record_id is not None:
                # Fetch original data for balance reversal
                self.cursor.execute("SELECT debited, credited, amount FROM transactions WHERE id = ?", (record_id,))
                original_data = self.cursor.fetchone()
                if not original_data:
                     self.conn.rollback(); raise ValueError(f"Update Error: Original transaction with ID {record_id} not found.")
                original_debited = original_data['debited']
                original_credited = original_data['credited']
                original_amount = original_data['amount']

                # Reverse original balance impact
                if original_debited is not None and original_amount is not None:
                    self._update_account_balance(original_debited, original_amount, 'subtract')
                if original_credited is not None and original_amount is not None:
                    self._update_account_balance(original_credited, original_amount, 'add')

                # Prepare UPDATE query
                update_columns_clause = []
                update_values = []
                col_val_dict = dict(zip(columns, values))

                for col in columns:
                     col_lower = col.lower()
                     # Only include columns that exist in DB and are not handled automatically
                     if col_lower in db_cols_lower_set and col_lower not in ['id', 'created_at', 'updated_at']:
                         update_columns_clause.append(f"{col} = ?")
                         update_values.append(col_val_dict[col])

                # Add 'updated_at' if column exists
                if 'updated_at' in db_cols_lower_set:
                     update_columns_clause.append("updated_at = CURRENT_TIMESTAMP")

                set_clause = ', '.join(update_columns_clause)
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
                final_values = update_values + [record_id]

            # --- INSERT Logic ---
            else:
                insert_columns = []
                insert_values = []
                col_val_dict = dict(zip(columns, values))

                for col in columns:
                    col_lower = col.lower()
                    # Only include columns that exist in DB and are not the PK (usually)
                    if col_lower in db_cols_lower_set and col_lower != 'id':
                        insert_columns.append(col)
                        insert_values.append(col_val_dict[col])

                # Add timestamps if columns exist
                current_time = sqlite3.Timestamp.now()
                if 'created_at' in db_cols_lower_set and 'created_at' not in [c.lower() for c in insert_columns]:
                     insert_columns.append('created_at')
                     insert_values.append(current_time)
                if 'updated_at' in db_cols_lower_set and 'updated_at' not in [c.lower() for c in insert_columns]:
                     insert_columns.append('updated_at')
                     insert_values.append(current_time)

                placeholders = ', '.join(['?'] * len(insert_columns))
                query = f"INSERT INTO {self.table_name} ({', '.join(insert_columns)}) VALUES ({placeholders})"
                final_values = insert_values

            # --- 6. Execute SQL and Update Balances ---
            print(f"Executing Query: {query}")
            print(f"With Values: {final_values}")
            self.cursor.execute(query, final_values)

            # Apply the NEW transaction's balance impact
            if debited_account_id is not None:
                 self._update_account_balance(debited_account_id, amount, 'add')
            if credited_account_id is not None:
                 self._update_account_balance(credited_account_id, amount, 'subtract')

            # --- 7. Commit Transaction ---
            self.conn.commit()
            QMessageBox.information(dialog, "Success", f"Transaction {'updated' if update else 'created'} successfully!")
            dialog.accept()
            return True

        except (sqlite3.Error, ValueError, TypeError) as e:
            # --- 8. Rollback on Error ---
            self.conn.rollback()
            error_message = f"Failed to save transaction: {str(e)}"
            print(f"ERROR during save: {error_message}")
            print(f"Failed Query (approx): {query}")
            print(f"Failed Values (approx): {final_values}")
            QMessageBox.critical(dialog, "Database Error", error_message)
            return False


    # --- edit method ---
    def edit(self, main_window):
        """Opens a search dialog to select a transaction, then opens the edit dialog."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name # Search transactions
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item or 'id' not in selected_item:
                QMessageBox.warning(main_window, "Selection Error", "No valid transaction selected or ID missing.")
                return
            try:
                record_id = int(selected_item['id'])
            except (ValueError, TypeError):
                 QMessageBox.warning(main_window, "Selection Error", "Invalid transaction ID format.")
                 return

            try:
                # Fetch the full record using a temp cursor with row factory
                # Needed for pre-filling the edit dialog correctly
                temp_cursor = self.conn.cursor()
                temp_cursor.row_factory = sqlite3.Row
                temp_cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (record_id,))
                record_row = temp_cursor.fetchone() # Get the sqlite3.Row object

                if not record_row:
                    QMessageBox.warning(main_window, "Error", f"Record with ID {record_id} not found!")
                    return

                # Get column names to structure the dialog
                columns = self.get_columns()

                # Create and configure the edit dialog
                dialog = QDialog(main_window)
                dialog.setWindowTitle(f"Edit Transaction (ID: {record_id})")
                dialog.setMinimumWidth(450)
                layout = QVBoxLayout(dialog) # Set layout directly

                # Create input fields, passing the fetched record_row for pre-filling
                inputs = self._create_input_fields(columns, dialog, record_row)

                # Add Save/Cancel buttons
                button_layout = QHBoxLayout()
                save_button = QPushButton("Save Changes")
                save_button.clicked.connect(lambda: self._save_record(dialog, inputs, update=True, record_id=record_id))
                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(dialog.reject)
                button_layout.addStretch()
                button_layout.addWidget(save_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

                dialog.exec() # Show the dialog modally

            except sqlite3.Error as e:
                 QMessageBox.critical(main_window, "Database Error", f"Error preparing edit dialog: {str(e)}")
            except ValueError as e: # Catch column/conversion errors
                 QMessageBox.critical(main_window, "Configuration Error", str(e))
            except Exception as e: # Catch unexpected errors like the AttributeError
                 QMessageBox.critical(main_window, "Error", f"An unexpected error occurred setting up the edit dialog: {str(e)}")


    # --- delete method ---
    def delete(self, main_window):
        """Opens search, confirms, deletes transaction, and reverses balance impacts."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name # Search transactions
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item or 'id' not in selected_item:
                QMessageBox.warning(main_window, "Selection Error", "No valid transaction selected or ID missing.")
                return
            try:
                record_id = int(selected_item['id'])
            except (ValueError, TypeError):
                 QMessageBox.warning(main_window, "Selection Error", "Invalid transaction ID format.")
                 return

            # Fetch details for confirmation message
            description_info = ""
            try:
                 self.cursor.execute("SELECT description, date, amount FROM transactions WHERE id = ?", (record_id,))
                 desc_data = self.cursor.fetchone() # Row object
                 if desc_data:
                      desc_text = desc_data['description'] or 'N/A'
                      if len(desc_text) > 80: desc_text = desc_text[:77] + "..."
                      amount_formatted = "{:,.2f}".format(float(desc_data['amount'])) if desc_data['amount'] is not None else 'N/A'
                      description_info = f"\nDescription: {desc_text}\nDate: {desc_data['date']}\nAmount: {amount_formatted}"
            except (sqlite3.Error, ValueError, TypeError) as e:
                 print(f"Error fetching/formatting details for delete confirmation (ID: {record_id}): {e}")

            # Confirmation dialog
            confirm_msg = (f"Are you sure you want to delete transaction ID {record_id}?{description_info}\n\n"
                           "WARNING: This will PERMANENTLY delete the record and reverse its impact on account balances.")
            confirm = QMessageBox.question(main_window, "Confirm Delete", confirm_msg,
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           QMessageBox.StandardButton.No)

            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    # --- Begin Transaction for Delete and Balance Reversal ---
                    self.cursor.execute("BEGIN")

                    # Fetch original accounts/amount within the transaction
                    self.cursor.execute("SELECT debited, credited, amount FROM transactions WHERE id = ?", (record_id,))
                    original_data = self.cursor.fetchone()
                    if not original_data:
                        self.conn.rollback()
                        QMessageBox.warning(main_window, "Not Found", f"Transaction ID {record_id} no longer exists.")
                        return

                    original_debited = original_data['debited']
                    original_credited = original_data['credited']
                    original_amount = original_data['amount']

                    # Reverse balance impact BEFORE deleting
                    if original_debited is not None and original_amount is not None:
                        self._update_account_balance(original_debited, original_amount, 'subtract') # Reverse the add
                    if original_credited is not None and original_amount is not None:
                        self._update_account_balance(original_credited, original_amount, 'add') # Reverse the subtract

                    # Delete the transaction record
                    delete_count = self.cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,)).rowcount

                    # --- Commit or Rollback ---
                    if delete_count == 0:
                         self.conn.rollback()
                         QMessageBox.warning(main_window, "Deletion Failed", f"Transaction ID {record_id} could not be deleted. Balances reverted.")
                    else:
                        self.conn.commit()
                        QMessageBox.information(main_window, "Success", f"Transaction ID {record_id} deleted and balances updated.")
                        # Recommend refresh if table is visible
                        current_widget = main_window.centralWidget()
                        if isinstance(current_widget, QTableWidget) and current_widget.objectName() == "transactionsViewTable":
                             QMessageBox.information(main_window, "Refresh Recommended", "Transaction deleted. Please 'View Transactions' again or use the filter/refresh button.")

                except (sqlite3.Error, ValueError, TypeError) as e:
                    self.conn.rollback() # Rollback on any error
                    error_msg = f"Failed to delete transaction ID {record_id}: {str(e)}"
                    print(f"ERROR during delete: {error_msg}")
                    QMessageBox.critical(main_window, "Database Error", error_msg)

# --- END OF FILE transactions_crud.py ---