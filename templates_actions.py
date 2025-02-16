#libraries
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud import CRUD

class TemplatesActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.templates_menu = self.create_templates_actions()
    
    def create_templates_actions(self):
    # Add CRUD actions to the templatess menu
        templates_menu = QMenu("Templates", self.main_window)

        # Create CRUD actions
        create_templates = QAction("Create Template", self.main_window)
        read_templates = QAction("View Templates", self.main_window)
        update_templates = QAction("Update Template", self.main_window)
        delete_templates = QAction("Delete Template", self.main_window)

        # Connect actions to their respective methods
        create_templates.triggered.connect(self.create_templates)
        read_templates.triggered.connect(self.read_templates)
        update_templates.triggered.connect(self.update_templates)
        delete_templates.triggered.connect(self.delete_templates)

        # Add CRUD actions to the templatess menu
        templates_menu.addAction(create_templates)
        templates_menu.addAction(read_templates)
        templates_menu.addAction(update_templates)
        templates_menu.addAction(delete_templates)

        return templates_menu

    def create_templates(self):
        crud = CRUD("transaction_templates")
        crud.create(self.main_window)

    def read_templates(self):
        crud = CRUD("transaction_templates")
        crud.read(self.main_window)

    def update_templates(self):
        crud = CRUD("transaction_templates")
        crud.edit(self.main_window)

    def delete_templates(self):
        crud = CRUD("transaction_templates")
        crud.delete(self.main_window)


"""
    TABLES TO CHANGE
    
    CREATE TABLE IF NOT EXISTS transaction_templates (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS template_transactions (
        id INTEGER PRIMARY KEY,
        template_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (template_id) REFERENCES transaction_templates(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS template_transaction_details (
        id INTEGER PRIMARY KEY,
        template_transaction_id INTEGER NOT NULL,
        debit_account INTEGER NOT NULL,
        credit_account INTEGER NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (template_transaction_id) REFERENCES template_transactions(id) ON DELETE CASCADE
    );
"""
