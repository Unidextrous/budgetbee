# The AccountManager class handles account-related operations such as
# setting and updating balances, renaming accounts, etc.
class AccountManager:
    def __init__(self, db):
        # Initialize with a database connection
        self.db = db
    
    # Method to add an account
    def add_account(self, account, balance):
        # Insert a new account into the accounts table with starting and current balance
        self.db.execute("INSERT INTO accounts (account, starting_balance, balance) VALUES (?, ?, ?)",
           (account, balance, balance)
        )

    def get_accounts(self):
        # Fetch all account names from the accounts table
        return [row[0] for row in self.db.fetchall("SELECT account FROM accounts")]
    
    # Method to get the starting balance of a specific account
    def get_starting_balance(self, account):
        # Fetch the starting balance for the specified account
        balance = self.db.fetchone("SELECT starting_balance FROM accounts WHERE account = ?", (account,))
        if balance:
            return balance[0]   # Return the starting balance if found
        else:
            return None # Return None if the account doesn't exist

    # Method to get the current balance of an account (or the total balance of all accounts if '*' is passed)
    def get_balance(self, account):
        if account == "*":
            # If '*' is passed, sum the balances of all accounts
            balance = self.db.fetchall("SELECT SUM(balance) FROM accounts")
        else:
            # Otherwise, fetch the balance of the specified account
            balance = self.db.fetchall("SELECT balance FROM accounts WHERE account = ?", (account,))

        return balance[0][0]    # Return the balance (or sum of balances)

    # Method to update the balance of a specific account
    def update_balance(self, account, new_balance):
        # Update the balance of the specified account
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))

    # Method to rename an account
    def rename_account(self, old_name, new_name):
        # Update the account name in the accounts table
        self.db.execute("UPDATE accounts SET account = ? WHERE account = ?", (new_name, old_name))
        # Update the account name in the transactions table to maintain consistency
        self.db.execute("UPDATE transactions SET account = ? WHERE account = ?", (new_name, old_name))

    # Method to reset the balance of a specific account
    def reset_balance(self, account, new_balance):
        # Reset the balance to a new value for the specified account
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))

    # Method to delete an account and all related transactions
    def delete(self, account):
        # Delete the account from the accounts table
        self.db.execute("DELETE FROM accounts WHERE account = ?", (account,))
        # Delete all transactions related to the account
        self.db.execute("DELETE FROM transactions WHERE account = ?", (account,))

    # Method to adjust the balance of an account by a certain amount
    def adjust_balance(self, account, amount):
        # Get the current balance of the account
        current_balance = self.get_balance(account)
        # Calculate the new balance by adding the adjustment amount
        new_balance = current_balance + amount
        # Update the account with the new balance
        self.db.execute("UPDATE accounts SET balance = ? WHERE account = ?", (new_balance, account))