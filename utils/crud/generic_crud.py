# utils/crud/generic_crud.py

from PySide6.QtWidgets import (QMessageBox, QTableWidget, QTableWidgetItem,
                              QDialog, QVBoxLayout, QLineEdit,
                              QPushButton, QLabel, QHBoxLayout, QComboBox)
from PySide6.QtCore import Qt
import sqlite3
from .base_crud import BaseCRUD
from .search_dialog import AdvancedSearchDialog
from utils.formatters import normalize_text, format_table_name

class GenericCRUD(BaseCRUD):
    def __init__(self, table_name):
        super().__init__(table_name)

    def read(self, main_window):
        self.cursor.execute(f"SELECT * FROM {self.table_name}")
        records = self.cursor.fetchall()
        columns = self.get_columns()

        # Filter out normalized_name and create display columns
        display_columns = [col for col in columns if col.lower() != 'normalized_name']
        normalized_name_index = columns.index('normalized_name') if 'normalized_name' in columns else -1

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

    def _get_search_type(self, column_name):
        """Determine search type based on column name."""

        if self.table_name == 'transactions':
            search_types = {
                'debit_account': 'debit_account',
                'credit_account': 'credit_account',
                'category_id': 'category'
            }
            return search_types.get(column_name)
        else:
            return 'generic'

    def _format_display_text(self, selected, column_name):
        """Format the display text for the search dialog."""

        if self.table_name == 'transactions':
            if column_name in ['debit_account', 'credit_account']:
                return f"{selected.get('name', '')} ({selected.get('code', '')})"
            return selected.get('name', '')
        else:
            return selected.get('name','')
    def _create_input_fields(self, columns, dialog, record=None):
        inputs = {}
        layout = dialog.layout()

        for idx, column in enumerate(columns):
            if column.lower() in ['id', 'created_at', 'updated_at', 'status', 'normalized_name', 'balance']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            if column == 'is_active':
                combo = QComboBox()
                combo.addItems(["Yes", "No"])  # Display text
                inputs[column] = combo
                layout.addWidget(combo)

                # Set item data *and* handle current value correctly
                combo.setItemData(0, 1)  # Yes -> 1
                combo.setItemData(1, 0)  # No -> 0

                if record:
                    current_value = record[idx]
                    combo.setCurrentIndex(0 if current_value == 1 else 1)  # Select based on record value
                else:
                    combo.setCurrentIndex(0)  # Default to "Yes" (index 0)

            elif column in ['debit_account', 'credit_account'] and self.table_name == 'transactions':
                display_field = QLineEdit()
                display_field.setReadOnly(True)
                search_button = QPushButton("Search")
                inputs[column] = {
                    'display': display_field,
                    'value': record[idx] if record else None,
                    'button': search_button
                }
                field_layout = QHBoxLayout()
                field_layout.addWidget(display_field)
                field_layout.addWidget(search_button)
                layout.addLayout(field_layout)

                def create_search_handler(col_name, display_widget, input_dict):
                    def handle_search():
                        search_type = self._get_search_type(col_name)
                        search_dialog = AdvancedSearchDialog(
                            field_type=search_type,
                            parent=dialog,
                            db_path=self.db_path
                        )
                        if search_dialog.exec() == QDialog.Accepted:
                            selected = search_dialog.get_selected_item()
                            if selected:
                                display_text = self._format_display_text(selected, col_name)
                                display_widget.setText(display_text)
                                input_dict[col_name]['value'] = selected['id']
                    return handle_search

                search_button.clicked.connect(create_search_handler(column, display_field, inputs))

            elif column.endswith('_date') or column == 'date':
                date_input = QLineEdit()
                date_input.setReadOnly(True)
                date_button = QPushButton("Select Date")
                inputs[column] = {
                    'display': date_input,
                    'value': record[idx] if record else None,
                    'button': date_button
                }
                field_layout = QHBoxLayout()
                field_layout.addWidget(date_input)
                field_layout.addWidget(date_button)
                layout.addLayout(field_layout)

                def create_date_handler(col_name, display_widget, input_dict):
                    def handle_date_select():
                        from .date_select import DateSelectWindow
                        date_dialog = DateSelectWindow()
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget.setText(selected_date)
                            input_dict[col_name]['value'] = selected_date
                    return handle_date_select

                date_button.clicked.connect(create_date_handler(column, date_input, inputs))

            else:
                input_field = QLineEdit(str(record[idx]) if record else "")
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs

    def _save_record(self, dialog, inputs, update=False, record_id=None):
        columns = []
        values = []
        normalized_name = None

        for column, input_field in inputs.items():
            if isinstance(input_field, dict):
                value = input_field['value']
            elif isinstance(input_field, QComboBox):
                # ALWAYS get the itemData based on the CURRENT index.
                value = input_field.itemData(input_field.currentIndex())
                if value is None:
                   value = 0

            elif isinstance(input_field, QLineEdit):
                value = input_field.text()
            else:
                value = None

            if value == "" and column not in ['description']:
                QMessageBox.warning(dialog, "Error", f"Please fill in {format_table_name(column)}")
                return False

            columns.append(column)
            values.append(value)

            if column.lower() == "name":
                normalized_name = normalize_text(value)

        if "normalized_name" not in columns and normalized_name:
            columns.append("normalized_name")
            values.append(normalized_name)

        try:
            if update:
                set_clause = ', '.join([f"{col} = ?" for col in columns if col.lower() not in ['id', 'created_at', 'updated_at']])
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
                values.append(record_id)
            else:
                query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
            self.cursor.execute(query, values)
            self.conn.commit()
            QMessageBox.information(dialog, "Success", f"Record {'updated' if update else 'created'} successfully!")
            dialog.close()
            return True
        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "Error", f"Failed to save record: {str(e)}")
            return False

    def create(self, main_window):
        dialog = QDialog(main_window)
        dialog.setWindowTitle(f"Create New Record in {self.formatted_table_name}")
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        columns = self.get_columns()
        inputs = self._create_input_fields(columns, dialog)
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self._save_record(dialog, inputs))
        layout.addWidget(save_button)
        dialog.exec()


    def edit(self, main_window):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name
        )
        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item:
                return
            record_id = selected_item['id']
            self.cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (record_id,))
            record = self.cursor.fetchone()
            if not record:
                QMessageBox.warning(main_window, "Error", "Record not found!")
                return
            dialog = QDialog(main_window)
            dialog.setWindowTitle(f"Edit Record in {self.formatted_table_name}")
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            columns = self.get_columns()
            inputs = self._create_input_fields(columns, dialog, record)
            save_button = QPushButton("Save")
            save_button.clicked.connect(lambda: self._save_record(dialog, inputs, update=True, record_id=record_id))
            layout.addWidget(save_button)
            dialog.exec()

    def delete(self, main_window):
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item: return

            record_id = selected_item['id']
            confirm = QMessageBox.question(
                main_window, "Confirm Delete",
                f"Are you sure you want to delete the record with ID {record_id}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                try:
                    self.cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (record_id,))
                    self.conn.commit()
                    QMessageBox.information(main_window, "Success", "Record deleted successfully!")
                except sqlite3.Error as e:
                    QMessageBox.critical(main_window, "Database Error", str(e))

    def open_search(self, field_type, filter_value=None, parent=None):
        dialog = AdvancedSearchDialog(
            field_type=field_type,
            filter_value=filter_value,
            parent=parent,
            db_path=self.db_path,
            table_name = self.table_name
        )
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_selected_item()
        return None