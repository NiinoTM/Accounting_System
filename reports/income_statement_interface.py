import sqlite3
from create_database import DatabaseManager
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                              QMessageBox, QHBoxLayout, QScrollArea)
from PySide6.QtCore import Qt
from utils.crud.generic_crud import GenericCRUD
from utils.formatters import format_table_name
from PySide6.QtGui import QPalette, QColor


def generate_income_statement_data(start_date, end_date):
    """
    Generates income statement data.
    """
    db_manager = DatabaseManager()
    try:
        with db_manager as db:
            db.cursor.execute("""
                SELECT
                    a.name AS account_name,
                    at.name AS account_type,
                    SUM(CASE
                        WHEN t.debited = a.id THEN t.amount
                        WHEN t.credited = a.id THEN -t.amount
                        ELSE 0
                    END) AS balance
                FROM transactions t
                JOIN accounts a ON t.debited = a.id OR t.credited = a.id
                JOIN account_types at ON a.type_id = at.id
                WHERE t.date BETWEEN ? AND ?
                  AND at.name IN ('Revenue', 'Expense')
                GROUP BY a.name, at.name
                ORDER BY at.name, a.name
            """, (start_date, end_date))
            transactions = db.cursor.fetchall()

            revenues = []
            expenses = []
            total_revenue = 0
            total_expenses = 0

            for row in transactions:
                account_name = row['account_name']
                account_type = row['account_type']
                balance = row['balance']

                if account_type == 'Revenue':
                    revenues.append((account_name, balance))
                    total_revenue += balance
                elif account_type == 'Expense':
                    expenses.append((account_name, balance))
                    total_expenses += balance

            net_income = total_revenue - total_expenses

            return {
                'Revenues': revenues,
                'Expenses': expenses,
                'Net Income': net_income
            }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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
        self.revenue_section = self.create_section("REVENUE")
        self.content_layout.addWidget(self.revenue_section)

        # Expenses Section
        self.expenses_section = self.create_section("EXPENSES")
        self.content_layout.addWidget(self.expenses_section)

        # Net Income/Loss
        self.net_income_widget = QWidget()
        net_income_layout = QHBoxLayout(self.net_income_widget)
        self.net_income_label = QLabel("NET INCOME")
        self.net_income_amount = QLabel("$ 0.00")
        net_income_layout.addWidget(self.net_income_label)
        net_income_layout.addStretch()
        net_income_layout.addWidget(self.net_income_amount)
        self.content_layout.addWidget(self.net_income_widget)


        # Wrap content in scroll area
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)

        self.layout.addWidget(scroll)
        self.apply_styles()



    def create_section(self, title):
        """Create a section widget with title"""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 5px;
            border-bottom: 2px solid #3498db;
        """)
        layout.addWidget(title_label)
        return section

    def add_line_item(self, section, name, amount, is_total=False):
        """Add a line item to a section.  Wraps totals in a bordered widget."""
        if is_total:
            # Create a wrapper widget for the total
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            wrapper_layout.setSpacing(0)  # Remove spacing

            # --- Top Border Line ---
            top_line = QWidget()
            top_line.setFixedHeight(1)  # Set a fixed height for the line
            top_line.setStyleSheet("background-color: #555;")  # Set the line color
            wrapper_layout.addWidget(top_line)

            item = QWidget()
            layout = QHBoxLayout(item)
            layout.setContentsMargins(0, 5, 0, 5)

            name_label = QLabel(format_table_name(name))
            amount_label = QLabel(f"$ {abs(amount):.2f}")
            amount_label.setAlignment(Qt.AlignRight)
            amount_label.setStyleSheet("""
                font-family: 'Consolas', monospace;
                font-weight: bold; /* Make total amounts bold */
            """)

            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(amount_label)

            wrapper_layout.addWidget(item)

            # --- Bottom Border Line ---
            bottom_line = QWidget()
            bottom_line.setFixedHeight(1)  # Set a fixed height for the line
            bottom_line.setStyleSheet("background-color: #555;")  # Set the line color
            wrapper_layout.addWidget(bottom_line)


            section.layout().addWidget(wrapper)  # Add the wrapper
            return abs(amount)

        else:
            # Regular line item (no wrapper needed)
            item = QWidget()
            layout = QHBoxLayout(item)
            layout.setContentsMargins(0, 5, 0, 5)

            name_label = QLabel(format_table_name(name))
            amount_label = QLabel(f"$ {abs(amount):.2f}")
            amount_label.setAlignment(Qt.AlignRight)
            amount_label.setStyleSheet("""
                font-family: 'Consolas', monospace;
            """)

            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(amount_label)

            section.layout().addWidget(item)
            return abs(amount)

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
            """Generates and displays the income statement"""
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

                report_data = generate_income_statement_data(self.start_date, self.end_date)

                if report_data:
                    # Add Revenue items
                    total_revenue = 0
                    for account, amount in report_data['Revenues']:
                        self.add_line_item(self.revenue_section, account, amount)
                        total_revenue += amount
                    self.add_line_item(self.revenue_section, "Total Revenue", total_revenue, True)

                    # Add Expense items
                    total_expenses = 0
                    for account, amount in report_data['Expenses']:
                        self.add_line_item(self.expenses_section, account, amount)
                        total_expenses += amount
                    self.add_line_item(self.expenses_section, "Total Expenses", total_expenses, True)

                    # Update Net Income/Loss
                    net_income = report_data['Net Income']
                    self.net_income_label.setText("NET INCOME" if net_income >= 0 else "NET LOSS")
                    self.net_income_amount.setText(f"$ {abs(net_income):.2f}")
                    self.net_income_amount.setStyleSheet("""
                        font-family: 'Consolas', monospace;
                        font-weight: bold;
                    """)

                    # --- Wrap Net Income/Loss in a bordered widget (CORRECTED) ---
                    wrapper = QWidget()
                    wrapper_layout = QVBoxLayout(wrapper)
                    wrapper_layout.setContentsMargins(0, 0, 0, 0)
                    wrapper_layout.setSpacing(0)

                    # Top Line
                    top_line = QWidget()
                    top_line.setFixedHeight(1)
                    top_line.setStyleSheet("background-color: #555;")
                    wrapper_layout.addWidget(top_line)  # Add top line

                    # Add the existing net_income_widget
                    wrapper_layout.addWidget(self.net_income_widget)

                    # Bottom Line
                    bottom_line = QWidget()
                    bottom_line.setFixedHeight(1)
                    bottom_line.setStyleSheet("background-color: #555;")
                    wrapper_layout.addWidget(bottom_line) # Add bottom line

                    self.content_layout.addWidget(wrapper) #add wrapper to layout


                else:
                    QMessageBox.warning(self, "Report Generation", "No data found for the selected period.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")

    def show_report_on_main_window(self):
        self.main_window.setCentralWidget(self)