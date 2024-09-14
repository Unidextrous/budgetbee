from datetime import datetime

def menu(balance_manager, category_manager, transaction_manager, budget_manager):
    print("View Menu:")
    print("1. View balances")
    print("2. View categories")
    print("3. View transactions")
    print("4. View budgets")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        accounts = balance_manager.get_accounts()
        if not accounts:
            print("No accounts found. Please set the balance of at least one account first.")
            return
        total_balance = 0.0
        for account in accounts:
            balance = balance_manager.get_balance(account)
            total_balance += balance
            print(f"- {account}: ${balance}")
        print(f"- TOTAL BALANCE: ${total_balance}")
        
            
    elif choice == "2":
        categories = category_manager.get_categories()
        if categories:
            print("Categories:")
            for category in categories:
                print(f"- {category}")
        else:
            print("No categories found.")

    elif choice == "3":
        categories = category_manager.get_categories()
        if not categories:
            print("No categories found. Please add at least one category first.")
            return
            
        accounts = balance_manager.get_accounts()
        if not accounts:
            print("No accounts found. Please set a balance fot at least one account.")
            return
            
        print("1. Search by category")
        print("2. Search by account")
        choice_sub = input("Enter your choice (1/2): ")

        if choice_sub not in ["1", "2"]:
            print("Invalid choice. Please enter 1 or 2.")
            return

        try:
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                
            if choice_sub == "1":
                print("1. View INCOME categories")
                print("2. View EXPENSE categories")
                choice_sub_sub = input("Enter your choice (1/2): ")
                
                if choice_sub_sub not in ["1", "2"]:
                    print("Invalid choice. Please enter 1 or 2.")
                    return
                if choice_sub_sub == "1":
                    category_type = "INCOME"
                elif choice_sub_sub == "2":
                    category_type = "EXPENSE"
                categories = category_manager.get_categories(category_type)
                if not categories:
                    print(f"No available {category_type} categories.")
                    return

                print(f"Available {category_type} categories: {', '.join(set(categories))}")
                category = input("Enter the transaction category (* for ALL): ").upper()
                if category == "*":
                    transactions = transaction_manager.get_transactions_by_category_type(category_type, start_date, end_date)
                elif category in categories:
                    # Get transactions of the specific category
                    transactions = transaction_manager.get_transactions_by_category(category, start_date, end_date)
                else:
                    print("Category not found. Please enter a valid category.")
                    return
            
            elif choice_sub == "2":
                accounts = balance_manager.get_accounts()
                if not accounts:
                    print("No accounts found. Please set the balance of at least one account first.")
                    return

                print(f"Available accounts: {', '.join(set(accounts))}")
                account = input("Enter the transaction account (* for ALL): ").upper()
                if account not in accounts and account != "*":
                    print("Account not found. Please enter a valid account.")
                    return
                
                transactions = transaction_manager.get_transactions_by_account(account, start_date, end_date)
            
            if transactions:
                print(f"Transactions from {start_date} to {end_date}:")
                for txn in transactions:
                    txn_id, account, amount, remaining_balance, category, details, date = txn
                    print(f"ID: {txn_id}, Account: {account} Amount: {amount}, Remaining Balance: {remaining_balance} Category: {category}, Details: {details}, Date: {date}")
            else:
                print("No transactions found for the specified date range.")
        except ValueError:
            print("Invalid date format. Please enter dates in YYYY-MM-DD format.")

    elif choice == "4":
        try:
            categories = category_manager.get_categories()
            if not categories:
                print("No categories found. Please add at least one category first.")
                return
            
            start_date_str = input("Enter the start date for budgets (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date for budgets (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the transaction category (* for ALL): ").upper()
            if category not in categories and category != "*":
                print("Category not in tracker. Please enter a valid category.")
                return

            budgets_in_range, previous_budgets = budget_manager.get_budgets_by_category(category, start_date, end_date)
            if budgets_in_range or previous_budgets:
                print("Budgets:")
            if budgets_in_range:
                for budget in budgets_in_range:
                    id, category, limit, date = budget
                    print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Date: {date}")
            if previous_budgets:
                most_recent_budget = previous_budgets[0]
                id, category, limit, date = most_recent_budget
                print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Start Date: {date}")
            if not budgets_in_range and not previous_budgets:
                print("No budgets found for the specified range.")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")