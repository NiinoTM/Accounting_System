

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit,
                              QTableWidget, QTableWidgetItem,
                              QPushButton, QLabel, QHBoxLayout)  # Import QHBoxLayout
from utils.formatters import normalize_text, format_table_name
import sqlite3

class AdvancedSearchDialog(QDialog):
    SEARCH_CONFIGS = {
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
        'generic': {  # New generic type
            'table': None,  # Will be set in __init__
            'search_columns': None,  # Will be set in __init__
            'display_columns': None,  # Will be set in __init__
            'base_query': None  # Will be set in __init__
        }
    }


    def __init__(self, field_type, filter_value=None, parent=None, db_path=None, table_name=None):
        """
        Initialize search dialog.
        """
        super().__init__(parent)
        self.field_type = field_type  # Store field_type as an instance variable

        if self.field_type not in self.SEARCH_CONFIGS:
            raise ValueError(f"Invalid field type: {self.field_type}")

        if self.field_type == 'generic':
            if not table_name:
                raise ValueError("table_name must be provided for generic search type")
            self.table_name = table_name
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

            # Fetch column information dynamically
            self.cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns_info = self.cursor.fetchall()
            self.display_columns = [col[1] for col in columns_info] #column names
            self.search_columns = self.display_columns  # By default, search all columns
            self.base_query = f"SELECT {', '.join(self.display_columns)} FROM {self.table_name}"
            self.raw_column_names = self.display_columns

        else:

            config = self.SEARCH_CONFIGS[self.field_type]
            self.table_name = config['table']
            self.search_columns = config['search_columns']
            self.display_columns = config['display_columns']
            self.base_query = config['base_query']
            # Extract raw column names
            self.raw_column_names = [col.split(' AS ')[0].split('.')[-1] for col in self.display_columns]


        self.filter_value = filter_value
        self.selected_item = None

        # Set up database connection
        self.db_path = db_path or 'data/financial_system.db'
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Use row factory for dictionary-like access
        self.cursor = self.conn.cursor()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Search {format_table_name(self.table_name)}")
        self.setGeometry(200, 200, 800, 500)

        layout = QVBoxLayout()

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search...")
        self.search_input.textChanged.connect(self.update_results)
        layout.addWidget(self.search_input)

        # Results table
        self.results_table = QTableWidget()

        if self.SEARCH_CONFIGS.get(self.field_type) != 'generic':
            header_labels = [col.split(' AS ')[-1].replace(' AS ', '').strip() for col in self.display_columns] # Clean up labels
            header_labels = [format_table_name(col) for col in header_labels]
        else:
             header_labels = [format_table_name(col) for col in self.display_columns]


        self.results_table.setColumnCount(len(header_labels))
        self.results_table.setHorizontalHeaderLabels(header_labels)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.cellDoubleClicked.connect(self.select_item_and_close)  # Double-click to select
        layout.addWidget(self.results_table)

        # Buttons (Horizontal Layout)
        button_layout = QHBoxLayout()  # Use QHBoxLayout for horizontal arrangement

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_item_and_close) # connect to select_item_and_close
        button_layout.addWidget(self.select_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)  # Add the horizontal button layout

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.update_results()

    def update_results(self):
        """Update the results table based on the search input"""
        search_term = self.search_input.text().strip()
        normalized_term = normalize_text(search_term)  # Normalize for case-insensitive search

        query = self.base_query
        params = []

        if search_term:
            where_clauses = []
            for column in self.search_columns:
                where_clauses.append(f"LOWER({column}) LIKE ?")  # Use LOWER for case-insensitivity
                params.append(f"%{normalized_term}%")  # Use normalized term for searching

            where_clause = " OR ".join(where_clauses)
            if 'WHERE' in query:
                query += f" AND ({where_clause})"
            else:
                query += f" WHERE {where_clause}"

        if self.filter_value is not None:
            if 'WHERE' in query:
                query += " AND parent_id = ?"  # Corrected: No f-string needed
            else:
                query += " WHERE parent_id = ?"
            params.append(self.filter_value)

        self.cursor.execute(query, params)
        results = self.cursor.fetchall()

        # Update table
        self.results_table.setRowCount(len(results))
        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self.status_label.setText(f"{len(results)} items found")

        if len(results) == 1:  # Auto-select if only one result
            self.results_table.selectRow(0)

    def select_item_and_close(self):
        """Select the currently highlighted item and close the dialog"""
        selected_rows = self.results_table.selectedIndexes()  # Use selectedIndexes()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        selected_data = {}

        # Use raw_column_names to create the dictionary
        for i in range(self.results_table.columnCount()):
            raw_col_name = self.raw_column_names[i]
            selected_data[raw_col_name] = self.results_table.item(row, i).text()

        self.selected_item = selected_data
        self.accept()

    def get_selected_item(self):
        """Return the selected item"""
        return self.selected_item

    def closeEvent(self, event):
        """Clean up database connection when dialog is closed"""
        self.conn.close()
        super().closeEvent(event)