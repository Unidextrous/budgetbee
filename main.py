import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
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
                balance REAL NOT NULL
            )
        """)
        conn.commit()

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT
            )
        """)
        conn.commit()

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
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

class AccountsScreen(Screen):
    accounts = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, owner, name, balance FROM accounts")
            self.accounts = c.fetchall()

        # Update the UI
        self.ids.accts_list.clear_widgets()
        for acct in self.accounts:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            label = Label(
                text=f"{acct[1]} - {acct[2]} - {acct[3]:.2f}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40
            )
            delete_btn.bind(on_release=lambda btn, acct_id=acct[0]: self.delete_account(acct_id))

            box.add_widget(label)
            box.add_widget(delete_btn)

            self.ids.accts_list.add_widget(box)

    def delete_account(self, acct_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM accounts WHERE id=?", (acct_id,))
            conn.commit()
        # Refresh the screen
        self.on_pre_enter()

class AddAccountScreen(Screen):
    def add_account(self, owner, name, balance):
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
                INSERT INTO accounts (owner, name, balance)
                VALUES (?, ?, ?)
            """, (owner, name, balance))
            conn.commit()

        self.manager.current = "accounts"

class CategoriesScreen(Screen):
    categories = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, type FROM categories")
            self.categories = c.fetchall()

        # Update the UI
        self.ids.cats_list.clear_widgets()
        for cat in self.categories:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            label = Label(
                text=f"{cat[1]} - {cat[2]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40
            )
            delete_btn.bind(on_release=lambda btn, cat_id=cat[0]: self.delete_category(cat_id))

            box.add_widget(label)
            box.add_widget(delete_btn)

            self.ids.cats_list.add_widget(box)

    def delete_category(self, cat_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
            conn.commit()
        # Refresh the screen
        self.on_pre_enter()

class AddCategoryScreen(Screen):
    def add_category(self, name):
        type = None
        if self.ids.income_btn.state == "down":
            type = "Income"
        elif self.ids.expense_btn.state == "down":
            type = "Expense"

        if not name or not type:
            return  # simple validation

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO categories (name, type)
                VALUES (?, ?)
            """, (name, type))
            conn.commit()

        self.manager.current = "categories"

class TransactionsScreen(Screen):
    transactions = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT t.id, a.name, t.amount, t.category, t.date, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                ORDER BY t.date DESC
            """)
            self.transactions = c.fetchall()

        # Update the UI
        self.ids.txns_list.clear_widgets()
        for txn in self.transactions:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            label = Label(
                text=f"{txn[1]} - ${txn[2]:.2f} - {txn[3]} - {txn[4]} - {txn[5]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40
            )
            delete_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.delete_transaction(txn_id))

            box.add_widget(label)
            box.add_widget(delete_btn)

            self.ids.txns_list.add_widget(box)

    def delete_transaction(self, txn_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
            conn.commit()
        # Refresh the screen
        self.on_pre_enter()

class AddTransactionScreen(Screen):
    account_spinner = ObjectProperty(None)
    category_spinner = ObjectProperty(None)

    def on_pre_enter(self):
        # Refresh account list each time the screen is shown
        self.refresh_spinners()

    def refresh_spinners(self):
        conn = sqlite3.connect("budgetbee.db")

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts")
        accounts = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT name FROM categories")
        categories = [row[0] for row in cursor.fetchall()]

        conn.close()

        # Update spinner values
        self.account_spinner.values = accounts
        self.category_spinner.values = categories
        
    def add_transaction(self, account_name, category, amount, date, description):
        if not account_name or not category or not amount:
            return  # simple validation

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if not description:
            description = "No description"

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Find the account_id by name
            c.execute("SELECT id FROM accounts WHERE name=?", (account_name,))
            account = c.fetchone()
            if not account:
                return
            account_id = account[0]

            c.execute("""
                INSERT INTO transactions (account_id, category, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, category, float(amount), date, description))
            conn.commit()

        # Go back to dashboard after saving
        self.manager.current = "transactions"

class BudgetBeeApp(App):
    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(AccountsScreen(name="accounts"))
        sm.add_widget(AddAccountScreen(name="add_account"))
        sm.add_widget(CategoriesScreen(name="categories"))
        sm.add_widget(AddCategoryScreen(name="add_category"))
        sm.add_widget(TransactionsScreen(name="transactions"))
        sm.add_widget(AddTransactionScreen(name="add_transaction"))
        return sm


if __name__ == "__main__":
    BudgetBeeApp().run()