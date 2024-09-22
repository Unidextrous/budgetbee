from datetime import datetime

class TransactionManager:
    def __init__(self, db, account_manager, category_manager):
        self.db = db
        self.account_manager = account_manager
        self.category_manager = category_manager

    def add_transaction(self, account, amount, remaining_balance, category, details, date):
        balance = self.account_manager.get_balance(account)
        
        # Add the new transaction first
        self.db.execute("""
            INSERT INTO transactions
            (account, amount, remaining_balance, category, details, date) VALUES(?, ?, ?, ?, ?, ?)
        """, (account, amount, 0, category, details, date.isoformat()))

        income_categories = self.category_manager.get_categories_by_type("INCOME")
        expense_categories = self.category_manager.get_categories_by_type("EXPENSE")

        if category in income_categories:
            category_type = "INCOME"
        elif category in expense_categories:
            category_type = "EXPENSE"
        
        # After adding, recalculate the remaining balances
        self.update_all_remaining_balances(account)
    
    def get_transactions_by_category(self, category, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (category, start_date_str, end_date_str))

    def get_transactions_by_category_type(self, category_type, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall("""
            SELECT t.* FROM transactions t
            JOIN categories c on t.category = c.category
            WHERE c.type = ? AND DATE (date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (category_type, start_date_str, end_date_str))
    
    def get_transactions_by_account(self, account, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        if account == "*":
            return self.db.fetchall("""
                SELECT * FROM transactions
                WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
            """, (start_date_str, end_date_str))
            
        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE account = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (account, start_date_str, end_date_str))

    def get_transaction_by_id(self, transaction_id):
         return self.db.fetchone("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    
    def get_transactions_after(self, account, date, transaction_id):
        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE account = ? AND (date > ? OR (date = ? AND id > ?))
            ORDER BY date, id
        """, (account, date, date, transaction_id))

    def update_transaction_account(self, transaction_id, category_type, new_account_name):
        # Get the old transaction details
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            old_account_name, amount = old_transaction[1], old_transaction[2]
            
            # Adjust balances between the two accounts
            if category_type == "INCOME":
                self.account_manager.adjust_balance(old_account_name, -amount)
                self.account_manager.adjust_balance(new_account_name, amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(old_account_name, amount)
                self.account_manager.adjust_balance(new_account_name, -amount)
            
            # Update the transaction account in the database
            self.db.execute("UPDATE transactions SET account = ? WHERE id = ?", (new_account_name, transaction_id))
            
    def update_transaction_amount(self, transaction_id, category_type, new_amount):
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            account, old_amount = old_transaction[1], old_transaction[2]
            if category_type == "INCOME":
                self.account_manager.adjust_balance(account, -old_amount)
                self.account_manager.adjust_balance(account, new_amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(account, old_amount)
                self.account_manager.adjust_balance(account, -new_amount)
        self.db.execute("UPDATE transactions SET amount = ? WHERE id = ?", (new_amount, transaction_id))
    
    def update_all_remaining_balances(self, account):
        starting_balance = self.account_manager.get_starting_balance(account)

        transactions = self.db.fetchall("""
            SELECT id, amount, category, date
            FROM transactions
            WHERE account = ?
            ORDER BY date, id
        """, (account,))

        remaining_balance = starting_balance

        for transaction in transactions:
            transaction_id, amount, category, date = transaction

            income_categories = self.category_manager.get_categories_by_type("INCOME")
            expense_categories = self.category_manager.get_categories_by_type("EXPENSE")
            if category in income_categories:
                remaining_balance += amount
            elif category in expense_categories:
                remaining_balance -= amount

            self.db.execute("""
                UPDATE transactions
                SET remaining_balance = ? WHERE id = ?
            """, (remaining_balance, transaction_id))

            self.db.execute("""
                UPDATE accounts
                SET balance = ? WHERE account = ?
            """, (remaining_balance, account))

    def update_category(self, transaction_id, new_category):
        self.db.execute("UPDATE transactions SET category = ? WHERE id = ?", (new_category, transaction_id))

    def update_transaction_details(self, transaction_id, new_details):
        self.db.execute("UPDATE transactions SET details = ? WHERE id = ?", (new_details, transaction_id))

    def update_transaction_date(self, budget_id, new_date):
        self.db.execute("UPDATE transactions SET date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def delete(self, transaction_id, category_type):
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            account_name, amount = transaction[1], transaction[2]
            
            # Subtract the amount from the account balance
            if category_type == "INCOME":
                self.account_manager.adjust_balance(account_name, -amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(account_name, amount)
        self.db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))