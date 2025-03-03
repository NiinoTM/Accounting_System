# utils/crud/search_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit,
                              QTableWidget, QTableWidgetItem,
                              QPushButton, QLabel, QHBoxLayout)
from utils.formatters import normalize_text, format_table_name
import sqlite3

class AdvancedSearchDialog(QDialog):
    SEARCH_CONFIGS = {  # (Keep this as before - unchanged)
        'debit_account': {
            'table': 'accounts',
            'search_columns': ['accounts.name', 'accounts.code'],
            'display_columns': ['accounts.id', 'accounts.code', 'accounts.name', 'account_types.name AS type_name'],
            'base_query': """
                SELECT accounts.id, accounts.code, accounts.name, account_types.name AS type_name
                FROM accounts
                JOIN account_types ON accounts.type_id = account_types.id
                WHERE account_types.normal_balance = 'DEBIT'
                AND accounts.is_active = 1
            """
        },
        'credit_account': {
            'table': 'accounts',
            'search_columns': ['accounts.name', 'accounts.code'],
            'display_columns': ['accounts.id', 'accounts.code', 'accounts.name', 'account_types.name AS type_name'],
            'base_query': """
                SELECT accounts.id, accounts.code, accounts.name, account_types.name AS type_name
                FROM accounts
                JOIN account_types ON accounts.type_id = account_types.id
                WHERE account_types.normal_balance = 'CREDIT'
                AND accounts.is_active = 1
            """
        },
        'category': {
            'table': 'categories',
            'search_columns': ['name'],
            'display_columns': ['id', 'name', 'description'],
            'base_query': """
                SELECT id, name, description
                FROM categories
            """
        },
        'generic': {
            'table': None,
            'search_columns': None,
            'display_columns': None,
            'base_query': None
        }
    }


    def __init__(self, field_type, filter_value=None, parent=None, db_path=None, table_name=None, additional_filter=None): # New parameter
        super().__init__(parent)
        self.field_type = field_type
        self.filter_value = filter_value
        self.selected_item = None
        self.db_path = db_path or 'data/financial_system.db'
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.additional_filter = additional_filter # Store the filter

        if self.field_type == 'generic':
            if not table_name:
                raise ValueError("table_name must be provided for generic search type")
            self.table_name = table_name
            self.cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns_info = self.cursor.fetchall()
            self.display_columns = [col[1] for col in columns_info]
            self.search_columns = self.display_columns
            self.base_query = f"SELECT {', '.join(self.display_columns)} FROM {self.table_name}"
            self.raw_column_names = self.display_columns

            # --- DYNAMIC FILTER APPLICATION ---
            if self.additional_filter:
                self.base_query += f" WHERE {self.additional_filter}"


        else: # keep this part
            config = self.SEARCH_CONFIGS[self.field_type]
            self.table_name = config['table']
            self.search_columns = config['search_columns']
            self.display_columns = config['display_columns']
            self.base_query = config['base_query']
            self.raw_column_names = [col.split(' AS ')[0].split('.')[-1] for col in self.display_columns]

        self.init_ui()

    def init_ui(self):  # (Keep this as before - unchanged)
        self.setWindowTitle(f"Search {format_table_name(self.table_name)}")
        self.setGeometry(200, 200, 800, 500)
        layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search...")
        self.search_input.textChanged.connect(self.update_results)
        layout.addWidget(self.search_input)
        self.results_table = QTableWidget()

        if self.SEARCH_CONFIGS.get(self.field_type) != 'generic':
            header_labels = [col.split(' AS ')[-1].replace(' AS ', '').strip() for col in self.display_columns]
            header_labels = [format_table_name(col) for col in header_labels]
        else:
             header_labels = [format_table_name(col) for col in self.display_columns]

        self.results_table.setColumnCount(len(header_labels))
        self.results_table.setHorizontalHeaderLabels(header_labels)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.cellDoubleClicked.connect(self.select_item_and_close)
        layout.addWidget(self.results_table)
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_item_and_close)
        button_layout.addWidget(self.select_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        self.update_results()


    def update_results(self):  # (Keep this as before - unchanged)
        search_term = self.search_input.text().strip()
        normalized_term = normalize_text(search_term)
        query = self.base_query
        params = []

        if search_term:
            where_clauses = []
            for column in self.search_columns:
                where_clauses.append(f"LOWER({column}) LIKE ?")
                params.append(f"%{normalized_term}%")
            where_clause = " OR ".join(where_clauses)
            # --- CRITICAL: Handle existing WHERE clause ---
            if 'WHERE' in query:
                query += f" AND ({where_clause})"
            else:
                query += f" WHERE {where_clause}"

        if self.filter_value is not None:
            if 'WHERE' in query:
                query += " AND parent_id = ?"
            else:
                query += " WHERE parent_id = ?"
            params.append(self.filter_value)

        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        self.results_table.setRowCount(len(results))
        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        self.status_label.setText(f"{len(results)} items found")
        if len(results) == 1:
            self.results_table.selectRow(0)

    def select_item_and_close(self): # (Keep this as before - unchanged)
        selected_rows = self.results_table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        selected_data = {}
        for i in range(self.results_table.columnCount()):
            raw_col_name = self.raw_column_names[i]
            selected_data[raw_col_name] = self.results_table.item(row, i).text()
        self.selected_item = selected_data
        self.accept()

    def get_selected_item(self):  # (Keep this as before - unchanged)
        return self.selected_item

    def closeEvent(self, event):  # (Keep this as before - unchanged)
        self.conn.close()
        super().closeEvent(event)