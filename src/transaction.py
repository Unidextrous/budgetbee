from datetime import datetime

class TransactionManager:
    def __init__(self, db, balance_manager):
        self.db = db
        self.balance_manager = balance_manager

    def add_transaction(self, account, amount, remaining_balance, category, details, date):
        self.db.execute("""INSERT INTO transactions
            (account, amount, remaining_balance, category, details, date) VALUES(?, ?, ?, ?, ?, ?)""",
            (account, amount, remaining_balance, category, details, date.isoformat())
        )
    
    def get_transactions_by_category(self, category, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        if category == "*":
            return self.db.fetchall(
                "SELECT * FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
                (start_date_str, end_date_str)
            )
            
        return self.db.fetchall(
            "SELECT * FROM transactions WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
            (category, start_date_str, end_date_str)
        )
    
    def get_transactions_by_account(self, account, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        if account == "*":
            return self.db.fetchall(
                "SELECT * FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
                (start_date_str, end_date_str)
            )
            
        return self.db.fetchall(
            "SELECT * FROM transactions WHERE account = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
            (account, start_date_str, end_date_str)
        )

    def get_transaction_by_id(self, transaction_id):
         return self.db.fetchone("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    
    def get_transactions_after(self, account, date, transaction_id):
        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE account = ?
            AND (date > ? OR (date = ? AND id > ?))
            ORDER BY date, id
        """, (account, date, date, transaction_id))
    
    def update_transaction_amount(self, transaction_id, new_amount):
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            account, old_amount = old_transaction[1], old_transaction[2]
            self.balance_manager.adjust_balance(account, old_amount)
            self.balance_manager.adjust_balance(account, -new_amount)
        self.db.execute("UPDATE transactions SET amount = ? WHERE id = ?", (new_amount, transaction_id))

    def update_transaction_account(self, transaction_id, new_account_name):
        # Get the old transaction details
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            old_account_name, amount = old_transaction[1], old_transaction[2]
            
            # Adjust balances between the two accounts
            self.balance_manager.adjust_balance(old_account_name, amount)
            self.balance_manager.adjust_balance(new_account_name, -amount)
            
            # Update the transaction account in the database
            self.db.execute("UPDATE transactions SET account = ? WHERE id = ?", (new_account_name, transaction_id))

    def update_remaining_balance(self, transaction_id, new_remaining_balance):
        self.db.execute("UPDATE transactions SET remaining_balance = ? WHERE id = ?", (new_remaining_balance, transaction_id))

    def update_category(self, transaction_id, new_category):
        self.db.execute("UPDATE transactions SET category = ? WHERE id = ?", (new_category, transaction_id))

    def update_transaction_details(self, transaction_id, new_details):
        self.db.execute("UPDATE transactions SET details = ? WHERE id = ?", (new_details, transaction_id))

    def update_transaction_date(self, budget_id, new_date):
        self.db.execute("UPDATE transactions SET date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def delete_transaction(self, transaction_id):
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            account_name, amount = transaction[1], transaction[2]
            
            # Subtract the amount from the account balance
            self.balance_manager.adjust_balance(account_name, amount)
        self.db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))