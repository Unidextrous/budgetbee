from datetime import datetime
from menus.menu_helpers import *

def menu(account_manager, category_manager, transaction_manager, budget_manager):
    # Display the menu options for adding or setting items
    print("Add Menu:")
    print("1. Add account")
    print("2. Add category")
    print("3. Add transaction")
    choice = input("Enter your choice (1/2/3): ")

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

        # Ensure category name is not "UNALLOCATED"
        if category == "UNALLOCATED":
            print("Invalid category name.")
            return

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
            check_for_accounts(account_manager)
            check_for_categories(category_manager)
            
            # Select an account and category for the transaction
            view_accounts(account_manager)
            account = select_account(account_manager)
            if not account:
                return
            
            view_categories(category_manager, False)
            category = select_category(category_manager, False)
            if not category:
                return
            
            # Get the transaction amount based on category type (INCOME or EXPENSE)
            if category_manager.get_category_type(category) == "INCOME":
                category_type = "INCOME"
                amount = float(input("Enter the transaction amount: $"))
            elif category_manager.get_category_type(category) == "EXPENSE":
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
            if category_type == "INCOME":
                new_balance = balance + amount
            elif category_type == "EXPENSE":
                if transaction_manager.is_within_budget_limit(category, amount, date.isoformat()):
                    new_balance = balance - amount
                else: return

            # Add transaction and update all remaining balances
            transaction_id = transaction_manager.add_transaction(account, amount, category, details, date)
            transaction_manager.update_all_remaining_balances(account)

            # Display appropriate message based on category type
            if category_type == "INCOME":
                print(f"Transaction of ${amount} added. New {account} balance: ${new_balance}")
            elif category_type == "EXPENSE":
                print(f"Transaction of -${amount} added. New {account} balance: ${new_balance}")
        except Exception as e:
            print(f"An error occurred in Add Transaction menu: {e}")
            return None

        # Check if "UNALLOCATED" category exists, if not, create it
        existing_categories = category_manager.get_categories_by_type()
        
        if "UNALLOCATED" not in existing_categories:
            # If "UNALLOCATED" category doesn't exist, create it
            category_manager.add_category("UNALLOCATED", "EXPENSE")

        if category_type == "INCOME" and len(category_manager.get_categories_by_type("EXPENSE")) > 1:
            allocate_to_budgets(category_manager, budget_manager, amount, date, transaction_id)
        elif len(category_manager.get_categories_by_type("EXPENSE")) == 1:
            budget_manager.set_budget("UNALLOCATED", amount, date, transaction_id)
        elif category_type == "EXPENSE":
            transaction_manager.deduct_from_budget(category, amount)

    # Handle invalid menu choice
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")