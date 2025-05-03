# reports/balance_sheet_core.py
import sqlite3
from create_database import DatabaseManager  # Or your DB manager path

class BalanceSheet:
    def __init__(self):
        self.db_manager = DatabaseManager()
        # Use the context manager for connection handling if preferred,
        # otherwise connect directly as before.
        # For this example, sticking to the original direct connection style.
        self.conn = sqlite3.connect(self.db_manager.db_path)
        # CRITICAL: Ensure row_factory is set for dictionary-like access
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def calcular_saldos_na_data(self, data):
        """Calculates account balances up to a specified date, ordered by account code."""

        query = """
        SELECT
            a.id, -- Keep id if needed elsewhere, otherwise optional here
            a.name,
            a.code, -- Fetch the code
            at.name as account_type,
            at.normal_balance,
            SUM(CASE
                WHEN t.debited = a.id THEN t.amount
                WHEN t.credited = a.id THEN -t.amount
                ELSE 0
            END) AS balance
        FROM accounts a
        LEFT JOIN transactions t ON (a.id = t.debited OR a.id = t.credited) AND t.date <= ?
        JOIN account_types at ON a.type_id = at.id
        WHERE a.type_id IN (
            SELECT id FROM account_types WHERE name IN (
                'Current Asset', 'Fixed Asset',
                'Current Liability', 'Long-term Liability', 'Equity'
            )
        ) -- Filter only relevant account types for balance sheet
        GROUP BY a.id, a.name, a.code, at.name, at.normal_balance -- Group by all selected non-aggregated columns
        -- ORDER BY account type group first, then by code within the group
        ORDER BY
            CASE at.name
                WHEN 'Current Asset' THEN 1
                WHEN 'Fixed Asset' THEN 2
                WHEN 'Current Liability' THEN 3
                WHEN 'Long-term Liability' THEN 4
                WHEN 'Equity' THEN 5
                ELSE 99 -- Should not happen with the WHERE clause, but good practice
            END,
            a.code ASC; -- Sort by code ascending within each type
        """

        self.cursor.execute(query, (data,))
        accounts = self.cursor.fetchall() # Fetches all accounts, now sorted correctly

        # Initialize lists
        ativos_circulantes = []
        ativos_fixos = []
        passivos_circulantes = []
        passivos_nao_circulantes = []
        patrimonio = []

        # Iterate through the *pre-sorted* accounts list and distribute them
        for conta in accounts:
            # Prepare the dictionary item (no need for code here unless interface needs it later)
            item = {'name': conta['name'], 'balance': conta['balance'] or 0} # Use 0 if balance is None

            if conta['account_type'] == 'Current Asset':
                ativos_circulantes.append(item)
            elif conta['account_type'] == 'Fixed Asset':
                ativos_fixos.append(item)
            elif conta['account_type'] == 'Current Liability':
                passivos_circulantes.append(item)
            elif conta['account_type'] == 'Long-term Liability':
                passivos_nao_circulantes.append(item)
            elif conta['account_type'] == 'Equity':
                patrimonio.append(item)
            # No else needed due to the WHERE clause filtering account types

        # No need to close connection here if using instance variables throughout lifespan
        # self.conn.close() # Remove this if conn is reused or closed later

        # The returned lists will now contain items sorted by account code within their type
        return ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio

    def close_connection(self):
        """Close db connection if it's open."""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None # Prevent trying to close again
                self.cursor = None
            except sqlite3.ProgrammingError:
                 # Ignore error if connection is already closed
                 pass