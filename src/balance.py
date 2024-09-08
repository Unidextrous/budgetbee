from datetime import datetime

class BalanceManager:
    def __init__(self, db):
        self.db = db
    
    def set_balance(self, account, balance, date_set):
        self.db.execute("INSERT INTO balances (account, balance, date_set) VALUES (?, ?, ?)",
           (account, balance, date_set.isoformat())
        )

    def get_accounts(self):
        return [row[0] for row in self.db.fetchall("SELECT account FROM balances")[::-1]]

    def get_balance(self, account):
        if account == "*":
            balance = self.db.fetchall("SELECT SUM(balance) FROM balances")
        else:
            balance = self.db.fetchall("SELECT balance FROM balances WHERE account = ?", (account,))

        return balance[0][0]

    def update_balance(self, account, new_balance):
        self.db.execute("UPDATE balances SET balance = ? WHERE account = ?", (new_balance, account))