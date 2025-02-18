from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QMessageBox, QHBoxLayout, QScrollArea)
from PySide6.QtCore import Qt
from .balance_sheet_core import BalanceSheet
from utils.crud.generic_crud import GenericCRUD
from utils.formatters import format_table_name
from .income_statement_core import generate_income_statement_data
from PySide6.QtGui import QPalette, QColor

class BalanceSheetWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Balance Sheet")
        self.init_ui()
        self.period_start = None
        self.period_end = None
        self.show_report_on_main_window()
        self.setup_dark_theme()

    def setup_dark_theme(self):
        """Sets up a dark theme for the UI."""
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
        """Initialize the UI components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Period Selection Area
        period_area = QWidget()
        period_layout = QHBoxLayout(period_area)
        self.period_label = QLabel("Select Period:")
        self.select_period_button = QPushButton("Select Period")
        self.select_period_button.clicked.connect(self.select_period)
        period_layout.addWidget(self.period_label)
        period_layout.addWidget(self.select_period_button)
        period_layout.addStretch()
        self.layout.addWidget(period_area)

        # Header
        self.header = QWidget()
        header_layout = QVBoxLayout(self.header)
        header_layout.setSpacing(5)
        
        title = QLabel("BALANCE SHEET")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)
        
        self.date_display = QLabel("As of --/--/----")
        self.date_display.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.date_display)
        self.layout.addWidget(self.header)

        # Content Area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(20)

        # Assets Column
        assets_column = self.create_column("ASSETS")
        self.current_assets_section = self.create_section("Current Assets")
        self.fixed_assets_section = self.create_section("Fixed Assets")
        assets_column.layout().addWidget(self.current_assets_section)
        assets_column.layout().addWidget(self.fixed_assets_section)
        assets_column.layout().addStretch()

        # Liabilities & Equity Column
        liab_equity_column = self.create_column("LIABILITIES & EQUITY")
        self.current_liab_section = self.create_section("Current Liabilities")
        self.noncurrent_liab_section = self.create_section("Long-Term Liabilities")
        self.equity_section = self.create_section("Equity")
        liab_equity_column.layout().addWidget(self.current_liab_section)
        liab_equity_column.layout().addWidget(self.noncurrent_liab_section)
        liab_equity_column.layout().addWidget(self.equity_section)
        liab_equity_column.layout().addStretch()

        content_layout.addWidget(assets_column)
        content_layout.addWidget(liab_equity_column)

        # Wrap content in scroll area
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        self.layout.addWidget(scroll)

        # Totals Area
        totals = QWidget()
        totals_layout = QHBoxLayout(totals)
        totals_layout.setSpacing(20)

        self.total_assets_label = self.create_total_label("TOTAL ASSETS")
        self.total_liab_equity_label = self.create_total_label("TOTAL LIABILITIES & EQUITY")

        totals_layout.addWidget(self.total_assets_label)
        totals_layout.addWidget(self.total_liab_equity_label)
        
        self.layout.addWidget(totals)
        self.apply_styles()

    def create_column(self, title):
        """Create a column widget with title"""
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db;
        """)
        layout.addWidget(title_label)
        return column

    def create_section(self, title):
        """Create a section widget with title"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)
        return section

    def create_total_label(self, text):
        """Create a total label with specific styling"""
        label = QLabel(f"{text}: $ 0.00")
        label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 10px;
            border-top: 3px double;
        """)
        return label

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                padding: 5px 15px;
                background: #3498db;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QScrollArea {
                background: #333;
                border: 1px solid #555;
                border-radius: 8px;
            }
        """)


    def format_amount(self, amount, is_right_side=False):
        """
        Format amount based on side of balance sheet and sign
        is_right_side: True for Liabilities & Equity, False for Assets
        """
        if is_right_side:
            # For right side (Liabilities & Equity), negative becomes positive
            display_amount = -amount if amount < 0 else amount
            sign = "" if amount < 0 else "-"
        else:
            # For left side (Assets), keep original sign
            display_amount = abs(amount)
            sign = "-" if amount < 0 else ""
            
        return f"$ {sign}{display_amount:.2f}"
    
    def add_line_item(self, section, name, amount, is_right_side=False):
        """Add a line item to a section if amount is not zero"""
        if amount == 0:
            return 0
            
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 5, 0, 5)
        
        name_label = QLabel(format_table_name(name))
        formatted_amount = self.format_amount(amount, is_right_side)
        amount_label = QLabel(formatted_amount)
        amount_label.setAlignment(Qt.AlignRight)
        amount_label.setStyleSheet("font-family: 'Consolas', monospace;")
        
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(amount_label)
        
        section.layout().addWidget(item)
        return amount  # Return actual amount, not abs

    def add_subtotal(self, section, text, amount, is_right_side=False):
        """Add a subtotal line to a section"""
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 10, 0, 5)
        
        text_label = QLabel(text)
        formatted_amount = self.format_amount(amount, is_right_side)
        amount_label = QLabel(formatted_amount)
        amount_label.setAlignment(Qt.AlignRight)
        
        text_label.setStyleSheet("""
            font-weight: bold;
            border-top: 1px solid #bdc3c7;
            padding-top: 5px;
        """)
        amount_label.setStyleSheet("""
            font-weight: bold;
            font-family: 'Consolas', monospace;
            border-top: 1px solid #bdc3c7;
            padding-top: 5px;
        """)
        
        layout.addWidget(text_label)
        layout.addStretch()
        layout.addWidget(amount_label)
        
        section.layout().addWidget(item)

    def select_period(self):
        """Opens period selection dialog"""
        crud = GenericCRUD("accounting_periods")
        period = crud.open_search(field_type='generic', parent=self.main_window)

        if period:
            self.period_start = period.get('start_date')
            self.period_end = period.get('end_date')
            self.date_display.setText(f"As of {self.period_end}")
            self.generate_report()

    def generate_report(self):
        """Generates and displays the balance sheet."""
        if not self.period_end:
            QMessageBox.warning(self, "Error", "Please select an accounting period.")
            return

        try:
            # Get balance sheet data
            balance_sheet = BalanceSheet()
            ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio = (
                balance_sheet.calcular_saldos_na_data(self.period_end)
            )

            # Get income statement data for the period
            income_data = generate_income_statement_data(self.period_start, self.period_end)
            net_income = income_data['Net Income'] if income_data else 0

            # Clear previous content
            for section in [self.current_assets_section, self.fixed_assets_section,
                          self.current_liab_section, self.noncurrent_liab_section,
                          self.equity_section]:
                while section.layout().count() > 1:  # Keep the title
                    item = section.layout().takeAt(1)
                    if item.widget():
                        item.widget().deleteLater()

            # Add new content - Assets (left side)
            total_current_assets = sum(self.add_line_item(self.current_assets_section, 
                                                        item['name'], 
                                                        item['balance'],
                                                        is_right_side=False)
                                     for item in ativos_circulantes)
            if total_current_assets != 0:
                self.add_subtotal(self.current_assets_section, "Total Current Assets", 
                                total_current_assets, is_right_side=False)

            total_fixed_assets = sum(self.add_line_item(self.fixed_assets_section, 
                                                      item['name'], 
                                                      item['balance'],
                                                      is_right_side=False)
                                   for item in ativos_fixos)
            if total_fixed_assets != 0:
                self.add_subtotal(self.fixed_assets_section, "Total Fixed Assets", 
                                total_fixed_assets, is_right_side=False)

            # Add new content - Liabilities (right side)
            total_current_liab = sum(self.add_line_item(self.current_liab_section, 
                                                      item['name'], 
                                                      item['balance'],
                                                      is_right_side=True)
                                   for item in passivos_circulantes)
            if total_current_liab != 0:
                self.add_subtotal(self.current_liab_section, "Total Current Liabilities", 
                                total_current_liab, is_right_side=True)

            total_noncurrent_liab = sum(self.add_line_item(self.noncurrent_liab_section, 
                                                         item['name'], 
                                                         item['balance'],
                                                         is_right_side=True)
                                      for item in passivos_nao_circulantes)
            if total_noncurrent_liab != 0:
                self.add_subtotal(self.noncurrent_liab_section, "Total Non-Current Liabilities", 
                                total_noncurrent_liab, is_right_side=True)

            # Add equity items including net income/loss (right side)
            total_equity = sum(self.add_line_item(self.equity_section, 
                                                item['name'], 
                                                item['balance'],
                                                is_right_side=True)
                             for item in patrimonio)
            
            # Add net income/loss to equity section if not zero
            if net_income != 0:
                self.add_line_item(self.equity_section, 
                                 "Net Income" if net_income >= 0 else "Net Loss", 
                                 -net_income,
                                 is_right_side=True)
                if net_income >= 0:
                    total_equity += net_income
                else:
                    total_equity -= net_income

            if total_equity != 0:
                self.add_subtotal(self.equity_section, "Total Equity", 
                                total_equity, is_right_side=True)

            # Update totals
            total_assets = total_current_assets + total_fixed_assets
            total_liab_equity = total_current_liab + total_noncurrent_liab + total_equity

            # Update total labels with proper sign formatting
            self.total_assets_label.setText(f"TOTAL ASSETS: {self.format_amount(total_assets, is_right_side=False)}")
            self.total_liab_equity_label.setText(
                f"TOTAL LIABILITIES & EQUITY: {self.format_amount(total_liab_equity, is_right_side=True)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")
        finally:
            balance_sheet.close_connection()

    def show_report_on_main_window(self):
        self.main_window.setCentralWidget(self)