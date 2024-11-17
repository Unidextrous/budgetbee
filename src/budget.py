from datetime import datetime

class BudgetManager:
    def __init__(self, db):
        self.db = db

    def set_budget(self, category, budget_limit, date, transaction_id):
        # Check if a budget for the same category and date already exists
        existing_budget = self.db.fetchone(
            "SELECT id, budget_limit FROM budgets WHERE category = ? AND transaction_id = ?",
            (category, transaction_id)
        )
        
        if existing_budget:
            # If it exists, add the new budget limit to the existing one
            budget_id, existing_limit = existing_budget
            new_limit = existing_limit + budget_limit
            self.db.execute(
                "UPDATE budgets SET budget_limit = ?, remaining_budget = ?, transaction_id = ? WHERE id = ?",
                (new_limit, new_limit, transaction_id, budget_id)
            )
            print(f"Updated budget for category {category}. New budget limit: ${new_limit}.")
        else:
            # If no existing budget for this category/date, insert a new one
            self.db.execute(
                "INSERT INTO budgets (category, budget_limit, remaining_budget, date, transaction_id) VALUES (?, ?, ?, ?, ?)",
                (category, budget_limit, budget_limit, date.isoformat(), transaction_id)
            )
            print(f"Set new budget for category {category} with limit: ${budget_limit}.")

    def get_budgets_by_category(self, category, start_date=None, end_date=None, ascending=True):
        # Retrieves budgets for a specific category within the specified date range.
        query = "SELECT * FROM budgets WHERE category = ?"
        params = [category]

        if start_date and end_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            query += " AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)"
            params.extend([start_date_str, end_date_str])

        if ascending:
            query += " ORDER BY date, id"
        else:
            query += " ORDER BY date DESC, id DESC"
        return self.db.fetchall(query, params)
    
    def get_budgets_by_date(self, start_date, end_date):
        # Retrieves all budgets within the specified date range.
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall(
            """SELECT * FROM budgets
               WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)""",
            (start_date_str, end_date_str)
        )
        
    def get_budgets_by_transaction_id(self, transaction_id):
        # Retrieves all budgets for the specified transaction ID.
        return self.db.fetchall(
            """SELECT * FROM budgets WHERE transaction_id = ?""",
            (transaction_id,)
        )
    
    def update_budget_limit(self, budget_id, new_limit):
        self.db.execute("UPDATE budgets SET budget_limit = ? WHERE id = ?", (new_limit, budget_id))

    def update_remaining_budget(self, budget_id, new_limit):
        self.db.execute("UPDATE budgets SET remaining_budget = ? WHERE id = ?", (new_limit, budget_id))

    def update_category(self, budget_id, new_category):
        self.db.execute("UPDATE budgets SET category = ? WHERE id = ?", (new_category, budget_id))

    def update_budget_date(self, budget_id, new_date):
        self.db.execute("UPDATE budgets SET date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def delete(self, budget_id):
        self.db.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))

    def delete_by_transaction_id(self, transaction_id):
        self.db.execute("DELETE FROM budgets WHERE transaction_id = ?", (transaction_id,))