from datetime import datetime

class BudgetManager:
    def __init__(self, db):
        self.db = db

    def set_budget(self, category, budget_limit, date):
        # Check if a budget for the same category and date already exists
        existing_budget = self.db.fetchone(
            "SELECT id, budget_limit FROM budgets WHERE category = ? AND date = ?",
            (category, date.isoformat())
        )
        
        if existing_budget:
            # If it exists, add the new budget limit to the existing one
            budget_id, existing_limit = existing_budget
            new_limit = existing_limit + budget_limit
            self.db.execute(
                "UPDATE budgets SET budget_limit = ? WHERE id = ?",
                (new_limit, budget_id)
            )
            print(f"Updated budget for category {category}. New budget limit: ${new_limit}.")
        else:
            # If no existing budget for this category/date, insert a new one
            self.db.execute(
                "INSERT INTO budgets (category, date, budget_limit) VALUES (?, ?, ?)",
                (category, date.isoformat(), budget_limit)
            )
            print(f"Set new budget for category {category} with limit: ${budget_limit}.")

    def get_budgets(self, start_date, end_date):
        # Retrieves all budgets within the specified date range.
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall(
            """SELECT id, category, budget_limit, date
            FROM budgets
            WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)""",
            (start_date_str, end_date_str)
        )
        
    def get_budget_by_id(self, budget_id):
         return self.db.fetchone("SELECT * FROM budgets WHERE id = ?", (budget_id,))
    
    def update_budget_limit(self, budget_id, new_limit):
        self.db.execute("UPDATE budgets SET budget_limit = ? WHERE id = ?", (new_limit, budget_id))

    def update_category(self, budget_id, new_category):
        self.db.execute("UPDATE budgets SET category = ? WHERE id = ?", (new_category, budget_id))

    def update_budget_date(self, budget_id, new_date):
        self.db.execute("UPDATE budgets SET date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def delete(self, budget_id):
        self.db.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))