# recurring_transactions/create_recurring_transaction.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog, QComboBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import QDate
from data.create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name
from datetime import datetime, date, timedelta

class CreateRecurringTransactionWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Create Recurring Transaction")
        self.db_manager = DatabaseManager()
        self.selected_debit_account = None
        self.selected_credit_account = None
        self.init_ui()

    def init_ui(self):
      layout = QVBoxLayout(self)

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
      self.frequency_fields_layout = QHBoxLayout()  # Layout for dynamic fields
      layout.addLayout(self.frequency_fields_layout)
      self.update_frequency_fields()  # to show on load

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
      self.confirm_button = QPushButton("Confirm")
      self.confirm_button.clicked.connect(self.create_recurring_transaction)
      layout.addWidget(self.confirm_button)

      self.setLayout(layout)

    def toggle_end_date(self):
        """Enables/Disables the end date selection based on radio button."""
        enable = self.select_end_date_radio.isChecked()
        self.end_date_input.setEnabled(enable)
        self.end_date_button.setEnabled(enable)
        if not enable:
            self.end_date_input.clear()  # Clear the date if disabled


    def select_account(self, account_type):
      search_dialog = AdvancedSearchDialog(
          field_type='generic',
          parent=self,
          db_path=self.db_manager.db_path,
          table_name='accounts'
          # No additional_filter here;  all account types are allowed.
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

        # Clear existing dynamic fields
        for i in reversed(range(self.frequency_fields_layout.count())):
            widget = self.frequency_fields_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Create new fields based on the selected frequency
        if frequency == "days":
            self.interval_label = QLabel("Interval (days):")
            self.interval_input = QLineEdit()
            self.frequency_fields_layout.addWidget(self.interval_label)
            self.frequency_fields_layout.addWidget(self.interval_input)
        else:
            # Initialize to None for other frequencies
            self.interval_label = None
            self.interval_input = None

    def create_recurring_transaction(self):
      # Validation
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
              # Insert into recurring_transactions
              db.cursor.execute(
                  """
                  INSERT INTO recurring_transactions (
                      description, debited, credited, amount, frequency, interval, start_date, end_date
                  )
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                  """,
                  (description, debited_account_id, credited_account_id, amount,
                   frequency, interval, start_date_str, end_date_str)
              )
              recurring_transaction_id = db.cursor.lastrowid

              # --- Calculate and Create Future Transactions ---
              current_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
              if end_date_str:
                  end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
              else:
                  end_date = date.today() + timedelta(days=365*70)  # 70 years from now

              while current_date <= end_date:
                  # Insert into future_transactions
                  db.cursor.execute(
                      """
                      INSERT INTO future_transactions (date, description, debited, credited, amount)
                      VALUES (?, ?, ?, ?, ?)
                      """,
                      (current_date.strftime('%Y-%m-%d'), description, debited_account_id,
                       credited_account_id, amount)
                  )

                  # Advance to the next date based on frequency
                  if frequency == "daily":
                      current_date += timedelta(days=1)
                  elif frequency == "weekly":
                      current_date += timedelta(weeks=1)
                  elif frequency == "monthly":
                      # Get the original day, but limit it to the max days in the target month
                      year = current_date.year + (1 if current_date.month == 12 else 0)
                      month = 1 if current_date.month == 12 else current_date.month + 1
                      
                      # Calculate the last day of the target month
                      if month == 2:  # February
                          last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
                      elif month in [4, 6, 9, 11]:  # 30-day months
                          last_day = 30
                      else:  # 31-day months
                          last_day = 31
                      
                      # Use the original day, but don't exceed the last day of the month
                      day = min(current_date.day, last_day)
                      current_date = date(year, month, day)
                  elif frequency == "yearly":
                      # Get original month and day
                      original_month = current_date.month
                      original_day = current_date.day
                      
                      # Handle Feb 29 for non-leap years
                      if original_month == 2 and original_day == 29:
                          next_year = current_date.year + 1
                          if not (next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0)):
                              original_day = 28
                      
                      current_date = date(current_date.year + 1, original_month, original_day)
                  elif frequency == "days":
                      current_date += timedelta(days=interval)

              db.commit()
              QMessageBox.information(self, "Success", "Recurring transaction created successfully!")
              self.close()

      except sqlite3.Error as e:
          QMessageBox.critical(self, "Database Error", str(e))
      except Exception as e:
          QMessageBox.critical(self, "Error", str(e)) # other errors