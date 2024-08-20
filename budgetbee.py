import sqlite3
from datetime import datetime
from matplotlib import pyplot as plt

class Transaction:
    def __init__(self, account, amount, category, date = None):
        self.account = account
        self.amount = amount
        self.category = category
        self.date = date or datetime.now()

class BudgetTracker:
    def __init__(self, db_name = "budget.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY, 
                    account TEXT,
                    amount REAL, 
                    category TEXT, 
                    date TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    budget_limit REAL
                )
            """)
    
    def add_transaction(self, account, amount, category, date):
        with self.conn:
            self.conn.execute("INSERT INTO transactions (account, amount, category, date) VALUES(?, ?, ?, ?)",
                (account, amount, category, date.isoformat()))
    
    def set_budget(self, category, budget_limit):
        with self.conn:
            self.conn.execute("REPLACE INTO budgets (category, budget_limit) VALUES (?, ?)", (category, budget_limit))
    
    def get_transactions(self):
        with self.conn:
            return self.conn.execute("SELECT * FROM transactions").fetchall()
    
    def get_transactions_by_date_range(self, start_date, end_date):
        with self.conn:
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()
            return self.conn.execute("SELECT * FROM transactions WHERE date BETWEEN ? AND ?", (start_date_str, end_date_str)).fetchall()
    
    def visualize_spending_vs_budget(self):
        with self.conn:
            spending_data = self.conn.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions
                GROUP BY category
            """).fetchall()

            budget_data = self.conn.execute("""
                SELECT category, budget_limit
                FROM budgets
            """).fetchall()

            spending_dict = {row[0]: row[1] for row in spending_data}
            budget_dict = {row[0]: row[1] for row in budget_data}

            categories = []
            spending = []
            budgets = []

            for category in budget_dict:
                categories.append(category)
                spending.append(spending_dict.get(category, 0))
                budgets.append(budget_dict[category])

            if categories and spending:
                x = range(len(categories))
                plt.figure(figsize = (10, 5))

                plt.grid(axis = "y", which = "both", linestyle = "--", linewidth = 0.5, color = "grey", zorder = 0)
                plt.yticks(range(0, int(max(max(spending), max(budgets)) + 100), 100))
                
                plt.bar(x, spending, width = 0.4, label = "Spending", align = "center", color = "blue", zorder = 3)
                plt.bar(x, budgets, width = 0.4, label = "Budget", align = "edge", color = "green", zorder = 3)

                plt.xlabel("Category")
                plt.ylabel("Amount")
                plt.title("Spending vs Budget by Category")
                plt.xticks(x, categories, rotation = 45)

                plt.legend()
                plt.tight_layout
                plt.show()
            else:
                print("No data available to visualize")
        
    def clear_data(self):
        with self.conn:
            self.conn.execute("DELETE FROM transactions")
            self.conn.execute("DELETE FROM budgets")
    
    def remove_transaction(self, transaction_id):
        with self.conn:
            self.conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            self.conn.execute("""
                UPDATE transactions
                SET id = id - 1
                WHERE id > ?
            """, (transaction_id,))
        
# To initialize the budget tracker:
# tracker = BudgetTracker()

# To clear transaction table (BE CAREFUL USING THIS FEATURE, IT WILL CLEAR THE DATA IN THE DATABASE)
# tracker.clear_data()

# To add a transaction:
# tracker.add_transaction(account: str, amount: float, category: str, date: date)
# Examples:
# tracker.add_transaction("Account 1", 50.75, "Groceries", datetime(2024, 8, 10, 0, 0, 0))
# tracker.add_transaction("Account 2", 1200, "Rent", datetime.now())

# To set a budget for a category:
# tracker.set_budget(category: str, amount: float)
# Example:
# tracker.set_budget("Groceries", 300)

# To retrieve and print all transactions:
# transactions = tracker.get_transactions()
# print("Transactions:")
# for transaction in transactions:
    # print(transaction)

# print()

# To retrieve and print all transactions in a date range:
# start_date = datetime(year: int, month: int, day: int)
# end_date = datetime(year: int, month: int, day: int, 23, 59, 59)
# print(f"Transactions between {start_date} and {end_date}")
# transactions_in_range = tracker.get_transactions_by_date_range(start_date, end_date)
# for transaction in transactions_in_range:
    # print(transaction)

# Visualize spending and budget by category
# tracker.visualize_spending_vs_budget()

# TEST

tracker = BudgetTracker()

# Clear existing data
tracker.clear_data()

# Add a few transactions
tracker.add_transaction("Account 1", 50.75, "Groceries", datetime(2024, 8, 10))
tracker.add_transaction("Account 2", 1200, "Rent", datetime.now())
tracker.add_transaction("Account 1", 200, "Utilities", datetime(2024, 8, 15))
tracker.add_transaction("Account 2", 100, "Groceries", datetime(2024, 8, 20))

# Set a budget for a category
tracker.set_budget("Groceries", 300)
tracker.set_budget("Rent", 1200)
tracker.set_budget("Utilities", 350)
tracker.set_budget("Allowance", 100)

# Visualize spending by category
tracker.visualize_spending_vs_budget()