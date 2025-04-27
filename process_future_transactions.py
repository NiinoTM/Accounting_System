# process_future_transactions.py

import sqlite3
from datetime import date, timedelta # Need timedelta for postpone validation
from PySide6.QtWidgets import (QMessageBox, QDialogButtonBox, QTableWidget,
                               QTableWidgetItem, QDialog, QVBoxLayout, QPushButton,
                               QLabel, QLineEdit, QHBoxLayout, QHeaderView)
from PySide6.QtCore import Qt, QDate # Import QDate
from create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog # Ensure this import is correct
from utils.formatters import format_table_name          # Ensure this import is correct
from utils.crud.date_select import DateSelectWindow     # Ensure this import is correct

def process_future_transactions(parent=None):
    """
    Fetches future transactions due today or earlier, allows user management
    (edit/delete/postpone) via a dialog, and then processes the remaining
    transactions by moving them to the main transactions table and updating balances.
    """
    db_manager = DatabaseManager()
    processed_transactions = [] # List to store details of successfully processed transactions
    transactions_to_process = [] # List to hold transactions fetched initially and managed by the dialog

    try:
        with db_manager as db:
            today = date.today().strftime('%Y-%m-%d')
            # Ensure row factory is set to get dict-like rows
            db.conn.row_factory = sqlite3.Row
            db.cursor = db.conn.cursor()

            db.cursor.execute("SELECT * FROM future_transactions WHERE date <= ?", (today,))
            future_transactions = db.cursor.fetchall()

            if not future_transactions:
                print("No future transactions to process.")
                return

            # --- Store transactions for potential editing ---
            # Convert Row objects to standard dictionaries for easier modification
            transactions_to_process = [dict(row) for row in future_transactions]
            print(f"Fetched {len(transactions_to_process)} potential future transactions.")

            # --- Show Edit/Manage Dialog ---
            if parent and transactions_to_process:
                 # Pass the list *by reference* so the dialog can modify it
                 if not manage_future_transactions(parent, transactions_to_process, db):
                    print("Future transaction processing cancelled by user.")
                    return  # User canceled the management dialog

            # --- Proceed with processing items *remaining* in the list ---
            # This list might now be shorter due to deletions/postponements
            if not transactions_to_process:
                print("No transactions remaining after management.")
                return

            print(f"Processing {len(transactions_to_process)} remaining future transactions...")
            for transaction_dict in transactions_to_process:
                # Optional Safety Check: Verify the transaction still exists in the DB before processing.
                # This prevents errors if it was deleted by another process between fetch and process.
                db.cursor.execute("SELECT 1 FROM future_transactions WHERE id = ?", (transaction_dict['id'],))
                if db.cursor.fetchone() is None:
                    print(f"Skipping transaction ID {transaction_dict['id']} as it no longer exists in future_transactions table.")
                    continue

                # --- Insert into main transactions table ---
                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (transaction_dict['date'], transaction_dict['description'], transaction_dict['debited'],
                     transaction_dict['credited'], transaction_dict['amount'],
                     transaction_dict['created_at'], transaction_dict['updated_at']) # Use original timestamps
                )
                print(f"Inserted transaction ID {transaction_dict['id']} (originally future) into main transactions table.")

                # --- Update Account Balances ---
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (transaction_dict['amount'], transaction_dict['debited'])
                )
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (transaction_dict['amount'], transaction_dict['credited'])
                )
                print(f"Updated account balances for transaction ID {transaction_dict['id']}.")

                # --- Delete from future_transactions ---
                db.cursor.execute("DELETE FROM future_transactions WHERE id = ?", (transaction_dict['id'],))
                print(f"Deleted transaction ID {transaction_dict['id']} from future_transactions table.")


                # --- Store Details for final summary ---
                processed_transactions.append(transaction_dict) # append processed transaction details


            db.commit()
            print("Committed database changes for processed future transactions.")

            # --- Display Processed Transactions Summary ---
            if processed_transactions:
                show_processed_summary_dialog(parent, processed_transactions, db.cursor)
            else:
                print("No transactions were ultimately processed in this run.")


    except sqlite3.Error as e:
        # Rollback changes if a database error occurs
        if db_manager.conn: # Check if connection object exists
            try:
                db_manager.conn.rollback()
                print(f"Database error occurred: {e}. Rolled back changes.")
            except sqlite3.Error as rb_err:
                 print(f"Database error occurred: {e}. Rollback failed: {rb_err}")
        else:
            print(f"Database error occurred: {e}. No active connection to rollback.")
        if parent:
            QMessageBox.critical(parent, "Database Error", f"Error processing future transactions: {str(e)}")

    except Exception as e: # Catch other potential errors (e.g., programming errors)
         # Rollback changes if an unexpected error occurs
         if db_manager.conn: # Check if connection object exists
              try:
                  db_manager.conn.rollback()
                  print(f"Unexpected error occurred: {e}. Rolled back changes.")
              except sqlite3.Error as rb_err:
                  print(f"Unexpected error occurred: {e}. Rollback failed: {rb_err}")
         else:
              print(f"Unexpected error occurred: {e}. No active connection to rollback.")
         if parent:
              QMessageBox.critical(parent, "Processing Error", f"An unexpected error occurred: {e}")

    finally:
        # Ensure row factory is reset if necessary, although context manager should handle connection closing
        if db_manager.conn:
            db_manager.conn.row_factory = None # Reset to default if needed


