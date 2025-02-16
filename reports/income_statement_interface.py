# reports/income_statement_interface.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit,
                              QPushButton, QMessageBox, QWidget, QHBoxLayout)
from PySide6.QtCore import Qt
from utils.crud.generic_crud import GenericCRUD
from .income_statement_core import generate_income_statement_data
from utils.formatters import format_table_name

class IncomeStatementWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Income Statement")
        self.layout = QVBoxLayout(self)

        # Period Selection
        top_layout = QHBoxLayout()
        self.period_label = QLabel("Select Accounting Period:")
        self.select_period_button = QPushButton("Select Period")
        self.select_period_button.clicked.connect(self.select_period)
        top_layout.addWidget(self.period_label)
        top_layout.addWidget(self.select_period_button)
        self.layout.addLayout(top_layout)

        # Report Display (QTextEdit)
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.layout.addWidget(self.report_text)

        self.start_date = None
        self.end_date = None

        self.show_report_on_main_window()

    def select_period(self):
        crud = GenericCRUD("accounting_periods")
        period = crud.open_search(field_type='generic', parent=self.main_window)

        if period:
            self.start_date = period.get('start_date')
            self.end_date = period.get('end_date')
            self.generate_report()

    def generate_report(self):
        if not self.start_date or not self.end_date:
            QMessageBox.warning(self.main_window, "Error", "Please select an accounting period.")
            return

        try:
            report_data = generate_income_statement_data(self.start_date, self.end_date)
            if report_data:
                self.display_report(report_data)
                self.show_report_on_main_window()
            else:
                QMessageBox.warning(self.main_window, "Report Generation", "No data found for the selected period.")

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to generate report: {e}")

    def display_report(self, report_data):
        html_report = self.format_report_html(report_data)
        self.report_text.setHtml(html_report)

    def format_report_html(self, report_data):
            """Formats report data into HTML, aligning amounts, no tables."""

            html = '<div style="font-family: monospace; text-align: center; width: 60%; margin: auto; font-size: 1.5em;">'  # Container div, increased font-size
            html += '<h2 style="margin-bottom: 0;">INCOME STATEMENT</h2>'
            html += f'<p style="margin-top: 0;">{self.start_date} to {self.end_date}</p>'
            html += '<div style="border-bottom: 2px solid black; margin-bottom: 10px;"></div>'

            # --- Revenues ---
            html += '<h3 style="margin-bottom: 5px; text-align: left;">REVENUES</h3>'
            html += '<div style="text-align: left;">'
            total_revenue = 0
            for account, amount in report_data['Revenues']:
                formatted_amount = f"$ {abs(amount):.2f}"
                html += f'<div>{format_table_name(account):<40}{formatted_amount:>12}</div>'
                total_revenue += amount
            html += f'<div style="margin-top: 5px;">Total Revenues:<span style="float: right; border-bottom: 1px solid black; padding-bottom: 2px; width: 150px; display: inline-block; text-align: right;">$ {abs(total_revenue):.2f}</span></div>'  # Increased width
            html += '</div>'

            # --- Expenses ---
            html += '<h3 style="margin-top: 15px; margin-bottom: 5px; text-align: left;">EXPENSES</h3>'
            html += '<div style="text-align: left;">'
            total_expenses = 0
            for account, amount in report_data['Expenses']:
                formatted_amount = f"$ {abs(amount):.2f}"
                html += f'<div>{format_table_name(account):<40}{formatted_amount:>12}</div>'
                total_expenses += amount
            html += f'<div style="margin-top: 5px;">Total Expenses:<span style="float: right; border-bottom: 1px solid black; padding-bottom: 2px; width: 150px; display: inline-block; text-align: right;">$ {abs(total_expenses):.2f}</span></div>'  # Increased width
            html += '</div>'

            # --- Net Income/Loss ---
            html += '<div style="border-top: 2px solid black; margin-top: 10px;"></div>'
            net_income = report_data['Net Income']
            if net_income >= 0:
                result_label = "Net Income"
                result_color = "green"
            else:
                result_label = "Net Loss"
                result_color = "red"
            html += f'<p style="font-weight: bold; color: {result_color}; margin-top: 10px;">{result_label}:  $ {abs(net_income):.2f}</p>'

            html += '</div>'  # Close container div
            return html

    def show_report_on_main_window(self):
        self.main_window.setCentralWidget(self)