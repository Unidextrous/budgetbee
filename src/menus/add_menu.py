from datetime import datetime

def menu(balance_manager, category_manager, transaction_manager, budget_manager):
    print("Add/Set:")
    print("1. Set balance")
    print("2. Add category")
    print("3. Add transaction")
    print("4. Add budget")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        pass
    
    elif choice == "2":
        category_manager.add_category(input("Enter the category name: ").upper())

    elif choice == "3":
        try:
            categories = category_manager.get_categories()
            if not categories:
                print("No categories found. Please set a budget for at least one category first.")
                return

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the transaction category: ").upper()
            if category not in categories:
                print("Category not in tracker. Please enter a valid category.")
                return

            account = input("Enter the account of the transaction: ")
            amount = float(input("Enter the transaction amount: "))
            details = input("Enter transaction details: ").upper()
            date_str = input("Enter the transaction date (YYYY-MM-DD): ")
            date = datetime.strptime(date_str, "%Y-%m-%d")
            transaction_manager.add_transaction(amount, category, details, date)
            print("Transaction added.")
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
                print("Category not in tracker. Please enter a valid category.")
                return

            budget_limit = float(input("Enter the budget limit: "))
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            budget_manager.add_budget(category, budget_limit, start_date)
            print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")