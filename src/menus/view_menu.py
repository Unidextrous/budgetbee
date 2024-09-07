from datetime import datetime

def menu(balance_manager, category_manager, transaction_manager, budget_manager):
    print("View:")
    print("1. View balances")
    print("2. View categories")
    print("3. View transactions")
    print("4. View budgets")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        pass

    elif choice == "2":
        categories = category_manager.get_categories()
        if categories:
            print("Categories:")
            for category in categories:
                print(f"- {category}")
        else:
            print("No categories found.")

    elif choice == "3":
        try:
            categories = category_manager.get_categories()
            if not categories:
                print("No categories found. Please add at least one category first.")
                return
            
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the transaction category (* for ALL): ").upper()
            if category not in categories and category != "*":
                print("Category not in tracker. Please enter a valid category.")
                return
            
            transactions = transaction_manager.get_transactions_by_category(category, start_date, end_date)
            total_spending = 0.0
            if transactions:
                print(f"Transactions from {start_date} to {end_date}:")
                for txn in transactions:
                    txn_id, amount, category, details, date = txn
                    print(f"ID: {txn_id}, Amount: {amount}, Category: {category} Details: {details}, Date: {date}")
                    total_spending += amount
            else:
                print("No transactions found for the specified date range.")
            print(f"Total spent over date range: {round(total_spending, 2)}")
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

            budgets_in_range, previous_budgets = budget_manager.get_budgets_by_date(category, start_date, end_date)
            if budgets_in_range or previous_budgets:
                print("Budgets:")
            total_budget_limit = 0.0
            if budgets_in_range:
                for budget in budgets_in_range:
                    id, category, limit, date = budget
                    print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Date: {date}")
                    total_budget_limit += limit
            if previous_budgets:
                most_recent_budget = previous_budgets[0]
                id, category, limit, date = most_recent_budget
                print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Start Date: {date}")
                total_budget_limit += limit
            else:
                print("No budgets found for the specified range.")
            print(f"Total budget limit for date range: {round(total_budget_limit, 2)}")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")