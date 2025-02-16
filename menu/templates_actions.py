#libraries
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud.generic_crud import GenericCRUD


class TemplatesActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.templates_menu = self.create_templates_actions()
        self.crud = GenericCRUD("transaction_templates") 
    
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
        self.crud.create(self.main_window)

    def read_templates(self):
        self.crud.read(self.main_window)

    def update_templates(self):
        self.crud.edit(self.main_window)

    def delete_templates(self):
        self.crud.delete(self.main_window)