def get_account_name(cursor, account_id):
    """Helper function to get account name by ID."""
    if account_id is None:
        return 'Invalid Account ID'
    try:
        cursor.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
        result = cursor.fetchone()
        # Note: fetchone() might return None if account_id doesn't exist
        return result['name'] if result else f'Unknown Account (ID:{account_id})'
    except (sqlite3.Error, KeyError, TypeError) as e:
         print(f"Error fetching account name for ID {account_id}: {e}")
         return f'Error (ID:{account_id})'


def show_processed_summary_dialog(parent, processed_transactions, db_cursor):
     """Shows a summary of transactions that were successfully processed."""
     if not parent:
         print("Processed Transactions (Console Output):")
         for trans in processed_transactions:
             print(f"  Date: {trans['date']}, Desc: {trans['description']}, Amount: {trans['amount']}")
         return

     dialog = QDialog(parent)
     dialog.setWindowTitle("Processed Future Transactions Summary")
     layout = QVBoxLayout(dialog)
     dialog.setMinimumSize(700, 300)

     table = QTableWidget()
     table.setColumnCount(5) # Date, Desc, Amount, Debited, Credited
     table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Debited Account", "Credited Account"])
     table.setRowCount(len(processed_transactions))
     table.setEditTriggers(QTableWidget.NoEditTriggers)
     table.verticalHeader().setVisible(False)
     table.setAlternatingRowColors(True)

     for row, trans in enumerate(processed_transactions):
         # Fetch account names here for the summary display
         debited_account_name = get_account_name(db_cursor, trans.get('debited')) # Use .get for safety
         credited_account_name = get_account_name(db_cursor, trans.get('credited'))

         table.setItem(row, 0, QTableWidgetItem(trans.get('date', 'N/A')))
         table.setItem(row, 1, QTableWidgetItem(trans.get('description', 'N/A')))

         amount_str = "N/A"
         try:
             amount_val = float(trans.get('amount', 0))
             amount_str = f"{amount_val:,.2f}"
         except (ValueError, TypeError):
             pass # Keep "N/A" or default if conversion fails
         amount_item = QTableWidgetItem(amount_str)
         amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
         table.setItem(row, 2, amount_item)

         table.setItem(row, 3, QTableWidgetItem(debited_account_name))
         table.setItem(row, 4, QTableWidgetItem(credited_account_name))

     table.resizeColumnsToContents()
     header = table.horizontalHeader()
     header.setSectionResizeMode(1, QHeaderView.Stretch) # Stretch description column

     layout.addWidget(table)
     ok_button = QPushButton("OK")
     ok_button.clicked.connect(dialog.accept)
     button_layout = QHBoxLayout()
     button_layout.addStretch()
     button_layout.addWidget(ok_button)
     button_layout.addStretch()
     layout.addLayout(button_layout)

     dialog.exec()


