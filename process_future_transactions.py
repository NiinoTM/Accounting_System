# process_future_transactions.py

import sqlite3
from datetime import date
from PySide6.QtWidgets import QMessageBox, QDialogButtonBox, QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt #import Qt
from create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog # Import
from utils.formatters import format_table_name


def process_future_transactions(parent=None):
    db_manager = DatabaseManager()
    processed_transactions = []  # List to store details of processed transactions
    transactions_to_process = [] #transactions for editing.

    try:
        with db_manager as db:
            today = date.today().strftime('%Y-%m-%d')
            db.cursor.execute("SELECT * FROM future_transactions WHERE date <= ?", (today,))
            future_transactions = db.cursor.fetchall()

            if not future_transactions:
                print("No future transactions to process.")
                return

            # --- Store transactions for potential editing ---
            transactions_to_process = [dict(row) for row in future_transactions]

            # --- Show Edit Dialog (if parent exists) ---
            if parent and transactions_to_process:
                 if not edit_future_transactions(parent, transactions_to_process, db):
                    return  # User canceled, so don't proceed

            # --- Proceed with processing (either original or edited data) ---
            for transaction in transactions_to_process:

                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (transaction['date'], transaction['description'], transaction['debited'],
                     transaction['credited'], transaction['amount'], transaction['created_at'],  # Use stored values
                     transaction['updated_at'])
                )

                db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (transaction['amount'], transaction['debited'])
                )
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (transaction['amount'], transaction['credited'])
                )

                db.cursor.execute("DELETE FROM future_transactions WHERE id = ?", (transaction['id'],))

                # --- Store Transaction Details ---
                processed_transactions.append(transaction) # append transactions


            db.commit()

            # --- Display Processed Transactions ---
            if processed_transactions:
                if parent: # if parent exists
                    dialog = QDialog(parent)
                    dialog.setWindowTitle("Processed Transactions")
                    layout = QVBoxLayout(dialog)

                    table = QTableWidget()
                    table.setColumnCount(4)  # Date, Description, Amount, Account
                    table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Account"])
                    table.setRowCount(len(processed_transactions))

                    for row, trans in enumerate(processed_transactions):
                        # Assuming you have a way to get account names by ID.  If not, you'll need a helper function.
                        debited_account_name = get_account_name(db.cursor, trans['debited'])
                        credited_account_name = get_account_name(db.cursor, trans['credited'])


                        table.setItem(row, 0, QTableWidgetItem(trans['date']))
                        table.setItem(row, 1, QTableWidgetItem(trans['description']))
                        table.setItem(row, 2, QTableWidgetItem(str(trans['amount'])))
                        table.setItem(row, 3, QTableWidgetItem(f"Debited: {debited_account_name}, Credited: {credited_account_name}"))

                    layout.addWidget(table)
                    dialog.exec()
                else: # prints to console if main window is closed.
                    print("Processed Transactions:")
                    for trans in processed_transactions:
                        print(f"  Date: {trans['date']}, Description: {trans['description']}, Amount: {trans['amount']}")


    except sqlite3.Error as e:
        if db.conn:
            db.conn.rollback()
        print(f"Database error: {e}")
        if parent:
            QMessageBox.critical(parent, "Database Error", str(e))

def get_account_name(cursor, account_id):
    """Helper function to get account name by ID."""
    cursor.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
    result = cursor.fetchone()
    return result['name'] if result else 'Unknown Account'

