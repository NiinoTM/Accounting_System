# utils/crud/transactions_crud.py

import sqlite3
from PySide6.QtWidgets import (QMessageBox, QComboBox, QDialog, QHBoxLayout,
                              QVBoxLayout, QLineEdit, QPushButton, QLabel)
from .generic_crud import GenericCRUD
from .search_dialog import AdvancedSearchDialog
from utils.formatters import format_table_name, normalize_text

class TransactionsCRUD(GenericCRUD):
    def __init__(self):
        super().__init__('transactions')

    def _create_input_fields(self, columns, dialog, record=None):
        inputs = {}
        layout = dialog.layout()

        for idx, column in enumerate(columns):
            if column.lower() in ['id', 'created_at', 'updated_at', 'status']:
                continue

            formatted_label = format_table_name(column)
            layout.addWidget(QLabel(formatted_label))

            if column in ['debited', 'credited', 'category_id']:

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
                        search_dialog = AdvancedSearchDialog(
                            field_type='generic',
                            table_name='accounts',
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
                date_button.clicked.connect(create_date_handler(column,date_input, inputs))
            else:
                input_field = QLineEdit(str(record[idx]) if record else "")
                inputs[column] = input_field
                layout.addWidget(input_field)

        return inputs

    def _get_search_type(self, column_name):
        return 'generic'

    def _format_display_text(self, selected, column_name):
        return f"{selected.get('name', '')} ({selected.get('code', '')})"

    def _update_account_balance(self, account_id, amount, operation):
        """Updates the balance of a given account (simplified)."""
        try:
            if operation == 'add':
                adjustment = amount
            elif operation == 'subtract':
                adjustment = -amount
            else:
                raise ValueError(f"Invalid operation: {operation}")

            # Update the account balance
            self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (adjustment, account_id))
            self.conn.commit()

        except sqlite3.Error as e:
            print(f"Error updating account balance: {e}")
            self.conn.rollback()
            raise


    def _save_record(self, dialog, inputs, update=False, record_id=None):
        """Saves a transaction record and updates account balances."""
        columns = []
        values = []
        normalized_name = None

        for column, input_field in inputs.items():
            if isinstance(input_field, dict):
                value = input_field['value']
            elif isinstance(input_field, QComboBox):
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
                # Reverse the original transaction
                self.cursor.execute("SELECT debited, credited, amount FROM transactions WHERE id = ?", (record_id,))
                original_debited, original_credited, original_amount = self.cursor.fetchone()

                self._update_account_balance(original_debited, original_amount, 'subtract')  # Reverse: subtract from debited
                self._update_account_balance(original_credited, original_amount, 'add')  # Reverse: add to credited

                set_clause = ', '.join([f"{col} = ?" for col in columns if col.lower() not in ['id', 'created_at', 'updated_at']])
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
                values.append(record_id)
            else:
                query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"

            self.cursor.execute(query, values)

            # Apply the new/updated transaction
            new_debited_account = inputs['debited']['value']
            new_credited_account = inputs['credited']['value']
            new_amount = float(inputs['amount'].text())

            self._update_account_balance(new_debited_account, new_amount, 'add')  # Debited: add
            self._update_account_balance(new_credited_account, new_amount, 'subtract')  # Credited: subtract


            self.conn.commit()
            QMessageBox.information(dialog, "Success", f"Transaction {'updated' if update else 'created'} successfully!")
            dialog.close()
            return True

        except (sqlite3.Error, ValueError) as e:
            QMessageBox.critical(dialog, "Error", f"Failed to save transaction: {str(e)}")
            self.conn.rollback()
            return False