# Renamed from edit_future_transactions for clarity
def manage_future_transactions(parent, transactions_list, db):
    """
    Displays a dialog to view, edit, delete, or postpone future transactions
    BEFORE they are processed. Modifies transactions_list directly by removing
    items that are deleted or postponed. Edits are saved directly to the DB.
    Returns True if user clicks OK ('Continue Processing'), False if Cancelled.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Manage Upcoming Future Transactions")
    dialog.setMinimumSize(750, 400) # Ensure enough width for buttons
    layout = QVBoxLayout(dialog)

    table = QTableWidget()
    # Column Count: ID, Date, Desc, Debit, Credit, Amount, Edit, Delete, Postpone = 9
    table.setColumnCount(9)
    table.setHorizontalHeaderLabels([
        "ID", "Date", "Description", "Debited", "Credited", "Amount",
        "", "", "" # Headers for Edit, Delete, Postpone buttons
    ])
    table.setEditTriggers(QTableWidget.NoEditTriggers) # Don't allow direct table editing
    table.setSelectionBehavior(QTableWidget.SelectRows) # Select whole rows
    table.setSelectionMode(QTableWidget.SingleSelection) # Only one row at a time
    layout.addWidget(table)

    # Configure Header Resizing
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID column size based on content
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Date
    header.setSectionResizeMode(2, QHeaderView.Stretch)          # Description stretches to fill space
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Debited Account Name
    header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Credited Account Name
    header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Amount
    header.setSectionResizeMode(6, QHeaderView.Fixed)            # Edit Button column fixed size
    header.setSectionResizeMode(7, QHeaderView.Fixed)            # Delete Button
    header.setSectionResizeMode(8, QHeaderView.Fixed)            # Postpone Button
    header.resizeSection(6, 80) # Width for Edit button column
    header.resizeSection(7, 80) # Width for Delete
    header.resizeSection(8, 90) # Width for Postpone

    # Optional: Hide the ID column from view if it's not needed for the user
    # table.setColumnHidden(0, True)


    def populate_table():
        """Clears and refills the table based on the current state of transactions_list."""
        table.setRowCount(0) # Clear existing rows before repopulating
        table.setRowCount(len(transactions_list))
        for row_idx, trans_dict in enumerate(transactions_list):
            # Fetch account names dynamically to reflect any potential edits
            debited_account_name = get_account_name(db.cursor, trans_dict.get('debited'))
            credited_account_name = get_account_name(db.cursor, trans_dict.get('credited'))

            # Column 0: ID
            id_item = QTableWidgetItem(str(trans_dict.get('id', 'N/A')))
            id_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_idx, 0, id_item)

            # Column 1: Date
            table.setItem(row_idx, 1, QTableWidgetItem(trans_dict.get('date', 'N/A')))
            # Column 2: Description
            table.setItem(row_idx, 2, QTableWidgetItem(trans_dict.get('description', '')))
            # Column 3: Debited Account Name
            table.setItem(row_idx, 3, QTableWidgetItem(debited_account_name))
            # Column 4: Credited Account Name
            table.setItem(row_idx, 4, QTableWidgetItem(credited_account_name))

            # Column 5: Amount (Formatted)
            amount_str = "N/A"
            try:
                amount_val = float(trans_dict.get('amount', 0))
                amount_str = f"{amount_val:,.2f}" # Format with commas and 2 decimal places
            except (ValueError, TypeError):
                 print(f"Warning: Could not format amount for row {row_idx}. Value: {trans_dict.get('amount')}")
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter) # Align amount right
            table.setItem(row_idx, 5, amount_item)

            # --- Action Buttons ---
            # Column 6: Edit Button
            edit_button = QPushButton("Edit")
            # Connect button click to edit_single_transaction, passing the row index
            edit_button.clicked.connect(lambda checked=False, row=row_idx: edit_single_transaction(row))
            table.setCellWidget(row_idx, 6, edit_button)

            # Column 7: Delete Button
            delete_button = QPushButton("Delete")
            # Connect button click to delete_future_occurrence, passing the row index
            delete_button.clicked.connect(lambda checked=False, row=row_idx: delete_future_occurrence(row))
            table.setCellWidget(row_idx, 7, delete_button)

            # Column 8: Postpone Button
            postpone_button = QPushButton("Postpone")
            # Connect button click to postpone_future_occurrence, passing the row index
            postpone_button.clicked.connect(lambda checked=False, row=row_idx: postpone_future_occurrence(row))
            table.setCellWidget(row_idx, 8, postpone_button)

        table.resizeRowsToContents() # Adjust row heights


    def edit_single_transaction(row):
        """Opens a dialog to edit details (Desc, Accounts, Amount) of a selected transaction."""
        if not (0 <= row < len(transactions_list)):
             QMessageBox.warning(dialog, "Selection Error", "Invalid row selected for editing.")
             return

        trans_dict = transactions_list[row] # Get the dictionary for the selected row

        # Create the editing sub-dialog
        edit_dialog = QDialog(dialog) # Parent is the main management dialog
        edit_dialog.setWindowTitle(f"Edit Future Transaction (ID: {trans_dict.get('id', 'N/A')})")
        edit_layout = QVBoxLayout(edit_dialog)
        edit_dialog.setMinimumWidth(450)

        # Date Display (Read-Only - Use Postpone button to change date)
        edit_layout.addWidget(QLabel("Date (Use 'Postpone' button to change):"))
        date_input = QLineEdit(trans_dict.get('date', ''))
        date_input.setReadOnly(True)
        edit_layout.addWidget(date_input)

        # Description Input
        edit_layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit(trans_dict.get('description', ''))
        edit_layout.addWidget(description_input)

        # Debited Account Selection
        edit_layout.addWidget(QLabel("Debited Account:"))
        debited_display = QLineEdit(get_account_name(db.cursor, trans_dict.get('debited'))) # Show current name
        debited_display.setReadOnly(True) # Display only, change via Search
        debited_search_button = QPushButton("Search")
        debited_layout = QHBoxLayout()
        debited_layout.addWidget(debited_display)
        debited_layout.addWidget(debited_search_button)
        edit_layout.addLayout(debited_layout)
        # Store the ID selected via search temporarily
        current_debited_id = trans_dict.get('debited') # Initialize with current ID

        def handle_debited_search():
            nonlocal current_debited_id # Allow modification of the outer variable
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=db.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected and 'id' in selected and 'name' in selected:
                    debited_display.setText(f"{selected['name']}") # Update display field
                    current_debited_id = selected['id'] # Update the temporary ID holder
                elif selected:
                    QMessageBox.warning(edit_dialog, "Selection Error", "Selected account is missing ID or Name.")
            search_dialog.close() # Ensure dialog is closed

        debited_search_button.clicked.connect(handle_debited_search)

        # Credited Account Selection (similar structure to Debited)
        edit_layout.addWidget(QLabel("Credited Account:"))
        credited_display = QLineEdit(get_account_name(db.cursor, trans_dict.get('credited')))
        credited_display.setReadOnly(True)
        credited_search_button = QPushButton("Search")
        credited_layout = QHBoxLayout()
        credited_layout.addWidget(credited_display)
        credited_layout.addWidget(credited_search_button)
        edit_layout.addLayout(credited_layout)
        current_credited_id = trans_dict.get('credited') # Initialize with current ID

        def handle_credited_search():
            nonlocal current_credited_id
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=db.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected and 'id' in selected and 'name' in selected:
                    credited_display.setText(f"{selected['name']}")
                    current_credited_id = selected['id']
                elif selected:
                    QMessageBox.warning(edit_dialog, "Selection Error", "Selected account is missing ID or Name.")
            search_dialog.close() # Ensure dialog is closed

        credited_search_button.clicked.connect(handle_credited_search)

        # Amount Input
        edit_layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit(str(trans_dict.get('amount', '0.0'))) # Use string representation
        edit_layout.addWidget(amount_input)

        # --- OK/Cancel Buttons for the Edit Sub-Dialog ---
        edit_button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # Connect OK to the function that validates, updates DB, updates list, and refreshes table
        edit_button_box.accepted.connect(lambda: update_transaction_data(
            row, description_input.text(),
            current_debited_id, # Pass the final selected ID
            current_credited_id, # Pass the final selected ID
            amount_input.text(), edit_dialog
        ))
        edit_button_box.rejected.connect(edit_dialog.reject) # Close sub-dialog on Cancel
        edit_layout.addWidget(edit_button_box)

        edit_dialog.exec() # Show the sub-dialog modally


    def update_transaction_data(row, new_description, new_debited_id, new_credited_id, new_amount_str, edit_dialog):
        """
        Validates input from the edit dialog, updates the database record directly,
        updates the dictionary in transactions_list, and refreshes the main table.
        """
        try:
            # Validate amount: must be convertible to float and positive
            new_amount_float = float(new_amount_str)
            if new_amount_float <= 0:
                QMessageBox.warning(edit_dialog, "Invalid Amount", "Amount must be a positive number.")
                return # Keep edit dialog open

            # Validate account IDs (basic check: not None)
            if new_debited_id is None or new_credited_id is None:
                 QMessageBox.warning(edit_dialog, "Account Error", "Both Debited and Credited accounts must be selected.")
                 return

            if new_debited_id == new_credited_id:
                 QMessageBox.warning(edit_dialog, "Account Error", "Debited and Credited accounts cannot be the same.")
                 return

            target_transaction_id = transactions_list[row]['id']

            # --- Update the database record ---
            # Use a transaction for the update
            try:
                db.cursor.execute("BEGIN")
                db.cursor.execute("""
                    UPDATE future_transactions
                    SET description = ?, debited = ?, credited = ?, amount = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_description, new_debited_id, new_credited_id, new_amount_float, target_transaction_id))
                db.commit() # Commit the change immediately for edits
                print(f"Successfully updated future_transaction ID {target_transaction_id} in database.")
            except sqlite3.Error as e:
                db.rollback() # Rollback on error
                print(f"Database error updating future_transaction ID {target_transaction_id}: {e}")
                QMessageBox.critical(edit_dialog, "Database Error", f"Failed to update transaction: {e}")
                return # Keep edit dialog open

            # --- Update the dictionary in the Python list (transactions_list) ---
            transactions_list[row]['description'] = new_description
            transactions_list[row]['debited'] = new_debited_id
            transactions_list[row]['credited'] = new_credited_id
            transactions_list[row]['amount'] = new_amount_float
            # Note: No need to update 'date' here, handled by Postpone

            populate_table()  # Refresh the main management table view
            edit_dialog.accept() # Close the small edit dialog successfully

        except ValueError:
            QMessageBox.warning(edit_dialog, "Invalid Amount", "Please enter a valid number for the amount.")
        except Exception as e: # Catch other unexpected errors during update
            QMessageBox.critical(edit_dialog, "Update Error", f"An unexpected error occurred: {e}")


    def delete_future_occurrence(row):
        """
        Handles the 'Delete' button click. Confirms, deletes from the DB,
        removes from transactions_list, and refreshes the table.
        """
        if not (0 <= row < len(transactions_list)):
             QMessageBox.warning(dialog,"Selection Error", "Invalid row selected for deletion.")
             return

        trans_to_delete = transactions_list[row]
        # Confirmation dialog
        confirm = QMessageBox.question(dialog, "Confirm Delete",
                                       f"Are you sure you want to permanently delete this future transaction?\n\n"
                                       f"ID: {trans_to_delete.get('id', 'N/A')}\n"
                                       f"Date: {trans_to_delete.get('date', 'N/A')}\n"
                                       f"Desc: {trans_to_delete.get('description', '')}\n\n"
                                       f"This action cannot be undone and removes it from future processing.",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No) # Default No

        if confirm == QMessageBox.Yes:
            target_transaction_id = trans_to_delete.get('id')
            if target_transaction_id is None:
                QMessageBox.critical(dialog, "Error", "Cannot delete transaction: Missing ID.")
                return

            try:
                # --- Delete directly from the database ---
                db.cursor.execute("BEGIN")
                delete_count = db.cursor.execute("DELETE FROM future_transactions WHERE id = ?", (target_transaction_id,)).rowcount
                db.commit()

                if delete_count > 0:
                    print(f"Deleted future_transaction ID {target_transaction_id} from database.")
                    # --- Remove from the Python list being processed ---
                    del transactions_list[row]
                    populate_table() # Refresh the table view
                    QMessageBox.information(dialog, "Deleted", "Future transaction deleted successfully.")
                else:
                    print(f"Attempted to delete ID {target_transaction_id}, but it was not found in the database.")
                    # Might have been deleted by another process, remove from list anyway?
                    try:
                        del transactions_list[row]
                        populate_table()
                        QMessageBox.warning(dialog, "Deletion Notice", f"Transaction ID {target_transaction_id} was not found in the database (already deleted?), removed from list.")
                    except IndexError:
                        pass # Already gone from list somehow

            except sqlite3.Error as e:
                db.rollback()
                print(f"Database error deleting future_transaction ID {target_transaction_id}: {e}")
                QMessageBox.critical(dialog, "Database Error", f"Failed to delete future transaction: {e}")
        # else: User clicked No


    def postpone_future_occurrence(row):
        """
        Handles the 'Postpone' button click. Opens date selector, validates date,
        updates the DB record's date, removes from transactions_list, and refreshes table.
        """
        if not (0 <= row < len(transactions_list)):
             QMessageBox.warning(dialog,"Selection Error", "Invalid row selected for postponement.")
             return

        trans_to_postpone = transactions_list[row]

        # --- Open Date Selection Dialog ---
        date_dialog = DateSelectWindow()
        # Try to set a reasonable default date (e.g., current date + 1 day)
        try:
             current_qdate = QDate.fromString(trans_to_postpone.get('date', ''), 'yyyy-MM-dd')
             if current_qdate.isValid():
                  # Set default selection to day after current date
                  date_dialog.calendar.setSelectedDate(current_qdate.addDays(1))
             else: # Fallback if current date is invalid format
                  date_dialog.calendar.setSelectedDate(QDate.currentDate().addDays(1))
        except Exception as e:
             print(f"Error setting default postpone date: {e}")
             date_dialog.calendar.setSelectedDate(QDate.currentDate().addDays(1)) # Fallback

        # --- Process Selected Date ---
        if date_dialog.exec() == QDialog.Accepted:
            new_qdate = date_dialog.calendar.selectedDate()
            new_date_str = new_qdate.toString('yyyy-MM-dd')
            today_str = date.today().strftime('%Y-%m-%d')

            # --- Validation: New date must be strictly after today ---
            if new_date_str <= today_str:
                QMessageBox.warning(dialog, "Invalid Date",
                                    f"The new date ({new_date_str}) must be after today ({today_str}).")
                return # Keep management dialog open, don't proceed

            target_transaction_id = trans_to_postpone.get('id')
            if target_transaction_id is None:
                QMessageBox.critical(dialog, "Error", "Cannot postpone transaction: Missing ID.")
                return

            # --- Update Date in Database ---
            try:
                db.cursor.execute("BEGIN")
                update_count = db.cursor.execute(
                    "UPDATE future_transactions SET date = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_date_str, target_transaction_id)
                ).rowcount
                db.commit()

                if update_count > 0:
                    print(f"Postponed future_transaction ID {target_transaction_id} to {new_date_str} in database.")
                    # --- Remove from the Python list being processed *today* ---
                    original_desc = trans_to_postpone.get('description', '') # Store before deleting
                    del transactions_list[row]
                    populate_table() # Refresh the table view
                    QMessageBox.information(dialog, "Postponed",
                                            f"Transaction '{original_desc}' postponed to {new_date_str}.\n"
                                            "It will not be processed today.")
                else:
                    print(f"Attempted to postpone ID {target_transaction_id}, but it was not found in the database.")
                    # Might have been deleted or processed already. Remove from list?
                    try:
                        del transactions_list[row]
                        populate_table()
                        QMessageBox.warning(dialog, "Postpone Notice", f"Transaction ID {target_transaction_id} was not found in the database (already processed/deleted?), removed from list.")
                    except IndexError:
                         pass # Already gone

            except sqlite3.Error as e:
                db.rollback()
                print(f"Database error postponing future_transaction ID {target_transaction_id}: {e}")
                QMessageBox.critical(dialog, "Database Error", f"Failed to postpone future transaction: {e}")
        # else: User cancelled the date selection dialog

    # --- Initial Table Population ---
    populate_table()

    # --- Main Dialog Buttons (OK/Cancel for the whole management window) ---
    main_button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    main_button_box.button(QDialogButtonBox.Ok).setText("Continue Processing") # Label OK button
    main_button_box.accepted.connect(dialog.accept) # OK clicked -> return True
    main_button_box.rejected.connect(dialog.reject) # Cancel clicked -> return False
    layout.addWidget(main_button_box)

    # Execute the dialog modally and return based on button clicked
    return dialog.exec() == QDialog.Accepted