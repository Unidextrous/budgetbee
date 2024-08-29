from datetime import datetime

def menu(income_manager, category_manager, budget_manager, transaction_manager):
    print("Edit:")
    print("1. Income")
    print("2. Category")
    print("3. Budget")
    print("4. Transaction")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == "1":
        try:
            income_id = int(input("Enter the ID of the income source to edit: "))
        except ValueError:
            print("Invalid ID. Please enter a number.")

        income = income_manager.get_income_by_id(income_id)

        if income == None:
            print(f"No income with ID {income_id}. Please enter a valid ID.")
            return
        
        id, amount, source, date = income
        print(f"ID: {id}, Amount: {amount}, Source: {source}, Date: {date}")
        print("1. Update amount")
        print("2. Update source")
        print("3. Update date")
        print("4. Delete income source")
        choice_sub = input("Enter your choice (1/2/3/4): ")

        if choice_sub == "1":
            try:
                new_amount = float(input("Enter the new income amount: "))
                income_manager.update_income_amount(income_id, new_amount)
                print(f"Income amount updated to {new_amount}.")
            except ValueError:
                print("Invalid amount. Please enter a valid number.")
        
        elif choice_sub == "2":
            new_source = input("Enter the new income source: ").upper()
            income_manager.update_income_source(income_id, new_source)
            print(f"Income source updated to {new_source}.")
        
        elif choice_sub == "3":
            try:
                new_date_str = input("Enter the new date (YYYY-MM-DD): ")
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d")
                income_manager.update_income_date(income_id, new_date)
                print(f"Income date updated to {new_date}.")
            except ValueError:
                print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

        elif choice_sub == "4":
            delete = input("Are you sure you wish to delete this income source? Y/N: ").upper()
            if delete == "Y":
                income_manager.remove_income_source(income_id)
                print(f"Income source with ID {income_id} deleted.")
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    elif choice == "2":
        categories = category_manager.get_categories()
        if not categories:
            print("No categories available to rename.")
            return

        print(f"Available categories: {', '.join(categories)}")
        category = input("Enter the category to edit: ").upper()
        if category not in categories:
            print("Category not found.")
            return
        
        print("1. Rename category")
        print("2. Delete category")
        choice_sub = input("Enter your choice (1/2): ")

        if choice_sub == "1":
            new_name = input("Enter the new name for the category: ").upper()
            if new_name in categories:
                print("New category name already exists.")
                return

            category_manager.rename_category(category, new_name)
            print(f"Category renamed from {category} to {new_name}.")

        elif choice_sub == "2":
            delete = input("Are you sure you wish to delete this category? Y/N: ").upper()
            if delete == "Y":
                category_manager.delete_category(category)
                print(f"Category {category} deleted.")

        else:
            print("Invalid choice. Please enter 1 or 2.")

    elif choice == "3":
        try:
            budget_id = int(input("Enter the ID of the budget to edit: "))
        except ValueError:
            print("Invalid ID. Please enter a number.")

        budget = budget_manager.get_budget_by_id(budget_id)

        if budget == None:
            print(f"No budget with ID {budget_id}. Please enter a valid ID.")
            return
        
        id, category, limit, date = budget
        print(f"ID: {id}, Category: {category}, Limit: {limit}, Date: {date}")
        print("1. Update budget limit")
        print("2. Update budget category")
        print("3. Update budget date")
        print("4. Delete budget")
        choice_sub = input("Enter your choice (1/2/3/4): ")

        if choice_sub == "1":
            try:
                new_limit = float(input("Enter the new budget limit: "))
                budget_manager.update_budget_limit(budget_id, new_limit)
                print(f"Budget limit updated to {new_limit}.")
            except ValueError:
                print("Invalid amount. Please enter a valid number.")

        elif choice_sub == "2":
            new_category = input("Enter new category: ").upper()
            categories = category_manager.get_categories()
            print(categories)
            if new_category in categories:
                budget_manager.update_category(budget_id, new_category)
                print(f"Category updated to {new_category}.")
            else:
                print("Category does not exist. Please enter a valid category.")

        elif choice_sub == "3":
            try:
                new_date_str = input("Enter the new date (YYYY-MM-DD): ")
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d")
                budget_manager.update_budget_date(budget_id, new_date)
                print(f"Budget date updated to {new_date}.")
            except ValueError:
                print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

        elif choice_sub == "4":
            delete = input("Are you sure you wish to delete this budget? Y/N: ").upper()
            if delete == "Y":
                budget_manager.remove_budget(budget_id)
                print(f"Budget with ID {budget_id} deleted.")

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    elif choice == "4":
        try:
            transaction_id = int(input("Enter the ID of the transaction to edit: "))
        except ValueError:
            print("Invalid ID. Please enter a number.")

        transaction = transaction_manager.get_transaction_by_id(transaction_id)

        if transaction == None:
            print(f"No transaction with ID {transaction_id}. Please enter a valid ID.")
            return
        
        txn_id, amount, category, details, date = transaction
        print(f"ID: {txn_id}, Amount: {amount}, Category: {category}, Details: {details}, Date: {date}")
        print("1. Update transaction amount")
        print("2. Update transaction category")
        print("3. Update transaction details")
        print("4. Update transaction date")
        print("5. Delete transaction")
        choice_sub = input("Enter your choice (1/2/3): ")

        if choice_sub == "1":
            try:
                new_amount = float(input("Enter the new transaction amount: "))
                transaction_manager.update_transaction_amount(transaction_id, new_amount)
                print(f"Transaction amount updated to {new_amount}.")
            except ValueError:
                print("Invalid amount. Please enter a valid number.")

        elif choice_sub == "2":
            new_category = input("Enter new category: ").upper()
            categories = category_manager.get_categories()
            if new_category in categories:
                transaction_manager.update_category(transaction_id, new_category)
                print(f"Category updated to {new_category}.")
            else:
                print("Category does not exist. Please enter a valid category.")
        
        elif choice_sub == "3":
            new_details = input("Enter the new transaction details: ")
            transaction_manager.update_transaction_details(transaction_id, new_details)
            print(f"Transaction details updated to {new_details}.")

        elif choice_sub == "4":
            try:
                new_date_str = input("Enter the new date (YYYY-MM-DD): ")
                new_date = datetime.strptime(new_date_str, "%Y-%m-%d")
                transaction_manager.update_transaction_date(transaction_id, new_date)
                print(f"Transaction date updated to {new_date}.")
            except ValueError:
                print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

        elif choice_sub == "5":
            delete = input("Are you sure you wish to delete this transaction? Y/N: ").upper()
            if delete == "Y":
                transaction_manager.remove_transaction(transaction_id)
                print(f"Transaction with ID {transaction_id} deleted.")

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")