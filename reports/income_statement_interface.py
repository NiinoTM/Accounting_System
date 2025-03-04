import sqlite3
from create_database import DatabaseManager
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QMessageBox, QHBoxLayout, QScrollArea)
from PySide6.QtCore import Qt
from utils.crud.generic_crud import GenericCRUD
from utils.formatters import format_table_name
from PySide6.QtGui import QPalette, QColor
from reports.income_statement_core import generate_income_statement_data

class IncomeStatementWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Income Statement")
        self.init_ui()
        self.start_date = None
        self.end_date = None
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
        self.period_label = QLabel("Select Accounting Period:")
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

        title = QLabel("INCOME STATEMENT")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)

        self.period_display = QLabel("For the Period")
        self.period_display.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(self.period_display)
        self.layout.addWidget(self.header)

        # Content Area
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(20)

        # Revenue Section
        self.revenue_section = self.create_section("REVENUE", text_color="#50C878")  # Green color for revenue
        self.content_layout.addWidget(self.revenue_section)

        # Expenses Section
        self.expenses_section = self.create_section("EXPENSES", text_color="#FF6B6B")  # Red color for expenses
        self.content_layout.addWidget(self.expenses_section)

        # Wrap content in scroll area
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)

        self.layout.addWidget(scroll)
        self.apply_styles()

    def create_section(self, title, text_color="#FFFFFF"):
        """Create a section widget with title and specified color"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 5px;
            border-bottom: 2px solid {text_color};
            color: {text_color};
        """)
        layout.addWidget(title_label)
        return section

    def add_line_item(self, section, name, amount, is_total=False, text_color=None):
        """Add a line item to a section with color coding.
        Revenue items are green, expense items are red."""
        if text_color is None:
            if "revenue" in section.layout().itemAt(0).widget().text().lower():
                text_color = "#50C878"  # Green for revenue
            else:
                text_color = "#FF6B6B"  # Red for expenses

        if is_total:
            # Create a wrapper widget for the total
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            wrapper_layout.setSpacing(0)  # Remove spacing

            # --- Top Border Line ---
            top_line = QWidget()
            top_line.setFixedHeight(1)  # Set a fixed height for the line
            top_line.setStyleSheet(f"background-color: {text_color};")  # Set the line color to match text
            wrapper_layout.addWidget(top_line)

            item = QWidget()
            layout = QHBoxLayout(item)
            layout.setContentsMargins(0, 5, 0, 5)

            name_label = QLabel(format_table_name(name))
            amount_label = QLabel(f"$ {abs(amount):.2f}")
            amount_label.setAlignment(Qt.AlignRight)
            amount_label.setStyleSheet(f"""
                font-family: 'Consolas', monospace;
                font-weight: bold;
                color: {text_color};
            """)
            
            name_label.setStyleSheet(f"font-weight: bold; color: {text_color};")

            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(amount_label)

            wrapper_layout.addWidget(item)

            # --- Bottom Border Line ---
            bottom_line = QWidget()
            bottom_line.setFixedHeight(1)  # Set a fixed height for the line
            bottom_line.setStyleSheet(f"background-color: {text_color};")  # Set the line color to match text
            wrapper_layout.addWidget(bottom_line)

            section.layout().addWidget(wrapper)  # Add the wrapper
            return amount  # Return the actual amount, not abs value

        else:
            # Regular line item (no wrapper needed)
            item = QWidget()
            layout = QHBoxLayout(item)
            layout.setContentsMargins(0, 5, 0, 5)

            name_label = QLabel(format_table_name(name))
            amount_label = QLabel(f"$ {abs(amount):.2f}")
            amount_label.setAlignment(Qt.AlignRight)
            amount_label.setStyleSheet(f"""
                font-family: 'Consolas', monospace;
                color: {text_color};
            """)
            
            name_label.setStyleSheet(f"color: {text_color};")

            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(amount_label)

            section.layout().addWidget(item)
            return amount  # Return the actual amount, not abs value

    def apply_styles(self):
        """Apply global styles to the window."""
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

    def select_period(self):
        """Opens period selection dialog"""
        crud = GenericCRUD("accounting_periods")
        period = crud.open_search(field_type='generic', parent=self.main_window)

        if period:
            self.start_date = period.get('start_date')
            self.end_date = period.get('end_date')
            self.period_display.setText(f"For the Period {self.start_date} to {self.end_date}")
            self.generate_report()

    def generate_report(self):
        """Generates and displays the income statement with color coding"""
        if not self.start_date or not self.end_date:
            QMessageBox.warning(self, "Error", "Please select an accounting period.")
            return

        try:
            # Clear previous content
            while self.revenue_section.layout().count() > 1:  # Keep the title
                item = self.revenue_section.layout().takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
            while self.expenses_section.layout().count() > 1:
                item = self.expenses_section.layout().takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
                    
            # Clear the existing Net Income widget if it exists
            if hasattr(self, 'net_income_wrapper'):
                if self.content_layout.indexOf(self.net_income_wrapper) != -1:
                    self.content_layout.removeWidget(self.net_income_wrapper)
                    self.net_income_wrapper.deleteLater()

            # Use the core function to ensure consistent calculations
            report_data = generate_income_statement_data(self.start_date, self.end_date)

            if report_data:
                # Add Revenue items with green color
                revenue_color = "#50C878"  # Green for revenue
                total_revenue = 0
                for account, amount in report_data['Revenues']:
                    self.add_line_item(self.revenue_section, account, amount, text_color=revenue_color)
                    total_revenue += amount
                self.add_line_item(self.revenue_section, "Total Revenue", total_revenue, is_total=True, text_color=revenue_color)

                # Add Expense items with red color
                expense_color = "#FF6B6B"  # Red for expenses
                total_expenses = 0
                for account, amount in report_data['Expenses']:
                    self.add_line_item(self.expenses_section, account, amount, text_color=expense_color)
                    total_expenses += amount
                self.add_line_item(self.expenses_section, "Total Expenses", total_expenses, is_total=True, text_color=expense_color)

                # Get Net Income directly from the report data
                net_income = report_data['Net Income']
                
                # Determine color based on whether it's income or loss
                net_color = "#50C878" if net_income >= 0 else "#FF6B6B"  # Green for profit, red for loss

                # Create a new net income widget
                self.net_income_wrapper = QWidget()
                wrapper_layout = QVBoxLayout(self.net_income_wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.setSpacing(0)

                # Top Line
                top_line = QWidget()
                top_line.setFixedHeight(2)  # Slightly thicker for emphasis
                top_line.setStyleSheet(f"background-color: {net_color};")
                wrapper_layout.addWidget(top_line)

                # Net Income Widget
                self.net_income_widget = QWidget()
                net_income_layout = QHBoxLayout(self.net_income_widget)
                net_income_layout.setContentsMargins(0, 8, 0, 8)  # More padding for emphasis
                
                # Set appropriate label based on whether net income is positive or negative
                self.net_income_label = QLabel("NET INCOME" if net_income >= 0 else "NET LOSS")
                self.net_income_amount = QLabel(f"$ {abs(net_income):.2f}")
                
                # Style the labels with proper color
                self.net_income_label.setStyleSheet(f"""
                    font-weight: bold;
                    color: {net_color};
                    font-size: 16px;
                """)
                self.net_income_amount.setStyleSheet(f"""
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                    color: {net_color};
                    font-size: 16px;
                """)
                
                net_income_layout.addWidget(self.net_income_label)
                net_income_layout.addStretch()
                net_income_layout.addWidget(self.net_income_amount)
                
                wrapper_layout.addWidget(self.net_income_widget)

                # Bottom Line
                bottom_line = QWidget()
                bottom_line.setFixedHeight(2)  # Slightly thicker for emphasis
                bottom_line.setStyleSheet(f"background-color: {net_color};")
                wrapper_layout.addWidget(bottom_line)

                # Add the wrapper to the content layout
                self.content_layout.addWidget(self.net_income_wrapper)

            else:
                QMessageBox.warning(self, "Report Generation", "No data found for the selected period.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def show_report_on_main_window(self):
        self.main_window.setCentralWidget(self)