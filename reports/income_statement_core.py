import sqlite3
from create_database import DatabaseManager

def generate_income_statement_data(start_date, end_date):
    """
    Generates income statement data.
    """
    db_manager = DatabaseManager()
    try:
        with db_manager as db:
            # Query to get transaction data with correct sign based on account type
            db.cursor.execute("""
                SELECT
                    a.name AS account_name,
                    at.name AS account_type,
                    SUM(CASE
                        WHEN t.debited = a.id THEN t.amount
                        WHEN t.credited = a.id THEN -t.amount
                        ELSE 0
                    END) AS balance
                FROM transactions t
                JOIN accounts a ON t.debited = a.id OR t.credited = a.id
                JOIN account_types at ON a.type_id = at.id
                WHERE t.date BETWEEN ? AND ?
                  AND at.name IN ('Revenue', 'Expense')
                GROUP BY a.name, at.name
                ORDER BY at.name, a.name
            """, (start_date, end_date))
            transactions = db.cursor.fetchall()

            revenues = []
            expenses = []
            total_revenue = 0
            total_expenses = 0

            for row in transactions:
                account_name = row['account_name']
                account_type = row['account_type']
                balance = row['balance']

                if account_type == 'Revenue':
                    # Revenue accounts normally have credit balances (negative in our query)
                    # So we negate the balance to show revenue as positive
                    adjusted_balance = -balance
                    revenues.append((account_name, adjusted_balance))
                    total_revenue += adjusted_balance
                elif account_type == 'Expense':
                    # Expense accounts normally have debit balances (positive in our query)
                    # So we keep the balance as is (already positive)
                    expenses.append((account_name, balance))
                    total_expenses += balance

            # Calculate net income: revenue MINUS expenses
            net_income = total_revenue - total_expenses

            return {
                'Revenues': revenues,
                'Expenses': expenses,
                'Total Revenue': total_revenue,
                'Total Expenses': total_expenses,
                'Net Income': net_income
            }

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None