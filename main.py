import sqlite3
from datetime import datetime, date, timedelta
from calendar import month_name, monthrange
from matplotlib import pyplot as plt
import io
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.lang import Builder

# Load the Kivy KV layout file
Builder.load_file("budgetbee.kv")

# Database file name
DB_NAME = "budgetbee.db"

# Database file name
def init_db():
    """Initialize the database tables for accounts, categories, and transactions"""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()

        # Accounts table
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT DEFAULT 'Checking',
                owner TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL,
                starting_balance REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Categories table
        c.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Ensure the System category exists (used for internal/account transactions)
        c.execute("SELECT id FROM categories WHERE name=?", ("System",))
        if not c.fetchone():
            c.execute("INSERT INTO categories (name, type) VALUES (?, ?)", ("System", "system"))

        # Transactions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                projected INTEGER DEFAULT 0,
                fulfilled INTEGER DEFAULT 0,
                status TEXT DEFAULT "Pending",
                is_transfer INTEGER DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)

        # Check if "Transfer To" exists
        c.execute("SELECT id FROM categories WHERE name=?", ("Transfer To",))
        if not c.fetchone():
            c.execute("""
                INSERT INTO categories (name, type, is_active)
                VALUES (?, ?, 1)
            """, ("Transfer To", "Expense"))
        
        # Check if "Transfer From" exists
        c.execute("SELECT id FROM categories WHERE name=?", ("Transfer From",))
        if not c.fetchone():
            c.execute("""
                INSERT INTO categories (name, type, is_active)
                VALUES (?, ?, 1)
            """, ("Transfer From", "Income"))

        # Budgets table
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_date TEXT NOT NULL UNIQUE,
                end_date TEXT UNIQUE
            )
        """)

        # Budgeted categories table
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgeted_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                allocated_amount REAL NOT NULL,
                alloc_desc TEXT,
                FOREIGN KEY(budget_id) REFERENCES budgets(id),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)

        # Budget transactions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS budget_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                transaction_id INTEGER NOT NULL,
                FOREIGN KEY(budget_id) REFERENCES budgets(id),
                FOREIGN KEY(transaction_id) REFERENCES transactions(id)
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

def recalc_budget_ranges(conn):
    c = conn.cursor()
    c.execute("SELECT id, start_date FROM budgets ORDER BY start_date ASC")
    budgets = c.fetchall()

    for i, (budget_id, start_date) in enumerate(budgets):
        if i < len(budgets) - 1:
            # End date = day before next budget's start date
            next_start = budgets[i+1][1]
            end_date = (datetime.strptime(next_start, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            # Last budget = Current
            end_date = "Current"

        c.execute("UPDATE budgets SET end_date=? WHERE id=?", (end_date, budget_id))
    conn.commit()

# -----------------------------
# Calendar Popup
# -----------------------------
class CalendarPopup(Popup):
    def __init__(self, target_input, year=None, month=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Select Date"
        self.size_hint = (0.9, 0.8)

        self.target_input = target_input

        today = date.today()
        self.year = year or today.year
        self.month = month or today.month

        self.build_calendar()

    def build_calendar(self):
        main_layout = BoxLayout(orientation="vertical", spacing=5, padding=5)

        # Navigation
        nav_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        prev_year_btn = Button(text="<", size_hint_x=None, width=40)
        next_year_btn = Button(text=">", size_hint_x=None, width=40)
        year_label = Button(text=f"{self.year}", background_color=(0,0,0,0), disabled=True)
        prev_month_btn = Button(text="<", size_hint_x=None, width=40)
        next_month_btn = Button(text=">", size_hint_x=None, width=40)
        month_label = Button(text=f"{month_name[self.month]}", background_color=(0,0,0,0), disabled=True)
        prev_year_btn.bind(on_release=self.prev_year)
        next_year_btn.bind(on_release=self.next_year)
        prev_month_btn.bind(on_release=self.prev_month)
        next_month_btn.bind(on_release=self.next_month)
        nav_layout.add_widget(prev_year_btn)
        nav_layout.add_widget(year_label)
        nav_layout.add_widget(next_year_btn)
        nav_layout.add_widget(prev_month_btn)
        nav_layout.add_widget(month_label)
        nav_layout.add_widget(next_month_btn)

        self.month_label = month_label
        self.year_label = year_label
        main_layout.add_widget(nav_layout)

        # Calendar grid
        self.grid = GridLayout(cols=7, spacing=5, padding=5)
        main_layout.add_widget(self.grid)

        self.refresh_calendar()
        self.content = main_layout

    def refresh_calendar(self):
        self.grid.clear_widgets()

        # Days of week headers
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            self.grid.add_widget(Button(text=d, size_hint_y=None, height=30, disabled=True))
    
        first_weekday, num_days = monthrange(self.year, self.month)

        # Fill in blanks for first week
        for _ in range((first_weekday + 7) % 7):
            self.grid.add_widget(Button(text="", size_hint_y=None, height=30, disabled=True))

        # Add day buttons
        for day in range(1, num_days + 1):
            btn = Button(text=str(day), size_hint_y=None, height=40)
            btn.bind(on_release=self.select_date)
            self.grid.add_widget(btn)
        
        self.year_label.text = f"{self.year}"
        self.month_label.text = f"{month_name[self.month]}"

    def prev_year(self, instance):
        self.year -= 1
        self.refresh_calendar()

    def next_year(self, instance):
        self.year += 1
        self.refresh_calendar()

    def prev_month(self, instance):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.refresh_calendar()

    def next_month(self, instance):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.refresh_calendar()

    def select_date(self, instance):
        selected_day = int(instance.text)
        self.target_input.text = f"{self.year:04d}-{self.month:02d}-{selected_day:02d}"
        self.dismiss()

# -----------------------------
# Screens
# -----------------------------
class DashboardScreen(Screen):
    total_balance = StringProperty("0.00")
    checking_balance = StringProperty("0.00")
    savings_balance = StringProperty("0.00")
    benefits_balance = StringProperty("0.00")

    def on_pre_enter(self):
        """Update total balance before entering the dashboard"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            c.execute("SELECT SUM(balance) FROM accounts WHERE is_active = 1")
            total = c.fetchone()[0] or 0.0
            self.total_balance = f"{total:.2f}"

            c.execute("SELECT SUM(balance) FROM accounts WHERE type = 'Checking' AND is_active = 1")
            total_checking = c.fetchone()[0] or 0.0
            self.checking_balance = f"{total_checking:.2f}"

            c.execute("SELECT SUM(balance) FROM accounts WHERE type = 'Savings' AND is_active = 1")
            total_savings = c.fetchone()[0] or 0.0
            self.savings_balance = f"{total_savings:.2f}"

            c.execute("SELECT SUM(balance) FROM accounts WHERE type = 'Benefits' AND is_active = 1")
            total_benefits = c.fetchone()[0] or 0.0
            self.benefits_balance = f"{total_benefits:.2f}"

