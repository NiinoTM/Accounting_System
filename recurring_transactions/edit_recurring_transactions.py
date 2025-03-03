# edit_recurring_transactions.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog, QComboBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import QDate
from data.create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from datetime import datetime, date, timedelta

class EditRecurringTransactionWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Edit Recurring Transaction")
        self.db_manager = DatabaseManager()
        self.selected_recurring_transaction_id = None
        self.selected_debit_account = None
        self.selected_credit_account = None
        self.interval_input = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Select Recurring Transaction
        select_recurring_layout = QHBoxLayout()
        self.select_recurring_label = QLabel("Recurring Transaction to Edit:")
        self.select_recurring_input = QLineEdit()
        self.select_recurring_input.setReadOnly(True)
        self.select_recurring_button = QPushButton("Select Recurring Transaction")
        self.select_recurring_button.clicked.connect(self.select_recurring_transaction)
        select_recurring_layout.addWidget(self.select_recurring_label)
        select_recurring_layout.addWidget(self.select_recurring_input)
        select_recurring_layout.addWidget(self.select_recurring_button)
        layout.addLayout(select_recurring_layout)

        # Description
        description_layout = QHBoxLayout()
        self.description_label = QLabel("Description:")
        self.description_input = QLineEdit()
        description_layout.addWidget(self.description_label)
        description_layout.addWidget(self.description_input)
        layout.addLayout(description_layout)

        # Debited Account
        debited_layout = QHBoxLayout()
        self.debited_label = QLabel("Debited Account:")
        self.debited_input = QLineEdit()
        self.debited_input.setReadOnly(True)
        self.debited_button = QPushButton("Select")
        self.debited_button.clicked.connect(lambda: self.select_account("debited"))
        debited_layout.addWidget(self.debited_label)
        debited_layout.addWidget(self.debited_input)
        debited_layout.addWidget(self.debited_button)
        layout.addLayout(debited_layout)

        # Credited Account
        credited_layout = QHBoxLayout()
        self.credited_label = QLabel("Credited Account:")
        self.credited_input = QLineEdit()
        self.credited_input.setReadOnly(True)
        self.credited_button = QPushButton("Select")
        self.credited_button.clicked.connect(lambda: self.select_account("credited"))
        credited_layout.addWidget(self.credited_label)
        credited_layout.addWidget(self.credited_input)
        credited_layout.addWidget(self.credited_button)
        layout.addLayout(credited_layout)

        # Amount
        amount_layout = QHBoxLayout()
        self.amount_label = QLabel("Amount:")
        self.amount_input = QLineEdit()
        amount_layout.addWidget(self.amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)

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

        # End Date (Optional - Radio Buttons for selection)
        end_date_layout = QHBoxLayout()
        self.end_date_label = QLabel("End Date:")
        self.end_date_input = QLineEdit()
        self.end_date_input.setReadOnly(True)
        self.end_date_button = QPushButton("Select Date")
        self.end_date_button.clicked.connect(self.select_end_date)

        self.no_end_date_radio = QRadioButton("No End Date")
        self.no_end_date_radio.setChecked(True)  # Default to no end date
        self.select_end_date_radio = QRadioButton("Select End Date")
        # Group the radio buttons so only one can be selected at a time
        self.end_date_group = QButtonGroup(self)
        self.end_date_group.addButton(self.no_end_date_radio)
        self.end_date_group.addButton(self.select_end_date_radio)
        self.end_date_group.buttonClicked.connect(self.toggle_end_date) # Connect group

        end_date_layout.addWidget(self.end_date_label)
        end_date_layout.addWidget(self.end_date_input)
        end_date_layout.addWidget(self.end_date_button)
        layout.addLayout(end_date_layout)

        end_date_options_layout = QHBoxLayout()
        end_date_options_layout.addWidget(self.no_end_date_radio)
        end_date_options_layout.addWidget(self.select_end_date_radio)
        layout.addLayout(end_date_options_layout)

        self.end_date_button.setEnabled(False) # disable by default
        self.end_date_input.setEnabled(False)

        # Confirm Button
        self.confirm_button = QPushButton("Confirm Edit")
        self.confirm_button.clicked.connect(self.edit_recurring_transaction)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)
        self.disable_fields_for_no_selection()

    def disable_fields_for_no_selection(self):
        self.description_input.setEnabled(False)
        self.debited_button.setEnabled(False)
        self.debited_input.setEnabled(False)
        self.credited_button.setEnabled(False)
        self.credited_input.setEnabled(False)
        self.amount_input.setEnabled(False)
        self.frequency_combo.setEnabled(False)
        # Check if interval_input is initialized before trying to use it
        if self.interval_input:
            self.interval_input.setEnabled(False)
        self.start_date_button.setEnabled(False)
        self.start_date_input.setEnabled(False)
        self.end_date_button.setEnabled(False)
        self.end_date_input.setEnabled(False)
        self.no_end_date_radio.setEnabled(False)
        self.select_end_date_radio.setEnabled(False)
        self.confirm_button.setEnabled(False)

    def enable_fields_for_selection(self):
        self.description_input.setEnabled(True)
        self.debited_button.setEnabled(True)
        self.debited_input.setEnabled(True)
        self.credited_button.setEnabled(True)
        self.credited_input.setEnabled(True)
        self.amount_input.setEnabled(True)
        self.frequency_combo.setEnabled(True)
        if self.interval_input:
            self.interval_input.setEnabled(True)
        self.start_date_button.setEnabled(True)
        self.start_date_input.setEnabled(True)
        self.end_date_button.setEnabled(True)
        self.end_date_input.setEnabled(True)
        self.no_end_date_radio.setEnabled(True)
        self.select_end_date_radio.setEnabled(True)
        self.confirm_button.setEnabled(True)

    def populate_fields(self, recurring_transaction_data):
        self.selected_recurring_transaction_id = recurring_transaction_data['id']
        self.description_input.setText(recurring_transaction_data['description'])

        # Fetch and set debited account name and code
        with self.db_manager as db:
            db.cursor.execute("SELECT name, code FROM accounts WHERE id = ?", (recurring_transaction_data['debited'],))
            debited_account = db.cursor.fetchone()
            if debited_account:
                self.selected_debit_account = {'id': recurring_transaction_data['debited'], 'name': debited_account['name'], 'code': debited_account['code']}
                self.debited_input.setText(f"{debited_account['name']} ({debited_account['code']})")
            else:
                self.debited_input.clear()
                self.selected_debit_account = None

            # Fetch and set credited account name and code
            db.cursor.execute("SELECT name, code FROM accounts WHERE id = ?", (recurring_transaction_data['credited'],))
            credited_account = db.cursor.fetchone()
            if credited_account:
                self.selected_credit_account = {'id': recurring_transaction_data['credited'], 'name': credited_account['name'], 'code': credited_account['code']}
                self.credited_input.setText(f"{credited_account['name']} ({credited_account['code']})")
            else:
                self.credited_input.clear()
                self.selected_credit_account = None

        self.amount_input.setText(str(recurring_transaction_data['amount']))
        self.frequency_combo.setCurrentText(recurring_transaction_data['frequency'])
        if recurring_transaction_data['frequency'] == 'days' and recurring_transaction_data['interval'] is not None:
            self.interval_input = self.interval_input if hasattr(self, 'interval_input') and self.interval_input else QLineEdit() # Ensure interval_input exists
            self.interval_input.setText(str(recurring_transaction_data['interval']))
            if not hasattr(self, 'interval_label'): # Create label if it doesn't exist
                self.interval_label = QLabel("Interval (days):")
                self.frequency_fields_layout.addWidget(self.interval_label)
                self.frequency_fields_layout.addWidget(self.interval_input)

        else:
            self.update_frequency_fields() # to ensure interval field is hidden if frequency is not 'days'

        self.start_date_input.setText(recurring_transaction_data['start_date'])
        if recurring_transaction_data['end_date']:
            self.select_end_date_radio.setChecked(True)
            self.no_end_date_radio.setChecked(False)
            self.end_date_input.setEnabled(True)
            self.end_date_button.setEnabled(True)
            self.end_date_input.setText(recurring_transaction_data['end_date'])
        else:
            self.no_end_date_radio.setChecked(True)
            self.select_end_date_radio.setChecked(False)
            self.end_date_input.clear()
            self.end_date_input.setEnabled(False)
            self.end_date_button.setEnabled(False)
        self.enable_fields_for_selection()


    def select_recurring_transaction(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='recurring_transactions'
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected_transaction = search_dialog.get_selected_item()
            if selected_transaction:
                self.select_recurring_input.setText(f"Recurring Transaction ID: {selected_transaction['id']}")
                self.populate_fields(selected_transaction)


    def select_account(self, account_type):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts'
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                if account_type == "debited":
                    self.selected_debit_account = selected
                    self.debited_input.setText(f"{selected['name']} ({selected['code']})")
                elif account_type == "credited":
                    self.selected_credit_account = selected
                    self.credited_input.setText(f"{selected['name']} ({selected['code']})")

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
            self.interval_input = QLineEdit() # Now interval_input will be created if frequency is days
            self.frequency_fields_layout.addWidget(self.interval_label)
            self.frequency_fields_layout.addWidget(self.interval_input)
        else:
            self.interval_label = None
            self.interval_input = None # Set to None when not 'days' frequency

    def toggle_end_date(self):
        enable = self.select_end_date_radio.isChecked()
        self.end_date_input.setEnabled(enable)
        self.end_date_button.setEnabled(enable)
        if not enable:
            self.end_date_input.clear()

    def edit_recurring_transaction(self):
        if self.selected_recurring_transaction_id is None:
            QMessageBox.warning(self, "Error", "No recurring transaction selected for editing.")
            return

        # Validation (No changes here)
        if not all([self.description_input.text(), self.debited_input.text(),
                    self.credited_input.text(), self.amount_input.text(),
                    self.start_date_input.text()]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields.")
            return

        try:
            amount = float(self.amount_input.text())
            if amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid amount.")
            return

        description = self.description_input.text().strip()
        debited_account_id = self.selected_debit_account['id']
        credited_account_id = self.selected_credit_account['id']
        frequency = self.frequency_combo.currentText()
        interval = None
        if frequency == "days":
            try:
                interval = int(self.interval_input.text())
                if interval <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Error", "Please enter a valid interval (positive integer).")
                return

        start_date_str = self.start_date_input.text()
        end_date_str = self.end_date_input.text() if self.select_end_date_radio.isChecked() else None

        try:
            with self.db_manager as db:
                # --- Fetch original details BEFORE UPDATE ---
                db.cursor.execute("SELECT description, debited, credited FROM recurring_transactions WHERE id = ?", (self.selected_recurring_transaction_id,))
                original_transaction_data = db.cursor.fetchone()
                if original_transaction_data:
                    original_description = original_transaction_data['description']
                    original_debited_id = original_transaction_data['debited']
                    original_credited_id = original_transaction_data['credited']
                else:
                    QMessageBox.critical(self, "Database Error", "Could not retrieve original transaction details.")
                    return

                # Update recurring_transactions table (No changes here)
                db.cursor.execute(
                    """
                    UPDATE recurring_transactions
                    SET description = ?, debited = ?, credited = ?, amount = ?,
                        frequency = ?, interval = ?, start_date = ?, end_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (description, debited_account_id, credited_account_id, amount,
                     frequency, interval, start_date_str, end_date_str, self.selected_recurring_transaction_id)
                )

                # --- Delete ALL existing future transactions related to THIS recurring transaction ---
                # Using original details to ensure all related future transactions are deleted
                db.cursor.execute(
                    "DELETE FROM future_transactions WHERE debited = ? AND credited = ? AND description = ?",
                    (original_debited_id, original_credited_id, original_description)
                )


                # --- Regenerate Future Transactions (No changes here) ---
                current_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                else:
                    end_date = date.today() + timedelta(days=365*70) # 70 years

                while current_date <= end_date:
                    db.cursor.execute(
                        """
                        INSERT INTO future_transactions (date, description, debited, credited, amount)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (current_date.strftime('%Y-%m-%d'), description, debited_account_id,
                         credited_account_id, amount)
                    )
                    # Advance to the next date based on frequency (same logic as before)
                    if frequency == "daily":
                        current_date += timedelta(days=1)
                    elif frequency == "weekly":
                        current_date += timedelta(weeks=1)
                    elif frequency == "monthly":
                        year = current_date.year + (1 if current_date.month == 12 else 0)
                        month = 1 if current_date.month == 12 else current_date.month + 1
                        last_day = 31 if month in [1,3,5,7,8,10,12] else 30
                        if month == 2:
                            last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
                        day = min(current_date.day, last_day)
                        current_date = date(year, month, day)
                    elif frequency == "yearly":
                        original_month = current_date.month
                        original_day = current_date.day
                        if original_month == 2 and original_day == 29:
                            next_year = current_date.year + 1
                            if not (next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0)):
                                original_day = 28
                        current_date = date(current_date.year + 1, original_month, original_day)

                    elif frequency == "days":
                        current_date += timedelta(days=interval)

                db.commit()
                QMessageBox.information(self, "Success", "Recurring transaction updated successfully and future transactions regenerated!")
                self.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))