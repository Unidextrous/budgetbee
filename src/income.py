from datetime import datetime

class IncomeManager:
    def __init__(self, db):
        self.db = db

    def add_income_source(self, amount, source, date):
        self.db.execute("INSERT INTO income (amount, source, date) VALUES(?, ?, ?)",
            (amount, source, date.isoformat()))
    
    def get_income_by_date(self, start_date, end_date):
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        income_in_range = self.db.fetchall("""
            SELECT *
            FROM income
            WHERE DATE(date) >= DATE(?) AND DATE(date) <= DATE(?)
        """, (start_date_str, end_date_str))

        return income_in_range

    def get_income_by_id(self, income_id):
        return self.db.fetchone("SELECT * FROM income WHERE id = ?", (income_id,))
    
    def update_income_amount(self, income_id, new_amount):
        self.db.execute("UPDATE income SET amount = ? WHERE id = ?", (new_amount, income_id))
        
    def update_income_source(self, income_id, new_source):
        self.db.execute("UPDATE income SET source = ? WHERE id = ?", (new_source, income_id))

    def update_income_date(self, income_id, new_date):
        self.db.execute("UPDATE income SET date = ? WHERE id = ?", (new_date.isoformat(), income_id))

    def remove_income_source(self, income_id):
        self.db.execute("DELETE FROM income WHERE id = ?", (income_id,))