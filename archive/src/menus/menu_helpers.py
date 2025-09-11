from datetime import datetime

def check_for_accounts(account_manager):
    accounts = account_manager.get_accounts()
    if not accounts:
        print("No accounts found. Please set the balance of at least one account first.")
        return

def check_for_categories(category_manager):
    categories = category_manager.get_categories_by_type()
    if "UNALLOCATED" in categories:
        categories.remove("UNALLOCATED")
    if not categories:
        print("No categories found. Please add at least one category first.")
        return

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

def allocate_to_budgets(category_manager, budget_manager, amount, date, transaction_id):
    remaining_amount = amount
    print(f"Total income: ${amount}")

    while remaining_amount > 0:
        set_budget = input(f"You have ${remaining_amount} left to allocate. Would you like to allocate it to a budget category? (Y/N): ").strip().upper()
        if set_budget == "Y":
            # Fetch available expense categories for budgeting
            view_categories(category_manager, False, "EXPENSE")
            budget_category = input("Enter the category to allocate budget: ").upper()

            # Validate the category input
            if category_manager.get_category_type(budget_category) == "EXPENSE":
                # Ask for the amount to allocate to the chosen category
                budget_limit = -1  # Initialize with an invalid value
                while budget_limit <= 0:
                    try:
                        budget_limit = float(input(f"Enter the budget amount (MAX: ${remaining_amount}): $"))
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
        budget_manager.set_budget("UNALLOCATED", remaining_amount, date, transaction_id)

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

def update_amount(category_manager, transaction_manager, budget_manager, category, amount, new_amount, date_str, transaction_id):
    category_type = category_manager.get_category_type(category)
    date = datetime.strptime(date_str[:10], "%Y-%m-%d")

    if category_type == "INCOME":
        # Delete existing budget
        budget_manager.delete_by_transaction_id(transaction_id)
        # Reallocate budget to account for decrease in income
        allocate_to_budgets(category_manager, budget_manager, new_amount, date, transaction_id)

    elif category_type == "EXPENSE":
        if new_amount > amount:
            # Check to make sure that the new amount is within the budget
            if transaction_manager.is_within_budget_limit(category, (new_amount - amount), date):
                # Deduct difference from remaining budget
                transaction_manager.deduct_from_budget(category, (new_amount - amount))
        elif new_amount < amount:
            # Refund difference (amount - new_amount) to budget
            transaction_manager.refund_budget(category, amount - new_amount)
    
    transaction_manager.update_transaction_amount(transaction_id, category, new_amount)

# Confirms the deletion of an item (account, category, or transaction)
def confirm_deletion(manager, item, item_type, category_type=None):
    delete = input(f"Are you sure you wish to delete this {item_type}? Y/N: ").upper()
    if delete == "Y":
        if item_type == "Transaction":
            manager.delete(item, category_type)
        else:
            manager.delete(item)
        print(f"{item_type} {item} deleted.")
