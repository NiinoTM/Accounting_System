# crud.py
from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QInputDialog
import sqlite3
from pathlib import Path

class CRUD:
    def __init__(self, table_name):
        self.table_name = table_name
        self.db_path = Path('data') / 'finance.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def get_columns(self):
        """Fetch column names for the table."""
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = [column[1] for column in self.cursor.fetchall()]
        return columns

    def create(self, main_window):
        """Create a new record in the table."""
        columns = self.get_columns()
        dialog = QDialog(main_window)
        dialog.setWindowTitle(f"Create New Record in {self.table_name}")
        layout = QVBoxLayout()

        inputs = {}
        for column in columns:
            if column.lower() not in ['id', 'created_at', 'updated_at']:  # Skip auto-generated fields
                layout.addWidget(QLabel(column))
                input_field = QLineEdit()
                inputs[column] = input_field
                layout.addWidget(input_field)

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_record(dialog, inputs))
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec()

    def save_record(self, dialog, inputs):
        """Save the new record to the database."""
        columns = []
        values = []
        for column, input_field in inputs.items():
            columns.append(column)
            values.append(input_field.text())

        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
        self.cursor.execute(query, values)
        self.conn.commit()
        QMessageBox.information(dialog, "Success", "Record created successfully!")
        dialog.close()

    def read(self, main_window):
        """Read and display all records from the table."""
        self.cursor.execute(f"SELECT * FROM {self.table_name}")
        records = self.cursor.fetchall()
        columns = self.get_columns()

        table = QTableWidget(main_window)
        table.setRowCount(len(records))
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        for row_idx, row in enumerate(records):
            for col_idx, col in enumerate(row):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(col)))

        main_window.setCentralWidget(table)

    def edit(self, main_window):
        """Edit an existing record in the table."""
        record_id, ok = QInputDialog.getInt(main_window, "Edit Record", "Enter the ID of the record to edit:")
        if not ok:
            return

        self.cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (record_id,))
        record = self.cursor.fetchone()
        if not record:
            QMessageBox.warning(main_window, "Error", "Record not found!")
            return

        columns = self.get_columns()
        dialog = QDialog(main_window)
        dialog.setWindowTitle(f"Edit Record in {self.table_name}")
        layout = QVBoxLayout()

        inputs = {}
        for idx, column in enumerate(columns):
            layout.addWidget(QLabel(column))
            input_field = QLineEdit(str(record[idx]))
            inputs[column] = input_field
            layout.addWidget(input_field)

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.update_record(dialog, inputs, record_id))
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec()

    def update_record(self, dialog, inputs, record_id):
        """Update the record in the database."""
        columns = []
        values = []
        for column, input_field in inputs.items():
            if column.lower() not in ['id', 'created_at', 'updated_at']:  # Skip auto-generated fields
                columns.append(column)
                values.append(input_field.text())

        set_clause = ', '.join([f"{col} = ?" for col in columns])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        values.append(record_id)
        self.cursor.execute(query, values)
        self.conn.commit()
        QMessageBox.information(dialog, "Success", "Record updated successfully!")
        dialog.close()

    def delete(self, main_window):
        """Delete a record from the table."""
        record_id, ok = QInputDialog.getInt(main_window, "Delete Record", "Enter the ID of the record to delete:")
        if not ok:
            return

        confirm = QMessageBox.question(main_window, "Confirm Delete", "Are you sure you want to delete this record?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,))
            self.conn.commit()
            QMessageBox.information(main_window, "Success", "Record deleted successfully!")