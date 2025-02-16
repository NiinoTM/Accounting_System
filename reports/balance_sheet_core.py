# reports/balance_sheet_core.py
import sqlite3
from data.create_database import DatabaseManager  # Or your DB manager path

class BalanceSheet:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.conn = sqlite3.connect(self.db_manager.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def calcular_saldos_na_data(self, data):
        """Calculates account balances up to a specified date."""

        query = """
        SELECT
            a.name,
            a.code,
            at.name as account_type,
            at.normal_balance,
            SUM(CASE
                WHEN t.debited = a.id THEN t.amount
                WHEN t.credited = a.id THEN -t.amount
                ELSE 0
            END) AS balance
        FROM accounts a
        LEFT JOIN transactions t ON a.id = t.debited OR a.id = t.credited
        JOIN account_types at ON a.type_id = at.id
        WHERE t.date <= ? OR t.date IS NULL  -- Include transactions up to the date
        GROUP BY a.id, a.name
        ORDER BY a.name
        """

        self.cursor.execute(query, (data,))
        accounts = self.cursor.fetchall()


        ativos_circulantes = []
        ativos_fixos = []
        passivos_circulantes = []
        passivos_nao_circulantes = []
        patrimonio = []

        for conta in accounts:
            if conta['account_type'] == 'Current Asset':
                ativos_circulantes.append({'name': conta['name'], 'balance': conta['balance'] or 0}) # 0 if None
            elif conta['account_type'] == 'Fixed Asset':
                ativos_fixos.append({'name': conta['name'], 'balance': conta['balance'] or 0})
            elif conta['account_type'] == 'Current Liability':
                passivos_circulantes.append({'name': conta['name'], 'balance': conta['balance'] or 0})
            elif conta['account_type'] == 'Long-term Liability':
                passivos_nao_circulantes.append({'name': conta['name'], 'balance': conta['balance'] or 0})
            elif conta['account_type'] == 'Equity':
                patrimonio.append({'name': conta['name'], 'balance': conta['balance'] or 0})

        self.conn.close()
        return ativos_circulantes, ativos_fixos, passivos_circulantes, passivos_nao_circulantes, patrimonio

    def close_connection(self):
        """Close db connection"""
        self.conn.close()