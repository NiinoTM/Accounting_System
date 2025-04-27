# utils/crud/transaction_filter_dialog.py
import sqlite3
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox,
                              QDateEdit, QListWidget, QPushButton, QDialogButtonBox,
                              QHBoxLayout, QLabel, QMessageBox, QAbstractItemView,
                              QComboBox, QGroupBox, QCheckBox, QFrame, QSizePolicy)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont, QIcon
from create_database import DatabaseManager
from .search_dialog import AdvancedSearchDialog

class TransactionFilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Transactions")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        self.db_manager = DatabaseManager()
        self.selected_account_ids = []  # To store IDs of selected accounts

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- GENERAL OPTIONS GROUP ---
        self.general_group = QGroupBox("General Options")
        self.general_group.setFont(QFont("", weight=QFont.Bold))
        general_layout = QFormLayout(self.general_group)
        general_layout.setSpacing(10)
        
        # Number of Transactions
        self.num_transactions_spinbox = QSpinBox()
        self.num_transactions_spinbox.setRange(1, 10000)
        self.num_transactions_spinbox.setValue(15)
        self.num_transactions_spinbox.setMinimumHeight(28)
        general_layout.addRow("Number of Transactions:", self.num_transactions_spinbox)
        
        main_layout.addWidget(self.general_group)
        
        # --- DATE RANGE GROUP ---
        self.date_group = QGroupBox("Date Range (Optional)")
        self.date_group.setFont(QFont("", weight=QFont.Bold))
        date_layout = QFormLayout(self.date_group)
        date_layout.setSpacing(10)
        
        # Date selectors with optional checkboxes
        self.use_start_date = QCheckBox("Use Start Date")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setEnabled(False)  # Disabled by default
        
        self.use_end_date = QCheckBox("Use End Date")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setEnabled(False)  # Disabled by default
        
        # Date layouts
        start_date_layout = QHBoxLayout()
        start_date_layout.addWidget(self.use_start_date)
        start_date_layout.addWidget(self.start_date_edit)
        
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(self.use_end_date)
        end_date_layout.addWidget(self.end_date_edit)
        
        date_layout.addRow("Start Date:", start_date_layout)
        date_layout.addRow("End Date:", end_date_layout)
        
        # Connect checkbox signals
        self.use_start_date.toggled.connect(self.start_date_edit.setEnabled)
        self.use_end_date.toggled.connect(self.end_date_edit.setEnabled)
        
        main_layout.addWidget(self.date_group)
        
        # --- ACCOUNTS GROUP ---
        self.accounts_group = QGroupBox("Accounts (Optional)")
        self.accounts_group.setFont(QFont("", weight=QFont.Bold))
        accounts_layout = QVBoxLayout(self.accounts_group)
        accounts_layout.setSpacing(10)
        
        # Create a frame with a slight border for the account list
        list_frame = QFrame()
        list_frame.setFrameShape(QFrame.StyledPanel)
        list_frame.setFrameShadow(QFrame.Sunken)
        list_frame_layout = QVBoxLayout(list_frame)
        list_frame_layout.setContentsMargins(2, 2, 2, 2)
        
        # Account list with better styling
        self.account_list_widget = QListWidget()
        self.account_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.account_list_widget.setAlternatingRowColors(True)
        self.account_list_widget.setMinimumHeight(100)
        list_frame_layout.addWidget(self.account_list_widget)
        
        accounts_layout.addWidget(list_frame)
        
        # Button layout with improved styling
        account_button_layout = QHBoxLayout()
        
        self.add_account_button = QPushButton("Add Account")
        self.add_account_button.setMinimumHeight(30)
        self.add_account_button.setIcon(QIcon.fromTheme("list-add"))
        
        self.remove_account_button = QPushButton("Remove Selected")
        self.remove_account_button.setMinimumHeight(30)
        self.remove_account_button.setIcon(QIcon.fromTheme("list-remove"))
        self.remove_account_button.setEnabled(False)  # Disabled until selection
        
        account_button_layout.addWidget(self.add_account_button)
        account_button_layout.addWidget(self.remove_account_button)
        
        accounts_layout.addLayout(account_button_layout)
        main_layout.addWidget(self.accounts_group)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # --- OK and Cancel Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setMinimumHeight(30)
        button_box.button(QDialogButtonBox.Cancel).setMinimumHeight(30)
        main_layout.addWidget(button_box)
        
        # Connect signals
        self.add_account_button.clicked.connect(self.add_account)
        self.remove_account_button.clicked.connect(self.remove_account)
        self.account_list_widget.itemSelectionChanged.connect(self.update_button_states)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def update_button_states(self):
        """Update button states based on selection"""
        self.remove_account_button.setEnabled(len(self.account_list_widget.selectedItems()) > 0)

    def add_account(self):
        """Opens account search and adds the selected account to the list."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='accounts',
            additional_filter='is_active = 1'  # Only show active accounts
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected_account = search_dialog.get_selected_item()
            if selected_account:
                try:
                    # Ensure ID is treated as integer
                    account_id = int(selected_account['id'])
                    # Use .get() for safety
                    account_name = f"{selected_account.get('name', 'N/A')} ({selected_account.get('code', 'N/A')})"

                    # Prevent duplicates based on ID
                    if account_id not in self.selected_account_ids:
                        self.selected_account_ids.append(account_id)
                        self.account_list_widget.addItem(account_name)
                        # Store the ID with the QListWidgetItem for easy retrieval later
                        item = self.account_list_widget.item(self.account_list_widget.count() - 1)
                        if item:  # Check item was created successfully
                            item.setData(Qt.UserRole, account_id)
                    else:
                        QMessageBox.information(self, "Duplicate", f"Account '{account_name}' already selected.")
                except (ValueError, KeyError) as e:
                    QMessageBox.warning(self, "Selection Error", f"Could not add selected account: {e}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An unexpected error occurred adding the account: {e}")

    def remove_account(self):
        """Removes the currently selected account from the list."""
        selected_items = self.account_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an account to remove.")
            return

        # Since selection mode is SingleSelection, there will be at most one item
        current_item = selected_items[0]
        account_id = current_item.data(Qt.UserRole)  # Retrieve stored ID

        # Remove from internal ID list if ID was stored correctly
        if account_id is not None and account_id in self.selected_account_ids:
            self.selected_account_ids.remove(account_id)

        # Remove the item from the visual list widget
        self.account_list_widget.takeItem(self.account_list_widget.row(current_item))

    def get_filters(self):
        """Retrieves and validates the selected filter criteria."""
        limit = self.num_transactions_spinbox.value()

        # Get dates only if checkboxes are checked
        start_date = None
        if self.use_start_date.isChecked():
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            
        end_date = None
        if self.use_end_date.isChecked():
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        # --- Basic Validation ---
        if limit <= 0:
            QMessageBox.warning(self, "Validation Error", "Number of transactions must be greater than 0.")
            return None  # Indicate validation failure

        # Check if start date is after end date (only if both are provided)
        if start_date and end_date and start_date > end_date:
            QMessageBox.warning(self, "Date Error", "Start date cannot be after end date.")
            return None  # Indicate validation failure

        # Return a copy of the account ID list to prevent modification outside this class
        # Return None for account_ids if the list is empty, consistent with date filters
        account_ids_to_return = list(self.selected_account_ids) if self.selected_account_ids else None

        # Return the filters dictionary
        return {
            'limit': limit,
            'start_date': start_date,
            'end_date': end_date,
            'account_ids': account_ids_to_return
        }

    def accept(self):
        """Override the default accept behavior to validate filters first."""
        filters = self.get_filters()
        # Only close if filters are valid
        if filters is not None:
            super().accept()