import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.dropdown import ObjectProperty
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
    account_spinner = ObjectProperty(None)

    def on_pre_enter(self):
        # Refresh account list each time the screen is shown
        self.refresh_accounts()

    def refresh_accounts(self):
        conn = sqlite3.connect("budgetbee.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts")
        accounts = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Update spinner values
        self.account_spinner.values = accounts

    def add_transaction(self, account_name, amount, category, date, description):
        if not account_name or not amount or not category:
            return  # simple validation

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Find the account_id by name
            c.execute("SELECT id FROM accounts WHERE name=?", (account_name,))
            account = c.fetchone()
            if not account:
                return
            account_id = account[0]

            c.execute("""
                INSERT INTO transactions (account_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, float(amount), category, date, description))
            conn.commit()

        # Go back to dashboard after saving
        self.manager.current = "dashboard"

class TransactionsScreen(Screen):
    transactions = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT account_id, amount, category, date, description FROM transactions ORDER BY date DESC")
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