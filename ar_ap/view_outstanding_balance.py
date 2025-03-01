# ar_ap/view_outstanding_balance.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QMessageBox, QDialog,
                               QHBoxLayout)
from PySide6.QtCore import Qt
from data.create_database import DatabaseManager
from utils.formatters import format_table_name

class OutstandingBalanceWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Outstanding Balances")
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Debtor Section
        debtor_label = QLabel("Debtors")
        debtor_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(debtor_label)

        self.debtor_table = QTableWidget()
        self.debtor_table.setColumnCount(3)  # ID, Name, Amount
        self.debtor_table.setHorizontalHeaderLabels(["ID", "Name", "Amount"])
        self.debtor_table.horizontalHeader().setStretchLastSection(True)
        self.debtor_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make read-only
        self.debtor_table.cellDoubleClicked.connect(self.show_debtor_transactions)
        layout.addWidget(self.debtor_table)

        # Creditor Section
        creditor_label = QLabel("Creditors")
        creditor_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(creditor_label)

        self.creditor_table = QTableWidget()
        self.creditor_table.setColumnCount(3)  # ID, Name, Amount
        self.creditor_table.setHorizontalHeaderLabels(["ID", "Name", "Amount"])
        self.creditor_table.horizontalHeader().setStretchLastSection(True)
        self.creditor_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make read-only
        self.creditor_table.cellDoubleClicked.connect(self.show_creditor_transactions)
        layout.addWidget(self.creditor_table)

        self.setLayout(layout)
        self.load_data()


    def load_data(self):
        try:
            with self.db_manager as db:
                # --- Debtors ---
                db.cursor.execute("SELECT id, name, amount FROM debtor_creditor WHERE account = 1")
                debtors = db.cursor.fetchall()
                self.debtor_table.setRowCount(len(debtors))
                for row, debtor in enumerate(debtors):
                    self.debtor_table.setItem(row, 0, QTableWidgetItem(str(debtor['id'])))
                    self.debtor_table.setItem(row, 1, QTableWidgetItem(debtor['name']))
                    self.debtor_table.setItem(row, 2, QTableWidgetItem(str(debtor['amount'])))

                # --- Creditors ---
                db.cursor.execute("SELECT id, name, amount FROM debtor_creditor WHERE account = 2")
                creditors = db.cursor.fetchall()
                self.creditor_table.setRowCount(len(creditors))
                for row, creditor in enumerate(creditors):
                    self.creditor_table.setItem(row, 0, QTableWidgetItem(str(creditor['id'])))
                    self.creditor_table.setItem(row, 1, QTableWidgetItem(creditor['name']))
                    self.creditor_table.setItem(row, 2, QTableWidgetItem(str(creditor['amount'])))

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def show_debtor_transactions(self, row, column):
        self.show_transactions(row, column, self.debtor_table, "Debtor")


    def show_creditor_transactions(self, row, column):
        self.show_transactions(row, column, self.creditor_table, "Creditor")


    def show_transactions(self, row, column, table, party_type):
        """Shows transactions for the selected debtor/creditor."""
        try:
            item = table.item(row, 0)  # Get the ID from the first column
            if not item:
                return  # Safety check: No item at selected row/col

            party_id = int(item.text()) # gets id

        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid ID")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{party_type} Transactions")
        layout = QVBoxLayout(dialog)

        transaction_table = QTableWidget()
        transaction_table.setColumnCount(4) # id, date, detail, amount
        transaction_table.setHorizontalHeaderLabels(["ID", "Date", "Details", "Amount"])
        transaction_table.horizontalHeader().setStretchLastSection(True)
        transaction_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(transaction_table)


        try:
            with self.db_manager as db:
                db.cursor.execute("""SELECT id, date, details, amount
                                     FROM debtor_creditor_transactions
                                     WHERE debtor_creditor = ?""", (party_id,))
                transactions = db.cursor.fetchall()

                transaction_table.setRowCount(len(transactions))
                for row_num, trans in enumerate(transactions):
                    transaction_table.setItem(row_num, 0, QTableWidgetItem(str(trans['id'])))
                    transaction_table.setItem(row_num, 1, QTableWidgetItem(trans['date']))
                    transaction_table.setItem(row_num, 2, QTableWidgetItem(trans['details']))
                    transaction_table.setItem(row_num, 3, QTableWidgetItem(str(trans['amount'])))

        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "Database Error", str(e))
            dialog.reject() # closes and returns to the main window
            return

        dialog.exec() # shows window