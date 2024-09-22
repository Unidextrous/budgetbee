from datetime import datetime
from menus.menu_helpers import *

def menu(account_manager, category_manager, transaction_manager, budget_manager):
    print("Add/Set Menu:")
    print("1. Add account")
    print("2. Add category")
    print("3. Add transaction")
    print("4. Set budget")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        try:
            account = input("Enter the account name: ").upper()
            accounts = account_manager.get_accounts()
            if account in accounts:
                print("Account already exists. Please edit account or enter different account.")
                return
            
            balance = float(input("Enter the starting balance: $"))
            account_manager.set_balance(account, balance)
            if balance >= 0:
                print(f"Balance of ${balance} set for {account} account.")
            else:
                print(f"Balance of -${balance * -1} set for {account} account.")
        except Exception as e:
            print(f"An error occurred in Add Account menu: {e}")
    
    elif choice == "2":
        print("1. Add INCOME category")
        print("2. Add EXPENSE category")
        choice_sub = input("Enter your choice (1/2): ")
        if choice_sub not in ["1", "2"]:
            print("Invalid choice. Please enter 1 or 2.")
            return
        
        if choice_sub == "1":
            category_type = "INCOME"
        elif choice_sub == "2":
            category_type = "EXPENSE"

        category = input("Enter the category name: ").upper()
        category_manager.add_category(category, category_type)

    elif choice == "3":
        try:
            accounts = account_manager.get_accounts()
            if not accounts:
                print("No accounts found. Please set the balance of at least one account first.")
                return

            income_categories = category_manager.get_categories_by_type("INCOME")
            expense_categories = category_manager.get_categories_by_type("EXPENSE")
            categories = income_categories + expense_categories
            if not categories:
                print("No categories found. Please add at least one category first.")
                return
            
            account = select_account(account_manager)
            if not account:
                return
            category = select_category(category_manager)
            if not category:
                return

            if category in income_categories:
                category_type = "INCOME"
                amount = float(input("Enter the transaction amount: $"))
            elif category in expense_categories:
                category_type = "EXPENSE"
                amount = float(input("Enter the transaction amount: -$"))
            
            if amount < 0:
                print("Invalid input. Please enter a positive number.")
                return

            balance = account_manager.get_balance(account)
            details = input("Enter transaction details: ").upper()
            date = input_date()

            balance = account_manager.get_balance(account)
            if category in income_categories:
                new_balance = balance + amount
            elif category in expense_categories:
                new_balance = balance - amount
            transaction_manager.update_all_remaining_balances(account)
            transaction_manager.add_transaction(account, amount, new_balance, category, details, date)
            if category in income_categories:
                print(f"Transaction of ${amount} added. New {account} balance: ${new_balance}")
            elif category in expense_categories:
                print(f"Transaction of -${amount} added. New {account} balance: ${new_balance}")
        except Exception as e:
            print(f"An error occurred in Add Transaction menu: {e}")

    elif choice == "4":
        try:
            income_categories = category_manager.get_categories_by_type("INCOME")
            expense_categories = category_manager.get_categories_by_type("EXPENSE")
            if not income_categories:
                print("No EXPENSE categories found. Please set a budget for at least one EXPENSE category first.")
                return            
            print(f"Available categories: {', '.join(set(expense_categories))}")
            category = input("Enter the budget category name: ").upper()
            if category not in expense_categories:
                if category in income_categories:
                    print(f"{category} is an INCOME category. Please set the budget for an EXPENSE category.")
                    return
                print("Category not found. Please enter a valid category.")
                return

            budget_limit = float(input("Enter the budget limit: $"))
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            budget_manager.set_budget(category, budget_limit, start_date)
            print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
        except Exception as e:
            print(f"An error occurred in Set Budget menu: {e}")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")