from datetime import datetime

class BalanceManager:
    def __init__(self, db):
        self.db = db
    
    def set_balance(self, account, starting_balance, date_set):
        self.db.execute("INSERT INTO balances (account, balance, date_set) VALUES (?, ?, ?)",
           (account, starting_balance, date_set.isoformat())
        )

    def get_accounts(self):
        return [row[0] for row in self.db.fetchall("SELECT account FROM balances")[::-1]]

    def get_balances(self, account):
        if account == "*":
            balances = self.db.fetchall(
                """SELECT * FROM balances
            """)
        else:
            balances = self.db.fetchall(
                """SELECT * FROM balances WHERE account = ?"""
                (account,)
            )

        return balances