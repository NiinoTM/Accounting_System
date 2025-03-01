# process_future_transactions.py

import sqlite3
from datetime import date
from PySide6.QtWidgets import QMessageBox
from data.create_database import DatabaseManager  # Import DatabaseManager


def process_future_transactions(parent=None):
    """
    Checks for and processes any future transactions that are due.
    Transfers them to the 'transactions' table and updates account balances.
    """
    db_manager = DatabaseManager()  # Create instance
    try:
        with db_manager as db:  # Use context manager for automatic cleanup

            # --- 1. Get future transactions that are due ---
            today = date.today().strftime('%Y-%m-%d')
            db.cursor.execute("SELECT * FROM future_transactions WHERE date <= ?", (today,))
            future_transactions = db.cursor.fetchall()

            if not future_transactions:
                print("No future transactions to process.")  # Debugging print
                return  # Nothing to do

            processed_count = 0
            # --- 2. Process each due transaction ---
            for transaction in future_transactions:
                # --- 2a. Insert into 'transactions' ---
                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (transaction['date'], transaction['description'], transaction['debited'],
                     transaction['credited'], transaction['amount'], transaction['created_at'],
                     transaction['updated_at'])
                )

                # --- 2b. Update account balances ---
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (transaction['amount'], transaction['debited'])
                )
                db.cursor.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                    (transaction['amount'], transaction['credited'])
                )

                # --- 2c. Delete from 'future_transactions' ---
                db.cursor.execute("DELETE FROM future_transactions WHERE id = ?", (transaction['id'],))
                processed_count += 1

            db.commit()  # Commit *outside* the loop
            print(f"Processed {processed_count} future transactions.")

            # --- 3. Show confirmation message ---
            if processed_count > 0:
              if parent:
                QMessageBox.information(parent, "Transactions Processed",
                                        f"{processed_count} scheduled transactions have been processed and added to the main transaction log.")
              else: # if main window is off or doesnt exists.
                print(f"{processed_count} scheduled transactions have been processed and added to the main transaction log.")

    except sqlite3.Error as e:
        if db.conn:  # Check if connection exists before rollback
            db.conn.rollback()
        print(f"Database error processing future transactions: {e}") #for console
        if parent:  # Only show QMessageBox if a parent is provided
          QMessageBox.critical(parent, "Database Error", str(e))