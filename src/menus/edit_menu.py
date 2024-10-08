from datetime import datetime
from menus.menu_helpers import *

# Updates the balance for the specified account in the account manager
def update_balance(account_manager, account_name):
    try:
        # Retrieve current balance
        current_balance = account_manager.get_balance(account_name)

        # Display the current balance (formatted for positive/negative values)
        if current_balance >= 0:
            print(f"Current balance: ${current_balance}")
        else:
            print(f"Current balance: -${current_balance * -1}")
        
        # Prompt the user for a new balance
        new_balance = float(input("Enter the new balance: $"))

        # Update the balance in the account manager
        account_manager.reset_balance(account_name, new_balance)

        # Display the updated balance
        if new_balance >= 0:
            print(f"{account_name} balance set to ${new_balance}")
        else:
            print(f"{account_name} balance set to -${new_balance * -1}")
    except Exception as e:
        # Catch and display any errors that occur
        print(f"An error occurred: {e}")
        return None

# Confirms the deletion of an item (account, category, or transaction)
def confirm_deletion(manager, item, item_type, category_type=None):
    delete = input(f"Are you sure you wish to delete this {item_type}? Y/N: ").upper()
    if delete == "Y":
        if item_type == "Transaction":
            manager.delete(item, category_type)
        else:
            manager.delete(item)
        print(f"{item_type} {item} deleted.")

