import unicodedata
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QLabel


class SearchDialog(QDialog):
    def __init__(self, items, prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pesquisar")
        self.setGeometry(200, 200, 600, 400)
        
        self.items = items
        self.selected_item = None
        
        # Layout
        layout = QVBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome do item...")
        self.search_input.textChanged.connect(self.update_results)
        layout.addWidget(self.search_input)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(1)
        self.results_table.setHorizontalHeaderLabels(["Nome"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.cellDoubleClicked.connect(self.select_item)
        layout.addWidget(self.results_table)
        
        # Select button
        self.select_button = QPushButton("Selecionar")
        self.select_button.clicked.connect(self.select_item)
        layout.addWidget(self.select_button)
        
        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.update_results()

    def update_results(self):
        """Update the results table based on the search input"""
        search_term = self.search_input.text().strip().lower()
        
        # Normalize search term
        normalized_term = unicodedata.normalize('NFD', search_term)\
            .encode('ascii', 'ignore').decode('ascii')
        
        # Filter items
        matches = [
            item for item in self.items
            if normalized_term in unicodedata.normalize('NFD', item.name)
            .encode('ascii', 'ignore').decode('ascii').lower()
        ]
        
        # Update table
        self.results_table.setRowCount(len(matches))
        for i, item in enumerate(matches):
            self.results_table.setItem(i, 0, QTableWidgetItem(item.name))
        
        # Auto-select if only one match
        if len(matches) == 1:
            self.selected_item = matches[0]
            self.accept()
        
        # Update status label
        self.status_label.setText(f"{len(matches)} itens encontrados.")

    def select_item(self):
        """Select the currently highlighted item"""
        selected_row = self.results_table.currentRow()
        if selected_row >= 0:
            self.selected_item = self.items[selected_row]
            self.accept()

    def get_selected_item(self):
        """Return the selected item"""
        return self.selected_item