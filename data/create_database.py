import sqlite3
from pathlib import Path

def create_database():
    # Create .data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = data_dir / 'finance.db'
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # SQL statements to create tables
    create_tables_sql = """
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
        parent_id INTEGER REFERENCES categories(id),
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
        name VARCHAR(100) NOT NULL UNIQUE,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'OPEN',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Debts and Credits
    CREATE TABLE IF NOT EXISTS debt_credit_records (
        id INTEGER PRIMARY KEY,
        party_name VARCHAR(100) NOT NULL,
        description TEXT,
        type VARCHAR(20) NOT NULL,
        amount DECIMAL(15,2) NOT NULL,
        remaining_amount DECIMAL(15,2) NOT NULL,
        due_date DATE,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        related_account_id INTEGER REFERENCES accounts(id),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Payment/Collection History
    CREATE TABLE IF NOT EXISTS payment_history (
        id INTEGER PRIMARY KEY,
        debt_credit_id INTEGER REFERENCES debt_credit_records(id),
        amount DECIMAL(15,2) NOT NULL,
        payment_date DATE NOT NULL,
        payment_method VARCHAR(50),
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Assets register
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        purchase_date DATE NOT NULL,
        purchase_cost DECIMAL(15,2) NOT NULL,
        asset_account_id INTEGER REFERENCES accounts(id),
        current_value DECIMAL(15,2),
        status VARCHAR(20) DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Depreciation Schedule
    CREATE TABLE IF NOT EXISTS depreciation (
        id INTEGER PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id),
        depreciation_method VARCHAR(50),
        useful_life_years INTEGER NOT NULL,
        salvage_value DECIMAL(15,2),
        annual_rate DECIMAL(5,2),
        accumulated_depreciation DECIMAL(15,2) DEFAULT 0.00,
        last_depreciation_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Transactions
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        description TEXT,
        debit_account INTEGER NOT NULL,
        credit_account INTEGER NOT NULL,
        amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (debit_account) REFERENCES accounts(id),
        FOREIGN KEY (credit_account) REFERENCES accounts(id)
    ); 

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

    # Default account types data
    default_account_types = [
        ('Current Asset', 'DEBIT', 'Assets expected to be converted to cash within one year'),
        ('Fixed Asset', 'DEBIT', 'Long-term tangible business assets'),
        ('Current Liability', 'CREDIT', 'Debts due within one year'),
        ('Long-term Liability', 'CREDIT', 'Debts due after one year'),
        ('Equity', 'CREDIT', "Owner's stake in the business"),
        ('Revenue', 'CREDIT', 'Income from business activities'),
        ('Expense', 'DEBIT', 'Costs incurred in business operations')
    ]

    try:
        # Create tables
        cursor.executescript(create_tables_sql)
        
        # Insert default account types if they don't exist
        cursor.execute("SELECT COUNT(*) FROM account_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO account_types (name, normal_balance, description) VALUES (?, ?, ?)",
                default_account_types
            )
        
        # Commit the changes
        conn.commit()
        print("Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    
    finally:
        # Close the connection
        conn.close()