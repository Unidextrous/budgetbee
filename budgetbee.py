import sqlite3
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from collections import defaultdict

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
                    details TEXT,
                    category TEXT, 
                    date TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT,
                    budget_limit REAL,
                    start_date TEXT,
                    PRIMARY KEY (category, start_date)
                )
            """)
    
    def add_transaction(self, amount, category, details, date):
        with self.conn:
            self.conn.execute("INSERT INTO transactions (amount, category, details, date) VALUES(?, ?, ?, ?)",
                (amount, category, details, date.isoformat()))
    
    def set_budget(self, category, budget_limit, start_date):
        with self.conn:
            self.conn.execute("REPLACE INTO budgets (category, start_date, budget_limit) VALUES (?, ?, ?)",
                (category, start_date.isoformat(), budget_limit)
            )
    
    def get_transactions(self, category, start_date, end_date):
        with self.conn:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            if category == "*":
                category_condition = "1=1"
            else:
                category_condition = "category = ?"
                return self.conn.execute(
                    "SELECT SUM(amount), 'TOTAL', NULL, NULL, NULL FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
                    (start_date_str, end_date_str)
                ).fetchone()

            return self.conn.execute(
                "SELECT * FROM transactions WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
                (category, start_date_str, end_date_str)
            ).fetchall()
        
    def get_budgets(self, start_date, end_date):
        with self.conn:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
        
            budgets_in_range = self.conn.execute("""
                SELECT category, SUM(budget_limit) as total_budget
                FROM budgets
                WHERE DATE(start_date) >= DATE(?) AND DATE(start_date) <= DATE(?)
                GROUP BY category
            """, (start_date_str, end_date_str)).fetchall()

            previous_budgets = self.conn.execute("""
                SELECT category, budget_limit, start_date
                FROM budgets
                WHERE DATE(start_date) < DATE(?)
                ORDER BY start_date DESC
            """, (start_date_str,)).fetchall()

            return budgets_in_range, previous_budgets
    
    def get_categories(self):
        with self.conn:
            return [row[0] for row in self.conn.execute("SELECT category FROM budgets").fetchall()[::-1]]
    
    def visualize_bar(self, start_date, end_date):
        with self.conn:
            spending_data = self.conn.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
                GROUP BY category
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))).fetchall()

            budgets_in_range, previous_budgets = self.get_budgets(start_date, end_date)

            spending_dict = {row[0]: row[1] for row in spending_data}
            budget_dict = {row[0]: row[1] for row in budgets_in_range}

            for category, budget_limit, budget_start_date in previous_budgets:
                spent_before_start = self.conn.execute("""
                    SELECT SUM(amount)
                    FROM transactions
                    WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) < DATE(?)
                """, (category, budget_start_date, start_date)).fetchone()[0] or 0.0

                adjusted_budget = budget_limit - spent_before_start

                if category in budget_dict:
                    budget_dict[category] += adjusted_budget
                else:
                    budget_dict[category] = adjusted_budget
            
            total_spending = sum(spending_dict.values())
            total_budget = sum(budget_dict.values())

            spending_dict['TOTAL'] = total_spending
            budget_dict['TOTAL'] = total_budget

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
                plt.tight_layout()
                plt.show()
            else:
                print("No data available to visualize.")

    def visualize_line(self, category, start_date, end_date):
        with self.conn:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            if category == "*":
                category_condition = "1 = 1"
            else:
                category_condition = "category = ?"

            transactions_query = """
                SELECT DATE(date), SUM(amount)
                FROM transactions
                WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
                AND ({})
                GROUP BY DATE(date)
                ORDER BY DATE(date)
            """.format(category_condition)

            transactions_params = (start_date_str, end_date_str)
            if category != "*":
                transactions_params = (start_date_str, end_date_str, category)

            transactions = self.conn.execute(transactions_query, transactions_params).fetchall()
    
            budgets_query = """
                SELECT DATE(start_date), SUM(budget_limit)
                FROM budgets
                WHERE DATE(start_date) >= DATE(?) AND DATE(start_date) <= DATE(?)
                AND ({})
                GROUP BY DATE(start_date)
                ORDER BY DATE(start_date)
            """.format(category_condition)

            budgets_params = (start_date_str, end_date_str)
            if category != "*":
                budgets_params = (start_date_str, end_date_str, category)

            budgets = self.conn.execute(budgets_query, budgets_params).fetchall()

            spending_over_time = defaultdict(float)
            budget_over_time = defaultdict(float)

            cumulative_spending = 0.0
            cumulative_budget = 0.0

            previous_spending_date = start_date_str
            for date, amount in transactions:
                while previous_spending_date < date:
                    spending_over_time[previous_spending_date] = cumulative_spending
                    previous_spending_date = (datetime.strptime(previous_spending_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                cumulative_spending += amount
                spending_over_time[date] = cumulative_spending
                previous_spending_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            
            while previous_spending_date <= end_date_str:
                spending_over_time[previous_spending_date] = cumulative_spending
                previous_spending_date = (datetime.strptime(previous_spending_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

            previous_budget_date = start_date_str
            for date, budget in budgets:
                while previous_budget_date < date:
                    budget_over_time[previous_budget_date] = cumulative_budget
                    previous_budget_date = (datetime.strptime(previous_budget_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                cumulative_budget += budget
                budget_over_time[date] = cumulative_budget
                previous_budget_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

                while previous_budget_date <= end_date_str:
                    budget_over_time[previous_budget_date] = cumulative_budget
                    previous_budget_date = (datetime.strptime(previous_budget_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

            dates = sorted(set(spending_over_time.keys()) | set(budget_over_time.keys()))
            spending_values = [spending_over_time[date] for date in dates]
            budget_values = [budget_over_time[date] for date in dates]

            plt.figure(figsize = (10, 5))
            plt.plot(dates, spending_values, label = "Cumulative Spending", color = "blue")
            plt.plot(dates, budget_values, label = "Cumulative Budget", color = "green")
            plt.xlabel("Date")
            plt.ylabel("Amount")
            plt.title(f"Cumulative Spending vs Budget Over Time ({category})")
            plt.legend()
            plt.grid(True)
            plt.xticks(rotation = 45)
            plt.tight_layout()
            plt.show()


    def clear_data(self):
        with self.conn:
            self.conn.execute("DELETE FROM transactions")
            self.conn.execute("DELETE FROM budgets")
    
    def remove_transaction(self, transaction_id):
        with self.conn:
            self.conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        
tracker = BudgetTracker()
tracker.clear_data()

def main():
    tracker = BudgetTracker()
    
    while True:
        print("\nOptions:")
        print("1. Set a budget")
        print("2. Add a transaction")
        print("3. Display transactions in a category and date range")
        print("4. Visualize by Category")
        print("5. Visualize Over Time")
        print("6. Delete a transaction")
        print("7. Exit")
        choice = input("Enter your choice (1/2/3/4/5/6/7): ")

        if choice == "1":
            try:
                category = input("Enter the category name: ").upper()
                budget_limit = float(input("Enter the budget limit: "))
                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                tracker.set_budget(category, budget_limit, start_date)
                print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")

        elif choice == "2":    
            try:
                categories = tracker.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                    continue

                print(f"Available categories: {', '.join(set(categories))}")
                category = input("Enter the transaction category: ").upper()
                if category not in categories:
                    print("Category not in tracker. Please enter a valid category.")
                    continue

                amount = float(input("Enter the transaction amount: "))
                details = input("Enter transaction details: ").upper()
                date_str = input("Enter the transaction date (YYYY-MM-DD): ")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                tracker.add_transaction(amount, category, details, date)
                print("Transaction added.")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")
        
        elif choice == "3":
            try:
                categories = tracker.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                    continue

                print(f"Available categories: {', '.join(set(categories))} (* for ALL)")
                category = input("Enter the transaction category: ").upper()
                if category not in categories:
                    print("Category not in tracker. Please enter a valid category.")
                    continue

                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                transactions = tracker.get_transactions(category, start_date, end_date)
                if transactions:
                    print(f"Transactions from {start_date} to {end_date}:")
                    for txn in transactions:
                        txn_id, amount, category, details, date = txn
                        print(f"ID: {txn_id}, Amount: {amount}, Category: {category}, Details: {details}, Date: {date}")
                else:
                    print("No transactions found for the specified date range.")
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "4":
            try:
                start_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                tracker.visualize_bar(start_date, end_date)
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "5":
            try:
                categories = tracker.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                
                print(f"Available categories: {', '.join(set(categories))} (* for TOTAL)")
                category = input("Enter the category for visualization: ").upper()

                start_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date for visualization (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                tracker.visualize_line(category, start_date, end_date)
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "6":
            try:
                txn_id = int(input("Enter the transaction ID to delete: "))
                tracker.remove_transaction(txn_id)
                print(f"Transaction with ID {txn_id} deleted.")
            except ValueError:
                print("Invalid input. Please enter a valid transaction ID.")

        elif choice == "7":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

if __name__ == "__main__":
    main()