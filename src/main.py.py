from datetime import datetime

from database import Database
from transaction import TransactionManager
from budget import BudgetManager
from category import CategoryManager
from visualization import Visualizer

def clear_data(db):
    with db.conn:
        db.conn.execute("DELETE FROM transactions")
        db.conn.execute("DELETE FROM budgets")

def main():
    db = Database()
    db.create_tables()
    
    category_manager = CategoryManager(db)
    transaction_manager = TransactionManager(db)
    budget_manager = BudgetManager(db)
    visualizer = Visualizer(db)
    
    while True:
        print("\nOptions:")
        print("1. Set a budget")
        print("2. Add a transaction")
        print("3. Visualize by Category")
        print("4. Visualize Over Time")
        print("5. Delete a transaction")
        print("6. Exit")
        choice = input("Enter your choice (1/2/3/4/5/6): ")

        if choice == "1":
            try:
                category = input("Enter the category name: ").upper()
                budget_limit = float(input("Enter the budget limit: "))
                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                budget_manager.set_budget(category, budget_limit, start_date)
                print(f"Budget set for category {category} with limit {budget_limit} as of {start_date_str}.")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")

        elif choice == "2":    
            try:
                categories = category_manager.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                    continue

                print(f"Available categories: {', '.join(set(categories))}")
                category = input("Enter the transaction category: ").upper()
                if category not in categories:
                    print("Category not in tracker. Please enter a valid category.")
                    continue

                amount = float(input("Enter the transaction amount: "))
                details = input("Enter transaction details: ").upper()
                date_str = input("Enter the transaction date (YYYY-MM-DD): ")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                transaction_manager.add_transaction(amount, category, details, date)
                print("Transaction added.")
            except ValueError:
                print("Invalid input. Please enter the correct data format.")
        
        elif choice == "3":
            try:
                start_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                visualizer.visualize_bar(budget_manager, start_date, end_date)
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "4":
            try:
                categories = category_manager.get_categories()
                if not categories:
                    print("No categories found. Please set a budget for at least one category first.")
                
                print(f"Available categories: {', '.join(set(categories))} (* for TOTAL)")
                category = input("Enter the category for visualization: ").upper()

                start_date_str = input("Enter the start date for visualization (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date for visualization (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                visualizer.visualize_line(category, start_date, end_date)
            except ValueError:
                print("Invalid date format. Please enter dates in YYYY-MM-DD format.")
        
        elif choice == "5":
            try:
                txn_id = int(input("Enter the transaction ID to delete: "))
                transaction_manager.remove_transaction(txn_id)
                print(f"Transaction with ID {txn_id} deleted.")
            except ValueError:
                print("Invalid input. Please enter a valid transaction ID.")

        elif choice == "6":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")
    
    if db.db_name == "test.db":
        clear_data(db)

if __name__ == "__main__":
    main()