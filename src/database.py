import sqlite3

class Database:
    def __init__(self, db_name="budget.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def execute(self, query, params=()):
        with self.conn:
            return self.conn.execute(query, params)
    
    def fetchall(self, query, params=()):
        return self.execute(query, params).fetchall()
    
    def fetchone(self, query, params=()):
        return self.execute(query, params).fetchone()
    
    def close(self):
        self.conn.close()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    account TEXT PRIMARY KEY, 
                    balance REAL,
                    date_set TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category TEXT PRIMARY KEY
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    account TEXT,
                    amount REAL, 
                    remaining_balance REAL,
                    category TEXT,
                    details TEXT, 
                    date TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    budget_limit REAL,
                    start_date TEXT
                )
            """)