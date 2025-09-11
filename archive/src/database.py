import sqlite3

# The Database class implements the Singleton pattern to manage a single connection to the SQLite database.
class Database:
    _instance = None  # Class variable to hold the single instance of Database

    def __new__(cls):  
        if cls._instance is None:  
            # Create a new instance if one doesn't exist
            cls._instance = super(Database, cls).__new__(cls)  
            # Establish a connection to the SQLite database
            cls._instance.conn = sqlite3.connect("budgetbee/budget.db")  
        return cls._instance  # Return the singleton instance

    # Method to execute a query with optional parameters
    def execute(self, query, params=()):
        try:
            with self.conn:  # Use a context manager for transaction management
                return self.conn.execute(query, params)  # Execute the query
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")  # Handle database errors

    # Method to fetch all results from a query
    def fetchall(self, query, params=()):
        try:
            return self.execute(query, params).fetchall()  # Return all results
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")  # Handle database errors

    # Method to fetch a single result from a query
    def fetchone(self, query, params=()):
        try:
            return self.execute(query, params).fetchone()  # Return one result
        except sqlite3.DatabaseError as e:
            print(f"Database error: {e}")  # Handle database errors

    # Method to close the database connection
    def close(self):
        self.conn.close()  # Close the connection

    # Method to create necessary tables in the database
    def create_tables(self):
        with self.conn:  # Use a context manager for transaction management
            # Create accounts table if it does not exist
            self.conn.execute(""" 
                CREATE TABLE IF NOT EXISTS accounts (
                    account TEXT PRIMARY KEY, 
                    starting_balance REAL,
                    balance REAL
                )
            """)
            # Create categories table if it does not exist
            self.conn.execute(""" 
                CREATE TABLE IF NOT EXISTS categories (
                    category TEXT PRIMARY KEY,
                    type TEXT CHECK (type IN ("INCOME", "EXPENSE"))
                )
            """)
            # Create transactions table if it does not exist
            self.conn.execute(""" 
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    account TEXT,
                    amount REAL, 
                    remaining_balance REAL,
                    category TEXT,
                    details TEXT, 
                    date TEXT,
                    FOREIGN KEY (account) REFERENCES accounts (account),
                    FOREIGN KEY (category) REFERENCES categories (category)
                )
            """)
            # Create budgets table if it does not exist
            self.conn.execute(""" 
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY,
                    category TEXT,
                    budget_limit REAL,
                    remaining_budget REAL,
                    date TEXT,
                    transaction_id INTEGER,
                    FOREIGN KEY (category) REFERENCES categories (category),
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id)
                )
            """)