from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from collections import defaultdict

class Visualizer:
    def __init__(self, db, budget_manager, transaction_manager):
        self.db = db
        self.budget_manager = budget_manager
        self.transaction_manager = transaction_manager

    def visualize_bar(self, start_date, end_date):
            
        spending_data = self.db.fetchall("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
            GROUP BY category
        """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        budgets_in_range, previous_budgets = self.budget_manager.get_budgets_by_category("*", start_date, end_date)

        spending_dict = {row[0]: row[1] for row in spending_data}
        budget_dict = {row[0]: row[1] for row in budgets_in_range}

        try:
            for category, budget_limit, budget_start_date in previous_budgets:
                spent_before_start = self.db.conn.fetchone("""
                    SELECT SUM(amount)
                    FROM transactions
                    WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) < DATE(?)
                """, (category, budget_start_date, start_date))[0] or 0.0
                
                adjusted_budget = budget_limit - spent_before_start

                if category in budget_dict:
                    budget_dict[category] += adjusted_budget
                else:
                    budget_dict[category] = adjusted_budget
        except ValueError:
            print("Missing data for this time range.")

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

        transactions = self.db.fetchall(transactions_query, transactions_params)
    
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

        budgets = self.db.fetchall(budgets_query, budgets_params)

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

    def visualize_pie(self, start_date, end_date):
        spending_data = self.db.fetchall("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
            GROUP BY category
        """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        if not spending_data:
            print("No spending data available for the given date range.")
            return

        categories = [row[0] for row in spending_data]
        amounts = [row[1] for row in spending_data]

        plt.figure(figsize=(8, 8))
        plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        plt.title(f"Spending Distribution by Category ({start_date.date()} - {end_date.date()})")
        plt.show()