import sqlite3

class Database:
    _instance = None  
    
    def __new__(cls):  
        if cls._instance is None:  
            cls._instance = super(Database, cls).__new__(cls)  
            cls._instance.conn = sqlite3.connect("budgetbee/budget.db")  
        return cls._instance  


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
                CREATE TABLE IF NOT EXISTS accounts (
                    account TEXT PRIMARY KEY, 
                    starting_balance REAL,
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
                    FOREIGN KEY (account) REFERENCES accounts (account)
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