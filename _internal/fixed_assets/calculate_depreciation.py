# fixed_assets/calculate_depreciation.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QMessageBox, QDateEdit, QDialog)
from PySide6.QtCore import QDate
from create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.depreciation_methods import calculate_depreciation  # Import
from datetime import datetime, date, timedelta
import json, os

class CalculateDepreciationWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Calculate Depreciation")
        self.db_manager = DatabaseManager()
        self.settings_file = os.path.join("data", "depreciation_account.json")
        self.selected_asset = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Select Asset
        self.select_asset_button = QPushButton("Select Asset")
        self.select_asset_button.clicked.connect(self.select_asset)
        self.selected_asset_label = QLabel("Selected Asset: None")

        layout.addWidget(self.select_asset_button)
        layout.addWidget(self.selected_asset_label)

        # Select Calculation Date
        self.date_label = QLabel("Calculate Depreciation Up To:")
        self.calculation_date_edit = QDateEdit(QDate.currentDate())
        self.calculation_date_edit.setCalendarPopup(True)
        self.calculation_date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self.date_label)
        layout.addWidget(self.calculation_date_edit)

        # Calculate Button
        self.calculate_button = QPushButton("Calculate and Schedule Depreciation")
        self.calculate_button.clicked.connect(self.calculate_and_schedule)
        self.calculate_button.setEnabled(False)
        layout.addWidget(self.calculate_button)

        # Results (use QLabel for now)
        self.results_label = QLabel("Depreciation Results will appear here.")
        layout.addWidget(self.results_label)
        self.setLayout(layout)

    def select_asset(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='fixed_assets'
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_asset = selected
                self.selected_asset_label.setText(f"Selected Asset: {selected['asset_name']} (ID: {selected['asset_id']})")
                self.calculate_button.setEnabled(True)  # Enable button
            else:
                self.selected_asset = None
                self.selected_asset_label.setText("Selected Asset: None")
                self.calculate_button.setEnabled(False) # Disable button


    def calculate_and_schedule(self):
        if not self.selected_asset:
            QMessageBox.warning(self, "Error", "Please select an asset.")
            return

        calculation_date = self.calculation_date_edit.date().toPython()

        try:
            with self.db_manager as db:
                # --- 1. Fetch Asset Details ---
                db.cursor.execute("SELECT * FROM fixed_assets WHERE asset_id = ?", (self.selected_asset['asset_id'],))
                asset = db.cursor.fetchone()
                if not asset:
                    QMessageBox.warning(self, "Error", "Asset not found.")
                    return

                # --- 2. Fetch Existing Depreciation Schedule ---
                db.cursor.execute("""SELECT * FROM depreciation_schedule
                                     WHERE asset_id = ? ORDER BY period_end_date""",
                                  (asset['asset_id'],))
                depreciation_schedule = db.cursor.fetchall()

                # --- 3. Determine Start Date for Calculations ---
                if depreciation_schedule:
                    # Continue from the day *after* the last depreciation
                    last_depreciation_date = datetime.strptime(depreciation_schedule[-1]['period_end_date'], '%Y-%m-%d').date()
                    start_date = date(last_depreciation_date.year, last_depreciation_date.month, 1) # first of the month
                    current_book_value = depreciation_schedule[-1]['book_value'] #get from db
                    start_date = start_date.replace(day=1) # first day of the month

                    if (start_date.year, start_date.month) > (calculation_date.year, calculation_date.month):
                        QMessageBox.information(self, "Nothing to calculate", "Depreciation already calculated up to date for this asset")
                        return
                    # advance to the next month
                    if start_date.month == 12:
                        start_date = date(start_date.year + 1, 1, 1)
                    else:
                         start_date = date(start_date.year, start_date.month + 1, 1)



                else:
                    # Start from the purchase date (first depreciation)
                    start_date = datetime.strptime(asset['purchase_date'], '%Y-%m-%d').date()
                    current_book_value = asset['original_cost']

                # --- 4. Load Depreciation Expense Account ID ---
                if not os.path.exists(self.settings_file):
                    QMessageBox.critical(self, "Error", "Depreciation expense account not set.  Please configure it in Fixed Asset Settings.")
                    return
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                depreciation_account_id = settings.get("depreciation_account_id")
                if not depreciation_account_id:
                    QMessageBox.critical(self, "Error", "Depreciation expense account not set in Fixed Asset Settings.")
                    return

                # --- 5. Depreciation Calculation and Scheduling Loop ---
                accumulated_depreciation = 0  # Initialize
                if depreciation_schedule:  # if is not the first time calculating
                  accumulated_depreciation = depreciation_schedule[-1]['accumulated_depreciation']
                current_date = start_date
                while (current_date.year, current_date.month) <= (calculation_date.year, calculation_date.month):
                    # Calculate end of current month
                    if current_date.month == 12:
                        next_month = 1
                        next_year = current_date.year + 1
                    else:
                        next_month = current_date.month + 1
                        next_year = current_date.year

                    period_end_date = date(next_year, next_month, 1) - timedelta(days=1) # last day of the current month.

                    # Calculate depreciation for the period
                    depreciation_amount, error = calculate_depreciation(
                        asset['depreciation_method'],
                        asset['original_cost'],
                        asset['salvage_value'],
                        life=asset['useful_life_years'],
                        rate=asset['depreciation_rate'],
                        total_units=asset['total_estimated_units'],
                        current_book_value=current_book_value,
                        period = (current_date.year - datetime.strptime(asset['purchase_date'],'%Y-%m-%d').date().year) * 12 + (current_date.month - datetime.strptime(asset['purchase_date'],'%Y-%m-%d').date().month) + 1 # calculate months that have passed

                    )
                    if error:
                        QMessageBox.critical(self, "Depreciation Calculation Error", error)
                        return # stops if there is an error.

                    if asset['depreciation_method'] != "Units of Production":
                      depreciation_amount = depreciation_amount/12

                    accumulated_depreciation += depreciation_amount
                    current_book_value -= depreciation_amount

                    # Ensure book value doesn't go below salvage
                    current_book_value = max(current_book_value, asset['salvage_value'])
                    if current_book_value == asset['salvage_value']:
                        depreciation_amount = 0

                    # --- 6. Insert into 'depreciation_schedule' ---
                    db.cursor.execute(
                        """
                        INSERT INTO depreciation_schedule (
                            asset_id, period_start_date, period_end_date,
                            depreciation_expense, accumulated_depreciation, book_value
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (asset['asset_id'], current_date.strftime('%Y-%m-%d'), period_end_date.strftime('%Y-%m-%d'),
                         depreciation_amount, accumulated_depreciation, current_book_value)
                    )
                    schedule_id = db.cursor.lastrowid
                    # --- 7. Create Transaction in 'future_transactions' ---
                    db.cursor.execute(
                        """
                        INSERT INTO future_transactions (date, description, debited, credited, amount)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (current_date.strftime('%Y-%m-%d'), f"Depreciation - {asset['asset_name']}",
                         depreciation_account_id, asset['account_id'], depreciation_amount)
                    )

                    transaction_id = db.cursor.lastrowid
                    # --- 8. update transaction id ---
                    db.cursor.execute(
                        "UPDATE depreciation_schedule SET transaction_id = ? WHERE schedule_id = ?",
                        (transaction_id, schedule_id)
                    )

                    # Move to the next month
                    current_date = date(next_year, next_month, 1)  # First day of next month
                    if current_book_value == asset['salvage_value']:
                      break; # stops calculating if book value reaches salvage value

                db.commit()
                QMessageBox.information(self, "Success", "Depreciation calculated and scheduled successfully!")
                self.close()

        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))