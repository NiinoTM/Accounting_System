from PySide6.QtWidgets import QMessageBox, QMenu
from PySide6.QtGui import QAction

#modules
from utils.crud import CRUD

class CategoriesActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.categories_menu = self.create_categories_actions()

    def create_categories_actions(self):
        # Create the main categoriess menu
        categories_menu = QMenu("Categories", self.main_window)

        # Create CRUD actions
        create_categories = QAction("Create Category", self.main_window)
        read_categories = QAction("View Categories", self.main_window)
        update_categories = QAction("Update Category", self.main_window)
        delete_categories = QAction("Delete Category", self.main_window)

        # Connect actions to their respective methods
        create_categories.triggered.connect(self.create_categories)
        read_categories.triggered.connect(self.read_categories)
        update_categories.triggered.connect(self.update_categories)
        delete_categories.triggered.connect(self.delete_categories)

        # Add CRUD actions to the categoriess menu
        categories_menu.addAction(create_categories)
        categories_menu.addAction(read_categories)
        categories_menu.addAction(update_categories)
        categories_menu.addAction(delete_categories)

        return categories_menu

    def create_categories(self):
        crud = CRUD("categories")
        crud.create(self.main_window)

    def read_categories(self):
        crud = CRUD("categories")
        crud.read(self.main_window)

    def update_categories(self):
        crud = CRUD("categories")
        crud.edit(self.main_window)

    def delete_categories(self):
        crud = CRUD("categories")
        crud.delete(self.main_window)
