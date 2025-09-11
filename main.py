import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.lang import Builder

Builder.load_file("budgetbee.kv")

DB_NAME = "budgetbee.db"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL,
                description TEXT
            )
        """)
        conn.commit()
        
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        """)
        conn.commit()


class DashboardScreen(Screen):
    total_balance = StringProperty("0.00")

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(amount) FROM transactions")
            total = c.fetchone()[0] or 0.0
            self.total_balance = f"{total:.2f}"

class AddAccountScreen(Screen):
    def add_account(self, owner, name, balance, description):
        if not owner or not name:
            return  # simple validation

        if not balance:
            balance = 0.00
        else:
            try:
                balance = float(balance)
            except:
                return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO accounts (owner, name, balance, description)
                VALUES (?, ?, ?, ?)
            """, (owner, name, balance, description))
            conn.commit()

        # Go back to dashboard after saving
        self.manager.current = "dashboard"


class AccountsScreen(Screen):
    accounts = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT owner, name, balance, description FROM accounts")
            self.accounts = c.fetchall()

        # Update the UI
        self.ids.accts_list.clear_widgets()
        for a in self.accounts:
            self.ids.accts_list.add_widget(
                Label(text=f"{a[0]} - {a[1]} - {a[2]:.2f} - {a[3]}")
            )

class AddTransactionScreen(Screen):
    def add_transaction(self, amount, category, date, description, person):
        if not amount or not category or not person:
            return  # simple validation

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO transactions (amount, category, date, description, person)
                VALUES (?, ?, ?, ?, ?)
            """, (float(amount), category, date, description, person))
            conn.commit()

        # Go back to dashboard after saving
        self.manager.current = "dashboard"


class TransactionsScreen(Screen):
    transactions = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT amount, category, date, description, person FROM transactions ORDER BY date DESC")
            self.transactions = c.fetchall()

        # Update the UI
        self.ids.trans_list.clear_widgets()
        for t in self.transactions:
            self.ids.trans_list.add_widget(
                Label(text=f"${t[0]:.2f} - {t[1]} - {t[2]} - {t[3]} - {t[4]}")
            )


class BudgetBeeApp(App):
    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AddAccountScreen(name="add_account"))
        sm.add_widget(AccountsScreen(name="accounts"))
        sm.add_widget(AddTransactionScreen(name="add_transaction"))
        sm.add_widget(TransactionsScreen(name="transactions"))
        return sm


if __name__ == "__main__":
    BudgetBeeApp().run()