# ar_ap/new_ar_ap.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QRadioButton, QHBoxLayout)
from create_database import DatabaseManager
from utils.formatters import normalize_text

class NewDebtorCreditorWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("New Debtor/Creditor")
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name Input
        name_layout = QHBoxLayout()
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Debtor/Creditor Selection (Radio Buttons)
        type_layout = QHBoxLayout()
        self.debtor_radio = QRadioButton("Debtor")
        self.creditor_radio = QRadioButton("Creditor")
        self.debtor_radio.setChecked(True)  # Default to Debtor
        type_layout.addWidget(self.debtor_radio)
        type_layout.addWidget(self.creditor_radio)
        layout.addLayout(type_layout)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_record)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_record(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty.")
            return

        account_type = 1 if self.debtor_radio.isChecked() else 2  # 1 for Debtor, 2 for Creditor    
        normalized_name = normalize_text(name)

        try:
            with self.db_manager as db:
                # --- Check for existing normalized name FIRST ---
                db.cursor.execute(
                    "SELECT id FROM debtor_creditor WHERE normalized_name = ?",
                    (normalized_name,)
                )
                if db.cursor.fetchone():  # If a record with the normalized name exists
                    QMessageBox.critical(self, "Error", "A Debtor/Creditor with this name already exists.")
                    return  # Stop the save process


                db.cursor.execute(
                    """
                    INSERT INTO debtor_creditor (name, normalized_name, account, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, normalized_name, account_type, 0.0)
                )
                db.commit()
                QMessageBox.information(self, "Success", "Record created successfully!")
                self.close()

        except sqlite3.Error as e:  # Catch any other database errors
            QMessageBox.critical(self, "Database Error", str(e))