# reports/actual_cashflow.py

import sqlite3
import json
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QHBoxLayout, QScrollArea)
from PySide6.QtCore import Qt
from create_database import DatabaseManager
from utils.crud.generic_crud import GenericCRUD
from utils.formatters import format_table_name

class ActualCashflowWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Actual Cash Flow")
        self.db_manager = DatabaseManager()
        self.period_start = None
        self.period_end = None
        self.accounts = self.load_cashflow_accounts()
        self.init_ui()
        self.show_report_on_main_window()  # Show on main window
        self.setup_dark_theme()

    def setup_dark_theme(self):
        """Sets up a dark theme for the UI."""
        from PySide6.QtGui import QPalette, QColor
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        self.setStyleSheet("""
            QToolTip {
                color: #ffffff;
                background-color: #2a82da;
                border: 1px solid white;
            }
        """)

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        # Period Selection
        period_area = QWidget()
        period_layout = QHBoxLayout(period_area)
        self.period_label = QLabel("Select Accounting Period:")
        self.select_period_button = QPushButton("Select Period")
        self.select_period_button.clicked.connect(self.select_period)
        period_layout.addWidget(self.period_label)
        period_layout.addWidget(self.select_period_button)
        period_layout.addStretch()
        self.layout.addWidget(period_area)

        # Header (Title and Date)
        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        self.title_label = QLabel("CASH FLOW STATEMENT")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.date_label = QLabel("For the Period: --/--/---- to --/--/----")
        self.date_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.date_label)
        self.layout.addWidget(self.header_widget)

        # Content Area (Sections will be added here)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # Wrap content in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(scroll_area)

        # Totals Section (outside the scroll area)
        self.totals_widget = QWidget()
        self.totals_layout = QVBoxLayout(self.totals_widget)
        self.initial_balance_label = QLabel("Initial Balance: $0.00")
        self.total_inflows_label = QLabel("Total Inflows: $0.00")
        self.total_outflows_label = QLabel("Total Outflows: $0.00")
        self.net_cashflow_label = QLabel("Net Cash Flow: $0.00")
        self.ending_balance_label = QLabel("Ending Balance: $0.00")
        self.totals_layout.addWidget(self.initial_balance_label)
        self.totals_layout.addWidget(self.total_inflows_label)
        self.totals_layout.addWidget(self.total_outflows_label)
        self.totals_layout.addWidget(self.net_cashflow_label)
        self.totals_layout.addWidget(self.ending_balance_label)
        self.layout.addWidget(self.totals_widget)

        # Apply Styles
        self.setStyleSheet("""
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def load_cashflow_accounts(self):
        """Loads the cash flow accounts from the JSON file."""
        settings_file = os.path.join("data", "cashflow_accounts.json")
        try:
            with open(settings_file, "r") as f:
                accounts = json.load(f)
                return accounts
        except (FileNotFoundError, json.JSONDecodeError):
            QMessageBox.critical(self, "Error", "Could not load cash flow accounts. Please configure them in settings.")
            return []

    def select_period(self):
        crud = GenericCRUD("accounting_periods")
        period = crud.open_search(field_type='generic', parent=self)
        if period:
            self.period_start = period.get('start_date')
            self.period_end = period.get('end_date')
            self.date_label.setText(f"For the Period: {self.period_start} to {self.period_end}")
            self.generate_report()

    def generate_report(self):
        if not self.period_start or not self.period_end or not self.accounts:
            return

        # Clear previous content from content_layout (scroll area)
        while self.content_layout.count() > 0:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            with self.db_manager as db:
                string_accounts = [str(account) for account in self.accounts]
                placeholders = ', '.join(['?'] * len(string_accounts))
                
                # Initial balance calculation
                initial_balance_query = f"""
                    SELECT 
                        SUM(CASE WHEN t.debited IN ({placeholders}) THEN t.amount ELSE 0 END) as total_debits,
                        SUM(CASE WHEN t.credited IN ({placeholders}) THEN t.amount ELSE 0 END) as total_credits
                    FROM transactions t
                    WHERE (t.debited IN ({placeholders}) OR t.credited IN ({placeholders}))
                    AND t.date < ?
                """
                params = string_accounts * 4 + [self.period_start]
                db.cursor.execute(initial_balance_query, params)
                balance_data = db.cursor.fetchone()
                
                initial_balance = 0
                if balance_data:
                    total_debits = float(balance_data['total_debits'] or 0)
                    total_credits = float(balance_data['total_credits'] or 0)
                    initial_balance = total_debits - total_credits
                
                self.initial_balance_label.setText(f"Initial Balance: ${initial_balance:.2f}")

                # Get transactions within the period
                period_query = f"""
                    SELECT t.description, t.amount, t.date, t.debited, t.credited
                    FROM transactions t
                    WHERE (t.debited IN ({placeholders}) OR t.credited IN ({placeholders}))
                    AND t.date BETWEEN ? AND ?
                    ORDER BY t.date
                """
                period_params = string_accounts * 2 + [self.period_start, self.period_end]
                db.cursor.execute(period_query, period_params)
                transactions = db.cursor.fetchall()

                inflows = []
                outflows = []
                total_inflows = 0
                total_outflows = 0

                for trans in transactions:
                    description = trans['description']
                    amount = float(trans['amount'])
                    debited_account = str(trans['debited'])
                    credited_account = str(trans['credited'])
                    
                    if debited_account in string_accounts:
                        inflows.append({'description': description, 'amount': amount})
                        total_inflows += amount
                    
                    if credited_account in string_accounts:
                        outflows.append({'description': description, 'amount': amount})
                        total_outflows += amount

                # Add inflows section
                inflow_label = QLabel("Cash Inflows")
                inflow_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
                self.content_layout.addWidget(inflow_label)
                
                if inflows:
                    for inflow in inflows:
                        self.add_transaction_line(inflow['description'], inflow['amount'], is_positive=True)
                else:
                    self.content_layout.addWidget(QLabel("No cash inflows for this period"))

                # Add outflows section
                outflow_label = QLabel("Cash Outflows")
                outflow_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
                self.content_layout.addWidget(outflow_label)
                
                if outflows:
                    for outflow in outflows:
                        self.add_transaction_line(outflow['description'], outflow['amount'], is_positive=False)
                else:
                    self.content_layout.addWidget(QLabel("No cash outflows for this period"))

                # Update totals
                self.total_inflows_label.setText(f"Total Inflows: ${total_inflows:.2f}")
                self.total_outflows_label.setText(f"Total Outflows: ${total_outflows:.2f}")
                net_cashflow = total_inflows - total_outflows
                self.net_cashflow_label.setText(f"Net Cash Flow: ${net_cashflow:.2f}")
                
                # Update ending balance
                ending_balance = initial_balance + net_cashflow
                self.ending_balance_label.setText(f"Ending Balance: ${ending_balance:.2f}")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def add_transaction_line(self, description, amount, is_positive=True):
        item_layout = QHBoxLayout()
        desc_label = QLabel(description)
        display_amount = amount if is_positive else -amount
        amount_label = QLabel(f"${abs(display_amount):.2f}")
        amount_label.setAlignment(Qt.AlignRight)
        amount_label.setStyleSheet("color: green;" if is_positive else "color: red;")
        item_layout.addWidget(desc_label)
        item_layout.addStretch()
        item_layout.addWidget(amount_label)
        self.content_layout.addLayout(item_layout)
    
    def show_report_on_main_window(self):
        self.main_window.setCentralWidget(self)