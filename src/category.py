class CategoryManager:
    def __init__(self, db):
        self.db = db  # Initialize with a reference to the database connection

    # Method to add a new category to the database
    def add_category(self, category, category_type):
        # Insert the new category into the categories table
        self.db.execute("""
            INSERT INTO categories (category, type) VALUES (?, ?)
        """, (category, category_type))
        print(f"Category '{category}' added as {category_type}.")
    
    # Method to retrieve categories, optionally filtered by type
    def get_categories_by_type(self, category_type=None):
        query = "SELECT category FROM categories"  # Base query
        params = ()
        if category_type:
            query += " WHERE type = ?"  # Add filter for category type
            params = (category_type,)
        
        with self.db.conn:  # Use a context manager for transaction management
            return [row[0] for row in self.db.fetchall(query, params)]  # Return list of categories

    # Method to get the category associated with a specific transaction ID
    def get_category_by_transaction_id(self, transaction_id):
        return self.db.fetchone("SELECT category FROM transactions WHERE id = ?", (transaction_id,))[0]

    # Method to get the type of a specific category
    def get_category_type(self, category):
        return self.db.fetchone("SELECT type FROM categories WHERE category = ?", (category,))[0]
        
    # Method to rename a category and update associated records
    def rename_category(self, old_name, new_name):
        self.db.execute("UPDATE categories SET category = ? WHERE category = ?", (new_name, old_name))  # Rename category
        self.db.execute("UPDATE budgets SET category = ? WHERE category = ?", (new_name, old_name))  # Update budgets
        self.db.execute("UPDATE transactions SET category = ? WHERE category = ?", (new_name, old_name))  # Update transactions

    # Method to delete a category and all associated records
    def delete(self, category):
        self.db.execute("DELETE FROM categories WHERE category = ?", (category,))  # Delete category
        self.db.execute("DELETE FROM budgets WHERE category = ?", (category,))  # Delete associated budgets
        self.db.execute("DELETE FROM transactions WHERE category = ?", (category,))  # Delete associated transactions
