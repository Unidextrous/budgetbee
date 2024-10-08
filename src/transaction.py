from datetime import datetime

class TransactionManager:
    def __init__(self, db, account_manager, category_manager):
        # Initialize the TransactionManager with database and managers for accounts and categories
        self.db = db
        self.account_manager = account_manager
        self.category_manager = category_manager

    def add_transaction(self, account, amount, category, details, date):
        # Add a new transaction to the database, initially with a remaining balance of 0
        self.db.execute("""
            INSERT INTO transactions
            (account, amount, remaining_balance, category, details, date) VALUES(?, ?, ?, ?, ?, ?)
        """, (account, amount, 0, category, details, date.isoformat()))
        
        # Recalculate and update all remaining balances for the account
        self.update_all_remaining_balances(account)

        # Get and return the last inserted transaction ID
        transaction_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return transaction_id

    def get_transactions_by_account(self, account, start_date, end_date):
        # Fetch transactions for a specific account within a date range. If account is "*", fetch all transactions.
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
    
    def get_transactions_by_category(self, category, start_date, end_date):
        # Fetch transactions for a specific category between a start and end date
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (category, start_date_str, end_date_str))

    def get_all_transactions(self, start_date, end_date):
        # Fetch all transactions between a start and end date
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        return self.db.fetchall("""
            SELECT * FROM transactions
            WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (start_date_str, end_date_str))

    def get_transaction_by_id(self, transaction_id):
         # Retrieve a specific transaction by its ID
         return self.db.fetchone("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    
    def get_total_spending_by_category(self, category, start_date, end_date):
        # Calculates total spending for a specific category within a date range.
        result = self.db.fetchone(
            """SELECT SUM(amount) 
            FROM transactions 
            WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)""",
            (category, start_date, end_date)
        )

        # Return the total amount, or 0 if no transactions found
        return result[0] if result[0] is not None else 0.0

    def update_transaction_account(self, transaction_id, category, new_account_name):
        # Update the account associated with a transaction and adjust balances accordingly
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            old_account_name, amount = old_transaction[1], old_transaction[2]

            # Adjust the balances between the old and new accounts based on the transaction type (INCOME/EXPENSE)
            category_type = self.category_manager.get_category_type(category)
            
            if category_type == "INCOME":
                self.account_manager.adjust_balance(old_account_name, -amount)
                self.account_manager.adjust_balance(new_account_name, amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(old_account_name, amount)
                self.account_manager.adjust_balance(new_account_name, -amount)
            
            # Update the transaction record with the new account
            self.db.execute("UPDATE transactions SET account = ? WHERE id = ?", (new_account_name, transaction_id))
            
    def update_transaction_amount(self, transaction_id, category, new_amount):
        # Update the transaction amount and adjust the corresponding account balance
        old_transaction = self.get_transaction_by_id(transaction_id)
        if old_transaction:
            account, old_amount = old_transaction[1], old_transaction[2]

            # Adjust the balance based on the category type (INCOME/EXPENSE)
            category_type = self.category_manager.get_category_type(category)

            if category_type == "INCOME":
                self.account_manager.adjust_balance(account, -old_amount)
                self.account_manager.adjust_balance(account, new_amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(account, old_amount)
                self.account_manager.adjust_balance(account, -new_amount)

        # Update the amount in the transaction record
        self.db.execute("UPDATE transactions SET amount = ? WHERE id = ?", (new_amount, transaction_id))
    
    def update_all_remaining_balances(self, account):
        # Recalculate and update the remaining balance for each transaction for the given account
        starting_balance = self.account_manager.get_starting_balance(account)

        # Fetch all transactions for the account, ordered by date and ID
        transactions = self.db.fetchall("""
            SELECT id, amount, category, date
            FROM transactions
            WHERE account = ?
            ORDER BY date, id
        """, (account,))

        remaining_balance = starting_balance

        # Iterate through transactions and update remaining balances based on transaction type
        for transaction in transactions:
            transaction_id, amount, category, date = transaction

            category_type = self.category_manager.get_category_type(category)

            if category_type == "INCOME":
                remaining_balance += amount
            elif category_type == "EXPENSE":
                remaining_balance -= amount

            # Update the remaining balance for the current transaction
            self.db.execute("""
                UPDATE transactions
                SET remaining_balance = ? WHERE id = ?
            """, (remaining_balance, transaction_id))

            # Update the account's balance
            self.db.execute("""
                UPDATE accounts
                SET balance = ? WHERE account = ?
            """, (remaining_balance, account))

    def update_category(self, transaction_id, new_category):
        # Update the category of a specific transaction
        self.db.execute("UPDATE transactions SET category = ? WHERE id = ?", (new_category, transaction_id))

    def update_transaction_details(self, transaction_id, new_details):
        # Update the details (description) of a specific transaction
        self.db.execute("UPDATE transactions SET details = ? WHERE id = ?", (new_details, transaction_id))

    def update_transaction_date(self, budget_id, new_date):
        # Update the date of a specific transaction
        self.db.execute("UPDATE transactions SET date = ? WHERE id = ?", (new_date.isoformat(), budget_id))

    def delete(self, transaction_id, category_type):
        # Delete a transaction and adjust the corresponding account balance
        transaction = self.get_transaction_by_id(transaction_id)
        if transaction:
            account_name, amount = transaction[1], transaction[2]
            
            # Adjust the account balance based on transaction type (INCOME/EXPENSE)
            if category_type == "INCOME":
                self.account_manager.adjust_balance(account_name, -amount)
            elif category_type == "EXPENSE":
                self.account_manager.adjust_balance(account_name, amount)
        
        # Delete the transaction from the database
        self.db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))