import sqlite3
from datetime import datetime
from matplotlib import pyplot as plt

class BudgetTracker:
    def __init__(self, db_name = "budget.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
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
    
    def add_transaction(self, amount, category, date):
        with self.conn:
            self.conn.execute("INSERT INTO transactions (amount, category, date) VALUES(?, ?, ?)",
                (amount, category, date.isoformat()))
    
    def set_budget(self, category, budget_limit):
        with self.conn:
            self.conn.execute("REPLACE INTO budgets (category, budget_limit) VALUES (?, ?)", (category, budget_limit))
    
    def get_transactions(self, category, start_date, end_date):
        with self.conn:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            if category == "*":
                return self.conn.execute(
                    "SELECT * FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)", (start_date_str, end_date_str)
                ).fetchall()
            return self.conn.execute(
                "SELECT * FROM transactions WHERE category = ? AND DATE(date) >= ? AND DATE(date) <= DATE(?)", (category, start_date_str, end_date_str)
            ).fetchall()
    
    def get_categories(self):
        with self.conn:
            return [row[0] for row in self.conn.execute("SELECT category FROM budgets").fetchall()[::-1]]
    
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
                print("No data available to visualize.")
        
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
        
tracker = BudgetTracker()
tracker.clear_data()

def main():
    tracker = BudgetTracker()
    
    while True:
        print("\nOptions:")
        print("1. Set a budget for a category")
        print("2. Add a transaction")
        print("3. Display transactions in a category and date range")
        print("4. Visualize spending vs budget")
        print("5. Delete a transaction")
        print("6. Exit")
        choice = input("Enter your choice (1/2/3/4/5/6): ")

        if choice == "1":
            try:
                category = input("Enter the category name: ").upper()
                budget_limit = input("Enter the budget limit: ")
                tracker.set_budget(category, budget_limit)
                print(f"Budget set for category {category}: {budget_limit}")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")

        elif choice == "2":    
            try:
                categories = tracker.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                    continue

                print(f"Available categories: {', '.join(categories)}")
                category = input("Enter the transaction category: ").upper()
                if category not in categories:
                    print("Category not in tracker. Please enter a valid category.")
                    continue

                amount = float(input("Enter the transaction amount: "))
                date_str = input("Enter the transaction date (YYYY-MM-DD): ")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                tracker.add_transaction(amount, category, date)
                print("Transaction added.")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")
        
        elif choice == "3":
            try:
                categories = tracker.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                    continue

                print(f"Available categories: {', '.join(categories)} (* for ALL)")
                category = input("Enter the transaction category: ").upper()

                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                transactions = tracker.get_transactions(category, start_date, end_date)
                if transactions:
                    print(f"Transactions from {start_date} to {end_date}:")
                    for txn in transactions:
                        txn_id, amount, category, date = txn
                        print(f"ID: {txn_id}, Amount: {amount}, Category: {category}, Date: {date}")
                else:
                    print("No transactions found for the specified date range.")
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "4":
            tracker.visualize_spending_vs_budget()
        
        elif choice == "5":
            try:
                txn_id = int(input("Enter the transaction ID to delete: "))
                tracker.remove_transaction(txn_id)
                print(f"Transaction with ID {txn_id} deleted.")
            except ValueError:
                print("Invalid input. Please enter a valid transaction")

        elif choice == "6":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()