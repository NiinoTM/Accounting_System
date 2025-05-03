# --- START OF FILE transactions_crud.py ---

# utils/crud/transactions_crud.py

import sqlite3
from PySide6.QtWidgets import (QMessageBox, QComboBox, QDialog, QHBoxLayout,
                              QVBoxLayout, QLineEdit, QPushButton, QLabel,
                              QTableWidget, QTableWidgetItem, QHeaderView) # Keep HeaderView
from PySide6.QtCore import Qt, QDate, QLocale
from .generic_crud import GenericCRUD
from .search_dialog import AdvancedSearchDialog
from .date_select import DateSelectWindow
from utils.formatters import format_table_name, normalize_text

class TransactionsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__('transactions')
        # Set row factory for the connection used by this instance
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor() # Ensure cursor uses the row factory

    def read(self, main_window, filters=None):
        """Read and display transactions, including source type."""
        base_query = """
            SELECT
                t.id,
                t.date,
                t.description,
                da.name AS debited_account_name,
                ca.name AS credited_account_name,
                t.amount,
                t.source_type  -- Fetch source_type
            FROM transactions t
            JOIN accounts da ON t.debited = da.id
            JOIN accounts ca ON t.credited = ca.id
        """
        where_clauses = []
        params = []

        # --- Filter processing ---
        if filters:
            if filters.get('start_date'):
                where_clauses.append("t.date >= ?")
                params.append(filters['start_date'])
            if filters.get('end_date'):
                where_clauses.append("t.date <= ?")
                params.append(filters['end_date'])
            if filters.get('account_ids'):
                account_ids = filters['account_ids']
                if account_ids:
                    placeholders = ', '.join('?' * len(account_ids))
                    where_clauses.append(f"(t.debited IN ({placeholders}) OR t.credited IN ({placeholders}))")
                    params.extend(account_ids)
                    params.extend(account_ids)
            limit = filters.get('limit', 15)
            if not isinstance(limit, int) or limit <= 0: limit = 15
        else:
            limit = 15

        if where_clauses:
            query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
        else:
            query = base_query

        query += " ORDER BY t.date DESC, t.id DESC"
        query += " LIMIT ?"
        params.append(limit)
        # --- End of Filter processing ---

        try:
            self.cursor.execute("PRAGMA busy_timeout = 5000;")
            self.cursor.execute(query, params)
            records = self.cursor.fetchall()

            # --- Display in Table ---
            table = QTableWidget(main_window)
            table.setObjectName("transactionsViewTable")
            # Add "Source Type" column
            columns = ["ID", "Date", "Description", "Debited Account", "Credited Account", "Amount", "Source Type"]
            table.setRowCount(len(records))
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSortingEnabled(False)
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setWordWrap(True)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            # Populate the table widget
            for row_idx, record_row in enumerate(records):
                 id_item = QTableWidgetItem(str(record_row['id']))
                 id_item.setTextAlignment(Qt.AlignCenter)
                 table.setItem(row_idx, 0, id_item)
                 table.setItem(row_idx, 1, QTableWidgetItem(str(record_row['date'])))
                 table.setItem(row_idx, 2, QTableWidgetItem(str(record_row['description'] or '')))
                 table.setItem(row_idx, 3, QTableWidgetItem(str(record_row['debited_account_name'])))
                 table.setItem(row_idx, 4, QTableWidgetItem(str(record_row['credited_account_name'])))
                 try:
                     amount_str = "{:,.2f}".format(float(record_row['amount']))
                 except (ValueError, TypeError):
                     amount_str = str(record_row['amount'] or '0.00')
                 amount_item = QTableWidgetItem(amount_str)
                 amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Align amount right
                 table.setItem(row_idx, 5, amount_item)
                 # Populate the new Source Type column
                 source_type_item = QTableWidgetItem(str(record_row['source_type']))
                 source_type_item.setTextAlignment(Qt.AlignCenter)
                 table.setItem(row_idx, 6, source_type_item)


            # --- Column Sizing Strategy ---
            header = table.horizontalHeader()
            # Make columns interactive initially for user resizing
            for i in range(table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
            # Resize based on content first
            table.resizeColumnsToContents()
            # Set minimum widths for better readability
            if table.columnWidth(0) < 60: table.setColumnWidth(0, 60)   # ID
            if table.columnWidth(1) < 90: table.setColumnWidth(1, 90)   # Date
            if table.columnWidth(5) < 100: table.setColumnWidth(5, 100) # Amount
            if table.columnWidth(6) < 100: table.setColumnWidth(6, 100) # Source Type
            # Allow Description, Debited, Credited to be wider
            if table.columnWidth(2) < 200: table.setColumnWidth(2, 200) # Description
            if table.columnWidth(3) < 150: table.setColumnWidth(3, 150) # Debited
            if table.columnWidth(4) < 150: table.setColumnWidth(4, 150) # Credited
            # Optional: Set Description to stretch if desired after initial sizing
            # header.setSectionResizeMode(2, QHeaderView.Stretch)

            table.resizeRowsToContents()
            table.setSortingEnabled(True) # Allow sorting after population
            main_window.setCentralWidget(table)
            main_window.setWindowTitle("FinTrack - View Transactions")

        except sqlite3.Error as e:
            QMessageBox.critical(main_window, "Database Error", f"Failed to fetch transactions: {str(e)}")
        except Exception as e:
             QMessageBox.critical(main_window, "Display Error", f"An error occurred displaying transactions: {str(e)}")


    # --- _create_input_fields method ---
    def _create_input_fields(self, columns, dialog, record=None):
        """Creates input fields, ignoring source_type."""
        inputs = {}
        layout = dialog.layout()

        record_data = None
        if record:
             record_id_for_fetch = None
             try: record_id_for_fetch = record['id']
             except (KeyError, TypeError): print("Warning: 'id' key not found or invalid record object passed to _create_input_fields.")
             if record_id_for_fetch is not None:
                 try:
                     temp_cursor = self.conn.cursor()
                     temp_cursor.row_factory = sqlite3.Row
                     temp_cursor.execute("""
                         SELECT
                             t.id, t.date, t.description, t.amount,
                             t.debited as debited_id, t.credited as credited_id,
                             da.name as debit_name, da.code as debit_code,
                             ca.name as credit_name, ca.code as credit_code
                             -- No need to fetch source_type here, it's handled separately
                         FROM transactions t
                         LEFT JOIN accounts da ON t.debited = da.id
                         LEFT JOIN accounts ca ON t.credited = ca.id
                         WHERE t.id = ?""", (record_id_for_fetch,))
                     record_data = temp_cursor.fetchone()
                 except sqlite3.Error as e:
                     print(f"Error fetching full details for edit (ID: {record_id_for_fetch}): {e}")
                     record_data = record # Fallback

        for idx, column in enumerate(columns):
            col_lower = column.lower()
            # Skip internal, timestamp, and the source_type columns
            if col_lower in ['id', 'created_at', 'updated_at', 'status', 'source_type']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            current_value = None
            if record_data:
                 try:
                     if col_lower == 'debited': current_value = record_data['debited_id']
                     elif col_lower == 'credited': current_value = record_data['credited_id']
                     else: current_value = record_data[col_lower]
                 except KeyError:
                     print(f"Warning: Key '{col_lower}' not found in fetched record_data for pre-filling.")
                     current_value = None

            # --- Account Selection ---
            if col_lower in ['debited', 'credited']:
                display_field = QLineEdit()
                display_field.setReadOnly(True)
                search_button = QPushButton("Search")
                field_id_value = None
                if record_data:
                    if col_lower == 'debited':
                         field_id_value = record_data.get('debited_id')
                         debit_name = record_data.get('debit_name')
                         debit_code = record_data.get('debit_code')
                         if debit_name: display_field.setText(f"{debit_name} ({debit_code or '?'})")
                         elif field_id_value is not None: display_field.setText(f"Account ID: {field_id_value}")
                    elif col_lower == 'credited':
                         field_id_value = record_data.get('credited_id')
                         credit_name = record_data.get('credit_name')
                         credit_code = record_data.get('credit_code')
                         if credit_name: display_field.setText(f"{credit_name} ({credit_code or '?'})")
                         elif field_id_value is not None: display_field.setText(f"Account ID: {field_id_value}")
                elif current_value is not None:
                    field_id_value = current_value
                    display_field.setText(f"Account ID: {current_value}")
                inputs[column] = {'display': display_field, 'value': field_id_value, 'button': search_button}
                field_layout = QHBoxLayout()
                field_layout.addWidget(display_field)
                field_layout.addWidget(search_button)
                layout.addLayout(field_layout)
                def create_search_handler(col_name_closure, display_widget_closure, input_dict_closure):
                    def handle_search():
                        search_dialog = AdvancedSearchDialog(field_type='generic', table_name='accounts', parent=dialog, db_path=self.db_path, additional_filter='is_active = 1')
                        if search_dialog.exec() == QDialog.Accepted:
                            selected = search_dialog.get_selected_item()
                            if selected:
                                display_text = self._format_display_text(selected, col_name_closure)
                                display_widget_closure.setText(display_text)
                                try: input_dict_closure[col_name_closure]['value'] = int(selected['id'])
                                except (ValueError, KeyError, TypeError):
                                     QMessageBox.warning(dialog, "Selection Error", "Invalid account selected (missing or invalid ID).")
                                     input_dict_closure[col_name_closure]['value'] = None
                    return handle_search
                search_button.clicked.connect(create_search_handler(column, display_field, inputs))

            # --- Date Selection ---
            elif col_lower.endswith('_date') or col_lower == 'date':
                date_input = QLineEdit()
                date_input.setPlaceholderText("YYYY-MM-DD")
                date_input.setReadOnly(True)
                date_button = QPushButton("Select Date")
                current_date_val = None
                if current_value is not None:
                    current_date_val = str(current_value)
                    date_input.setText(current_date_val)
                inputs[column] = {'display': date_input, 'value': current_date_val, 'button': date_button}
                field_layout = QHBoxLayout()
                field_layout.addWidget(date_input)
                field_layout.addWidget(date_button)
                layout.addLayout(field_layout)
                def create_date_handler(col_name_closure, display_widget_closure, input_dict_closure):
                    def handle_date_select():
                        date_dialog = DateSelectWindow()
                        current_date_str = input_dict_closure[col_name_closure].get('value') if isinstance(input_dict_closure.get(col_name_closure), dict) else None
                        initial_date = QDate.currentDate()
                        if current_date_str:
                             parsed_date = QDate.fromString(current_date_str, 'yyyy-MM-dd')
                             if parsed_date.isValid(): initial_date = parsed_date
                        date_dialog.calendar.setSelectedDate(initial_date)
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget_closure.setText(selected_date)
                            if col_name_closure in input_dict_closure and isinstance(input_dict_closure[col_name_closure], dict):
                                input_dict_closure[col_name_closure]['value'] = selected_date
                            else: print(f"Error: Input dictionary structure invalid for date '{col_name_closure}'.")
                    return handle_date_select
                date_button.clicked.connect(create_date_handler(column, date_input, inputs))

            # --- General Text/Number Input (Description, Amount) ---
            else:
                current_text_val = ""
                if current_value is not None:
                    current_text_val = str(current_value or '')
                input_field = QLineEdit(current_text_val)
                if col_lower == 'amount':
                    input_field.setLocale(QLocale.C) # Ensure '.' decimal separator
                elif col_lower == 'description':
                    input_field.setMaxLength(255)
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs


    # --- _get_search_type method ---
    # (Remains the same)
    def _get_search_type(self, column_name):
        if column_name.lower() in ['debited', 'credited']:
            return 'generic'
        return 'generic'


    # --- _format_display_text method ---
    # (Remains the same)
    def _format_display_text(self, selected, column_name):
        if column_name.lower() in ['debited', 'credited']:
             code = selected.get('code', 'N/A') or 'N/A'
             name = selected.get('name', 'N/A')
             return f"{name} ({code})"
        return selected.get('description', selected.get('name', 'N/A'))


    # --- _update_account_balance method ---
    # (Remains the same)
    def _update_account_balance(self, account_id, amount, operation):
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
            raise
        except Exception as e:
             print(f"Unexpected error during balance update for ID {account_id}: {e}")
             raise


    # --- _save_record method ---
    def _save_record(self, dialog, inputs, update=False, record_id=None):
        """Saves a transaction, setting source_type='GENERAL' for new records."""
        columns = []
        values = []
        debited_account_id = None
        credited_account_id = None
        amount = None
        transaction_date = None

        required_fields = ['date', 'debited', 'credited', 'amount']

        # --- 1. Data Extraction and Initial Validation ---
        for column, input_widget in inputs.items():
            col_lower = column.lower()
            value = None
            if isinstance(input_widget, dict):
                value = input_widget['value']
                if col_lower in ['debited', 'credited'] and value is not None:
                    try: value = int(value)
                    except (ValueError, TypeError):
                         QMessageBox.warning(dialog, "Input Error", f"Invalid Account ID for '{format_table_name(column)}'. Selection might be corrupted.")
                         return False
            elif isinstance(input_widget, QComboBox):
                 idx = input_widget.currentIndex()
                 if idx >= 0: value = input_widget.itemData(idx)
                 else: value = None
            elif isinstance(input_widget, QLineEdit):
                value = input_widget.text().strip()
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
                     value = amount
                 except (ValueError, TypeError):
                     QMessageBox.warning(dialog, "Input Error", f"Invalid amount format: '{value}'. Please enter a valid positive number (using '.' as decimal separator).")
                     return False
            elif col_lower == 'description' and value is not None:
                 value = normalize_text(value)

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

            db_column_names = self.get_columns()
            db_cols_lower_set = {name.lower() for name in db_column_names}

            # --- UPDATE Logic (Source Type is NOT updated) ---
            if update and record_id is not None:
                # Fetch original details for balance reversal
                # The check preventing edit already happened in the 'edit' method
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

                # Prepare UPDATE statement, excluding source_type
                update_columns_clause = []
                update_values = []
                col_val_dict = dict(zip(columns, values))

                for col in columns:
                     col_lower = col.lower()
                     # Only update columns that exist in the table and are not internal/timestamp/source_type
                     if col_lower in db_cols_lower_set and col_lower not in ['id', 'created_at', 'updated_at', 'source_type']:
                         update_columns_clause.append(f"{col} = ?")
                         update_values.append(col_val_dict[col])

                if 'updated_at' in db_cols_lower_set:
                     update_columns_clause.append("updated_at = CURRENT_TIMESTAMP")

                set_clause = ', '.join(update_columns_clause)
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
                final_values = update_values + [record_id]

            # --- INSERT Logic (Set source_type to 'GENERAL') ---
            else:
                insert_columns = []
                insert_values = []
                col_val_dict = dict(zip(columns, values))

                for col in columns:
                    col_lower = col.lower()
                    # Only include columns that exist in the table (excluding id)
                    if col_lower in db_cols_lower_set and col_lower != 'id':
                        insert_columns.append(col)
                        insert_values.append(col_val_dict[col])

                # **** Add source_type explicitly for INSERT ****
                if 'source_type' in db_cols_lower_set and 'source_type' not in [c.lower() for c in insert_columns]:
                    insert_columns.append('source_type')
                    insert_values.append('GENERAL') # Default source for manual/template adds

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

            # --- 6. Execute SQL and Update Balances (new impact) ---
            print(f"Executing Query: {query}") # Debugging
            print(f"With Values: {final_values}") # Debugging
            self.cursor.execute(query, final_values)

            # Apply new balance impact
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
        """Opens search, checks source_type, then opens edit dialog ONLY if source is 'GENERAL'."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name # Search transactions table
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
                # Fetch the full record, *including* source_type for the check
                temp_cursor = self.conn.cursor()
                temp_cursor.row_factory = sqlite3.Row
                # Select all columns plus source_type explicitly if needed, though '*' should include it
                temp_cursor.execute(f"SELECT *, source_type FROM {self.table_name} WHERE id = ?", (record_id,))
                record_row = temp_cursor.fetchone()

                if not record_row:
                    QMessageBox.warning(main_window, "Error", f"Record with ID {record_id} not found!")
                    return

                # **** CHECK SOURCE TYPE BEFORE PROCEEDING ****
                source_type = record_row['source_type']
                if source_type != 'GENERAL':
                    QMessageBox.warning(
                        main_window,
                        "Edit Restricted",
                        f"This transaction originated from the '{source_type}' module. "
                        f"It cannot be edited from the general transaction menu.\n\n"
                        f"Please use the specific module (AR/AP or Fixed Assets) to modify it."
                    )
                    return # Stop the edit process here

                # --- Proceed with edit dialog only if source_type is 'GENERAL' ---
                columns = self.get_columns() # Get column names for dialog creation

                dialog = QDialog(main_window)
                dialog.setWindowTitle(f"Edit General Transaction (ID: {record_id})")
                dialog.setMinimumWidth(450)
                layout = QVBoxLayout(dialog)

                # Create input fields, pre-filling with data from record_row
                inputs = self._create_input_fields(columns, dialog, record_row)

                button_layout = QHBoxLayout()
                save_button = QPushButton("Save Changes")
                # Connect save to _save_record, passing update=True and record_id
                save_button.clicked.connect(lambda: self._save_record(dialog, inputs, update=True, record_id=record_id))
                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(dialog.reject)
                button_layout.addStretch()
                button_layout.addWidget(save_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)

                dialog.exec() # Show the edit dialog

            except sqlite3.Error as e:
                 QMessageBox.critical(main_window, "Database Error", f"Error preparing edit dialog: {str(e)}")
            except Exception as e:
                 QMessageBox.critical(main_window, "Error", f"An unexpected error occurred setting up the edit dialog: {str(e)}")


    # --- delete method ---
    def delete(self, main_window):
        """Opens search, confirms, checks source_type, then deletes transaction ONLY if source is 'GENERAL'."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name # Search transactions table
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

            description_info = ""
            source_type = None # Variable to store the source type
            try:
                 # Fetch details for confirmation AND source_type for the check
                 self.cursor.row_factory = sqlite3.Row # Ensure row factory is set for this cursor too
                 self.cursor.execute("SELECT description, date, amount, source_type FROM transactions WHERE id = ?", (record_id,))
                 trans_data = self.cursor.fetchone()
                 if trans_data:
                      source_type = trans_data['source_type'] # <<< Get the source type
                      desc_text = trans_data['description'] or 'N/A'
                      if len(desc_text) > 80: desc_text = desc_text[:77] + "..."
                      amount_formatted = "{:,.2f}".format(float(trans_data['amount'])) if trans_data['amount'] is not None else 'N/A'
                      # Include source type in the confirmation message details
                      description_info = (f"\nDescription: {desc_text}\nDate: {trans_data['date']}\nAmount: {amount_formatted}"
                                          f"\nSource: {source_type}")
                 else:
                     QMessageBox.warning(main_window, "Not Found", f"Transaction ID {record_id} not found for deletion.")
                     return # Stop if transaction doesn't exist

            except (sqlite3.Error, ValueError, TypeError) as e:
                 print(f"Error fetching details/source_type for delete confirmation (ID: {record_id}): {e}")
                 QMessageBox.critical(main_window, "Error", "Could not fetch transaction details for deletion.")
                 return

            # **** CHECK SOURCE TYPE BEFORE CONFIRMATION DIALOG ****
            if source_type != 'GENERAL':
                QMessageBox.warning(
                    main_window,
                    "Deletion Restricted",
                    f"This transaction originated from the '{source_type}' module. "
                    f"It cannot be deleted from the general transaction menu.\n\n"
                    f"Please use the specific module (AR/AP or Fixed Assets) to delete it."
                )
                return # Stop the delete process here

            # --- Proceed with confirmation only if source_type is 'GENERAL' ---
            confirm_msg = (f"Are you sure you want to delete transaction ID {record_id}?{description_info}\n\n"
                           "WARNING: This will PERMANENTLY delete the record and reverse its impact on account balances.")
            confirm = QMessageBox.question(main_window, "Confirm Delete", confirm_msg,
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           QMessageBox.StandardButton.No)

            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    # Start DB transaction for atomicity
                    self.cursor.execute("BEGIN")

                    # Re-fetch balance details right before deletion (source_type already confirmed as GENERAL)
                    self.cursor.execute("SELECT debited, credited, amount FROM transactions WHERE id = ?", (record_id,))
                    original_data = self.cursor.fetchone()
                    if not original_data: # Check if it was deleted between confirmation and now
                        self.conn.rollback()
                        QMessageBox.warning(main_window, "Not Found", f"Transaction ID {record_id} no longer exists.")
                        return

                    original_debited = original_data['debited']
                    original_credited = original_data['credited']
                    original_amount = original_data['amount']

                    # Reverse balance impacts
                    if original_debited is not None and original_amount is not None:
                        self._update_account_balance(original_debited, original_amount, 'subtract')
                    if original_credited is not None and original_amount is not None:
                        self._update_account_balance(original_credited, original_amount, 'add')

                    # Delete the transaction record
                    delete_count = self.cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,)).rowcount

                    if delete_count == 0: # Should not happen if fetch worked, but good check
                         self.conn.rollback()
                         QMessageBox.warning(main_window, "Deletion Failed", f"Transaction ID {record_id} could not be deleted (already gone?). Balances reverted.")
                    else:
                        # Commit the changes (deletion and balance updates)
                        self.conn.commit()
                        QMessageBox.information(main_window, "Success", f"Transaction ID {record_id} deleted and balances updated.")
                        # Refresh logic (optional but recommended)
                        current_widget = main_window.centralWidget()
                        if isinstance(current_widget, QTableWidget) and current_widget.objectName() == "transactionsViewTable":
                             # Suggest refresh instead of trying to auto-refresh complex filtered views
                             QMessageBox.information(main_window, "Refresh Recommended", "Transaction deleted. Please 'View Transactions' again or use the filter/refresh button if available.")

                except (sqlite3.Error, ValueError, TypeError) as e:
                    # Rollback on any error during the delete process
                    self.conn.rollback()
                    error_msg = f"Failed to delete transaction ID {record_id}: {str(e)}"
                    print(f"ERROR during delete: {error_msg}")
                    QMessageBox.critical(main_window, "Database Error", error_msg)

# --- END OF FILE transactions_crud.py ---