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
            accounts = account_manager.get_accounts()
            if not accounts:
                print("No accounts found. Please set the balance of at least one account first.")
                return

            # Fetch available categories for INCOME and EXPENSE
            income_categories = category_manager.get_categories_by_type("INCOME")
            expense_categories = category_manager.get_categories_by_type("EXPENSE")
            if "UNALLOCATED" in expense_categories:
                expense_categories.remove("UNALLOCATED")
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
            transaction_id = transaction_manager.add_transaction(account, amount, category, details, date)

            # Display appropriate message based on category type
            if category in income_categories:
                print(f"Transaction of ${amount} added. New {account} balance: ${new_balance}")
            elif category in expense_categories:
                print(f"Transaction of -${amount} added. New {account} balance: ${new_balance}")
        except Exception as e:
            print(f"An error occurred in Add Transaction menu: {e}")
            return None

        # Check if "UNALLOCATED" category exists, if not, create it
        unallocated_category = "UNALLOCATED"
        existing_categories = category_manager.get_categories_by_type()
        
        if unallocated_category not in existing_categories:
            # If "UNALLOCATED" category doesn't exist, create it
            category_manager.add_category(unallocated_category, "EXPENSE")

        if category_type == "INCOME" and len(expense_categories) > 0:
            remaining_amount = amount
            print(f"Total income: ${amount}")

            while remaining_amount > 0:
                set_budget = input(f"You have ${remaining_amount} left to allocate. Would you like to allocate it to a budget category? (Y/N): ").strip().upper()
                if set_budget == "Y":
                    # Fetch available expense categories for budgeting
                    print(f"Available categories: {', '.join(expense_categories)}")
                    budget_category = input("Enter the category to allocate budget: ").upper()

                    # Validate the category input
                    if budget_category in expense_categories:
                        # Ask for the amount to allocate to the chosen category
                        budget_limit = -1  # Initialize with an invalid value
                        while budget_limit <= 0:
                            try:
                                budget_limit = float(input(f"Enter the budget amount (MAX ${remaining_amount}): $"))
                                if budget_limit <= 0:
                                    print("Please enter a positive budget amount. If you'd like to change the amount of a budget, go to edit menu.")
                                elif budget_limit > remaining_amount:
                                    print(f"Amount exceeds remaining income. Please enter a value less than or equal to ${remaining_amount}.")
                                    budget_limit = -1  # Reset to invalid
                            except ValueError:
                                print("Invalid input. Please enter a valid number.")

                        # Set the budget for the selected category
                        budget_manager.set_budget(budget_category, budget_limit, date, transaction_id)
                        print(f"Budget of ${budget_limit} allocated to category {budget_category}.")

                        # Update remaining amount
                        remaining_amount -= budget_limit

                    else:
                        print("Invalid category. Please enter a valid expense category.")
                else:
                    # If user declines to allocate more budget, break the loop
                    break

            if remaining_amount > 0:
                print(f"${remaining_amount} of income remains unallocated.")
                budget_manager.set_budget(unallocated_category, remaining_amount, date, transaction_id)
        elif len(expense_categories) == 0:
            print(f"${amount} of income remains unallocated.")
            budget_manager.set_budget(unallocated_category, amount, date, transaction_id)

    # Handle invalid menu choice
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")