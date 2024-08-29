from datetime import datetime

def menu(income_manager, category_manager, budget_manager, transaction_manager):
    print("Add:")
    print("1. Add income")
    print("2. Add category")
    print("3. Add budget")
    print("4. Add transaction")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        try:
            category = "INCOME"
            amount = float(input("Enter the amount of income: "))
            source = input("Enter income source: ").upper()
            date_received_str = input("Enter the date that the income was received (YYYY-MM-DD): ")
            date_received = datetime.strptime(date_received_str, "%Y-%m-%d")
            income_manager.add_income_source(amount, source, date_received)
            print(f"Income of {amount} received on {date_received} from {source}.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")

    if choice == "2":
        category_manager.add_category(input("Enter the category name: ").upper())

    elif choice == "3":
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
            budget_manager.set_budget(category, budget_limit, start_date)
            print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")
    
    elif choice == "4":
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

            amount = float(input("Enter the transaction amount: "))
            details = input("Enter transaction details: ").upper()
            date_str = input("Enter the transaction date (YYYY-MM-DD): ")
            date = datetime.strptime(date_str, "%Y-%m-%d")
            transaction_manager.add_transaction(amount, category, details, date)
            print("Transaction added.")
        except ValueError:
            print("Invalid input. Please enter the correct data format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")