def edit_future_transactions(parent, transactions, db):
    """Displays a dialog to edit future transactions before processing."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Edit Future Transactions")
    dialog.setMinimumSize(800, 300)
    layout = QVBoxLayout(dialog)

    table = QTableWidget()
    table.setColumnCount(6)  # Date, Description, Debited, Credited, Amount, Edit
    table.setHorizontalHeaderLabels(["Date", "Description", "Debited Account", "Credited Account", "Amount", ""])
    table.setEditTriggers(QTableWidget.NoEditTriggers)  # Don't allow direct editing in the table
    layout.addWidget(table)
    from PySide6.QtWidgets import QHeaderView  # Import

    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)    # Date
    header.setSectionResizeMode(1, QHeaderView.Stretch)    # Description
    header.setSectionResizeMode(2, QHeaderView.ResizeToContents)    # Debited Account
    header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Credited Account
    header.setSectionResizeMode(4, QHeaderView.ResizeToContents)   # Amount
    header.setSectionResizeMode(5, QHeaderView.Fixed)        # Edit
    header.resizeSection(5, 80)

    def populate_table():
        table.setRowCount(len(transactions))
        for row_idx, trans in enumerate(transactions):
            debited_account_name = get_account_name(db.cursor, trans['debited'])
            credited_account_name = get_account_name(db.cursor, trans['credited'])
            table.setItem(row_idx, 0, QTableWidgetItem(trans['date']))
            table.setItem(row_idx, 1, QTableWidgetItem(trans['description']))
            table.setItem(row_idx, 2, QTableWidgetItem(f"{debited_account_name}"))
            table.setItem(row_idx, 3, QTableWidgetItem(f"{credited_account_name}"))
            table.setItem(row_idx, 4, QTableWidgetItem(str(trans['amount'])))

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked, row=row_idx: edit_single_transaction(row))
            table.setCellWidget(row_idx, 5, edit_button)

    def edit_single_transaction(row):
        trans = transactions[row]

        edit_dialog = QDialog(dialog)
        edit_dialog.setWindowTitle("Edit Transaction")
        edit_layout = QVBoxLayout(edit_dialog)

        # --- Date ---
        edit_layout.addWidget(QLabel("Date:"))
        date_input = QLineEdit(trans['date'])
        date_input.setReadOnly(True)  # Usually, you wouldn't change the date in this context
        edit_layout.addWidget(date_input)

        # --- Description ---
        edit_layout.addWidget(QLabel("Description:"))
        description_input = QLineEdit(trans['description'])
        edit_layout.addWidget(description_input)

        # --- Debited Account ---
        edit_layout.addWidget(QLabel("Debited Account:"))
        debited_display = QLineEdit(get_account_name(db.cursor, trans['debited']))
        debited_display.setReadOnly(True)
        debited_search_button = QPushButton("Search")
        debited_layout = QHBoxLayout()
        debited_layout.addWidget(debited_display)
        debited_layout.addWidget(debited_search_button)
        edit_layout.addLayout(debited_layout)
        debited_account_id = trans['debited']  # Store current ID

        def handle_debited_search():
            nonlocal debited_account_id
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=db.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected:
                    debited_display.setText(f"{selected['name']}")
                    debited_account_id = selected['id']  # Update ID

        debited_search_button.clicked.connect(handle_debited_search)


        # --- Credited Account ---
        edit_layout.addWidget(QLabel("Credited Account:"))
        credited_display = QLineEdit(get_account_name(db.cursor, trans['credited']))
        credited_display.setReadOnly(True)
        credited_search_button = QPushButton("Search")
        credited_layout = QHBoxLayout()
        credited_layout.addWidget(credited_display)
        credited_layout.addWidget(credited_search_button)
        edit_layout.addLayout(credited_layout)
        credited_account_id = trans['credited'] #store id

        def handle_credited_search():
            nonlocal credited_account_id
            search_dialog = AdvancedSearchDialog(
                field_type='generic', parent=edit_dialog, db_path=db.db_path, table_name='accounts'
            )
            if search_dialog.exec() == QDialog.Accepted:
                selected = search_dialog.get_selected_item()
                if selected:
                    credited_display.setText(f"{selected['name']}")
                    credited_account_id = selected['id'] #update the ID

        credited_search_button.clicked.connect(handle_credited_search)

        # --- Amount ---
        edit_layout.addWidget(QLabel("Amount:"))
        amount_input = QLineEdit(str(trans['amount']))
        edit_layout.addWidget(amount_input)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: update_transaction(row, description_input.text(),
                                                        debited_account_id, debited_display.text(),
                                                        credited_account_id, credited_display.text(),
                                                        amount_input.text(), edit_dialog))
        button_box.rejected.connect(edit_dialog.reject)
        edit_layout.addWidget(button_box)

        edit_dialog.exec()

    def update_transaction(row, new_description, new_debited_id, new_debited_name,
                           new_credited_id, new_credited_name, new_amount, edit_dialog):
        try:
            new_amount_float = float(new_amount) # convert and check if its a float
            transactions[row]['description'] = new_description
            transactions[row]['debited'] = new_debited_id
            transactions[row]['credited'] = new_credited_id
            transactions[row]['amount'] = new_amount_float

            populate_table()  # Refresh the main table
            edit_dialog.accept()

        except ValueError:
            QMessageBox.warning(edit_dialog, "Invalid Amount", "Please enter a valid number.")



    populate_table()

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    return dialog.exec() == QDialog.Accepted