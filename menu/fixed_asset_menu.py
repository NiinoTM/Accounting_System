# menu/fixed_asset_menu.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from fixed_assets.import_fixed_asset import ImportFixedAssetWindow  # Import
from fixed_assets.settings import FixedAssetSettingsWindow # Import

class FixedAssetActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.fixed_asset_menu = self.create_fixed_asset_menu()

    def create_fixed_asset_menu(self):
        fixed_asset_menu = QMenu("Fixed Assets", self.main_window)

        import_asset_action = QAction("Register Pre-Existing Asset", self.main_window)
        import_asset_action.triggered.connect(self.open_import_fixed_asset)
        fixed_asset_menu.addAction(import_asset_action)

        # --- Add Settings Action ---
        settings_action = QAction("Settings", self.main_window)
        settings_action.triggered.connect(self.open_settings)
        fixed_asset_menu.addAction(settings_action)

        return fixed_asset_menu

    def open_import_fixed_asset(self):
        self.import_asset_window = ImportFixedAssetWindow(self.main_window)
        self.import_asset_window.show()

    def open_settings(self):
        """Opens the fixed asset settings window."""
        self.settings_window = FixedAssetSettingsWindow(self.main_window)
        self.settings_window.show()