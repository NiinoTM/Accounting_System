##### ATTENTION: IMPORTANT IMPROVEMENT POINT: NEED TO CONSIDER THE IMPACT OF DELETING THE DEBTOR/CREDITOR TO THE TRANSACTIONS ALREADY DONE

# ar_ap/delete_ar_ap.py

import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QMessageBox, QRadioButton, QHBoxLayout, QDialog)
from data.create_database import DatabaseManager
from utils.crud.search_dialog import AdvancedSearchDialog

class DeleteDebtorCreditorWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Delete Debtor/Creditor")
        self.db_manager = DatabaseManager()
        self.selected_record = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Search Button
        self.search_button = QPushButton("Select Debtor/Creditor")
        self.search_button.clicked.connect(self.open_search)
        layout.addWidget(self.search_button)

        # Name Input (read-only)
        name_layout = QHBoxLayout()
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)  # Make read-only
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Debtor/Creditor Selection (Radio Buttons, also read-only)
        type_layout = QHBoxLayout()
        self.debtor_radio = QRadioButton("Debtor")
        self.creditor_radio = QRadioButton("Creditor")
        self.debtor_radio.setEnabled(False)  # Disable interaction
        self.creditor_radio.setEnabled(False)
        type_layout.addWidget(self.debtor_radio)
        type_layout.addWidget(self.creditor_radio)
        layout.addLayout(type_layout)


        # Delete Button (initially disabled)
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_record)
        self.delete_button.setEnabled(False)  # Disable until a record is selected
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def open_search(self):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=self,
            db_path=self.db_manager.db_path,
            table_name='debtor_creditor'
        )
        if search_dialog.exec() == QDialog.Accepted:
            self.selected_record = search_dialog.get_selected_item()
            if self.selected_record:
                self.populate_fields()
                self.delete_button.setEnabled(True)

    def populate_fields(self):
        if self.selected_record:
            self.name_input.setText(self.selected_record['name'])
            if self.selected_record['account'] == '1':
                self.debtor_radio.setChecked(True)
            elif self.selected_record['account'] == '2':
                self.creditor_radio.setChecked(True)


    def delete_record(self):
        if not self.selected_record:
            return

        # Confirmation Dialog
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this debtor/creditor?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                with self.db_manager as db:
                    db.cursor.execute(
                        "DELETE FROM debtor_creditor WHERE id = ?",
                        (self.selected_record['id'],)
                    )
                    db.commit()
                    QMessageBox.information(self, "Success", "Record deleted successfully!")
                    self.close()  # Close the window after deletion
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", str(e))