# -----------------------------
# Accounts screens
# -----------------------------
class AccountsScreen(Screen):
    accounts = ListProperty([])     # List of active accounts

    def on_pre_enter(self):
        """Fetch active accounts and populate the UI"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, owner, name, balance, type
                FROM accounts
                WHERE is_active = 1
                ORDER BY owner ASC, name ASC
            """)
            self.accounts = c.fetchall()
            if self.accounts:
                self.acct_id = self.accounts[0][0]

        # Update the UI list
        self.ids.accts_list.clear_widgets()
        for acct in self.accounts:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            if acct[3] >= 0:
                amount_display = f"${acct[3]:.2f}"
            else:
                amount_display = f"-${-acct[3]:.2f}"

            # Display account info
            label = Label(text=f"{acct[1]} | {acct[2]} | {amount_display} | {acct[4]}", halign="center", valign="middle")
            label.bind(size=label.setter("text_size"))

            # Edit button
            edit_btn = Button(text="Edit", size_hint_x=None)
            edit_btn.bind(on_release=lambda btn, acct_id=acct[0]: self.edit_account(acct_id))

            # Delete button
            delete_btn = Button(text="X", size_hint_x=None, width=40)
            delete_btn.bind(on_release=lambda btn, acct_id=acct[0]: self.delete_account(acct_id))

            box.add_widget(label)
            box.add_widget(edit_btn)
            box.add_widget(delete_btn)

            self.ids.accts_list.add_widget(box)
        
        # Make list height adjust to number of items
        self.ids.accts_list.bind(minimum_height=self.ids.accts_list.setter('height'))

    def edit_account(self, acct_id):
        edit_screen = self.manager.get_screen("edit_account")
        edit_screen.load_account(acct_id)
        self.manager.current = "edit_account"

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
    def on_pre_enter(self):
        self.ids.type_spinner.text = "Checking"
        self.ids.owner.text = ""
        self.ids.name.text = ""
        self.ids.balance.text = ""

    """Add a new account or reactivate a deleted account"""
    def add_account(self, owner, name, balance):
        acct_type = self.ids.type_spinner.text

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
            else:
                # New account
                c.execute("""
                    INSERT INTO accounts (type, owner, name, balance, starting_balance, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)""",
                    (acct_type, owner, name, balance, balance)
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

class EditAccountScreen(Screen):
    def load_account(self, acct_id):
        self.acct_id = acct_id
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT type, owner, name, balance FROM accounts WHERE id=?", (acct_id,))
            row = c.fetchone()
            if row:
                self.ids.type_spinner.text = row[0]
                self.ids.owner.text = row[1]
                self.ids.name.text = row[2]
                self.ids.balance.text = str(row[3])

    def save_account(self):
        new_type = self.ids.type_spinner.text
        new_owner = self.ids.owner.text
        new_name = self.ids.name.text
        try:
            new_balance = float(self.ids.balance.text)
        except:
            if not self.ids.balance.text:
                new_balance = 0

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Get old account name
            c.execute("SELECT type, name, balance, starting_balance FROM accounts WHERE id=?", (self.acct_id,))

            row = c.fetchone()
            
            old_type = row[0]
            old_name = row[1]
            old_balance = row[2]
            old_starting_balance = row[3]

            if not new_type or not new_owner or not new_name:
                return
            
            c.execute("""
                UPDATE accounts
                SET type=?, owner=?, name=?, balance=?
                WHERE id=?
                """, (new_type, new_owner, new_name, new_balance, self.acct_id)
            )

            # If the name changed, update system transactions
            if old_name != new_name:
                c.execute("""
                    UPDATE transactions
                    SET description = REPLACE(description, ?, ?)
                    WHERE account_id=? AND description LIKE ?""",
                    (old_name, new_name, self.acct_id, f'%{old_name}%')
                )

            if old_balance != new_balance:
                balance_diff = new_balance - old_balance
                new_starting_balance = old_starting_balance + balance_diff
                
                c.execute("""
                    UPDATE accounts
                    SET balance = ?, starting_balance = ?
                    WHERE id=?""",
                    (new_balance, new_starting_balance, self.acct_id)
                )

                c.execute("""
                    UPDATE transactions
                    SET amount = REPLACE(amount, ?, ?)
                    WHERE account_id=? AND amount LIKE ?""",
                    (old_starting_balance, new_starting_balance, self.acct_id, f"%{old_starting_balance}%")
                )
                
            conn.commit()

        # Go back to summary view
        summary_screen = self.manager.get_screen("accounts")
        summary_screen.acct_id = self.acct_id
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
            c.execute("""
                SELECT id, name, type
                FROM categories
                WHERE name != 'System' AND name != 'Transfer To' AND name != 'Transfer From' AND is_active = 1
                ORDER BY type DESC, name ASC""")
            self.categories = c.fetchall()

        # Update the UI
        self.ids.cats_list.clear_widgets()
        for cat in self.categories:
            self.category_id = cat[0]

            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            label = Label(text=f"{cat[1]} | {cat[2]}", halign="center", valign="middle")
            label.bind(size=label.setter("text_size"))

            # Edit button
            edit_btn = Button(text="Edit", size_hint_x=None)
            edit_btn.bind(on_release=lambda btn, cat_id=cat[0]: self.edit_category(cat_id))

            # Delete button
            delete_btn = Button(text="X", size_hint_x=None,width=40)
            delete_btn.bind(on_release=lambda btn, cat_id=cat[0]: self.delete_category(cat_id))

            box.add_widget(label)
            box.add_widget(edit_btn)
            box.add_widget(delete_btn)

            self.ids.cats_list.add_widget(box)
        
        # **Bind height to children**
        self.ids.cats_list.bind(minimum_height=self.ids.cats_list.setter('height'))

    def edit_category(self, category_id):
        edit_screen = self.manager.get_screen("edit_category")
        edit_screen.load_category(category_id)
        self.manager.current = "edit_category"

    def delete_category(self, cat_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE categories SET is_active=0 WHERE id=?", (cat_id,))
            conn.commit()
            self.on_pre_enter()

class AddCategoryScreen(Screen):
    def on_pre_enter(self):
        # Reset name field
        self.ids.name.text = ""

        # Reset toggle buttons
        self.ids.income_btn.state = "normal"
        self.ids.expense_btn.state = "normal"

    def add_category(self, name, type):
        if not name or not type:
            return
        
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Check if category exists
            c.execute("SELECT id, is_active FROM categories WHERE name=?", (name,))
            row = c.fetchone()

            if row:
                cat_id, is_active = row
                if is_active == 0:
                    # Reactivate
                    c.execute("UPDATE categories SET is_active=1, type=? WHERE id=?", 
                            (type, cat_id))
                    conn.commit()
                    self.manager.current = "categories"
                    return cat_id
                else:
                    # Already exists and active
                    return None  
            else:
                # Create new
                c.execute("INSERT INTO categories (name, type, is_active) VALUES (?, ?, 1)", 
                        (name, type))
                conn.commit()
                self.manager.current = "categories"
                return c.lastrowid

class EditCategoryScreen(Screen):
    def load_category(self, category_id):
        self.category_id = category_id
        with sqlite3.connect(DB_NAME)as conn:
            c = conn.cursor()
            c.execute("SELECT name, type FROM categories WHERE id=?", (self.category_id,))
            row = c.fetchone()
            if row:
                self.ids.name.text = row[0]
                if row[1] == "Income":
                    self.ids.income_btn.state = "down"
                    self.ids.expense_btn.state = "normal"
                else:
                    self.ids.income_btn.state = "normal"
                    self.ids.expense_btn.state = "down"
    
    def save_category(self):
        new_name = self.ids.name.text
        if self.ids.income_btn.state == "down":
            new_type = "Income"
        elif self.ids.expense_btn.state == "down":
            new_type = "Expense"
        
        if not new_name or not new_type:
            return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Get old category
            c.execute("SELECT name, type FROM categories WHERE id=?", (self.category_id,))
            row = c.fetchone()

            old_name = row[0]
            old_type = row[1]

            if not new_name or not new_type:
                return
            
            c.execute("""
                UPDATE categories
                SET name=?, type=?
                WHERE id=?""",
                (new_name, new_type, self.category_id))
            
            c.execute("""
                UPDATE categories
                SET name=?, type=?
                WHERE id=?""",
                (new_name, new_type, self.category_id)
            )

            if old_type != new_type:
                c.execute("""
                    UPDATE transactions
                    SET amount=-amount
                    WHERE category_id=?""",
                    (self.category_id,))

                # Recalculate account balances
                c.execute("SELECT DISTINCT account_id FROM transactions WHERE category_id=?", (self.category_id,))
                account_ids = [row[0] for row in c.fetchall()]

                for acct_id in account_ids:
                    # Recalculate balance as starting_balance + sum(transactions)
                    c.execute("SELECT starting_balance FROM accounts WHERE id=?", (acct_id,))
                    starting_balance = c.fetchone()[0]

                    c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE account_id=?", (acct_id,))
                    total_transactions = c.fetchone()[0]

                    new_balance = starting_balance + total_transactions

                    c.execute("UPDATE accounts SET balance=? WHERE id=?", (new_balance, acct_id))

            conn.commit()
        
        categories_screen = self.manager.get_screen("categories")
        categories_screen.category_id = self.category_id
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
                SELECT t.id, a.name, c.name, t.amount, t.date, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN categories c ON t.category_id = c.id
                WHERE projected = 0 AND c.name != 'System'
                ORDER BY t.date DESC
            """)
            self.transactions = c.fetchall()

        # Update the UI
        self.ids.txns_list.clear_widgets()
        for txn in self.transactions:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            # Format amount display
            amount_display = f"${txn[3]:.2f}" if txn[3] >= 0 else f"-${-txn[3]:.2f}"

            label = Label(
                text=f"{txn[1]} | {txn[2]} | {amount_display} | {txn[4]} | {txn[5]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            box.add_widget(label)

            # Add delete button for non-system transactions
            if txn[2] != "System":
                edit_btn = Button(text="Edit", size_hint_x=None)
                edit_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.edit_transaction(txn_id))

                delete_btn = Button(text="X", size_hint_x=None, width=40)
                delete_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.delete_transaction(txn_id))
                
                box.add_widget(edit_btn)
                box.add_widget(delete_btn)

            self.ids.txns_list.add_widget(box)

        # **Bind height to children**
        self.ids.txns_list.bind(minimum_height=self.ids.txns_list.setter('height'))

    def edit_transaction(self, transaction_id):
        edit_screen = self.manager.get_screen("edit_transaction")
        edit_screen.load_transaction(transaction_id)
        self.manager.current = "edit_transaction"

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
        self.ids.account_spinner.text = "Select Account"
        self.ids.category_spinner.text = "Select Category"
        self.ids.amount.text = ""
        self.ids.description.text = ""
        self.ids.date.text = datetime.now().strftime('%Y-%m-%d')
    
    def open_calendar(self, target_input):
        popup = CalendarPopup(target_input=target_input)
        popup.open()

    def refresh_spinners(self):
        """Update spinner dropdown values"""
        conn = sqlite3.connect("budgetbee.db")

        c = conn.cursor()
        c.execute("""
            SELECT name
            FROM accounts
            WHERE is_active = 1
            ORDER BY owner ASC, name ASC
        """)
        accounts = [row[0] for row in c.fetchall()]
        c.execute("""
            SELECT name, type
            FROM categories
            WHERE name != 'System' AND is_active = 1
            ORDER BY type desc, name ASC
        """)
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

            if category_name in ["Transfer To", "Transfer From"]:
                is_transfer = 1
            else:
                is_transfer = 0

            # Insert the transaction
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, description, is_transfer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (account_id, category_id, float(amount), date, description, is_transfer))
        
            # Get the ID of the transaction we just added
            transaction_id = c.lastrowid

            # Update the account balance based on category type
            new_balance = current_balance + float(amount)
            
            c.execute("UPDATE accounts SET balance = ? WHERE id=?", (new_balance, account_id))

            conn.commit()
        
        self.link_transaction_to_budgets(transaction_id, date)

        # Go back to transactions screen
        self.manager.current = "transactions"

    def link_transaction_to_budgets(self, txn_id, txn_date):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Find the most recent budget that started before txn_date
            c.execute("""
                SELECT id, start_date, end_date FROM budgets
                WHERE start_date <= ?
                ORDER BY start_date DESC
                LIMIT 1
            """, (txn_date,))
            row = c.fetchone()
            if row:
                budget_id, start_date, end_date = row
                # Only link if txn_date <= end_date or end_date is None
                if end_date is None or txn_date <= end_date:
                    c.execute("""
                        INSERT OR IGNORE INTO budget_transactions (budget_id, transaction_id)
                        VALUES (?, ?)
                    """, (budget_id, txn_id))
            conn.commit()

class EditTransactionScreen(Screen):
    def open_calendar(self, target_input):
        popup = CalendarPopup(target_input=target_input)
        popup.open()

    def load_transaction(self, transaction_id):
        self.transaction_id = transaction_id
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT a.name, c.name, t.amount, t.date, t.description
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN categories c ON t.category_id = c.id
                WHERE t.id=?
            """, (transaction_id,))
            row = c.fetchone()

        if row:
            account_name, category_name, amount, date, description = row

            # Populate account spinner
            self.ids.account_spinner.values = self.get_account_names()
            self.ids.account_spinner.text = account_name

            # Populate category spinner, filter out 'System'
            c.execute("""
                SELECT name, type
                FROM categories
                WHERE name != 'System' AND is_active = 1
                ORDER BY type desc, name ASC
            """)
            rows = c.fetchall()

            categories = []
            for row in rows:
                name = str(row[0]) if row[0] else "Unnamed"
                cat_type = str(row[1]) if row[1] else "Unknown"
                categories.append(f"{name} - ({cat_type})")
                
            self.ids.category_spinner.values = categories
            if category_name:
                self.ids.category_spinner.text = category_name
            else:
                self.ids.category_spinner.text = "Select Category"

            if amount >= 0:
                self.ids.amount.text = str(amount)
            else:
                self.ids.amount.text = str(amount)[1:]
            self.ids.date.text = date
            self.ids.description.text = description

    def get_account_names(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM accounts")
            return [row[0] for row in c.fetchall()]
        
    def save_transaction(self):
        new_account = self.ids.account_spinner.text
        new_category = self.ids.category_spinner.text.split(" -")[0]
        new_amount = float(self.ids.amount.text)
        new_date = self.ids.date.text
        new_description = self.ids.description.text

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            c.execute("SELECT id FROM accounts WHERE name = ?", (new_account,))
            row = c.fetchone()
            new_account_id = row[0]

            c.execute("SELECT id, type FROM categories WHERE name = ?", (new_category,))
            row = c.fetchone()
            if row:
                new_category_id = row[0]
                new_category_name = new_category
                new_category_type = row[1]
            else:
                return
            
            if new_category_type == "Expense":
                new_amount = -new_amount

            if new_category_name in ["Transfer To", "Transfer From"]:
                is_transfer = 1
            else:
                is_transfer = 0

            # Get old transaction
            c.execute("SELECT account_id, category_id, amount, date, description FROM transactions WHERE id=?", (self.transaction_id,))
            row = c.fetchone()

            if not row:
                return

            old_account_id, old_category_id, old_amount, old_date, old_description = row

            # --- Update transaction row ---
            c.execute("""
                INSERT INTO transactions
                (account_id, category_id, amount, date, description, is_transfer)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_account_id, new_category_id, new_amount, new_date, new_description, is_transfer))

            c.execute("""
                DELETE FROM transactions WHERE id=?""",
                (self.transaction_id,)
            )

            # --- If account changed, adjust both old and new balances ---
            if old_account_id != new_account_id:
                # Subtract from old account
                c.execute("UPDATE accounts SET balance = balance - ? WHERE id=?", (old_amount, old_account_id))
                # Add to new account
                c.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (new_amount, new_account_id))

            # --- If account is the same, but amount changed ---
            elif old_amount != new_amount:
                amount_diff = new_amount - old_amount
                c.execute("UPDATE accounts SET balance = balance + ? WHERE id=?", (amount_diff, old_account_id))

            conn.commit()

        # Go back to transactions screen
        transactions_screen = self.manager.get_screen("transactions")
        transactions_screen.transaction_id = self.transaction_id
        self.manager.current = "transactions"

class BudgetManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    # -----------------------------
    # Budget Creation
    # -----------------------------
    def create_budget(self, name, start_date, end_date=None):
        """Create a new budget and return its ID"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO budgets (name, start_date, end_date)
                VALUES (?, ?, ?)
            """, (name, start_date, end_date))
            conn.commit()
            return c.lastrowid

    # -----------------------------
    # Allocated Categories
    # -----------------------------
    def add_budgeted_category(self, category_name, amount):
        if not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get category ID
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            # Check if allocation exists
            c.execute("""
                SELECT id FROM budgeted_categories
                WHERE budget_id=? AND category_id=?
            """, (self.budget_id, category_id))
            existing = c.fetchone()

            if existing:
                # Update existing allocation
                c.execute("""
                    UPDATE budgeted_categories
                    SET allocated_amount=allocated_amount + ?
                    WHERE id=?
                """, (amount, existing[0]))
            else:
                # Insert new
                c.execute("""
                    INSERT INTO budgeted_categories (budget_id, category_id, allocated_amount)
                    VALUES (?, ?, ?)
                """, (self.budget_id, category_id, amount))
            conn.commit()

        self.load_allocated_categories()
        self.update_summary_labels()

    def get_allocated_categories(self, budget_id):
        """Return list of tuples (id, category_name, amount)"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT bc.id, c.name, bc.allocated_amount
                FROM budgeted_categories bc
                JOIN categories c ON bc.category_id = c.id
                WHERE bc.budget_id=?
            """, (budget_id,))
            return c.fetchall()

    # -----------------------------
    # Projected Transactions
    # -----------------------------
    def add_projected_transaction(self, category_name, amount, description, date):
        if not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        if not description:
            description = "No Description"

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get category ID
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            # Insert projected transaction
            c.execute("""
                INSERT INTO transactions (category_id, amount, description, date, projected)
                VALUES (?, ?, ?, ?, 1)
            """, (category_id, amount, description, date))
            txn_id = c.lastrowid

            # Link to budget
            c.execute("INSERT INTO budget_transactions (budget_id, transaction_id) VALUES (?, ?)",
                    (self.budget_id, txn_id))
            conn.commit()

        self.load_projected_transactions()
        self.update_summary_labels()

    def get_projected_transactions(self, budget_id):
        """Return list of projected transactions for a budget"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT t.id, a.name, c.name, t.amount, t.date
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN categories c ON t.category_id = c.id
                JOIN budget_transactions bt ON t.id = bt.transaction_id
                WHERE bt.budget_id=? AND t.projected=1
            """, (budget_id,))
            return c.fetchall()

    # -----------------------------
    # Budget Summary
    # -----------------------------
    def get_budget_summary(self, budget_id):
        """Return a dict with totals: allocated, spent, projected, remaining"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Total allocated
            c.execute("SELECT SUM(allocated_amount) FROM budgeted_categories WHERE budget_id=?", (budget_id,))
            allocated = c.fetchone()[0] or 0

            # Get budget start & end
            c.execute("SELECT start_date, end_date FROM budgets WHERE id=?", (budget_id,))
            row = c.fetchone()
            if not row:
                # no such budget
                return {
                    "allocated": 0,
                    "spent": 0,
                    "projected": 0,
                    "remaining": 0
                }

            start_date, end_date = row

            # Total spent (transactions with amount < 0 in date range)
            if end_date:
                c.execute("""
                    SELECT SUM(amount) 
                    FROM transactions
                    WHERE projected=0 AND amount<0
                    AND date BETWEEN ? AND ?
                    AND is_transfer = 0
                """, (start_date, end_date))
            else:
                c.execute("""
                    SELECT SUM(amount) 
                    FROM transactions
                    WHERE projected=0 AND amount<0
                    AND date >= ?
                    AND is_transfer = 0
                """, (start_date,))
            
            spent = c.fetchone()[0] or 0
            spent = -spent  # flip to positive

            # Total projected (only pending, linked transactions)
            c.execute("""
                SELECT SUM(t.amount) 
                FROM transactions t
                JOIN budget_transactions bt ON t.id = bt.transaction_id
                WHERE bt.budget_id=? AND t.projected=1 AND t.status='Pending'
            """, (budget_id,))
            projected = c.fetchone()[0] or 0

        remaining = allocated - spent - projected
        return {
            "allocated": allocated,
            "spent": spent,
            "projected": projected,
            "remaining": remaining
        }

# -----------------------------
# Budget Screens
# -----------------------------
class BudgetsScreen(Screen):
    budgets = ListProperty([])

    def on_pre_enter(self):
        """Load all budgets from DB"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, start_date, end_date FROM budgets ORDER BY start_date DESC")
            self.budgets = c.fetchall()

        # Update UI list
        self.ids.budgets_list.clear_widgets()
        for b in self.budgets:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            label = Label(
                text=f"{b[1]} | {b[2]} - {b[3] or 'Current'}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            view_btn = Button(text="View", size_hint_x=None, width=80)
            view_btn.bind(on_release=lambda btn, budget_id=b[0]: self.view_budget(budget_id))
            delete_btn = Button(text="X", size_hint_x=None, width=40)
            delete_btn.bind(on_release=lambda btn, bid=b[0]: self.delete_budget(bid))

            box.add_widget(label)
            box.add_widget(view_btn)
            box.add_widget(delete_btn)
            self.ids.budgets_list.add_widget(box)

        self.ids.budgets_list.bind(minimum_height=self.ids.budgets_list.setter('height'))

    def view_budget(self, budget_id):
        self.manager.current = "budget_summary"
        self.manager.get_screen("budget_summary").load_budget(budget_id)

    def delete_budget(self, budget_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM budgets WHERE id=?", (budget_id,))

            # Recalculate  budget ranges and refresh the budgets list
            recalc_budget_ranges(conn)
            self.on_pre_enter()

class AddBudgetScreen(Screen):
    def on_pre_enter(self):
        """Reset fields"""
        self.ids.budget_name.text = ""
    
    def open_calendar(self, target_input):
        popup = CalendarPopup(target_input=target_input)
        popup.open()

    def add_budget(self, name, start_date):
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        start = datetime.strptime(start_date, "%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Step 1: Insert the new budget
            c.execute("""
                INSERT INTO budgets (name, start_date)
                VALUES (?, ?)
            """, (name, start_date))
            new_id = c.lastrowid

            # Step 2: Find overlapping budgets
            c.execute("""
                SELECT id, start_date, end_date FROM budgets
                WHERE id != ?
            """, (new_id,))
            overlaps = c.fetchall()

            for bid, s, e in overlaps:
                s = datetime.strptime(s, "%Y-%m-%d")
                e = datetime.strptime(e, "%Y-%m-%d") if e else None

                # Case A: existing budget starts before new and ends after new starts → cut it
                if s <= start and (e is None or e >= start):
                    new_end = start - timedelta(days=1)
                    c.execute("UPDATE budgets SET end_date=? WHERE id=?", (new_end.strftime("%Y-%m-%d"), bid))

                # Case B: existing budget starts after new budget → cut new one
                if s >= start:
                    new_end = s - timedelta(days=1)
                    c.execute("UPDATE budgets SET end_date=? WHERE id=?", (new_end.strftime("%Y-%m-%d"), new_id))

            conn.commit()

            self.link_existing_transactions_to_budget(new_id)

            # Now navigate to the summary screen
            self.manager.current = "budget_summary"
            self.manager.get_screen("budget_summary").load_budget(new_id)

    def link_existing_transactions_to_budget(self, budget_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT start_date, end_date FROM budgets WHERE id=?", (budget_id,))
            start_date, end_date = c.fetchone()

            if end_date:
                c.execute("""
                    SELECT id FROM transactions
                    WHERE date BETWEEN ? AND ? 
                """, (start_date, end_date))
            else:
                c.execute("""
                    SELECT id FROM transactions
                    WHERE date >= ?
                """, (start_date,))
            
            txn_ids = [row[0] for row in c.fetchall()]

            # Insert links
            for txn_id in txn_ids:
                c.execute("""
                    INSERT OR IGNORE INTO budget_transactions (budget_id, transaction_id)
                    VALUES (?, ?)
                """, (budget_id, txn_id))

            conn.commit()

class BudgetSummaryScreen(Screen):
    budget_id = None
    allocated_categories = ListProperty([])
    projected_transactions = ListProperty([])

    def on_pre_enter(self):
        # Clear old widgets
        self.ids.allocated_list.clear_widgets()
        self.ids.projected_list.clear_widgets()

        budget_manager = BudgetManager()
        budget_manager.get_budget_summary(self.budget_id)

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Allocated categories
            c.execute("""
                SELECT bc.id, cat.name, bc.allocated_amount
                FROM budgeted_categories bc
                JOIN categories cat ON bc.category_id = cat.id
                WHERE bc.budget_id=?
            """, (self.budget_id,))
            allocated = c.fetchall()

            for ac in allocated:
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
                row.add_widget(Label(
                    text=f"{ac[1]} - Allocated: ${ac[2]:.2f}",
                    halign="center", valign="middle"
                ))
                self.ids.allocated_list.add_widget(row)

            # Projected transactions (transactions table with projected=1)
            c.execute("""
                SELECT t.id, cat.name, t.description, t.amount, t.status
                FROM transactions t
                JOIN categories cat ON t.category_id = cat.id
                JOIN budget_transactions bt ON t.id = bt.transaction_id
                WHERE bt.budget_id=? AND t.projected=1
            """, (self.budget_id,))
            projected = c.fetchall()

            for proj in projected:
                proj_id, cat_name, desc, amt, status = proj
                row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

                row.add_widget(Label(text=f"{desc} (${amt:.2f})", size_hint_x=0.5))

                completed_btn = Button(text="Completed", size_hint_x=0.2)
                completed_btn.bind(on_release=lambda btn, pid=proj_id: self.update_projected_status(pid, "Completed"))
                row.add_widget(completed_btn)

                skipped_btn = Button(text="Skipped", size_hint_x=0.2)
                skipped_btn.bind(on_release=lambda btn, pid=proj_id: self.update_projected_status(pid, "Skipped"))
                row.add_widget(skipped_btn)

                delete_btn = Button(text="X", size_hint_x=0.1, width=40)
                delete_btn.bind(on_release=lambda btn, pid=proj_id: self.delete_projected_transaction(pid))
                row.add_widget(delete_btn)

                self.ids.projected_list.add_widget(row)

    def open_calendar(self, target_input):
        popup = CalendarPopup(target_input=target_input)
        popup.open()

    def load_budget(self, budget_id):
        self.budget_id = budget_id

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT name, start_date, end_date FROM budgets WHERE id=?", (budget_id,))
            row = c.fetchone()

        if row:
            name, start_date, end_date = row
            end = end_date if end_date else "Current"
            self.ids.budget_header.text = f"{name} | {start_date} - {end}"

        self.load_allocated_categories()
        self.load_projected_transactions()
        self.update_summary_labels()

        # Populate spinners
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT name
                FROM categories
                WHERE type = 'Income' AND name != 'System' AND is_active=1
                ORDER BY type desc, name ASC
            """)
            self.ids.alloc_category_spinner.values = [row[0] for row in c.fetchall()]

            c.execute("""
                SELECT name
                FROM categories
                WHERE type = 'Expense' AND name != 'System' AND is_active=1
                ORDER BY type DESC, name ASC""")
            self.ids.proj_category_spinner.values = [row[0] for row in c.fetchall()]

    def load_allocated_categories(self):
        """Load budgeted categories"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT bc.id, c.name, bc.allocated_amount, bc.alloc_desc
                FROM budgeted_categories bc
                JOIN categories c ON bc.category_id = c.id
                WHERE bc.budget_id=?
            """, (self.budget_id,))
            self.allocated_categories = c.fetchall()

        self.ids.allocated_list.clear_widgets()
        for bc in self.allocated_categories:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            label = Label(text=f"{bc[1]} | ${bc[2]:.2f} | {bc[3]}", halign="center", valign="middle")
            label.bind(size=label.setter("text_size"))

            delete_btn = Button(text="X", size_hint_x=None, width=40)
            delete_btn.bind(on_release=lambda btn, bc_id=bc[0]: self.delete_allocated_category(bc_id))

            box.add_widget(label)
            box.add_widget(delete_btn)
            self.ids.allocated_list.add_widget(box)

        self.ids.allocated_list.bind(minimum_height=self.ids.allocated_list.setter('height'))

    def load_projected_transactions(self):
        """Load projected transactions for this budget"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT t.id, c.name, t.amount, t.description, t.date, t.status
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                JOIN budget_transactions bt ON t.id = bt.transaction_id
                WHERE bt.budget_id=? AND t.projected=1
                ORDER BY date ASC
            """, (self.budget_id,))
            self.projected_transactions = c.fetchall()

        self.ids.projected_list.clear_widgets()
        for txn in self.projected_transactions:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            # Transaction label
            label = Label(
                text=f"{txn[1]} | ${txn[2]:.2f} | {txn[3]} | {txn[4]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            # Completed button
            complete_btn = Button(
                text="Completed",
                size_hint_x=None,
                width=100,
                height=40,
                font_size=14
            )
            complete_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.update_projected_status(txn_id, 'completed'))

            # Skipped button
            skip_btn = Button(
                text="Skipped",
                size_hint_x=None,
                width=100,
                height=40,
                font_size=14
            )
            skip_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.update_projected_status(txn_id, 'skipped'))

            # Delete button
            delete_btn = Button(
                text="X",
                size_hint_x=None,
                width=40,
                height=40,
                font_size=16
            )
            delete_btn.bind(on_release=lambda btn, txn_id=txn[0]: self.delete_projected_transaction(txn_id))

            # Disable buttons if already completed/skipped
            if txn[5] in ['completed', 'skipped']:
                complete_btn.disabled = True
                skip_btn.disabled = True
                complete_btn.background_color = (0.7, 0.7, 0.7, 1)
                skip_btn.background_color = (0.7, 0.7, 0.7, 1)
                
            box.add_widget(label)
            box.add_widget(complete_btn)
            box.add_widget(skip_btn)
            box.add_widget(delete_btn)

            self.ids.projected_list.add_widget(box)

        self.ids.projected_list.bind(minimum_height=self.ids.projected_list.setter('height'))

    def add_budgeted_category(self, category_name, amount, desc):
        if not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return
        
        if not desc:
            desc = "No Description"

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            c.execute("""
                INSERT INTO budgeted_categories (budget_id, category_id, allocated_amount, alloc_desc)
                VALUES (?, ?, ?, ?)
            """, (self.budget_id, category_id, amount, desc))
            conn.commit()

        self.ids.alloc_category_spinner.text = "Select Category"
        self.ids.alloc_amount.text = ""
        self.ids.alloc_desc.text = ""
        self.load_allocated_categories()
        self.update_summary_labels()

    def add_projected_transaction(self, category_name, amount, description, date):
        if not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return
        
        if not description:
            description = "No Description"

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get category ID
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            # Insert projected transaction
            c.execute("""
                INSERT INTO transactions (category_id, amount, description, date, projected, status)
                VALUES (?, ?, ?, ?, 1, 'Pending')
            """, (category_id, amount, description, date))
            txn_id = c.lastrowid

            c.execute("INSERT INTO budget_transactions (budget_id, transaction_id) VALUES (?, ?)",
                      (self.budget_id, txn_id))
            conn.commit()

        self.ids.proj_category_spinner.text = "Select Category"
        self.ids.proj_amount.text = ""
        self.ids.proj_desc.text = ""
        self.ids.proj_date.text = ""
        self.load_projected_transactions()
        self.update_summary_labels()

    def update_spent(self):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                
            """)

    def update_projected_status(self, txn_id, new_status):
        """Mark a projected transaction as completed or skipped"""
        if new_status not in ['completed', 'skipped']:
            return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("UPDATE transactions SET status=? WHERE id=?", (new_status, txn_id))
            conn.commit()
        
        self.on_pre_enter()

        # Reload list and summary
        self.load_projected_transactions()
        self.update_summary_labels()

    def edit_budget(self):
        budget_id = self.budget_id

        with sqlite3.connect(DB_NAME) as conn:
            # Get current values
            c = conn.cursor()
            c.execute("SELECT name, start_date FROM budgets WHERE id=?", (budget_id,))
            name, start_date = c.fetchone()

            layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

            name_input = TextInput(text=name, multiline=False)

            # Wrap start_input and "Pick Date" button together
            start_row = BoxLayout(orientation="horizontal", spacing=5, size_hint_y=None, height=40)
            start_input = TextInput(text=start_date, multiline=False, readonly=True)
            pick_date_btn = Button(text="Pick Date", size_hint_x=None, width=100)
            pick_date_btn.bind(on_release=lambda instance: self.open_calendar(start_input))
            start_row.add_widget(start_input)
            start_row.add_widget(pick_date_btn)

            save_btn = Button(text="Save", size_hint_y=None, height=40)

            def save_changes(instance):
                new_name = name_input.text.strip()
                new_start = start_input.text.strip()

                # Update the budget
                c.execute("UPDATE budgets SET name=?, start_date=? WHERE id=?",
                            (new_name, new_start, budget_id))
                conn.commit()

                # --- Recalculate all budget ranges ---
                recalc_budget_ranges(conn)

                popup.dismiss()
                self.load_budget(budget_id)  # refresh header + data

            save_btn.bind(on_release=save_changes)

            layout.add_widget(Label(text="Name:"))
            layout.add_widget(name_input)
            layout.add_widget(Label(text="Start Date (yyyy-mm-dd):"))
            layout.add_widget(start_row)   # instead of adding start_input directly
            layout.add_widget(save_btn)

            popup = Popup(title="Edit Budget", content=layout,
                        size_hint=(0.8, 0.6), auto_dismiss=True)
            popup.open()

    def delete_allocated_category(self, bc_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM budgeted_categories WHERE id=?", (bc_id,))
            conn.commit()
        self.load_allocated_categories()
        self.update_summary_labels()
        
    def delete_projected_transaction(self, txn_id):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
            c.execute("DELETE FROM budget_transactions WHERE transaction_id=?", (txn_id,))
            conn.commit()
        self.load_projected_transactions()
        self.update_summary_labels()

    def update_summary_labels(self):
        """Calculate totals for display"""
        manager = BudgetManager()
        summary = manager.get_budget_summary(self.budget_id)

        self.ids.allocated_label.text = ""
        self.ids.projected_label.text = ""
        self.ids.spent_label.text = ""
        self.ids.remaining_label.text = ""

        # Update with new values
        self.ids.allocated_label.text = f"Allocated: ${summary['allocated']:.2f}"
        self.ids.projected_label.text = f"Projected: ${summary['projected']:.2f}"
        self.ids.spent_label.text = f"Spent: ${summary['spent']:.2f}"
        self.ids.remaining_label.text = f"Remaining: ${summary['remaining']:.2f}"

class CategoryPieChartScreen(Screen):
    start_date = StringProperty("")
    end_date = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # --- Date Selection ---
        date_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.start_input = TextInput(text=self.start_date, hint_text="YYYY-MM-DD", multiline=False)
        self.end_input = TextInput(text=self.end_date, hint_text="YYYY-MM-DD", multiline=False)

        start_cal_btn = Button(text="Pick Date")
        start_cal_btn.bind(on_release=lambda x: CalendarPopup(self.start_input).open())

        end_cal_btn = Button(text="Pick Date")
        end_cal_btn.bind(on_release=lambda x: CalendarPopup(self.end_input).open())

        date_layout.add_widget(Label(text="From:"))
        date_layout.add_widget(self.start_input)
        date_layout.add_widget(start_cal_btn)
        date_layout.add_widget(Label(text="To:"))
        date_layout.add_widget(self.end_input)
        date_layout.add_widget(end_cal_btn)

        # --- Charts area ---
        self.chart_layout = BoxLayout(spacing=10)
        layout.add_widget(date_layout)
        layout.add_widget(self.chart_layout)

        # --- Refresh Button ---
        refresh_btn = Button(text="Update Charts", size_hint_y=None, height=50)
        refresh_btn.bind(on_release=lambda x: self.update_charts())
        layout.add_widget(refresh_btn)

        # --- Back Button ---
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_release=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def update_charts(self):
        """Draw side-by-side pie charts from real DB data."""
        self.chart_layout.clear_widgets()
        start_input = self.start_input.text
        end_input = self.end_input.text

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # --- Allocated budgets per category ---
            c.execute("""
                SELECT c.name, SUM(bc.allocated_amount)
                FROM budgets b
                JOIN budgeted_categories bc ON b.id = bc.budget_id
                JOIN categories c ON bc.category_id = c.id
                WHERE b.start_date BETWEEN ? AND ? AND c.name != 'System'
                GROUP BY c.name
            """, (start_input, end_input))
            budget_data = c.fetchall()

            # --- Actual spending per category ---
            c.execute("""
                SELECT c.name, SUM(t.amount)
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.projected = 0 AND t.date BETWEEN ? AND ? AND c.name != 'System'
                GROUP BY c.name
            """, (start_input, end_input))
            actual_data = c.fetchall()

        # --- Split results into labels + values ---
        categories_alloc = [row[0] for row in budget_data]
        allocated = [row[1] for row in budget_data]

        categories_actual = [row[0] for row in actual_data]
        actual = [abs(row[1]) for row in actual_data]  # ensure positive values


        # --- Build pie charts ---
        fig, axs = plt.subplots(1, 2, figsize=(8, 4))

        if allocated:
            axs[0].pie(allocated, labels=categories_alloc, autopct='%1.1f%%', startangle=90)
            axs[0].set_title("Allocated Budget")
        else:
            axs[0].set_title("No Budget Data")

        if actual:
            axs[1].pie(actual, labels=categories_actual, autopct='%1.1f%%', startangle=90)
            axs[1].set_title("Actual Spending")
        else:
            axs[1].set_title("No Actual Data")

        plt.tight_layout()

        # --- Convert matplotlib figure to Kivy Image ---
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)

        img = CoreImage(buf, ext="png")
        self.chart_layout.add_widget(Image(texture=img.texture))

    def go_back(self, instance):
        self.manager.current = "dashboard"

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
        sm.add_widget(EditAccountScreen(name="edit_account"))
        sm.add_widget(CategoriesScreen(name="categories"))
        sm.add_widget(AddCategoryScreen(name="add_category"))
        sm.add_widget(EditCategoryScreen(name="edit_category"))
        sm.add_widget(TransactionsScreen(name="transactions"))
        sm.add_widget(AddTransactionScreen(name="add_transaction"))
        sm.add_widget(EditTransactionScreen(name="edit_transaction"))
        sm.add_widget(BudgetsScreen(name="budgets"))
        sm.add_widget(BudgetSummaryScreen(name="budget_summary"))
        sm.add_widget(AddBudgetScreen(name="add_budget"))
        sm.add_widget(CategoryPieChartScreen(name="category_pie_chart"))
        return sm


if __name__ == "__main__":
    BudgetBeeApp().run()