# Displays the main edit menu and handles user input for account, category, transaction, and budget edits
def menu(account_manager, category_manager, transaction_manager, budget_manager):
    print("Edit:")
    print("1. Edit account")
    print("2. Edit category")
    print("3. Edit transaction")
    print("4. Edit budget")
    choice = input("Enter your choice (1/2/3/4): ")

    # Edit Account menu
    if choice == "1":
        account_name = select_account(account_manager)
        if not account_name:
            print(f"Account {account_name} not found. Please check the account name and try again.")
            return
        
        print("1. Rename account")
        print("2. Change balance (this will retroactively change the starting balance)")
        print("3. Delete account")
        account_choice = input("Enter your choice (1/2/3): ")

        if account_choice not in ["1", "2", "3"]:
            print("Invalid choice. Please enter 1, 2, or 3.")
            return
        
        # Rename account option
        if account_choice == "1":
            new_name = input("New account name: ").upper()
            if new_name in account_manager.get_accounts():
                print("New account name already exists.")
                return
            account_manager.rename_account(account_name, new_name)
            print(f"Renamed {account_name} to {new_name}")
        
        # Change account balance option
        elif account_choice == "2":
            update_balance(account_manager, account_name)

        # Delete account option
        elif account_choice == "3":
            confirm_deletion(account_manager, account_name, "Account")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    # Edit Category menu
    elif choice == "2":
        category = select_category(category_manager)
        if not category:
            print(f"Category {category} not found. Please check the category name and try again.")
            return

        print("1. Rename category")
        print("2. Delete category")
        category_choice = input("Enter your choice (1/2): ")

        # Rename category option
        if category_choice == "1":
            new_name = input("Enter the new name for the category: ").upper()
            categories = category_manager.get_categories_by_type()
            if new_name in categories:
                print("New category name already exists.")
                return

            category_manager.rename_category(category, new_name)
            print(f"Category renamed from {category} to {new_name}.")
        
        # Delete category option
        elif category_choice == "2":
            confirm_deletion(category_manager, category, "Category")

        else:
            print("Invalid choice. Please enter 1 or 2.")

    # Edit Transaction menu
    elif choice == "3":
        try:
            transaction_id = int(input("Enter the ID of the transaction to edit: "))
        except ValueError:
            print("Invalid input. Please enter a numeric transaction ID.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        # Retrieve the transaction by its ID
        transaction = transaction_manager.get_transaction_by_id(transaction_id)

        if transaction == None:
            print(f"Transaction with ID {transaction_id} not found. Please check the ID and try again.")
            return
        
        # Extract transaction details
        txn_id, account, amount, remaining_balance, category, details, date = transaction
        income_categories = category_manager.get_categories_by_type("INCOME")
        expense_categories = category_manager.get_categories_by_type("EXPENSE")

        # Format amount and remaining balance for display based on category type (income/expense)
        if category in income_categories:
            amount_as_str = f"${amount}"
        elif category in expense_categories:
            amount_as_str = f"-${amount}"
        if remaining_balance >= 0:
            remaining_balance_as_str = f"${remaining_balance}"
        else:
            remaining_balance_as_str = f"-${remaining_balance}"

        # Format transaction date for display
        date_object = datetime.fromisoformat(date)  # Assuming `date` is a string in ISO format like '2024-09-22T00:00:00'
        formatted_date = date_object.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
        
        print(f"ID: {txn_id}, Account: {account} Amount: {amount_as_str}, Remaining balance: {remaining_balance_as_str} Category: {category}, Details: {details}, Date: {formatted_date}")
        
        # Display transaction edit options
        print("1. Update transaction account")
        print("2. Update transaction amount")
        print("3. Update transaction category")
        print("4. Update transaction details")
        print("5. Update transaction date")
        print("6. Delete transaction")
        transaction_choice = input("Enter your choice (1/2/3/4/5/6): ")

        # Update transaction account option
        if transaction_choice == "1":
            accounts = account_manager.get_accounts()
            accounts.remove(account)
            if not accounts:
                print("No available accounts.")
                return
            print(f"Available accounts: {', '.join(accounts)}")
            new_account = input("Enter the new account name: ").upper()
            if new_account == account:
                print("Please enter a valid account.")
                return
            elif new_account not in accounts:
                print("Account not found. Please enter a valid account.")
                return
            transaction_manager.update_transaction_account(transaction_id, category, new_account)
            print(f"{account} balance updated to ${account_manager.get_balance(account)}")
            account = new_account

        # Update transaction amount option
        elif transaction_choice == "2":
            try:
                new_amount = float(input("Enter the new transaction amount: $"))
                if new_amount < 0:
                    raise ValueError("Amount must be positive.")

                transaction_manager.update_transaction_amount(transaction_id, category, new_amount)
                print(f"Transaction amount updated to ${new_amount}.")
            except ValueError as ve:
                print(f"Input error: {ve}")
                return None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None

        # Update transaction category option
        elif transaction_choice == "3":
            # Get the current category type (INCOME or EXPENSE)
            current_type = category_manager.get_category_type(category)
            
            # Fetch categories of the same type (INCOME or EXPENSE)
            categories = category_manager.get_categories_by_type(current_type)
            
            # Remove the current category from the list
            categories.remove(category)
            
            # Check if there are available categories of the same type
            if not categories:
                print(f"No available {current_type} categories.")
                return
            
            print(f"Available {current_type} categories: {', '.join(categories)}")
            new_category = input("Enter new category: ").upper()
            
            # Check if the entered category exists in the list of available categories
            if new_category in categories:
                transaction_manager.update_category(transaction_id, new_category)
                print(f"Category updated to {new_category}.")
            elif new_category == category:
                print("Invalid category.")
            else:
                print("Category does not exist. Please enter a valid category.")
        
        # Update transaction details option
        elif transaction_choice == "4":
            new_details = input("Enter the new transaction details: ").upper()
            transaction_manager.update_transaction_details(transaction_id, category, new_details)
            print(f"Transaction details updated to {new_details}.")

        # Update transaction date option
        elif transaction_choice == "5":
            new_date = input_date()  # Use input_date() here
            if new_date:
                transaction_manager.update_transaction_date(transaction_id, category, new_date)
                print(f"Transaction date updated to {new_date}.")
            else:
                return

        # Delete category option
        elif transaction_choice == "6":
            confirm_deletion(transaction_manager, transaction_id, "Transaction", category)
            transaction_manager.update_all_remaining_balances(account)

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")
            return
        
        transaction_manager.update_all_remaining_balances(account)
        print(f"{account} balance updated to ${account_manager.get_balance(account)}.")
        
    
    elif choice == "4":
        pass

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")