class CategoryManager:
    def __init__(self, db):
        self.db = db

    def get_categories(self):
        with self.db.conn:
            return [row[0] for row in self.db.fetchall("SELECT category FROM categories")[::-1]]

    def add_category(self, category):
        with self.db.conn:
            existing_categories = self.get_categories()
            if category in existing_categories:
                print("Category already exists.")
                return
            
            self.db.execute("""
                INSERT INTO categories (category)
                VALUES (?)
            """, (category,))
            print(f"Category '{category}' added.")

    def rename_category(self, old_name, new_name):
        self.db.execute("UPDATE categories SET category = ? WHERE category = ?", (new_name, old_name))
        self.db.execute("UPDATE budgets SET category = ? WHERE category = ?", (new_name, old_name))
        self.db.execute("UPDATE transactions SET category = ? WHERE category = ?", (new_name, old_name))

    def delete_category(self, name):
        self.db.execute("DELETE FROM categories WHERE category = ?", (name,))
        self.db.execute("DELETE FROM budgets WHERE category = ?", (name,))
        self.db.execute("DELETE FROM transactions WHERE category = ?", (name,))