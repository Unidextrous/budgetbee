from datetime import datetime

def menu(income_manager, category_manager, budget_manager, transaction_manager):
    print("View:")
    print("1. View income sources")
    print("2. View categories")
    print("3. View budgets")
    print("4. View transactions")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        try:
            start_date_str = input("Enter the start date (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            income = income_manager.get_income_by_date(start_date, end_date)
            if income:
                print(f"Income from {start_date} to {end_date}:")
                for paycheck in income:
                    paycheck_id, amount, source, date = paycheck
                    print(f"ID: {paycheck_id}, Amount: {amount}, Source: {source}, Date: {date}")
            else:
                print("No income found for the specified date range.")
        except ValueError:
            print("Invalid date format. Please enter dates in YYYY-MM-DD format.")

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
            
            start_date_str = input("Enter the start date for budgets (YYYY-MM-DD): ")
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date_str = input("Enter the end date for budgets (YYYY-MM-DD): ")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            print(f"Available categories: {', '.join(set(categories))}")
            category = input("Enter the transaction category (* for ALL): ").upper()
            if category not in categories:
                if category == "*":
                    pass
                else:
                    print("Category not in tracker. Please enter a valid category.")
                    return

            budgets_in_range, previous_budgets = budget_manager.get_budgets_by_date(category, start_date, end_date)
            if budgets_in_range or previous_budgets:
                print("Budgets:")
            if budgets_in_range:
                for budget in budgets_in_range:
                    id, category, limit, date = budget
                    print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Date: {date}")
            elif previous_budgets:
                most_recent_budget = previous_budgets[0]
                id, category, limit, date = most_recent_budget
                print(f"ID: {id}, Category: {category}, Budget Limit: {limit}, Start Date: {date}")
            else:
                print("No budgets found for the specified range.")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")


    elif choice == "4":
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

            transactions = transaction_manager.get_transactions_by_date(category, start_date, end_date)
            if transactions:
                print(f"Transactions from {start_date} to {end_date}:")
                for txn in transactions:
                    txn_id, amount, category, details, date = txn
                    print(f"ID: {txn_id}, Amount: {amount}, Category: {category} Details: {details}, Date: {date}")
            else:
                print("No transactions found for the specified date range.")
        except ValueError:
            print("Invalid date format. Please enter dates in YYYY-MM-DD format.")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")