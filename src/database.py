import sqlite3

class Database:
    def __init__(self, db_name="budgetbee/budget.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def execute(self, query, params=()):
        try:
            with self.conn:
                return self.conn.execute(query, params)
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
    
    def fetchall(self, query, params=()):
        try:
            return self.execute(query, params).fetchall()
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
    
    def fetchone(self, query, params=()):
        try:
            return self.execute(query, params).fetchone()
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")
    
    def close(self):
        self.conn.close()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    account TEXT PRIMARY KEY, 
                    balance REAL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category TEXT PRIMARY KEY,
                    type TEXT CHECK (type IN ("INCOME", "EXPENSE"))
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
                    date TEXT,
                    FOREIGN KEY (category) REFERENCES categories (category)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    budget_limit REAL,
                    start_date TEXT,
                    FOREIGN KEY (category) REFERENCES categories (category)
                )
            """)