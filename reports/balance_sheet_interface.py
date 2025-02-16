# reports/balance_sheet_interface.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QMessageBox, QTextEdit, QHBoxLayout, QDialog)
from PySide6.QtCore import Qt
from .balance_sheet_core import BalanceSheet
from utils.crud.generic_crud import GenericCRUD
from utils.formatters import format_table_name

class BalanceSheetWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Balance Sheet")
        self.layout = QVBoxLayout(self)

        # Date Selection
        top_layout = QHBoxLayout()
        self.date_label = QLabel("Select Date:")
        self.select_date_button = QPushButton("Select Date")
        self.select_date_button.clicked.connect(self.select_date)
        top_layout.addWidget(self.date_label)
        top_layout.addWidget(self.select_date_button)
        self.layout.addLayout(top_layout)


        # Report Display
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.layout.addWidget(self.report_text)

        self.selected_date = None
        self.show_report_on_main_window()


    def select_date(self):
        """Opens a date selection dialog and generates the report."""
        from utils.crud.date_select import DateSelectWindow
        date_dialog = DateSelectWindow()  # Use the DateSelectWindow
        if date_dialog.exec() == QDialog.Accepted:
            self.selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
            self.generate_report()

    def generate_report(self):
        """Generates and displays the balance sheet."""
        if not self.selected_date:
            QMessageBox.warning(self.main_window, "Error", "Please select a date.")
            return

        try:
            balance_sheet = BalanceSheet()
            (ativos_circulantes, ativos_fixos,
             passivos_circulantes, passivos_nao_circulantes,
             patrimonio) = balance_sheet.calcular_saldos_na_data(self.selected_date)

            # For simplicity, we'll assume DRP (Demonstrativo do Resultado do Período)
            # is 0.  In a real application, this would need to be calculated.
            lucro_drp = 0

            html_report = self.format_report_html(ativos_circulantes, ativos_fixos,
                                                  passivos_circulantes, passivos_nao_circulantes,
                                                  patrimonio, lucro_drp)
            self.report_text.setHtml(html_report)
            self.show_report_on_main_window() # Update central widget

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to generate report: {e}")
        finally:
            balance_sheet.close_connection() #close connection


    def format_report_html(self, ativos_circulantes, ativos_fixos,
                           passivos_circulantes, passivos_nao_circulantes,
                           patrimonio, lucro_drp):
        """Formats the balance sheet data into an HTML string."""

        html = '<div style="font-family: monospace; text-align: center; width: 80%; margin: auto; font-size: 1.2em;">'
        html += '<h2 style="margin-bottom: 0;">BALANCE SHEET</h2>'
        html += f'<p style="margin-top: 0;">As of {self.selected_date}</p>'
        html += '<div style="border-bottom: 2px solid black; margin-bottom: 10px;"></div>'

        html += '<table style="width: 100%; border-collapse: collapse;">'

        # --- Assets ---
        html += '<tr><td style="vertical-align: top;">' # Left Column (Assets)
        html += '<h3 style="margin-bottom: 5px; text-align: left;">ASSETS</h3>'
        html += '<table style="width: 100%;">'

        # Current Assets
        total_ativos_circulantes = 0
        if ativos_circulantes:  # Check if the list is not empty
            html += '<tr><td colspan="2" style="font-weight: bold; text-align: left;">Current Assets</td></tr>'
            for conta in ativos_circulantes:
                html += f'<tr><td style="text-align: left; padding-left: 20px;">{format_table_name(conta["name"])}</td><td style="text-align: right;">$ {conta["balance"]:.2f}</td></tr>'
                total_ativos_circulantes += conta['balance']
            html += f'<tr><td style="text-align: left; padding-top: 5px;">Total Current Assets:</td><td style="text-align: right; border-top: 1px solid black; padding-top: 5px;">$ {total_ativos_circulantes:.2f}</td></tr>'

        # Fixed Assets
        total_ativos_fixos = 0
        if ativos_fixos:
            html += '<tr><td colspan="2" style="font-weight: bold; text-align: left; padding-top: 10px;">Fixed Assets</td></tr>'
            for conta in ativos_fixos:
                html += f'<tr><td style="text-align: left; padding-left: 20px;">{format_table_name(conta["name"])}</td><td style="text-align: right;">$ {conta["balance"]:.2f}</td></tr>'
                total_ativos_fixos += conta["balance"]
            html += f'<tr><td style="text-align: left; padding-top: 5px;">Total Fixed Assets:</td><td style="text-align: right; border-top: 1px solid black; padding-top: 5px;">$ {total_ativos_fixos:.2f}</td></tr>'
        html += '</table>'
        html += '</td>' # Close Assets Column


        # --- Liabilities and Equity ---
        html += '<td style="vertical-align: top;">'  # Right Column (Liabilities/Equity)
        html += '<h3 style="margin-bottom: 5px; text-align: left;">LIABILITIES & EQUITY</h3>'
        html += '<table style="width: 100%;">'

        # Current Liabilities
        total_passivos_circulantes = 0
        if passivos_circulantes:
            html += '<tr><td colspan="2" style="font-weight: bold; text-align: left;">Current Liabilities</td></tr>'
            for conta in passivos_circulantes:
                html += f'<tr><td style="text-align: left; padding-left: 20px;">{format_table_name(conta["name"])}</td><td style="text-align: right;">$ {conta["balance"]:.2f}</td></tr>'
                total_passivos_circulantes += conta["balance"]
            html += f'<tr><td style="text-align: left; padding-top: 5px;">Total Current Liabilities:</td><td style="text-align: right; border-top: 1px solid black; padding-top: 5px;">$ {total_passivos_circulantes:.2f}</td></tr>'

        # Non-Current Liabilities
        total_passivos_nao_circulantes = 0
        if passivos_nao_circulantes:
             html += '<tr><td colspan="2" style="font-weight: bold; text-align: left; padding-top: 10px;">Non-Current Liabilities</td></tr>'
             for conta in passivos_nao_circulantes:
                html += f'<tr><td style="text-align: left; padding-left: 20px;">{format_table_name(conta["name"])}</td><td style="text-align: right;">$ {conta["balance"]:.2f}</td></tr>'
                total_passivos_nao_circulantes += conta['balance']
             html += f'<tr><td style="text-align: left; padding-top: 5px;">Total Non-Current Liabilities:</td><td style="text-align: right; border-top: 1px solid black; padding-top: 5px;">$ {total_passivos_nao_circulantes:.2f}</td></tr>'

        # Equity
        total_patrimonio = 0
        if patrimonio:
            html += '<tr><td colspan="2" style="font-weight: bold; text-align: left; padding-top: 10px;">Equity</td></tr>'
            for conta in patrimonio:
                html += f'<tr><td style="text-align: left; padding-left: 20px;">{format_table_name(conta["name"])}</td><td style="text-align: right;">$ {conta["balance"]:.2f}</td></tr>'
                total_patrimonio += conta["balance"]
            html += f'<tr><td style="text-align: left; padding-top: 5px;">Total Equity:</td><td style="text-align: right; border-top: 1px solid black; padding-top: 5px;">$ {total_patrimonio:.2f}</td></tr>'
        html += '</table>'
        html += '</td></tr>'  # Close Liabilities/Equity Column

        # --- Totals ---
        total_ativos = total_ativos_circulantes + total_ativos_fixos
        total_passivos_e_patrimonio = (total_passivos_circulantes +
                                        total_passivos_nao_circulantes +
                                        total_patrimonio + lucro_drp)
        html += '<tr style="border-top: 2px solid black;"><td style="font-weight: bold; text-align: left; padding-top: 10px;">Total Assets:</td><td style="font-weight: bold; text-align: right; padding-top: 10px;">$ {total_ativos:.2f}</td>'  # Totals row
        html += '<td style="font-weight: bold; text-align: left; padding-top: 10px;">Total Liabilities & Equity:</td><td style="font-weight: bold; text-align: right; padding-top: 10px;">$ {total_passivos_e_patrimonio:.2f}</td></tr>'  # Totals row

        html += '</table>'
        html += '</div>'  # Close container div
        return html

    def show_report_on_main_window(self):
        """Shows the report in the main window's central widget."""
        self.main_window.setCentralWidget(self)