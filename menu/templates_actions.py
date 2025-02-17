# templates_actions.py (remains the same)

from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtGui import QAction
from utils.crud.template_transactions_crud import TemplateTransactionCRUD


class TemplatesActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.templates_menu = self.create_templates_actions()
        self.crud = TemplateTransactionCRUD()  # Use the correct CRUD class

    def create_templates_actions(self):
        templates_menu = QMenu("Templates", self.main_window)
        create_templates = QAction("Create Template", self.main_window)
        read_templates = QAction("View Templates", self.main_window)
        update_templates = QAction("Edit Template", self.main_window)  # Added this line
        delete_templates = QAction("Delete Template", self.main_window)

        create_templates.triggered.connect(self.create_templates)
        read_templates.triggered.connect(self.read_templates)
        update_templates.triggered.connect(self.update_templates)  # Added this line
        delete_templates.triggered.connect(self.delete_templates)

        templates_menu.addAction(create_templates)
        templates_menu.addAction(read_templates)
        templates_menu.addAction(update_templates)  # Added this line
        templates_menu.addAction(delete_templates)

        return templates_menu
    
    def create_templates(self):
        self.crud.create_template(self.main_window)


    def read_templates(self):
        self.crud.read(self.main_window)


    def update_templates(self):
        """Handle edit template action."""
        self.crud.edit(self.main_window)

    def delete_templates(self):
        self.crud.delete(self.main_window)