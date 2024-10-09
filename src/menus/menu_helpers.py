from datetime import datetime

def select_account(account_manager):
    accounts = account_manager.get_accounts()
    if not accounts:
        print("No accounts available.")
        return None
    account_name = input("Enter the account name: ").upper()
    if account_name not in accounts:
        print(f"Account {account_name} not found.")
        return None
    return account_name

def select_category(category_manager, include_unallocated, category_type=None):
    if category_type == "INCOME":
        income_categories = category_manager.get_categories_by_type("INCOME")
        categories = income_categories
    elif category_type == "EXPENSE":
        expense_categories = category_manager.get_categories_by_type("EXPENSE")
        categories = expense_categories
    else:
        categories = category_manager.get_categories_by_type()
    if "UNALLOCATED" in categories and include_unallocated == False:
        categories.remove("UNALLOCATED")
    
    category = input("Enter the category: ").upper()
    if category not in categories:
        print(f"Category {category} not found.")
        return None
    return category

def input_date():
    try:
        date_str = input("Enter the date (YYYY-MM-DD): ")
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return None

def view_accounts(account_manager):
    # Function to get view accounts
    accounts = account_manager.get_accounts()
    if not accounts:
        # Notify if no accounts are found
        print("No accounts found. Please set the balance of at least one account first.")
        return
    
    total_balance = 0.0
    # Loop through each account to display its balance
    for account in accounts:
        balance = account_manager.get_balance(account)
        total_balance += balance
        # Display balance with positive or negative formatting
        if balance >= 0:
            print(f"- {account}: ${balance}")
        else:
            print(f"- {account}: -${balance * -1}")

    # Display the total balance
    if total_balance >= 0:
        print(f"TOTAL BALANCE: ${total_balance}")
    else:
        print(f"TOTAL BALANCE: -${total_balance * -1}")

def view_categories(category_manager, include_unallocated, category_type=None):
    # Function to view categories
    income_categories = category_manager.get_categories_by_type("INCOME")
    expense_categories = category_manager.get_categories_by_type("EXPENSE")

    if "UNALLOCATED" in expense_categories and include_unallocated == False:
        expense_categories.remove("UNALLOCATED")

    if income_categories or expense_categories:
        # Display income categories, if any exist
        if income_categories and category_type != "EXPENSE":
            print("INCOME categories:")
            for category in income_categories:
                print(f"- {category}")
        # Display expense categories, if any exist
        if expense_categories and category_type != "INCOME":
            print("EXPENSE categories")
            for category in expense_categories:
                print(f"- {category}")
    else:
        # Notify if no categories are found
        print("No categories found.")