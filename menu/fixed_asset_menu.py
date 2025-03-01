# menu/fixed_asset_menu.py

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from fixed_assets.import_fixed_asset import ImportFixedAssetWindow
from fixed_assets.settings import FixedAssetSettingsWindow
from fixed_assets.single_account_purchase import SingleAccountPurchaseWindow
from fixed_assets.multiple_account_purchase import MultipleAccountPurchaseWindow
from fixed_assets.purge_asset_records import PurgeAssetRecordsWindow  # Import

class FixedAssetActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.fixed_asset_menu = self.create_fixed_asset_menu()

    def create_fixed_asset_menu(self):
        fixed_asset_menu = QMenu("Fixed Assets", self.main_window)

        # --- Register Purchased Asset (Submenu) ---
        register_purchased_menu = QMenu("Register Purchased Asset", fixed_asset_menu)
        single_account_action = QAction("Single Account Purchase", self.main_window)
        single_account_action.triggered.connect(self.open_single_account_purchase)
        multiple_account_action = QAction("Multiple Accounts Purchase", self.main_window)
        multiple_account_action.triggered.connect(self.open_multiple_account_purchase)

        register_purchased_menu.addAction(single_account_action)
        register_purchased_menu.addAction(multiple_account_action)
        fixed_asset_menu.addMenu(register_purchased_menu)


        import_asset_action = QAction("Register Pre-Existing Asset", self.main_window)
        import_asset_action.triggered.connect(self.open_import_fixed_asset)
        fixed_asset_menu.addAction(import_asset_action)

        # --- Add Settings Action ---
        settings_action = QAction("Settings", self.main_window)
        settings_action.triggered.connect(self.open_settings)
        fixed_asset_menu.addAction(settings_action)

        # --- Purge Asset Records Action ---
        purge_asset_action = QAction("Purge Asset Records", self.main_window)
        purge_asset_action.triggered.connect(self.open_purge_asset_records)  # Connect
        fixed_asset_menu.addAction(purge_asset_action)  # Add to menu

        return fixed_asset_menu

    def open_import_fixed_asset(self):
        self.import_asset_window = ImportFixedAssetWindow(self.main_window)
        self.import_asset_window.show()

    def open_settings(self):
        self.settings_window = FixedAssetSettingsWindow(self.main_window)
        self.settings_window.show()

    def open_single_account_purchase(self):
        self.single_purchase_window = SingleAccountPurchaseWindow(self.main_window)
        self.single_purchase_window.show()

    def open_multiple_account_purchase(self):
        self.multiple_purchase_window = MultipleAccountPurchaseWindow(self.main_window)
        self.multiple_purchase_window.show()

    def open_purge_asset_records(self):  # NEW
        """Opens the purge asset records window."""
        self.purge_asset_window = PurgeAssetRecordsWindow(self.main_window)
        self.purge_asset_window.show()