from PySide6.QtWidgets import (QMessageBox, QTableWidget, QTableWidgetItem, 
                              QDialog, QHBoxLayout, QVBoxLayout, QLineEdit, 
                              QPushButton, QLabel, QInputDialog, QComboBox)
import sqlite3
from utils.formatters import normalize_text, format_table_name
from data.create_database import DatabaseManager
from utils.search_dialog import AdvancedSearchDialog

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

    def create(self, main_window):
        """Create a new record in the table."""
        self.parent = main_window
        columns = self.get_columns()
        dialog = QDialog(main_window)
        dialog.setWindowTitle(f"Create New Record in {self.formatted_table_name}")
        layout = QVBoxLayout()
        inputs = {}

        for column in columns:
            if column.lower() in ['id', 'created_at', 'updated_at', 'status', 'normalized_name']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            if column in ['debit_account', 'credit_account', 'category_id']:  # Removed 'parent_id'
                display_field = QLineEdit()
                display_field.setReadOnly(True)
                search_button = QPushButton("Search")
                
                inputs[column] = {
                    'display': display_field,
                    'value': None,
                    'button': search_button
                }

                field_layout = QHBoxLayout()
                field_layout.addWidget(display_field)
                field_layout.addWidget(search_button)
                layout.addLayout(field_layout)

                def create_search_handler(column_name, display_widget, input_dict):
                    def handle_search():
                        search_type = self._get_search_type(column_name)
                        dialog = AdvancedSearchDialog(
                            field_type=search_type,
                            parent=self.parent,
                            db_path=self.db_path
                        )
                        
                        if dialog.exec() == QDialog.Accepted:
                            selected = dialog.get_selected_item()
                            if selected:
                                display_text = self._format_display_text(selected, column_name)
                                display_widget.setText(display_text)
                                input_dict[column_name]['value'] = selected['ID']
                    return handle_search

                search_button.clicked.connect(
                    create_search_handler(column, display_field, inputs)
                )
            elif column == 'is_active':
                # Add dropdown for is_active
                combo = QComboBox()
                combo.addItem("Yes")
                combo.addItem("No")
                combo.setCurrentIndex(0)  # Default to "Yes"
                inputs[column] = combo
                layout.addWidget(combo)
            else:
                input_field = QLineEdit()
                inputs[column] = input_field
                layout.addWidget(input_field)

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_record(dialog, inputs))
        layout.addWidget(save_button)
        dialog.setLayout(layout)
        dialog.exec()


    def _get_search_type(self, column_name):
        """Determine search type based on column name."""
        search_types = {
            'debit_account': 'debit_account',
            'credit_account': 'credit_account',
            'category_id': 'category'
        }
        return search_types.get(column_name)

    def _format_display_text(self, selected, column_name):
        """Format display text based on column type."""
        if column_name in ['debit_account', 'credit_account']:
            return f"{selected['Name']} ({selected['Code']})"
        return selected['Name']

    def save_record(self, dialog, inputs):
        """Save the new record to the database."""
        columns = []
        values = []
        normalized_name = None

        for column, input_field in inputs.items():
            if isinstance(input_field, dict):
                if input_field['value'] is None:
                    QMessageBox.warning(dialog, "Error", f"Please select a value for {format_table_name(column)}")
                    return
                value = input_field['value']
            else:
                if isinstance(input_field, QComboBox):
                    value = input_field.currentText()
                elif isinstance(input_field, QLineEdit):
                    value = input_field.text()
                # Process the value as needed
                
            if not value:
                QMessageBox.warning(dialog, "Error", f"Please fill in {format_table_name(column)}")
                return
                
            columns.append(column)
            values.append(value)

            if column.lower() == "name":
                normalized_name = normalize_text(value)

        if "normalized_name" not in columns and normalized_name:
            columns.append("normalized_name")
            values.append(normalized_name)

        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
        
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            QMessageBox.information(dialog, "Success", "Record created successfully!")
            dialog.close()
        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "Error", f"Failed to save record: {str(e)}")

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
            formatted_label = format_table_name(column)        
            layout.addWidget(QLabel(formatted_label))
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

    def open_search(self, field_type, filter_value=None):
 
        dialog = AdvancedSearchDialog(
            field_type=field_type,
            filter_value=filter_value,
            parent=self.parent,
           db_path=self.db_path
        )
            
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selected_item()
        return None