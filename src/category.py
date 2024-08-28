class CategoryManager:
    def __init__(self, db):
        self.db = db

    def get_categories(self):
        with self.db.conn:
            return [row[0] for row in self.db.fetchall("SELECT category FROM budgets")[::-1]]

    def add_category(self, category):
        with self.db.conn:
            existing_categories = self.get_categories()
            if category in existing_categories:
                print("Category already exists.")
                return
            
            self.db.execute("""
                INSERT INTO budgets (category, budget_limit, start_date)
                VALUES (?, 0, DATE('now'))
            """, (category,))
            print(f"Category '{category}' added.")