# fixed_asset/import_fixed_asset.py

import sqlite3
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog, QComboBox)
from PySide6.QtCore import QDate
from data.create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name, normalize_text
from utils.depreciation_methods import calculate_depreciation
from datetime import datetime

class ImportFixedAssetWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Import Fixed Asset")
        self.db_manager = DatabaseManager()
        self.selected_period = None  # Store selected period
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Asset Name
        name_layout = QHBoxLayout()
        self.name_label = QLabel("Asset Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Asset Code
        code_layout = QHBoxLayout()
        self.code_label = QLabel("Asset Code:")
        self.code_input = QLineEdit()
        code_layout.addWidget(self.code_label)
        code_layout.addWidget(self.code_input)
        layout.addLayout(code_layout)


        # Purchase Date
        date_layout = QHBoxLayout()
        self.date_label = QLabel("Purchase Date:")
        self.date_input = QLineEdit()
        self.date_input.setReadOnly(True)
        self.date_button = QPushButton("Select Date")
        self.date_button.clicked.connect(self.select_date)
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(self.date_button)
        layout.addLayout(date_layout)

        # Original Cost
        cost_layout = QHBoxLayout()
        self.cost_label = QLabel("Original Cost:")
        self.cost_input = QLineEdit()
        cost_layout.addWidget(self.cost_label)
        cost_layout.addWidget(self.cost_input)
        layout.addLayout(cost_layout)

        # Salvage Value
        salvage_layout = QHBoxLayout()
        self.salvage_label = QLabel("Salvage Value:")
        self.salvage_input = QLineEdit()
        salvage_layout.addWidget(self.salvage_label)
        salvage_layout.addWidget(self.salvage_input)
        layout.addLayout(salvage_layout)

        # Depreciation Method
        method_layout = QHBoxLayout()
        self.method_label = QLabel("Depreciation Method:")
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            'Straight-Line',
            "Sum of the Years' Digit",
            'Declining Balance',
            'Double-Declining Balance',
            'Units of Production'
        ])
        self.method_combo.currentTextChanged.connect(self.update_depreciation_fields)
        method_layout.addWidget(self.method_label)
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        # --- Dynamic Fields (Useful Life, Depreciation Rate, Units) ---
        self.dynamic_fields_layout = QVBoxLayout()
        layout.addLayout(self.dynamic_fields_layout)

        # Initial setup (no fields initially)
        self.update_depreciation_fields()  # Call this to set up initial state

        # Accounting Period Selection
        period_layout = QHBoxLayout()
        self.period_label = QLabel("Accounting Period:")
        self.period_input = QLineEdit()
        self.period_input.setReadOnly(True)
        self.period_button = QPushButton("Select Period")
        self.period_button.clicked.connect(self.select_period)
        period_layout.addWidget(self.period_label)
        period_layout.addWidget(self.period_input)
        period_layout.addWidget(self.period_button)
        layout.addLayout(period_layout)


        # Import Button
        self.import_button = QPushButton("Import Asset")
        self.import_button.clicked.connect(self.import_asset)
        layout.addWidget(self.import_button)
        self.setLayout(layout)


    def select_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def select_period(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounting_periods'
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_period = selected
                self.period_input.setText(f"{selected['start_date']} - {selected['end_date']}")

    def update_depreciation_fields(self):
        method = self.method_combo.currentText()

        # Clear existing dynamic fields
        for i in reversed(range(self.dynamic_fields_layout.count())):
            widget = self.dynamic_fields_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.useful_life_label = None # reset
        self.useful_life_input = None
        self.depreciation_rate_label = None
        self.depreciation_rate_input = None
        self.units_produced_label = None
        self.units_produced_input = None
        self.total_units_label = None
        self.total_units_input = None

        if method in ('Straight-Line', "Sum of the Years' Digit"):
            self.useful_life_label = QLabel("Useful Life (Years):")
            self.useful_life_input = QLineEdit()
            self.dynamic_fields_layout.addWidget(self.useful_life_label)
            self.dynamic_fields_layout.addWidget(self.useful_life_input)

        elif method in ('Declining Balance', 'Double-Declining Balance'):
            self.useful_life_label = QLabel("Useful Life (Years):")
            self.useful_life_input = QLineEdit()
            self.depreciation_rate_label = QLabel("Depreciation Rate:")
            self.depreciation_rate_input = QLineEdit()
            self.dynamic_fields_layout.addWidget(self.useful_life_label)
            self.dynamic_fields_layout.addWidget(self.useful_life_input)
            self.dynamic_fields_layout.addWidget(self.depreciation_rate_label)
            self.dynamic_fields_layout.addWidget(self.depreciation_rate_input)


        elif method == 'Units of Production':
            self.total_units_label = QLabel("Total Estimated Units:")
            self.total_units_input = QLineEdit()
            self.dynamic_fields_layout.addWidget(self.total_units_label)
            self.dynamic_fields_layout.addWidget(self.total_units_input)

    def import_asset(self):
        # Input Validation
        if (not self.date_input.text() or not self.cost_input.text() or not self.salvage_input.text() or not self.name_input.text() or
                not self.code_input.text() or not self.selected_period):
            QMessageBox.warning(self, "Error", "Please fill in all required fields.")
            return

        try:
            original_cost = float(self.cost_input.text())
            salvage_value = float(self.salvage_input.text())
            if original_cost <= 0 or salvage_value < 0 or salvage_value >= original_cost:
                raise ValueError("Cost must be positive, and salvage value cannot be negative or greater/equal to cost.")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))  # Show specific error
            return

        asset_name = self.name_input.text().strip()
        asset_code = self.code_input.text().strip()
        purchase_date_str = self.date_input.text()  # Keep as string initially
        depreciation_method = self.method_combo.currentText()
        period_start_date_str = self.selected_period['start_date']

        # Convert dates to datetime objects for calculations
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        period_start_date = datetime.strptime(period_start_date_str, '%Y-%m-%d').date()

        # Validate purchase date is before period start
        if purchase_date > period_start_date:
            QMessageBox.warning(self, "Error", "Purchase date must be before the start of the accounting period.")
            return

        useful_life_years = None
        depreciation_rate = None
        units_produced_period = None  # Not needed at *import* time
        total_estimated_units = None

        # Dynamic field validation and value retrieval (as before)
        if depreciation_method in ('Straight-Line', "Sum of the Years' Digit"):
            try:
                useful_life_years = int(self.useful_life_input.text())
                if useful_life_years <= 0:
                    raise ValueError("Useful life must be positive.")
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Error", "Please enter a valid integer for useful life.")
                return

        elif depreciation_method in ('Declining Balance', 'Double-Declining Balance'):
            try:
                useful_life_years = int(self.useful_life_input.text())
                depreciation_rate = float(self.depreciation_rate_input.text())
                if useful_life_years <= 0 or depreciation_rate <= 0 or depreciation_rate > 1 :
                    raise ValueError("Useful life must be positive, and depreciation rate must be between 0 and 1.")
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Error", "Please enter valid values for useful life and depreciation rate.")
                return

        elif depreciation_method == 'Units of Production':
            try:
                total_estimated_units = int(self.total_units_input.text())
                if total_estimated_units <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Error", "Please enter a valid integer value for Total Estimated Units.")
                return
        try:
            with self.db_manager as db:

                # --- Create the Account ---
                db.cursor.execute(
                    """
                    INSERT INTO accounts (code, name, normalized_name, type_id, is_active)
                    VALUES (?, ?, ?, 2, 1)
                    """,
                    (asset_code, asset_name, normalize_text(asset_name))
                )
                account_id = db.cursor.lastrowid

                # --- Check for Duplicate Account (after creating the account)---
                db.cursor.execute("SELECT asset_id FROM fixed_assets WHERE account_id = ?", (account_id,))
                if db.cursor.fetchone():
                    QMessageBox.critical(self, "Error", "This account has already been imported as a fixed asset.")
                    db.conn.rollback()  # Rollback account creation
                    return

                # --- Insert into fixed_assets ---
                db.cursor.execute(
                    """
                    INSERT INTO fixed_assets (
                        asset_name, account_id, purchase_date, original_cost,
                        salvage_value, depreciation_method, useful_life_years,
                        depreciation_rate, total_estimated_units
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (asset_name, account_id, purchase_date_str, original_cost,  # Use string format
                     salvage_value, depreciation_method, useful_life_years,
                     depreciation_rate, total_estimated_units)
                )
                asset_id = db.cursor.lastrowid

                # --- Calculate Accumulated Depreciation up to Period Start ---
                accumulated_depreciation = 0.0
                current_book_value = original_cost

                # Calculate number of FULL months from purchase to period start
                months_to_depreciate = (period_start_date.year - purchase_date.year) * 12 + (period_start_date.month - purchase_date.month)
                if months_to_depreciate < 0:
                    QMessageBox.warning(self,"Error", "The period can't be prior to the purchase date")
                    return
                # Calculate depreciation for each full month
                #print(f"months {months_to_depreciate}") #for debugging
                for month in range(months_to_depreciate):

                    depreciation_for_month, error = calculate_depreciation(
                        depreciation_method,
                        original_cost,
                        salvage_value,
                        life=useful_life_years,
                        rate=depreciation_rate,
                        total_units=total_estimated_units,
                        current_book_value = current_book_value,
                        period= month + 1
                    )
                    if error:
                        QMessageBox.critical(self, "Depreciation Calculation Error", error)
                        db.conn.rollback()
                        return
                    if depreciation_method not in ["Units of Production"]:
                         depreciation_for_month = depreciation_for_month / 12
                    #print(f"dep month {depreciation_for_month}") # For debugging

                    accumulated_depreciation += depreciation_for_month
                    current_book_value -= depreciation_for_month  # Update book value

                    if current_book_value <= salvage_value:
                        current_book_value = salvage_value
                        depreciation_for_month = 0
                        break  # Stop depreciating once salvage value is reached

                # Ensure book value doesn't go below salvage
                current_book_value = max(current_book_value, salvage_value)


                # --- Insert into depreciation_schedule ---
                db.cursor.execute(
                    """
                    INSERT INTO depreciation_schedule (
                        asset_id, period_start_date, period_end_date,
                        depreciation_expense, accumulated_depreciation, book_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (asset_id, period_start_date_str, self.selected_period['end_date'],
                     0, accumulated_depreciation, current_book_value)  # 0 expense for initial entry
                )

                schedule_id = db.cursor.lastrowid


                # --- Create Initial Transaction ---
                settings_file = os.path.join("data", "owner_equity_account.json")
                if not os.path.exists(settings_file):
                    QMessageBox.critical(self, "Error", "Owner's Equity account not set.  Please configure it in Fixed Asset Settings.")
                    db.conn.rollback()
                    return

                with open(settings_file, "r") as f:
                    settings = json.load(f)
                equity_account_id = settings.get("owner_equity_account_id")
                if not equity_account_id:
                    QMessageBox.critical(self, "Error", "Owner's Equity account not set in Fixed Asset Settings.")
                    db.conn.rollback()
                    return


                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (period_start_date_str, f"{asset_name} - Imported", account_id, equity_account_id, current_book_value) # use current book
                    )

                transaction_id = db.cursor.lastrowid

                # --- update transaction id ---
                db.cursor.execute(
                    "UPDATE depreciation_schedule SET transaction_id = ? WHERE schedule_id = ?",
                    (transaction_id, schedule_id)
                )


                # --- Update Account Balances ---
                db.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (current_book_value, account_id))
                db.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (current_book_value, equity_account_id))

                db.commit()
                QMessageBox.information(self, "Success", "Fixed asset imported successfully!")
                self.close()



        except sqlite3.IntegrityError as e:
            db.conn.rollback()
            if "UNIQUE constraint failed: accounts.code" in str(e):
                QMessageBox.critical(self, "Database Error", "An account with this code already exists.")
            elif "UNIQUE constraint failed: accounts.name" in str(e):
                QMessageBox.critical(self, "Database Error", "An account with this name already exists.")
            elif "UNIQUE constraint failed: accounts.normalized_name" in str(e):
                 QMessageBox.critical(self, "Database Error", "An account with this name already exists.")
            else:
                QMessageBox.critical(self, "Database Error", str(e))


        except (sqlite3.Error, Exception) as e:
            db.conn.rollback()
            QMessageBox.critical(self, "Error", str(e))