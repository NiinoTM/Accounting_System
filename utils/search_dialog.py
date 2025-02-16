# search_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                              QTableWidget, QTableWidgetItem, 
                              QPushButton, QLabel)
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
        }
    }


    def __init__(self, field_type, filter_value=None, parent=None, db_path=None):
        """
        Initialize search dialog with dynamic configuration
        
        Args:
            field_type (str): Type of field to search ('debit_account', 'credit_account', 'parent', 'category')
            filter_value: Optional value to filter results (e.g., parent_id for categories)
            parent (QWidget): Parent widget
            db_path (str): Path to database file
        """
        super().__init__(parent)
        
        if field_type not in self.SEARCH_CONFIGS:
            raise ValueError(f"Invalid field type: {field_type}")
            
        config = self.SEARCH_CONFIGS[field_type]
        self.table_name = config['table']
        self.search_columns = config['search_columns']
        self.display_columns = config['display_columns']
        self.base_query = config['base_query']
        
        self.filter_value = filter_value
        self.selected_item = None
        
        # Set up database connection
        self.db_path = db_path or 'data/financial_system.db'
        self.conn = sqlite3.connect(self.db_path)
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
        header_labels = [col.split()[-1].replace('AS', '') for col in self.display_columns]
        header_labels = [format_table_name(col.strip()) for col in header_labels]
        
        self.results_table.setColumnCount(len(header_labels))
        self.results_table.setHorizontalHeaderLabels(header_labels)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.cellDoubleClicked.connect(self.select_item)
        layout.addWidget(self.results_table)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_item)
        button_layout.addWidget(self.select_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.update_results()

    def update_results(self):
        """Update the results table based on the search input"""
        search_term = self.search_input.text().strip()
        normalized_term = normalize_text(search_term)
        
        query = self.base_query
        params = []
        
        if search_term:
            where_clauses = []
            for column in self.search_columns:
                where_clauses.append(f"LOWER({column}) LIKE ?")
                params.append(f"%{search_term.lower()}%")
            
            where_clause = " OR ".join(where_clauses)
            if 'WHERE' in query:
                query = f"{query} AND ({where_clause})"
            else:
                query = f"{query} WHERE {where_clause}"
                
        if self.filter_value is not None:
            if 'WHERE' in query:
                query = f"{query} AND parent_id = ?"
            else:
                query = f"{query} WHERE parent_id = ?"
            params.append(self.filter_value)
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        # Update table
        self.results_table.setRowCount(len(results))
        for row_idx, row in enumerate(results):
            for col_idx, value in enumerate(row):
                self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
        
        self.status_label.setText(f"{len(results)} items found")
        
        if len(results) == 1:
            self.results_table.selectRow(0)

    def select_item(self):
        """Select the currently highlighted item"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        selected_data = {}
        header_labels = [self.results_table.horizontalHeaderItem(i).text() 
                        for i in range(self.results_table.columnCount())]
        
        for col, header in enumerate(header_labels):
            selected_data[header] = self.results_table.item(row, col).text()
        
        self.selected_item = selected_data
        self.accept()

    def get_selected_item(self):
        """Return the selected item"""
        return self.selected_item

    def closeEvent(self, event):
        """Clean up database connection when dialog is closed"""
        self.conn.close()
        super().closeEvent(event)