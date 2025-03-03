# recurring_transactions/new_recurring_transaction_from_template.py

import sqlite3
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QComboBox, QRadioButton, 
                               QButtonGroup, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import QDate
from create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from datetime import datetime, date, timedelta

class CreateRecurringTransactionFromTemplateWindow(QDialog):  # Fix 1: Use QDialog instead of QWidget
    def __init__(self, main_window):
        super().__init__(parent=main_window)  # Set parent to main_window
        self.main_window = main_window
        self.setWindowTitle("Create Recurring Transaction from Template")
        self.db_manager = DatabaseManager()
        self.selected_template = None
        self.template_transactions = []
        self.init_ui()

    def init_ui(self):
        self.setMinimumSize(800, 600)  # Set a reasonable minimum size
        layout = QVBoxLayout(self)

        # Template Selection
        template_layout = QHBoxLayout()
        self.template_label = QLabel("Template:")
        self.template_input = QLineEdit()
        self.template_input.setReadOnly(True)
        self.template_button = QPushButton("Select Template")
        self.template_button.clicked.connect(self.select_template)
        template_layout.addWidget(self.template_label)
        template_layout.addWidget(self.template_input)
        template_layout.addWidget(self.template_button)
        layout.addLayout(template_layout)

        # Transactions Preview Table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(4)
        self.transactions_table.setHorizontalHeaderLabels(["Description", "Debited Account", "Credited Account", "Amount"])
        self.transactions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.transactions_table)

        # Frequency
        frequency_layout = QHBoxLayout()
        self.frequency_label = QLabel("Frequency:")
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["daily", "weekly", "monthly", "yearly", "days"])
        self.frequency_combo.currentTextChanged.connect(self.update_frequency_fields)
        frequency_layout.addWidget(self.frequency_label)
        frequency_layout.addWidget(self.frequency_combo)
        layout.addLayout(frequency_layout)

        # Dynamic Frequency Fields (Interval)
        self.frequency_fields_layout = QHBoxLayout()
        layout.addLayout(self.frequency_fields_layout)
        self.update_frequency_fields()

        # Start Date
        start_date_layout = QHBoxLayout()
        self.start_date_label = QLabel("Start Date:")
        self.start_date_input = QLineEdit()
        self.start_date_input.setReadOnly(True)
        self.start_date_button = QPushButton("Select Date")
        self.start_date_button.clicked.connect(self.select_start_date)
        start_date_layout.addWidget(self.start_date_label)
        start_date_layout.addWidget(self.start_date_input)
        start_date_layout.addWidget(self.start_date_button)
        layout.addLayout(start_date_layout)

        # End Date
        end_date_layout = QHBoxLayout()
        self.end_date_label = QLabel("End Date:")
        self.end_date_input = QLineEdit()
        self.end_date_input.setReadOnly(True)
        self.end_date_button = QPushButton("Select Date")
        self.end_date_button.clicked.connect(self.select_end_date)
        self.no_end_date_radio = QRadioButton("No End Date")
        self.no_end_date_radio.setChecked(True)
        self.select_end_date_radio = QRadioButton("Select End Date")
        self.end_date_group = QButtonGroup(self)
        self.end_date_group.addButton(self.no_end_date_radio)
        self.end_date_group.addButton(self.select_end_date_radio)
        self.end_date_group.buttonClicked.connect(self.toggle_end_date)
        end_date_layout.addWidget(self.end_date_label)
        end_date_layout.addWidget(self.end_date_input)
        end_date_layout.addWidget(self.end_date_button)
        layout.addLayout(end_date_layout)

        end_date_options_layout = QHBoxLayout()
        end_date_options_layout.addWidget(self.no_end_date_radio)
        end_date_options_layout.addWidget(self.select_end_date_radio)
        layout.addLayout(end_date_options_layout)

        self.end_date_button.setEnabled(False)
        self.end_date_input.setEnabled(False)

        # Confirm Button
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.create_recurring_transactions)
        layout.addWidget(self.confirm_button)

    def toggle_end_date(self):
        enable = self.select_end_date_radio.isChecked()
        self.end_date_input.setEnabled(enable)
        self.end_date_button.setEnabled(enable)
        if not enable:
            self.end_date_input.clear()

    def select_template(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='transaction_templates'
        )
        if search_dialog.exec() == QDialog.Accepted:
            self.selected_template = search_dialog.get_selected_item()
            if self.selected_template:
                self.template_input.setText(self.selected_template['name'])
                self.load_template_transactions()

    def load_template_transactions(self):
        with self.db_manager as db:
            db.cursor.execute("""
                SELECT tt.description, da.name AS debit_name, da.code AS debit_code,
                       ca.name AS credit_name, ca.code AS credit_code, ttd.amount
                FROM template_transactions tt
                JOIN template_transaction_details ttd ON tt.id = ttd.template_transaction_id
                JOIN accounts da ON ttd.debited = da.id
                JOIN accounts ca ON ttd.credited = ca.id
                WHERE tt.template_id = ?
            """, (self.selected_template['id'],))
            self.template_transactions = db.cursor.fetchall()

        self.transactions_table.setRowCount(len(self.template_transactions))
        for row, trans in enumerate(self.template_transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(trans['description']))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(f"{trans['debit_name']} ({trans['debit_code']})"))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(f"{trans['credit_name']} ({trans['credit_code']})"))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(str(trans['amount'])))

    def select_start_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.start_date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def select_end_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.end_date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def update_frequency_fields(self):
        frequency = self.frequency_combo.currentText()
        for i in reversed(range(self.frequency_fields_layout.count())):
            widget = self.frequency_fields_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if frequency == "days":
            self.interval_label = QLabel("Interval (days):")
            self.interval_input = QLineEdit()
            self.frequency_fields_layout.addWidget(self.interval_label)
            self.frequency_fields_layout.addWidget(self.interval_input)

    def create_recurring_transactions(self):
        if not self.selected_template or not self.template_transactions:
            QMessageBox.warning(self, "Error", "Please select a template with transactions.")
            return
        if not self.start_date_input.text():
            QMessageBox.warning(self, "Error", "Please select a start date.")
            return

        frequency = self.frequency_combo.currentText()
        interval = int(self.interval_input.text()) if frequency == "days" else None
        start_date_str = self.start_date_input.text()
        end_date_str = self.end_date_input.text() if self.select_end_date_radio.isChecked() else None

        try:
            with self.db_manager as db:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today() + timedelta(days=365*70)

                for trans in self.template_transactions:
                    # Get account IDs from template data
                    db.cursor.execute("SELECT id FROM accounts WHERE code = ?", (trans['debit_code'],))
                    debited_id = db.cursor.fetchone()['id']
                    db.cursor.execute("SELECT id FROM accounts WHERE code = ?", (trans['credit_code'],))
                    credited_id = db.cursor.fetchone()['id']

                    # Insert recurring transaction
                    db.cursor.execute("""
                        INSERT INTO recurring_transactions (
                            description, debited, credited, amount, frequency, 
                            interval, start_date, end_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trans['description'], debited_id, credited_id, trans['amount'],
                        frequency, interval, start_date_str, end_date_str
                    ))
                    recurring_id = db.cursor.lastrowid

                    # Generate future transactions
                    current_date = start_date
                    while current_date <= end_date:
                        db.cursor.execute("""
                            INSERT INTO future_transactions (date, description, debited, credited, amount)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            current_date.strftime('%Y-%m-%d'), trans['description'],
                            debited_id, credited_id, trans['amount']
                        ))

                        # Calculate next date
                        if frequency == "daily":
                            current_date += timedelta(days=1)
                        elif frequency == "weekly":
                            current_date += timedelta(weeks=1)
                        elif frequency == "monthly":
                            year = current_date.year + (current_date.month == 12)
                            month = 1 if current_date.month == 12 else current_date.month + 1
                            last_day = 31 if month in [1,3,5,7,8,10,12] else 30
                            if month == 2:
                                last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
                            day = min(current_date.day, last_day)
                            current_date = date(year, month, day)
                        elif frequency == "yearly":
                            try:
                                current_date = date(current_date.year + 1, current_date.month, current_date.day)
                            except ValueError:
                                current_date = date(current_date.year + 1, current_date.month, 28)
                        elif frequency == "days":
                            current_date += timedelta(days=interval)

                db.commit()
                QMessageBox.information(self, "Success", "Recurring transactions created from template!")
                self.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))