class CategoryManager:
    def __init__(self, db):
        self.db = db

    def add_category(self, category, category_type):
        with self.db.conn:
            existing_categories = self.get_categories_by_type()
            if category in existing_categories:
                print("Category already exists.")
                return
            
            self.db.execute("""
                INSERT INTO categories (category, type) VALUES (?, ?)
            """, (category, category_type))
            print(f"Category '{category}' added as {category_type}.")
    
    def get_categories_by_type(self, category_type=None):
        query = "SELECT category FROM categories"
        params = ()
        if category_type:
            query += " WHERE type = ?"
            params = (category_type,)
        
        with self.db.conn:
            return [row[0] for row in self.db.fetchall(query, params)]

    def get_category_by_transaction_id(self, transaction_id):
        return self.db.fetchone("SELECT category FROM transactions WHERE id = ?", (transaction_id,))[0]

    def get_category_type(self, category):
        return self.db.fetchone("SELECT type FROM categories WHERE category = ?", (category,))[0]
        
    def rename_category(self, old_name, new_name):
        self.db.execute("UPDATE categories SET category = ? WHERE category = ?", (new_name, old_name))
        self.db.execute("UPDATE budgets SET category = ? WHERE category = ?", (new_name, old_name))
        self.db.execute("UPDATE transactions SET category = ? WHERE category = ?", (new_name, old_name))

    def delete(self, category):
        self.db.execute("DELETE FROM categories WHERE category = ?", (category,))
        self.db.execute("DELETE FROM budgets WHERE category = ?", (category,))
        self.db.execute("DELETE FROM transactions WHERE category = ?", (category,))