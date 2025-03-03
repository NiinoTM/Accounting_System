# utils/crud/account_crud.py

from PySide6.QtWidgets import (QMessageBox, QComboBox, QDialog, QHBoxLayout,
                              QVBoxLayout, QLineEdit, QPushButton, QLabel)
import sqlite3
from .generic_crud import GenericCRUD
from .search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name

class AccountCRUD(GenericCRUD):
    def __init__(self):
        super().__init__('accounts')

    def _create_input_fields(self, columns, dialog, record=None):
        inputs = {}
        layout = dialog.layout()

        for idx, column in enumerate(columns):
            if column.lower() in ['id', 'created_at', 'updated_at', 'status', 'normalized_name', 'balance']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            if column in ['debit_account', 'credit_account', 'category_id', 'type_id']:
                if column == 'type_id':
                    display_widget = QComboBox()
                    inputs[column] = {
                        'display': display_widget,
                        'value': None,  # Initialize value to None
                    }
                    field_layout = QHBoxLayout()
                    field_layout.addWidget(display_widget)
                    layout.addLayout(field_layout)
                    self.populate_account_types(display_widget)

                    # Set the initial value *unconditionally* after populating.
                    if record and record[idx] is not None:
                        # Editing: Find and set the current type_id
                        for i in range(display_widget.count()):
                            if display_widget.itemData(i) == record[idx]:
                                display_widget.setCurrentIndex(i)
                                inputs[column]['value'] = record[idx]
                                break
                    else:
                        # Creation: Set the default value (first item's data)
                        if display_widget.count() > 0:  # Ensure there's at least one item
                            inputs[column]['value'] = display_widget.itemData(0)  # Get data from first item
                            display_widget.setCurrentIndex(0)  # Select the first item


                    def type_id_changed(index, col=column):
                        selected_item = display_widget.itemData(index)
                        inputs[col]['value'] = selected_item if selected_item else None

                    display_widget.currentIndexChanged.connect(type_id_changed)

                else:
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


            elif column == 'is_active':
                combo = QComboBox()
                combo.addItems(["Yes", "No"])
                inputs[column] = combo
                layout.addWidget(combo)

                combo.setItemData(0, 1)
                combo.setItemData(1, 0)

                if record:
                    current_value = record[idx]
                    combo.setCurrentIndex(0 if current_value == 1 else 1)
                else:
                    combo.setCurrentIndex(0)


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

                def create_date_handler(column_name, display_widget, input_dict):
                    def handle_date_select():
                        from .date_select import DateSelectWindow
                        date_dialog = DateSelectWindow()
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget.setText(selected_date)
                            input_dict[column_name]['value'] = selected_date
                    return handle_date_select
                date_button.clicked.connect(create_date_handler(column,date_input, inputs))

            else:
                input_field = QLineEdit(str(record[idx]) if record else "")
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs

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

    def populate_account_types(self, combo_box):
        self.cursor.execute("SELECT id, name FROM account_types")
        for type_id, name in self.cursor.fetchall():
            combo_box.addItem(name, type_id)