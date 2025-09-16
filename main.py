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

# Load the Kivy KV layout file
Builder.load_file("budgetbee.kv")

# Database file name
DB_NAME = "budgetbee.db"

# Database file name
def init_db():
    """Initialize the database tables for accounts, categories, and transactions"""
    # Accounts table
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.commit()

    # Categories table
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

    # Ensure the System category exists (used for internal/account transactions)
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM categories WHERE name=?", ("System",))
        if not c.fetchone():
            c.execute("INSERT INTO categories (name, type) VALUES (?, ?)", ("System", "system"))
        conn.commit()

    # Transactions table
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category_id TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)
        conn.commit()

# -----------------------------
# Helper functions
# -----------------------------
def get_system_category_id():
    """Get the ID of the 'System' category, creating it if it doesn't exist"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Try to find the System category
        c.execute("SELECT id FROM categories WHERE name = 'System'")
        row = c.fetchone()

        return row[0]

# -----------------------------
# Screens
# -----------------------------
class DashboardScreen(Screen):
    total_balance = StringProperty("0.00")

    def on_pre_enter(self):
        """Update total balance before entering the dashboard"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT SUM(balance) FROM accounts WHERE is_active = 1")
            total = c.fetchone()[0] or 0.0
            self.total_balance = f"{total:.2f}"

# -----------------------------
# Accounts screens
# -----------------------------
class AccountsScreen(Screen):
    accounts = ListProperty([])     # List of active accounts

    def on_pre_enter(self):
        """Fetch active accounts and populate the UI"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, owner, name, balance FROM accounts WHERE is_active = 1")
            self.accounts = c.fetchall()

        # Update the UI list
        self.ids.accts_list.clear_widgets()
        for acct in self.accounts:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            # Display account info
            label = Label(
                text=f"{acct[1]} | {acct[2]} | {acct[3]:.2f}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            # Delete button
            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40
            )
            delete_btn.bind(on_release=lambda btn, acct_id=acct[0]: self.delete_account(acct_id))

            box.add_widget(label)
            box.add_widget(delete_btn)

            self.ids.accts_list.add_widget(box)
        
        # Make list height adjust to number of items
        self.ids.accts_list.bind(minimum_height=self.ids.accts_list.setter('height'))

    def delete_account(self, acct_id):
        # Make list height adjust to number of items
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Get account info
            c.execute("SELECT name, balance FROM accounts WHERE id=?", (acct_id,))
            row = c.fetchone()
            if not row:
                return
            acct_name, acct_balance = row

            # Add system transaction for account deletion
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, description)
                VALUES (?, ?, ?, DATE('now'), ?)
            """, (acct_id, get_system_category_id(), acct_balance, f"Deleted account {acct_name}"))

            # Mark account as inactive
            c = conn.cursor()
            c.execute("UPDATE accounts SET is_active = 0 WHERE id=?", (acct_id,))
            conn.commit()

        # Refresh the accounts list
        self.on_pre_enter()

class AddAccountScreen(Screen):
    """Add a new account or reactivate a deleted account"""
    def add_account(self, owner, name, balance):
        if not owner or not name:
            return  # Validate input

        # Convert balance to float
        if not balance:
            balance = 0.00
        else:
            try:
                balance = float(balance)
            except:
                return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Check if account exists
            c.execute("SELECT id, is_active FROM accounts WHERE name = ?", (name,))
            row = c.fetchone()

            if row:
                account_id, is_active = row

                if is_active == 1:
                    # Account already active → don't add
                    return False, "Account already exists."
                else:
                    # Reactivate the deleted account
                    c.execute(
                        "UPDATE accounts SET is_active = 1, balance = ? WHERE id = ?",
                        (balance, account_id)
                    )
                    conn.commit()

                    # Add system transaction for account reactivation
                    c.execute(
                        """
                        INSERT INTO transactions (account_id, category_id, amount, description, date)
                        VALUES (?, ?, ?, ?, DATE('now'))
                        """,
                        (account_id, get_system_category_id(),
                        balance, f'Reactivated {name}')
                    )
                    conn.commit()
                    self.manager.current = "accounts"
                    return True, "Account reactivated successfully."
            else:
                # New account
                c.execute(
                    "INSERT INTO accounts (owner, name, balance, is_active) VALUES (?, ?, ?, 1)",
                    (owner, name, balance)
                )
                account_id = c.lastrowid

                # Add system transaction for new account
                c.execute(
                    """
                    INSERT INTO transactions (account_id, category_id, amount, description, date)
                    VALUES (?, ?, ?, ?, DATE('now'))
                    """,
                    (account_id, get_system_category_id(), balance, f'Added {name}')
                )
                conn.commit()
                self.manager.current = "accounts"
                return True, "Account added successfully."
    
        self.manager.current = "accounts"

