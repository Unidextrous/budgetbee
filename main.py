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
                name TEXT NOT NULL,
                income_expense TEXT
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

        # Go back to dashboard after saving
        self.manager.current = "dashboard"


class AccountsScreen(Screen):
    accounts = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT owner, name, balance FROM accounts")
            self.accounts = c.fetchall()

        # Update the UI
        self.ids.accts_list.clear_widgets()
        for a in self.accounts:
            self.ids.accts_list.add_widget(
                Label(text=f"{a[0]} - {a[1]} - {a[2]:.2f}")
            )

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
        categories = [row[0] for row in cursor.fetchall()] + ["+ New"]

        conn.close()

        # Update spinner values
        self.account_spinner.values = accounts
        self.category_spinner.values = categories

    def check_new_category(self, text):
        if text == "+ New":
            # Open a popup for category name input
            content = BoxLayout(orientation="vertical", spacing=10, padding=10)
            input_box = TextInput(hint_text="Enter new category")

            # Income/Outcome buttons
            type_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
            income_btn = ToggleButton(text="Income", group="type")
            outcome_btn = ToggleButton(text="Outcome", group="type")
            type_layout.add_widget(income_btn)
            type_layout.add_widget(outcome_btn)

            btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
            btn_ok = Button(text="OK")
            btn_cancel = Button(text="Cancel")
            btn_layout.add_widget(btn_ok)
            btn_layout.add_widget(btn_cancel)

            content.add_widget(Label(text="New Category"))
            content.add_widget(input_box)
            content.add_widget(type_layout)
            content.add_widget(btn_layout)

            popup = Popup(title="Add Category", content=content, size_hint=(0.8, 0.5))

            def save_category(instance):
                new_cat = input_box.text.strip()
                cat_type = "income" if income_btn.state == "down" else "outcome" if outcome_btn.state == "down" else None
                if new_cat and cat_type:
                    # Insert into database
                    with sqlite3.connect(DB_NAME) as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO categories (name, income_expense) VALUES (?, ?)", (new_cat, cat_type))
                        conn.commit()

                    cats = list(self.category_spinner.values)
                    cats.insert(-1, new_cat)
                    self.category_spinner.values = cats
                    self.category_spinner.text = new_cat
                popup.dismiss()

            def cancel(instance):
                self.category_spinner.text = "Select Category"
                popup.dismiss()

            btn_ok.bind(on_release=save_category)
            btn_cancel.bind(on_release=cancel)
            popup.open()

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
        self.manager.current = "dashboard"

class TransactionsScreen(Screen):
    transactions = ListProperty([])

    def on_pre_enter(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Join with accounts to get the account name
            c.execute("""
                SELECT a.name, t.amount, t.category, t.date, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                ORDER BY t.date DESC
            """)
            self.transactions = c.fetchall()

        # Update the UI
        self.ids.trans_list.clear_widgets()
        for t in self.transactions:
            self.ids.trans_list.add_widget(
                Label(text=f"{t[0]} - ${t[1]:.2f} - {t[2]} - {t[3]} - {t[4]}")
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