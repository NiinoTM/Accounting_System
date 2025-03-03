# ar_ap/edit_ar_ap.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QRadioButton, QHBoxLayout, QDialog)
from create_database import DatabaseManager
from utils.formatters import normalize_text
from utils.crud.search_dialog import AdvancedSearchDialog

class EditDebtorCreditorWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Edit Debtor/Creditor")
        self.db_manager = DatabaseManager()
        self.selected_record = None  # Store the selected record
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Search Button (opens AdvancedSearchDialog)
        self.search_button = QPushButton("Select Debtor/Creditor")
        self.search_button.clicked.connect(self.open_search)
        layout.addWidget(self.search_button)

        # Name Input
        name_layout = QHBoxLayout()
        self.name_label = QLabel("Name: \n")
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Debtor/Creditor Selection (Radio Buttons)
        type_layout = QHBoxLayout()
        self.debtor_radio = QRadioButton("Debtor")
        self.creditor_radio = QRadioButton("Creditor")
        type_layout.addWidget(self.debtor_radio)
        type_layout.addWidget(self.creditor_radio)
        layout.addLayout(type_layout)

        # Edit Button (initially disabled)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_record)
        self.edit_button.setEnabled(False)  # Disable until a record is selected
        layout.addWidget(self.edit_button)

        self.setLayout(layout)

    def open_search(self):
        """Opens the Advanced Search dialog for debtor_creditor."""
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor'  # Specify the table
        )
        if search_dialog.exec() == QDialog.Accepted:
            self.selected_record = search_dialog.get_selected_item()
            if self.selected_record:
                self.populate_fields()
                self.edit_button.setEnabled(True) # Enable the Edit button


    def populate_fields(self):
        """Populates the fields with the selected record's data."""
        if self.selected_record:
            self.name_input.setText(self.selected_record['name'])
            # Set radio button based on 'account' value
            if self.selected_record['account'] == '1':
                self.debtor_radio.setChecked(True)
            elif self.selected_record['account'] == '2':
                self.creditor_radio.setChecked(True)


    def edit_record(self):
        """Edits the selected record in the database."""
        if not self.selected_record:
            return  # No record selected, shouldn't happen, but check anyway

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return

        account_type = 1 if self.debtor_radio.isChecked() else 2
        normalized_name = normalize_text(name)
        record_id = self.selected_record['id']


        try:
            with self.db_manager as db:
                # --- Check for existing normalized name (excluding current record) ---
                db.cursor.execute(
                    "SELECT id FROM debtor_creditor WHERE normalized_name = ? AND id != ?",
                    (normalized_name, record_id)
                )
                if db.cursor.fetchone():
                    QMessageBox.critical(self, "Error", "Another Debtor/Creditor with this name already exists.")
                    return

                # --- Update the record ---
                db.cursor.execute(
                    """
                    UPDATE debtor_creditor
                    SET name = ?, normalized_name = ?, account = ?
                    WHERE id = ?
                    """,
                    (name, normalized_name, account_type, record_id)
                )
                db.commit()
                QMessageBox.information(self, "Success", "Record updated successfully!")
                self.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))