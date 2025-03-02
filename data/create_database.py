# create_database.py (Modified)
import sqlite3
from pathlib import Path
from typing import List, Tuple

class DatabaseManager:
    def __init__(self, db_name: str = 'financial_system.db'):
        self.data_dir = Path('data')
        self.db_path = self.data_dir / db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self) -> None:
        """Establish database connection and set row_factory."""
        self.data_dir.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # <--- CRITICAL: Set row_factory here
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def commit(self) -> None:
        """Commit changes to database"""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """Rollback changes"""
        if self.conn:
            self.conn.rollback()

    @property
    def create_tables_sql(self) -> str:
        """SQL statements to create all necessary tables"""
        return """
        -- Chart of Accounts Types
        CREATE TABLE IF NOT EXISTS account_types (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            normal_balance VARCHAR(10) NOT NULL CHECK (normal_balance IN ('DEBIT', 'CREDIT')),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Categories for reporting and grouping
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            normalized_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Main accounts table
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            code VARCHAR(20) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL UNIQUE,
            normalized_name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            type_id INTEGER REFERENCES account_types(id),
            category_id INTEGER REFERENCES categories(id),
            is_active BOOLEAN DEFAULT true,
            balance DECIMAL(15,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Accounting Periods
        CREATE TABLE IF NOT EXISTS accounting_periods (
            id INTEGER PRIMARY KEY,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Debtors/Creditors
        CREATE TABLE IF NOT EXISTS debtor_creditor (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            normalized_name VARCHAR(100) NOT NULL UNIQUE,
            account INTEGER,
            amount DECIMAL(15, 2),
            FOREIGN KEY (account) REFERENCES accounts(id)
        );

        CREATE TABLE IF NOT EXISTS debtor_creditor_transactions (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            details TEXT,
            amount DECIMAL(15, 2),
            debtor_creditor INTEGER NOT NULL,
            type VARCHAR(20) NOT NULL,  -- Added 'type' column
            FOREIGN KEY (debtor_creditor) REFERENCES debtor_creditor(id)
        );

        -- Fixed Assets Table (Modified - Removed calculated fields)
        CREATE TABLE IF NOT EXISTS fixed_assets (
            asset_id INTEGER PRIMARY KEY,
            asset_name VARCHAR(255) NOT NULL,
            account_id INTEGER NOT NULL,
            purchase_date DATE NOT NULL,
            original_cost DECIMAL(19, 4) NOT NULL,
            salvage_value DECIMAL(19, 4) NOT NULL,
            depreciation_method TEXT NOT NULL,
            useful_life_years INTEGER,  -- Keep for initial setup
            depreciation_rate DECIMAL(5, 4), -- Keep for initial setup and DB, DDB
            total_estimated_units INTEGER,  -- Keep for Units of Production
            disposal_price DECIMAL(19, 4),
            disposal_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );

        -- Depreciation Schedule Table (NEW)
        CREATE TABLE IF NOT EXISTS depreciation_schedule (
            schedule_id INTEGER PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            period_start_date DATE NOT NULL,  -- Start of the period
            period_end_date DATE NOT NULL,    -- End of the period
            depreciation_expense DECIMAL(19, 4) NOT NULL,
            accumulated_depreciation DECIMAL(19, 4) NOT NULL,
            book_value DECIMAL(19, 4) NOT NULL,  -- Book value at period end
            units_produced_period INTEGER,  --  Units produced THIS period (for UP method)
            transaction_id INTEGER,           -- Link to the transaction that records this depreciation
            FOREIGN KEY (asset_id) REFERENCES fixed_assets(asset_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        );

        -- Transactions
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT,
            debited INTEGER NOT NULL,
            credited INTEGER NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debited) REFERENCES accounts(id),
            FOREIGN KEY (credited) REFERENCES accounts(id)
        );

        -- New table Future Transactions
        CREATE TABLE IF NOT EXISTS future_transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT,
            debited INTEGER NOT NULL,
            credited INTEGER NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debited) REFERENCES accounts(id),
            FOREIGN KEY (credited) REFERENCES accounts(id)
        );

        CREATE TABLE IF NOT EXISTS transaction_templates (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            normalized_name VARCHAR(100) NOT NULL UNIQUE
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
            debited INTEGER NOT NULL,  
            credited INTEGER NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (template_transaction_id) REFERENCES template_transactions(id) ON DELETE CASCADE,
            FOREIGN KEY (debited) REFERENCES accounts(id),
            FOREIGN KEY (credited) REFERENCES accounts(id)
        );

        -- NEW TABLE: Recurring Transactions
        CREATE TABLE IF NOT EXISTS recurring_transactions (
            id INTEGER PRIMARY KEY,
            description TEXT,
            debited INTEGER NOT NULL,
            credited INTEGER NOT NULL,
            amount REAL NOT NULL,
            frequency TEXT NOT NULL,  -- 'weekly', 'monthly', 'yearly', or 'days'
            interval INTEGER,          -- Number of days, if frequency is 'days'
            start_date DATE NOT NULL,
            end_date DATE,            -- NULL for no end date
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debited) REFERENCES accounts(id),
            FOREIGN KEY (credited) REFERENCES accounts(id)
            );
        """

    @property
    def default_account_types(self) -> List[Tuple[str, str, str]]:
        """Default account types data"""
        return [
            ('Current Asset', 'DEBIT', 'Assets expected to be converted to cash within one year'),
            ('Fixed Asset', 'DEBIT', 'Long-term tangible business assets'),
            ('Current Liability', 'CREDIT', 'Debts due within one year'),
            ('Long-term Liability', 'CREDIT', 'Debts due after one year'),
            ('Equity', 'CREDIT', "Owner's stake in the business"),
            ('Revenue', 'CREDIT', 'Income from business activities'),
            ('Expense', 'DEBIT', 'Costs incurred in business operations')
        ]

    def initialize_database(self) -> bool:
        """Initialize the database with tables and default data"""
        try:
            # Create tables
            self.cursor.executescript(self.create_tables_sql)

            # Insert default account types if they don't exist
            self.cursor.execute("SELECT COUNT(*) FROM account_types")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.executemany(
                    "INSERT INTO account_types (name, normal_balance, description) VALUES (?, ?, ?)",
                    self.default_account_types
                )

            # Commit the changes
            self.commit()
            print("Database initialized successfully!")
            return True

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            self.rollback()
            return False

def create_database():
    """Factory function to create and initialize the database"""
    with DatabaseManager() as db:
        return db.initialize_database()