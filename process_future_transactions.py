# process_future_transactions.py

import sqlite3
from datetime import date
from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout
from data.create_database import DatabaseManager


def process_future_transactions(parent=None):
    db_manager = DatabaseManager()
    processed_transactions = []  # List to store details of processed transactions

    try:
        with db_manager as db:
            today = date.today().strftime('%Y-%m-%d')
            db.cursor.execute("SELECT * FROM future_transactions WHERE date <= ?", (today,))
            future_transactions = db.cursor.fetchall()

            if not future_transactions:
                print("No future transactions to process.")
                return

            for transaction in future_transactions:
                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (transaction['date'], transaction['description'], transaction['debited'],
                     transaction['credited'], transaction['amount'], transaction['created_at'],
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