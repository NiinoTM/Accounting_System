# fixed_assets/single_account_purchase.py

import sqlite3
import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                               QMessageBox, QHBoxLayout, QDialog, QComboBox)
from PySide6.QtCore import QDate
from create_database import DatabaseManager
from utils.crud.date_select import DateSelectWindow
from utils.crud.search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name, normalize_text
from utils.depreciation_methods import calculate_depreciation
from datetime import datetime, date, timedelta

class SingleAccountPurchaseWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Single Account Asset Purchase")
        self.db_manager = DatabaseManager()
        self.selected_account = None
        self.selected_payment_account = None  # Store selected payment account
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Asset Name, Code, Purchase Date, Original Cost, Salvage Value,
        # Depreciation Method, Dynamic Fields - These all remain the same.
        # ... (All the UI setup code from before is unchanged) ...
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
        self.update_depreciation_fields()  # Set up initially

        # Payment Account Selection
        payment_account_layout = QHBoxLayout()
        self.payment_account_label = QLabel("Payment Account:")
        self.payment_account_input = QLineEdit()
        self.payment_account_input.setReadOnly(True)
        self.payment_account_button = QPushButton("Select Account")
        self.payment_account_button.clicked.connect(self.select_payment_account)
        payment_account_layout.addWidget(self.payment_account_label)
        payment_account_layout.addWidget(self.payment_account_input)
        payment_account_layout.addWidget(self.payment_account_button)
        layout.addLayout(payment_account_layout)

        # Purchase Button
        self.purchase_button = QPushButton("Register Purchase")
        self.purchase_button.clicked.connect(self.register_purchase)
        layout.addWidget(self.purchase_button)

        self.setLayout(layout)

    def select_date(self):
        date_dialog = DateSelectWindow()
        if date_dialog.exec() == QDialog.Accepted:
            self.date_input.setText(date_dialog.calendar.selectedDate().toString('yyyy-MM-dd'))

    def select_payment_account(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts',
            additional_filter="type_id IN (1, 2, 3, 4)"  # Include Liabilities
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected = search_dialog.get_selected_item()
            if selected:
                self.selected_payment_account = selected
                self.payment_account_input.setText(f"{selected['name']} ({selected['code']})")

    def update_depreciation_fields(self):
        method = self.method_combo.currentText()

        # Clear existing dynamic fields (same as in import_fixed_asset.py)
        for i in reversed(range(self.dynamic_fields_layout.count())):
            widget = self.dynamic_fields_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.useful_life_label = None
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
    def register_purchase(self):
        # Input Validation (same as before)
        if (not self.date_input.text() or not self.cost_input.text()
                or not self.salvage_input.text() or not self.name_input.text()
                or not self.code_input.text() or not self.selected_payment_account):
            QMessageBox.warning(self, "Error", "Please fill in all required fields and select a payment account.")
            return
        try:
            original_cost = float(self.cost_input.text())
            salvage_value = float(self.salvage_input.text())
            if original_cost <= 0 or salvage_value < 0 or salvage_value >= original_cost:
                raise ValueError("Cost must be positive, and salvage value cannot be negative or greater/equal to cost.")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        asset_name = self.name_input.text().strip()
        asset_code = self.code_input.text().strip()
        purchase_date_str = self.date_input.text()
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() # turns into date object
        depreciation_method = self.method_combo.currentText()

        useful_life_years = None
        depreciation_rate = None
        total_estimated_units = None

        # Dynamic field validation and value retrieval
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
                if useful_life_years <= 0 or depreciation_rate <= 0 or depreciation_rate > 1:
                    raise ValueError
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

                # --- Check for Duplicate Account (after creating) ---
                db.cursor.execute("SELECT asset_id FROM fixed_assets WHERE account_id = ?", (account_id,))
                if db.cursor.fetchone():
                    QMessageBox.critical(self, "Error", "This account is already associated with a fixed asset.")
                    db.conn.rollback()
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
                    (asset_name, account_id, purchase_date_str, original_cost,
                     salvage_value, depreciation_method, useful_life_years,
                     depreciation_rate, total_estimated_units)
                )
                asset_id = db.cursor.lastrowid

                # --- Create Purchase Transaction ---
                description = f"{asset_name} - Purchase"
                db.cursor.execute(
                    """
                    INSERT INTO transactions (date, description, debited, credited, amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (purchase_date_str, description, account_id, self.selected_payment_account['id'], original_cost)
                )

                # --- Update Account Balances ---
                db.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (original_cost, account_id))
                db.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (original_cost, self.selected_payment_account['id']))

                # --- Schedule Future Depreciation ---
                depreciation_settings_file = os.path.join("data", "depreciation_account.json")
                if not os.path.exists(depreciation_settings_file):
                    QMessageBox.critical(self, "Error", "Depreciation account not set. Please configure in settings")
                    db.conn.rollback()
                    return
                with open(depreciation_settings_file, "r") as f:
                    dep_settings = json.load(f)
                depreciation_account_id = dep_settings.get("depreciation_account_id")
                if not depreciation_account_id:
                    QMessageBox.critical(self, "Error", "Depreciation account not set in settings.")
                    db.conn.rollback()
                    return

                current_date = purchase_date  # Start from purchase date
                current_book_value = original_cost
                accumulated_depreciation = 0
                period = 1

                while True:  # Loop until break conditions are met
                    # Calculate depreciation for the *current* month
                    depreciation_amount, error = calculate_depreciation(
                        method=depreciation_method,
                        cost=original_cost,
                        salvage_value=salvage_value,
                        life=useful_life_years,
                        rate=depreciation_rate,
                        total_units=total_estimated_units,
                        current_book_value = current_book_value,
                        period = period #send the period to calculation
                    )
                    if error:
                        QMessageBox.warning(self, "Depreciation Calculation Error", error)
                        db.conn.rollback()
                        return
                    if depreciation_method != "Units of Production":
                         depreciation_amount = depreciation_amount / 12

                    current_book_value -= depreciation_amount
                    current_book_value = max(current_book_value, salvage_value) # to avoid going less than salvage
                    accumulated_depreciation += depreciation_amount
                    # Get period end date (last day of the current month)
                    if current_date.month == 12:
                        period_end_date = date(current_date.year, 12, 31)
                    else:
                        period_end_date = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)


                    # Insert into depreciation_schedule
                    db.cursor.execute(
                        """
                        INSERT INTO depreciation_schedule (
                            asset_id, period_start_date, period_end_date,
                            depreciation_expense, accumulated_depreciation, book_value
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (asset_id, current_date.strftime('%Y-%m-%d'), period_end_date.strftime('%Y-%m-%d'),
                         depreciation_amount, accumulated_depreciation, current_book_value)
                    )
                    schedule_id = db.cursor.lastrowid

                    # Insert into future_transactions
                    db.cursor.execute(
                        """
                        INSERT INTO future_transactions (date, description, debited, credited, amount)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (current_date.strftime('%Y-%m-%d'), f"Depreciation - {asset_name}",
                         depreciation_account_id, account_id, depreciation_amount)
                    )
                    transaction_id = db.cursor.lastrowid

                    # --- update transaction id ---
                    db.cursor.execute(
                    "UPDATE depreciation_schedule SET transaction_id = ? WHERE schedule_id = ?",
                    (transaction_id, schedule_id)
                    )


                    # ---  Move to the *next* month ---  THIS IS THE KEY FIX
                    if current_date.month == 12:
                        next_month = 1
                        next_year = current_date.year + 1
                    else:
                        next_month = current_date.month + 1
                        next_year = current_date.year
                    current_date = date(next_year, next_month, purchase_date.day) # using purchase date

                    # --- Exit Conditions ---
                    if current_book_value <= salvage_value:
                         break  # Stop if book value reaches salvage value

                    if useful_life_years is not None and period > useful_life_years * 12 :
                        break  # Stop if useful life (in months) is exceeded
                    period += 1

                db.commit()
                QMessageBox.information(self, "Success", "Fixed asset purchased and registered successfully!")
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