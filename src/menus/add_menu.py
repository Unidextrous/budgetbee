from datetime import datetime

def menu(balance_manager, category_manager, transaction_manager, budget_manager):
    print("Add/Set Menu:")
    print("1. Set balance")
    print("2. Add category")
    print("3. Add transaction")
    print("4. Set budget")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        try:
            account = input("Enter the account name: ").upper()
            accounts = balance_manager.get_accounts()
            if account in accounts:
                print("Account already exists. Please edit account or enter different account.")
                return
            
            balance = float(input("Enter the starting balance: $"))
            date_set_str = input("Enter the start date (YYYY-MM-DD): ")
            date_set = datetime.strptime(date_set_str, "%Y-%m-%d")
            balance_manager.set_balance(account, balance, date_set)
            print(f"Balance of ${balance} set for {account} account on {date_set_str}.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")
    
    elif choice == "2":
        category_manager.add_category(input("Enter the category name: ").upper())

    elif choice == "3":
        try:
            categories = category_manager.get_categories()
            if not categories:
                print("No categories found. Please set a budget for at least one category first.")
                return

            accounts = balance_manager.get_accounts()
            if not accounts:
                print("No accounts found. Please set the balance of at least one account first.")
                return

            print(f"Available accounts: {', '.join(set(accounts))}")
            account = input("Enter the account of the transaction: ").upper()
            if account not in accounts:
                print("Account not found. Please enter a valid account.")
                return

            amount = float(input("Enter the transaction amount ('-' for credit): $"))

            balance = balance_manager.get_balance(account)

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the transaction category: ").upper()
            if category not in categories:
                print("Category not found. Please enter a valid category.")
                return
            
            details = input("Enter transaction details: ").upper()
            date_str = input("Enter the transaction date (YYYY-MM-DD): ")
            date = datetime.strptime(date_str, "%Y-%m-%d")

            balance = balance_manager.get_balance(account)
            new_balance = balance - amount

            balance_manager.update_balance(account, new_balance)
            transaction_manager.add_transaction(account, amount, new_balance, category, details, date)
            print(f"Transaction of ${amount} added. New {account} balance: ${new_balance}")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")

    elif choice == "4":
        try:
            categories = category_manager.get_categories()
            if not categories:
                print("No categories found. Please set a budget for at least one category first.")
                return

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the category name: ").upper()
            if category not in categories:
                print("Category not found. Please enter a valid category.")
                return

            budget_limit = float(input("Enter the budget limit: $"))
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            budget_manager.set_budget(category, budget_limit, start_date)
            print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")