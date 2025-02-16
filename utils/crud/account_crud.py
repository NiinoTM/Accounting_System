# utils/crud/account_crud.py
from PySide6.QtWidgets import (QMessageBox, QComboBox, QDialog, QHBoxLayout,
                              QVBoxLayout, QLineEdit, QPushButton, QLabel)
import sqlite3
from .generic_crud import GenericCRUD  # Inherit from GenericCRUD
from .search_dialog import AdvancedSearchDialog #import the dialog
from utils.formatters import format_table_name

class AccountCRUD(GenericCRUD):
    """CRUD operations specific to the accounts table."""

    def __init__(self):
        super().__init__('accounts')  # Initialize with 'accounts' table

    def _create_input_fields(self, columns, dialog, record=None):
        """Overrides _create_input_fields to handle account-specific fields."""
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
                        'value': None,
                    }
                    field_layout = QHBoxLayout()
                    field_layout.addWidget(display_widget)
                    layout.addLayout(field_layout)
                    self.populate_account_types(display_widget)

                    current_type_id = record[idx] if record else None  # Get current value if editing
                    if current_type_id is not None:
                         for i in range(display_widget.count()):
                            if display_widget.itemData(i) == current_type_id:
                                display_widget.setCurrentIndex(i)
                                inputs[column]['value'] = current_type_id
                                break


                    def type_id_changed(index, col=column):
                        selected_item = display_widget.itemData(index)
                        inputs[col]['value'] = selected_item if selected_item else None

                    display_widget.currentIndexChanged.connect(type_id_changed)
                else:
                    # Use search dialog for other foreign key fields
                    display_field = QLineEdit()
                    display_field.setReadOnly(True)
                    search_button = QPushButton("Search")
                    inputs[column] = {
                        'display': display_field,
                        'value': record[idx] if record else None,  # Store current value
                        'button': search_button
                    }
                    field_layout = QHBoxLayout()
                    field_layout.addWidget(display_field)
                    field_layout.addWidget(search_button)
                    layout.addLayout(field_layout)

                    def create_search_handler(col_name, display_widget, input_dict):
                        def handle_search():
                            search_type = self._get_search_type(col_name)
                            search_dialog = AdvancedSearchDialog( #Assign to search_dialog
                                field_type=search_type,
                                parent=dialog, # Use dialog as the parent
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

            elif column == 'is_active':  # Handle is_active
                combo = QComboBox()
                combo.addItems(["Yes", "No"])
                combo.setCurrentIndex(0 if not record or record[idx] == 1 else 1) #set current index
                inputs[column] = combo
                layout.addWidget(combo)
            elif column.endswith('_date') or column == 'date': # handle dates
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
                        from .date_select import DateSelectWindow  # Import here
                        date_dialog = DateSelectWindow()
                        if date_dialog.exec() == QDialog.Accepted:
                            selected_date = date_dialog.calendar.selectedDate().toString('yyyy-MM-dd')
                            display_widget.setText(selected_date)
                            input_dict[column_name]['value'] = selected_date
                    return handle_date_select
                date_button.clicked.connect(create_date_handler(column,date_input, inputs))

            else:
                input_field = QLineEdit(str(record[idx]) if record else "")  # Default
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs

    def _get_search_type(self, column_name):
        """Determine search type based on column name."""
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
        """Populate the QComboBox with account types."""
        self.cursor.execute("SELECT id, name FROM account_types")
        for type_id, name in self.cursor.fetchall():
            combo_box.addItem(name, type_id)