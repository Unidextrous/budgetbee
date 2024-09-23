from datetime import datetime

def menu(account_manager, category_manager, transaction_manager, budget_manager):
    # Display the menu options for viewing items
    print("View Menu:")
    print("1. View account balances")
    print("2. View categories")
    print("3. View transactions")
    print("4. View budgets")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        # Option to view all account balances
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
        
            
    elif choice == "2":
        # Option to view categories (INCOME and EXPENSE)
        income_categories = category_manager.get_categories_by_type("INCOME")
        expense_categories = category_manager.get_categories_by_type("EXPENSE")

        if income_categories or expense_categories:
            # Display income categories, if any exist
            if income_categories:
                print("INCOME categories:")
            for category in income_categories:
                print(f"- {category}")
            # Display expense categories, if any exist
            if expense_categories:
                print("EXPENSE categories")
            for category in expense_categories:
                print(f"- {category}")
        else:
            # Notify if no categories are found
            print("No categories found.")

    elif choice == "3":
        # Option to view transactions
        categories = category_manager.get_categories_by_type()
        if not categories:
            # Notify if no categories exist
            print("No categories found. Please add at least one category first.")
            return
            
        accounts = account_manager.get_accounts()
        if not accounts:
            # Notify if no accounts exist
            print("No accounts found. Please set a balance fot at least one account.")
            return
        
        # User can search transactions by category or by account
        print("1. Search by account")
        print("2. Search by category")
        choice_sub = input("Enter your choice (1/2): ")

        if choice_sub not in ["1", "2"]:
            # Validate the choice
            print("Invalid choice. Please enter 1 or 2.")
            return

        try:
            # Get start and end dates for the transaction search
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            if choice_sub == "1":
                # View transactions by account
                accounts = account_manager.get_accounts()
                if not accounts:
                    print("No accounts found. Please set the balance of at least one account first.")
                    return

                print(f"Available accounts: {', '.join(set(accounts))}")
                account = input("Enter the transaction account (* for ALL): ").upper()
                if account not in accounts and account != "*":
                    print("Account not found. Please enter a valid account.")
                    return
                
                transactions = transaction_manager.get_transactions_by_account(account, start_date, end_date)
            
            elif choice_sub == "2":
                # View transactions by category (either INCOME or EXPENSE)
                print("1. View INCOME categories")
                print("2. View EXPENSE categories")
                category_type = input("Enter category type (INCOME/EXPENSE): ")
                
                if category_type not in ["INCOME", "EXPENSE"]:
                    print("Invalid category type. Please enter INCOME or EXPENSE.")

                # Get available categories based on the selected type
                categories = category_manager.get_categories_by_type(category_type)
                if not categories:
                    print(f"No available {category_type} categories.")
                    return

                print(f"Available {category_type} categories: {', '.join(set(categories))}")
                category = input("Enter the transaction category (* for ALL): ").upper()
                if category == "*":
                    # View all transactions for the category type
                    transactions = transaction_manager.get_transactions_by_category_type(category_type, start_date, end_date)
                elif category in categories:
                    # View transactions for the specific category
                    transactions = transaction_manager.get_transactions_by_category(category, start_date, end_date)
                else:
                    print("Category not found. Please enter a valid category.")
                    return
            
            # Display transactions found for the specified date range
            if transactions:
                formatted_start_date = start_date.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
                formatted_end_date = end_date.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'
                print(f"Transactions from {formatted_start_date} to {formatted_end_date}:")
                for txn in transactions:
                    txn_id, account, amount, remaining_balance, category, details, date = txn

                    # Format the transaction amount based on whether it's income or expense
                    category_type = category_manager.get_category_type(category)
                    if category_type == "INCOME":
                        amount_as_str = f"${amount}"
                    elif category_type == "EXPENSE":
                        amount_as_str = f"-${amount}"
                    
                    # Format the remaining balance
                    if remaining_balance >= 0:
                        remaining_balance_as_str = f"${remaining_balance}"
                    else:
                        remaining_balance_as_str = f"-${remaining_balance * -1}"

                    # Format the transaction date
                    date_object = datetime.fromisoformat(date)  # Assuming `date` is a string in ISO format like '2024-09-22T00:00:00'
                    formatted_date = date_object.strftime('%Y-%m-%d')  # Format to 'YYYY-MM-DD'                    

                    # Print transaction details
                    print(f"ID: {txn_id}, Account: {account} Amount: {amount_as_str}, Remaining Balance: {remaining_balance_as_str} Category: {category}, Details: {details}, Date: {formatted_date}")
            else:
                print("No transactions found for the specified date range.")
        except Exception as e:
            print(f"An error occurred in View Transaction menu: {e}")
            return None

    elif choice == "4":
        # Option to view budgets
        pass

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")