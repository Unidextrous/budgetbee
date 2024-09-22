from datetime import datetime

def select_account(account_manager):
    accounts = account_manager.get_accounts()
    if not accounts:
        print("No accounts available.")
        return None
    print(f"Available accounts: {', '.join(accounts)}")
    account_name = input("Enter the account name: ").upper()
    if account_name not in accounts:
        print("Account not found.")
        return None
    return account_name

def select_category(category_manager):
    income_categories = category_manager.get_categories_by_type("INCOME")
    expense_categories = category_manager.get_categories_by_type("EXPENSE")
    categories = income_categories + expense_categories
    if not categories:
        print("No categories available.")
        return None
    if income_categories:
        print(f"Available INCOME categories: {', '.join(income_categories)}")
    if expense_categories:
        print(f"Available EXPENSE categories: {', '.join(expense_categories)}")
    category = input("Enter the category: ").upper()
    if category not in categories:
        print("Category not found.")
        return None
    return category

def input_date():
    try:
        date_str = input("Enter the date (YYYY-MM-DD): ")
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return None