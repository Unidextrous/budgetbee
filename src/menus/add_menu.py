from datetime import datetime
from menus.menu_helpers import *

def menu(account_manager, category_manager, transaction_manager, budget_manager):
    # Display the menu options for adding or setting items
    print("Add/Set Menu:")
    print("1. Add account")
    print("2. Add category")
    print("3. Add transaction")
    print("4. Set budget")
    choice = input("Enter your choice (1/2/3/4): ")

    # Choice 1: Add account
    if choice == "1":
        try:
            # Get the account name from the user and convert it to uppercase
            account = input("Enter the account name: ").upper()
            existing_accounts = account_manager.get_accounts()

            # Check if the account already exists
            if account in existing_accounts:
                print("Account already exists. Please edit account or enter different account.")
                return
            
            # Get the starting balance from the user and add the account
            balance = float(input("Enter the starting balance: $"))
            account_manager.add_account(account, balance)

            # Display appropriate message based on the balance (positive or negative)
            if balance >= 0:
                print(f"Added account {account} with a balance of ${balance}.")
            else:
                print(f"Added account {account} with a balance of -${balance * -1}.")
        except Exception as e:
            print(f"An error occurred in Add Account menu: {e}")
            return None
    
    # Choice 2: Add category
    elif choice == "2":
        # Get the category from the user and convert it to uppercase
        category = input("Enter the category name: ").upper()

        # Get the category type from the user and convert it to uppercase
        category_type = input("Enter category type (INCOME/EXPENSE): ").strip().upper()

        # Check if the category already exists
        existing_categories = category_manager.get_categories_by_type()  # Retrieve existing categories
        if category in existing_categories:
            print("Category already exists.")  # Check for duplicates
            return
        
        # Add the category
        category_manager.add_category(category, category_type)

    # Choice 3: Add transaction
    elif choice == "3":
        try:
            # Ensure that at least one account and category exists before proceeding
            accounts = account_manager.get_accounts()
            if not accounts:
                print("No accounts found. Please set the balance of at least one account first.")
                return

            # Fetch available categories for INCOME and EXPENSE
            income_categories = category_manager.get_categories_by_type("INCOME")
            expense_categories = category_manager.get_categories_by_type("EXPENSE")
            categories = income_categories + expense_categories
            if not categories:
                print("No categories found. Please add at least one category first.")
                return
            
            # Select an account and category for the transaction
            account = select_account(account_manager)
            if not account:
                return
            category = select_category(category_manager)
            if not category:
                return

            # Get the transaction amount based on category type (INCOME or EXPENSE)
            if category in income_categories:
                category_type = "INCOME"
                amount = float(input("Enter the transaction amount: $"))
            elif category in expense_categories:
                category_type = "EXPENSE"
                amount = float(input("Enter the transaction amount: -$"))
            
            # Ensure the amount is positive
            if amount < 0:
                print("Invalid input. Please enter a positive number.")
                return

            # Get account transaction details from the user
            details = input("Enter transaction details: ").upper()
            date = input_date()

            # Update remaining balance based on category type and amount
            balance = account_manager.get_balance(account)            
            if category in income_categories:
                new_balance = balance + amount
            elif category in expense_categories:
                new_balance = balance - amount

            # Add transaction and update all remaining balances
            transaction_manager.update_all_remaining_balances(account)
            transaction_manager.add_transaction(account, amount, category, details, date)

            # Display appropriate message based on category type
            if category in income_categories:
                print(f"Transaction of ${amount} added. New {account} balance: ${new_balance}")
            elif category in expense_categories:
                print(f"Transaction of -${amount} added. New {account} balance: ${new_balance}")
        except Exception as e:
            print(f"An error occurred in Add Transaction menu: {e}")
            return None

    # Choice 4: Set budget
    elif choice == "4":
        try:
            # Fetch available EXPENSE categories
            income_categories = category_manager.get_categories_by_type("INCOME")
            expense_categories = category_manager.get_categories_by_type("EXPENSE")
            if not expense_categories:
                print("No EXPENSE categories found. Please add at least one EXPENSE category first.")
                return    

            # Display available expense categories and get the user's input for the category        
            print(f"Available categories: {', '.join(set(expense_categories))}")
            category = input("Enter the budget category name: ").upper()

            # Ensure the category is a valid EXPENSE category
            if category not in expense_categories:
                if category in income_categories:
                    print(f"{category} is an INCOME category. Please add an EXPENSE category.")
                    return
                print("Category not found. Please enter a valid category.")
                return
            
            # Get the budget limit and start date from the user
            budget_limit = float(input("Enter the budget limit: $"))
            if budget_limit < 0:
                raise ValueError("Amount must be positive.")

            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

            # Set the budget for the selected category
            budget_manager.set_budget(category, budget_limit, start_date)
            print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
        except ValueError as ve:
            print(f"Input error: {ve}")
            return None
        except Exception as e:
            print(f"An error occurred in Set Budget menu: {e}")
            return None

    # Handle invalid menu choice
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")