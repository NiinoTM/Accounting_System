import sqlite3
from data.create_database import DatabaseManager

db_manager = DatabaseManager()
with db_manager as db:
    db.cursor.execute("SELECT * FROM accounts WHERE type_id = 6")  # Or use a different condition if you know the account's code or name
    account_data = db.cursor.fetchall()
    print(account_data)