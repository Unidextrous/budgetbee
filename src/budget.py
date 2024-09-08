from datetime import datetime

class BudgetManager:
    def __init__(self, db):
        self.db = db

    def set_budget(self, category, budget_limit, start_date):
        self.db.execute("INSERT INTO budgets (category, start_date, budget_limit) VALUES (?, ?, ?)",
           (category, start_date.isoformat(), budget_limit)
        )

    def get_budgets_by_date(self, category, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        if category == "*":
            budgets_in_range = self.db.fetchall(
                """SELECT id, category, budget_limit, start_date
                FROM budgets
                WHERE DATE(start_date) >= DATE(?) AND DATE(start_date) <= DATE(?)""",
                (start_date_str, end_date_str)
            )
        else:
            budgets_in_range = self.db.fetchall(
                """SELECT id, category, budget_limit, start_date
                FROM budgets
                WHERE category = ? AND DATE(start_date) >= DATE(?) AND DATE(start_date) <= DATE(?)""",
                (category, start_date_str, end_date_str)
            )

        previous_budgets = self.db.fetchall("""
            SELECT id, category, budget_limit, start_date
            FROM budgets
            WHERE DATE(start_date) < DATE(?)
            ORDER BY start_date DESC
        """, (start_date_str,))

        return budgets_in_range, previous_budgets
    
    def get_budget_by_id(self, budget_id):
         return self.db.fetchone("SELECT * FROM budgets WHERE id = ?", (budget_id,))
    
    def update_budget_limit(self, budget_id, new_limit):
        self.db.execute("UPDATE budgets SET budget_limit = ? WHERE id = ?", (new_limit, budget_id))

    def update_category(self, budget_id, new_category):
        self.db.execute("UPDATE budgets SET category = ? WHERE id = ?", (new_category, budget_id))

    def update_budget_date(self, budget_id, new_date):
        self.db.execute("UPDATE budgets SET start_date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def remove_budget(self, budget_id):
        self.db.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))