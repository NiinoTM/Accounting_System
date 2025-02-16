# crud.py
from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QInputDialog, QComboBox
import sqlite3
from pathlib import Path

from utils.formatters import normalize_text, format_table_name
from data.create_database import DatabaseManager

class CRUD:
    def __init__(self, table_name):
        self.table_name = table_name
        self.formatted_table_name = format_table_name(table_name)
        self.db_path = DatabaseManager().db_path

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def get_columns(self):
        """Fetch column names for the table."""
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns = [column[1] for column in self.cursor.fetchall()]
        return columns
    
    def fetch_options(self, table_name):
        """Fetch ID and name from a referenced table for dropdown selection."""
        self.cursor.execute(f"SELECT id, name FROM {table_name}")
        return self.cursor.fetchall()  # Returns a list of (id, name) tuples


    def create(self, main_window):
        """Create a new record in the table."""
        columns = self.get_columns()
        dialog = QDialog(main_window)
        dialog.setWindowTitle(f"Create New Record in {self.formatted_table_name}")
        layout = QVBoxLayout()

        inputs = {}

        # Fetch options for type_id and category_id
        type_options = self.fetch_options("account_types")
        category_options = self.fetch_options("categories")

        for column in columns:
            if column.lower() in ['id', 'created_at', 'updated_at', 'status', 'normalized_name']:  
                continue  # Skip auto-generated fields

            formatted_label = format_table_name(column)        
            layout.addWidget(QLabel(formatted_label))

            if column == "type_id":
                type_dropdown = QComboBox()
                for id, name in type_options:
                    type_dropdown.addItem(name, id)  # Display name, store ID
                inputs[column] = type_dropdown
                layout.addWidget(type_dropdown)
            
            elif column == "category_id":
                category_dropdown = QComboBox()
                for id, name in category_options:
                    category_dropdown.addItem(name, id)
                inputs[column] = category_dropdown
                layout.addWidget(category_dropdown)

            else:
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
        normalized_name = None

        for column, input_field in inputs.items():
            if isinstance(input_field, QComboBox):  # Handle dropdown selection
                value = input_field.currentData()  # Get selected ID
            else:
                value = input_field.text()
            
            columns.append(column)
            values.append(value)

            if column.lower() == "name":
                normalized_name = normalize_text(value)

        if "normalized_name" not in columns and normalized_name:
            columns.append("normalized_name")
            values.append(normalized_name)

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
        
        # Filter out normalized_name from columns and create display columns
        display_columns = []
        for col in columns:
            if col.lower() != 'normalized_name':
                display_columns.append(col)
                
        if 'normalized_name' in columns:
            normalized_name_index = columns.index('normalized_name')
        else:
            normalized_name_index = -1

        # Format column headers
        formatted_columns = [format_table_name(col) for col in display_columns]
        
        table = QTableWidget(main_window)
        table.setRowCount(len(records))
        table.setColumnCount(len(display_columns))
        table.setHorizontalHeaderLabels(formatted_columns)

        for row_idx, row in enumerate(records):
            col_offset = 0
            for col_idx, col in enumerate(row):
                if col_idx == normalized_name_index:
                    col_offset = 1
                    continue
                table.setItem(row_idx, col_idx - col_offset, QTableWidgetItem(str(col)))

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
        dialog.setWindowTitle(f"Edit Record in {self.formatted_table_name}")
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