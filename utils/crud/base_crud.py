# utils/crud/base_crud.py
import sqlite3
from abc import ABC, abstractmethod
from utils.formatters import format_table_name
from data.create_database import DatabaseManager

class BaseCRUD(ABC):
    """Abstract base class for CRUD operations."""

    def __init__(self, table_name):
        self.table_name = table_name
        self.formatted_table_name = format_table_name(table_name)
        self.db_path = DatabaseManager().db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def get_columns(self):
        """Fetch column names for the table."""
        self.cursor.execute(f"PRAGMA table_info({self.table_name})")
        return [column[1] for column in self.cursor.fetchall()]

    @abstractmethod
    def create(self, main_window):
        """Create a new record.  Must be implemented by subclasses."""
        pass

    @abstractmethod
    def read(self, main_window):
        """Read and display records. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def edit(self, main_window):
        """Edit an existing record. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def delete(self, main_window):
        """Delete a record. Must be implemented by subclasses."""
        pass

    def close_connection(self):
        """Close the database connection."""
        self.conn.close()