
from PySide6.QtWidgets import (QMessageBox, QTableWidget, QTableWidgetItem,
                              QDialog, QHBoxLayout, QVBoxLayout, QLineEdit,
                              QPushButton, QLabel, QInputDialog, QComboBox)
import sqlite3
from utils.formatters import normalize_text, format_table_name
from data.create_database import DatabaseManager
from utils.search_dialog import AdvancedSearchDialog
from utils.date_select import DateSelectWindow

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
            if column.lower() in ['id', 'created_at', 'updated_at', 'status', 'normalized_name', 'balance']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            if column in ['debit_account', 'credit_account', 'category_id', 'type_id']:
                if column == 'type_id':
                    # Special handling for type_id: Dropdown
                    display_widget = QComboBox()
                    inputs[column] = {
                        'display': display_widget,
                        'value': None,  # Initialize value to None
                    }
                    field_layout = QHBoxLayout()
                    field_layout.addWidget(display_widget)
                    layout.addLayout(field_layout)
                    self.populate_account_types(display_widget)

                    def type_id_changed(index, col=column):
                        selected_item = display_widget.itemData(index)
                        inputs[col]['value'] = selected_item if selected_item else None

                    display_widget.currentIndexChanged.connect(type_id_changed)

                else:
                    # Existing search logic
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
                                    input_dict[column_name]['value'] = selected['id']
                        return handle_search

                    search_button.clicked.connect(create_search_handler(column, display_field, inputs))

            elif column == 'is_active':
                combo = QComboBox()
                combo.addItem("Yes")
                combo.addItem("No")
                combo.setCurrentIndex(0)
                inputs[column] = combo
                layout.addWidget(combo)

            elif column.endswith('_date') or column == 'date':
                date_input = QLineEdit()
                date_input.setReadOnly(True)
                date_button = QPushButton("Select Date")
                inputs[column] = {
                    'display': date_input,
                    'value': None,
                    'button': date_button
                }
                field_layout = QHBoxLayout()
                field_layout.addWidget(date_input)
                field_layout.addWidget(date_button)
                layout.addLayout(field_layout)

                def create_date_handler(column_name, display_widget, input_dict):
                    def handle_date_select():
                        date_dialog = DateSelectWindow()
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget.setText(selected_date)
                            input_dict[column_name]['value'] = selected_date
                    return handle_date_select

                date_button.clicked.connect(create_date_handler(column, date_input, inputs))
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
        search_types = {
            'debit_account': 'debit_account',
            'credit_account': 'credit_account',
            'category_id': 'category'
        }
        return search_types.get(column_name)

    def _format_display_text(self, selected, column_name):
        if column_name in ['debit_account', 'credit_account']:
            return f"{selected.get('name', '')} ({selected.get('code', '')})"
        return selected.get('name', '')

    def save_record(self, dialog, inputs):
        columns = []
        values = []
        normalized_name = None

        for column, input_field in inputs.items():
            if isinstance(input_field, dict):
                # Always get the value, even if it's None.  This is crucial.
                value = input_field['value']
            else:
                if isinstance(input_field, QComboBox):
                    value = input_field.currentText()
                elif isinstance(input_field, QLineEdit):
                    value = input_field.text()
                else:  # Handle other input types if needed
                    value = None

            # Allow empty values only for 'description' and 'type_id' if explicitly allowed
            if value == "" and column not in ['description', 'type_id']:
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
        print(query)
        print(values)

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
        """Edit an existing record in the table using AdvancedSearchDialog."""
        self.parent = main_window

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

            columns = self.get_columns()
            dialog = QDialog(main_window)
            dialog.setWindowTitle(f"Edit Record in {self.formatted_table_name}")
            layout = QVBoxLayout()
            inputs = {}

            for idx, column in enumerate(columns):
                if column.lower() == 'id':
                    continue

                formatted_label = format_table_name(column)
                layout.addWidget(QLabel(formatted_label))

                if column == 'type_id':
                    display_widget = QComboBox()
                    inputs[column] = {
                        'display': display_widget,
                        'value': None,  # Initialize
                    }
                    field_layout = QHBoxLayout()
                    field_layout.addWidget(display_widget)
                    layout.addLayout(field_layout)
                    self.populate_account_types(display_widget)

                    current_type_id = record[idx]
                    if current_type_id is not None:
                        for i in range(display_widget.count()):
                            if display_widget.itemData(i) == current_type_id:
                                display_widget.setCurrentIndex(i)
                                inputs[column]['value'] = current_type_id  # Set initial value
                                break
                    # Connect AFTER setting initial value
                    def type_id_changed(index, col=column):
                        selected_item = display_widget.itemData(index)
                        inputs[col]['value'] = selected_item if selected_item else None

                    display_widget.currentIndexChanged.connect(type_id_changed)

                else:
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
            if column.lower() not in ['id', 'created_at', 'updated_at']:
                columns.append(column)
                if isinstance(input_field, dict):
                    values.append(input_field['value'])  # Get 'value' from dict
                else:
                    values.append(input_field.text())

        set_clause = ', '.join([f"{col} = ?" for col in columns])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        values.append(record_id)
        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            QMessageBox.information(dialog, "Success", "Record updated successfully!")
            dialog.close()
        except sqlite3.Error as e:
            QMessageBox.critical(dialog, "Database Error", str(e))

    def populate_account_types(self, combo_box):
        """Populate the QComboBox with account types from the database."""
        self.cursor.execute("SELECT id, name FROM account_types")
        account_types = self.cursor.fetchall()
        for type_id, name in account_types:
            combo_box.addItem(name, type_id)

    def delete(self, main_window):
        """Delete a record from the table using AdvancedSearchDialog."""
        self.parent = main_window

        # Use AdvancedSearchDialog to find the record
        search_dialog = AdvancedSearchDialog(
            field_type='generic',
            parent=main_window,
            db_path=self.db_path,
            table_name=self.table_name
        )

        if search_dialog.exec() == QDialog.Accepted:
            selected_item = search_dialog.get_selected_item()
            if not selected_item:
                return  # No item selected

            record_id = selected_item['id']

            # Confirmation dialog
            confirm = QMessageBox.question(
                main_window,
                "Confirm Delete",
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