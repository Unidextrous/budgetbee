from datetime import datetime

class TransactionManager:
    def __init__(self, db):
        self.db = db

    def add_transaction(self, amount, category, details, date):
        self.db.execute("INSERT INTO transactions (amount, category, details, date) VALUES(?, ?, ?, ?)",
            (amount, category, details, date.isoformat()))
    
    def get_transactions(self, category, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        if category == "*":
            category = "TOTAL"
        else:
            return self.db.fetchone(
                "SELECT SUM(amount), 'TOTAL', NULL, NULL, NULL FROM transactions WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
                (start_date_str, end_date_str)
            )
            
        return self.dbfetchall(
            "SELECT * FROM transactions WHERE category = ? AND DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)",
            (category, start_date_str, end_date_str)
        )

    def remove_transaction(self, transaction_id):
        self.db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))