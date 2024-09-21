class AccountManager:
    def __init__(self, db):
        self.db = db
    
    def set_balance(self, account, balance):
        self.db.execute("INSERT INTO accounts (account, balance) VALUES (?, ?)",
           (account, balance)
        )

    def get_accounts(self):
        return [row[0] for row in self.db.fetchall("SELECT account FROM accounts")[::-1]]

    def get_balance(self, account):
        if account == "*":
            balance = self.db.fetchall("SELECT SUM(balance) FROM accounts")
        else:
            balance = self.db.fetchall("SELECT balance FROM accounts WHERE account = ?", (account,))

        return balance[0][0]

    def update_balance(self, account, new_balance):
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))

    def rename_account(self, old_name, new_name):
        self.db.execute("UPDATE accounts SET account = ? WHERE account = ?", (new_name, old_name))
        self.db.execute("UPDATE transactions SET account = ? WHERE account = ?", (new_name, old_name))

    def reset_balance(self, account, new_balance):
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))

    def delete_account(self, account):
        self.db.execute("DELETE FROM accounts WHERE account = ?", (account,))
        self.db.execute("DELETE FROM transactions WHERE account = ?", (account,))

    def adjust_balance(self, account, amount):
        # Get the current balance
        current_balance = self.get_balance(account)
        # Adjust the balance
        new_balance = current_balance + amount
        # Update the balance in the database
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))