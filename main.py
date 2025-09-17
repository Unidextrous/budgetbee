import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
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
                owner TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL,
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
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                projected INTEGER DEFAULT 0,
                fulfilled INTEGER DEFAULT 0,
                status TEXT DEFAULT "Pending",
                FOREIGN KEY(account_id) REFERENCES accounts(id),
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)

        # Budgets table
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                start_date TEXT NOT NULL,
                end_date TEXT,          -- Optional; can be null if paycheck-to-paycheck
                type TEXT               -- "paycheck", "monthly", "yearly"
            )
        """)

        # Budgeted categories table
        c.execute("""
            CREATE TABLE IF NOT EXISTS budgeted_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                allocated_amount REAL NOT NULL,
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
            c.execute("""
                SELECT id, owner, name, balance
                FROM accounts
                WHERE is_active = 1
                ORDER BY owner ASC, name ASC
            """)
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
    def on_pre_enter(self):
        self.ids.owner.text = ""
        self.ids.name.text = ""
        self.ids.balance.text = ""

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
                WHERE name != 'System' AND is_active = 1
                ORDER BY type DESC, name ASC""")
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
                WHERE projected = 0
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
        self.ids.account_spinner.text = "Select Account"
        self.ids.category_spinner.text = "Select Category"
        self.ids.amount.text = ""
        self.ids.description.text = ""
        self.ids.date.text = ""  # if you’re using a date field

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

            # Insert the transaction
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, description)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, category_id, float(amount), date, description))
        
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

import sqlite3

DB_NAME = "budgetbee.db"

class BudgetManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name

    # -----------------------------
    # Budget Creation
    # -----------------------------
    def create_budget(self, name, start_date, end_date=None, type="paycheck"):
        """Create a new budget and return its ID"""
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO budgets (name, start_date, end_date, type)
                VALUES (?, ?, ?, ?)
            """, (name, start_date, end_date, type))
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
    def add_projected_transaction(self, account_name, category_name, amount, date):
        if not account_name or not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get account ID
            c.execute("SELECT id FROM accounts WHERE name=?", (account_name,))
            row = c.fetchone()
            if not row:
                return
            account_id = row[0]

            # Get category ID
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            # Insert projected transaction
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, projected)
                VALUES (?, ?, ?, ?, 1)
            """, (account_id, category_id, amount, date))
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
                """, (start_date, end_date))
            else:
                c.execute("""
                    SELECT SUM(amount) 
                    FROM transactions
                    WHERE projected=0 AND amount<0
                    AND date >= ?
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
            c.execute("SELECT id, name, start_date, end_date, type FROM budgets ORDER BY start_date DESC")
            self.budgets = c.fetchall()

        # Update UI list
        self.ids.budgets_list.clear_widgets()
        for b in self.budgets:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            label = Label(
                text=f"{b[1]} | {b[2]} - {b[3] or 'Current'} | {b[4]}",
                halign="center",
                valign="middle"
            )
            label.bind(size=label.setter("text_size"))

            view_btn = Button(text="View", size_hint_x=None, width=80)
            view_btn.bind(on_release=lambda btn, budget_id=b[0]: self.view_budget(budget_id))
            delete_btn = Button(text="X", size_hint_x=0.1)
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

        # Refresh the budgets list
        self.on_pre_enter()

class AddBudgetScreen(Screen):
    def on_pre_enter(self):
        """Reset fields"""
        self.ids.budget_name.text = ""
        self.ids.start_date.text = datetime.now().strftime("%Y-%m-%d")
        self.ids.type_spinner.text = "Paycheck"  # default type

    def add_budget(self, name, start_date, type):
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date, "%Y-%m-%d")

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()

            # Step 1: Insert the new budget
            c.execute("""
                INSERT INTO budgets (name, start_date, type)
                VALUES (?, ?, ?)
            """, (name, start_date, type))
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
            return new_id

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

                delete_btn = Button(text="X", size_hint_x=0.1)
                delete_btn.bind(on_release=lambda btn, pid=proj_id: self.delete_projected_transaction(pid))
                row.add_widget(delete_btn)

                self.ids.projected_list.add_widget(row)

    def load_budget(self, budget_id):
        self.budget_id = budget_id
        self.load_allocated_categories()
        self.load_projected_transactions()
        self.update_summary_labels()

        # Populate spinners
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT name
                FROM categories
                WHERE type = 'Expense' AND name != 'System' AND is_active=1
                ORDER BY type desc, name ASC
            """)
            self.ids.alloc_category_spinner.values = [row[0] for row in c.fetchall()]

            c.execute("""
                SELECT name
                FROM accounts
                WHERE is_active=1
                ORDER BY owner ASC, name ASC
            """)
            self.ids.proj_account_spinner.values = [row[0] for row in c.fetchall()]

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
                SELECT bc.id, c.name, bc.allocated_amount
                FROM budgeted_categories bc
                JOIN categories c ON bc.category_id = c.id
                WHERE bc.budget_id=?
            """, (self.budget_id,))
            self.allocated_categories = c.fetchall()

        self.ids.allocated_list.clear_widgets()
        for bc in self.allocated_categories:
            box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            label = Label(text=f"{bc[1]} | ${bc[2]:.2f}", halign="center", valign="middle")
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
                SELECT t.id, a.name, c.name, t.amount, t.date, t.status
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
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
                text=f"{txn[1]} | {txn[2]} | ${txn[3]:.2f} | {txn[4]}",
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
                width=50,
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

    def add_budgeted_category(self, category_name, amount):
        if not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            c.execute("""
                INSERT INTO budgeted_categories (budget_id, category_id, allocated_amount)
                VALUES (?, ?, ?)
            """, (self.budget_id, category_id, amount))
            conn.commit()

        self.ids.alloc_category_spinner.text = "Select Category"
        self.ids.alloc_amount.text = ""
        self.load_allocated_categories()
        self.update_summary_labels()

    def add_projected_transaction(self, account_name, category_name, amount, date):
        if not account_name or not category_name or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            # Get account ID
            c.execute("SELECT id FROM accounts WHERE name=?", (account_name,))
            row = c.fetchone()
            if not row:
                return
            account_id = row[0]

            # Get category ID
            c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
            row = c.fetchone()
            if not row:
                return
            category_id = row[0]

            # Insert projected transaction
            c.execute("""
                INSERT INTO transactions (account_id, category_id, amount, date, projected, status)
                VALUES (?, ?, ?, ?, 1, 'Pending')
            """, (account_id, category_id, amount, date))
            txn_id = c.lastrowid

            c.execute("INSERT INTO budget_transactions (budget_id, transaction_id) VALUES (?, ?)",
                      (self.budget_id, txn_id))
            conn.commit()

        self.ids.proj_account_spinner.text = "Select Account"
        self.ids.proj_category_spinner.text = "Select Category"
        self.ids.proj_amount.text = ""
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
        sm.add_widget(BudgetsScreen(name="budgets"))
        sm.add_widget(BudgetSummaryScreen(name="budget_summary"))
        sm.add_widget(AddBudgetScreen(name="add_budget"))
        return sm


if __name__ == "__main__":
    BudgetBeeApp().run()