# -----------------------------
# Categories screens
# -----------------------------
class CategoriesScreen(Screen):
    categories = ListProperty([])

    def on_pre_enter(self):
        """Fetch categories and populate the UI, excluding System"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, type FROM categories WHERE name != 'System'")
            self.categories = c.fetchall()

        # Update the UI
        self.ids.cats_list.clear_widgets()
        for cat in self.categories:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            label = Label(
                text=f"{cat[1]} | {cat[2]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            # Delete button
            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40
            )
            delete_btn.bind(on_release=lambda btn, cat_id=cat[0]: self.delete_category(cat_id))

            box.add_widget(label)
            box.add_widget(delete_btn)

            self.ids.cats_list.add_widget(box)
        
        # **Bind height to children**
        self.ids.cats_list.bind(minimum_height=self.ids.cats_list.setter('height'))

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

# -----------------------------
# Transactions screens
# -----------------------------
class TransactionsScreen(Screen):
    transactions = ListProperty([])

    def on_pre_enter(self):
        """Fetch transactions and populate UI"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT t.id, a.name, t.amount, c.name, t.date, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN categories c ON t.category_id = c.id
                ORDER BY t.date DESC
            """)
            self.transactions = c.fetchall()

        # Update the UI
        self.ids.txns_list.clear_widgets()
        for txn in self.transactions:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            # Format amount display
            amount_display = f"${txn[2]:.2f}" if txn[2] >= 0 else f"-${-txn[2]:.2f}"

            label = Label(
                text=f"{txn[1]} | {amount_display} | {txn[3]} | {txn[4]} | {txn[5]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            box.add_widget(label)

            # Add delete button for non-system transactions
            if txn[3] != "System":
                delete_btn = Button(
                    text="X",
                    size_hint_x=None,
                    width=40
                )
                delete_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.delete_transaction(txn_id))
                box.add_widget(delete_btn)

            self.ids.txns_list.add_widget(box)

        # **Bind height to children**
        self.ids.txns_list.bind(minimum_height=self.ids.txns_list.setter('height'))

    def delete_transaction(self, txn_id):
        """Delete a transaction and adjust account balance"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get transaction details
            c.execute("""
                SELECT account_id, category_id, amount
                FROM transactions
                WHERE id=?
            """, (txn_id,))
            txn = c.fetchone()
            if txn:
                account_id, category_id, amount = txn

                # Update account balance
                c.execute(
                    "UPDATE accounts SET balance = balance - ? WHERE id=?",
                    (amount, account_id)
                )

                # Delete the transaction
                c.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
            conn.commit()

        # Refresh the screen
        self.on_pre_enter()

class AddTransactionScreen(Screen):
    account_spinner = ObjectProperty(None)
    category_spinner = ObjectProperty(None)

    def on_pre_enter(self):
        """Refresh account and category spinners when screen is shown"""
        self.refresh_spinners()

    def refresh_spinners(self):
        """Update spinner dropdown values"""
        conn = sqlite3.connect("budgetbee.db")

        c = conn.cursor()
        c.execute("SELECT name FROM accounts WHERE is_active = 1")
        accounts = [row[0] for row in c.fetchall()]
        c.execute("SELECT name, type FROM categories WHERE name != 'System'")
        categories = [f"{row[0]} - ({row[1]})" for row in c.fetchall()]

        conn.close()

        # Update spinner values
        self.account_spinner.values = accounts
        self.category_spinner.values = categories
        
    def add_transaction(self, account_name, category_display, amount, date, description):
        """Add a new transaction and update account balance"""
        if not account_name or not category_display or not amount:
            return  # simple validation
        
        # Extract category name from display text
        category_name = category_display.split(" -")[0]

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if not description:
            description = "No description"

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Get account ID and current balance
            c.execute("SELECT id, balance FROM accounts WHERE name=?", (account_name,))
            account = c.fetchone()
            if not account:
                return
            account_id, current_balance = account

            # Get category ID and type
            c.execute("SELECT id, type FROM categories WHERE name=?", (category_name,))
            category = c.fetchone()
            if not category:
                return
            category_id, category_type = category

            # Adjust amount based on category type 
            if category_type == "Income":
                amount = float(amount)
            elif category_type == "Expense":
                amount = -float(amount)

            # Insert the transaction
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, category_id, float(amount), date, description))

            # Update the account balance based on category type
            new_balance = current_balance + float(amount)
            
            c.execute("UPDATE accounts SET balance = ? WHERE id=?", (new_balance, account_id))

            conn.commit()

        # Go back to transactions screen
        self.manager.current = "transactions"

# -----------------------------
# App entry point
# -----------------------------
class BudgetBeeApp(App):
    def build(self):
        init_db()   # Ensure database exists
        sm = ScreenManager()

        # Add all screens
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