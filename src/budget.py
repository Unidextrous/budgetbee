from datetime import datetime

class BudgetManager:
    def __init__(self, db):
        self.db = db

    def set_budget(self, category, budget_limit, start_date):
            self.db.execute("REPLACE INTO budgets (category, start_date, budget_limit) VALUES (?, ?, ?)",
                (category, start_date.isoformat(), budget_limit)
            )

    def get_budgets(self, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        budgets_in_range = self.db.fetchall("""
            SELECT category, SUM(budget_limit) as total_budget
            FROM budgets
            WHERE DATE(start_date) >= DATE(?) AND DATE(start_date) <= DATE(?)
            GROUP BY category
        """, (start_date_str, end_date_str))

        previous_budgets = self.db.fetchall("""
            SELECT category, budget_limit, start_date
            FROM budgets
            WHERE DATE(start_date) < DATE(?)
            ORDER BY start_date DESC
        """, (start_date_str,))

        return budgets_in_range, previous_budgets