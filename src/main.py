from datetime import datetime

from database import Database
from income import IncomeManager
from transaction import TransactionManager
from budget import BudgetManager
from category import CategoryManager
from visualization import Visualizer

def clear_data(db):
    with db.conn:
        db.conn.execute("DELETE FROM income")
        db.conn.execute("DELETE FROM categories")
        db.conn.execute("DELETE FROM budgets")
        db.conn.execute("DELETE FROM transactions")

def main():
    db = Database()
    db.create_tables()
    
    category_manager = CategoryManager(db)
    income_manager = IncomeManager(db)
    budget_manager = BudgetManager(db)
    transaction_manager = TransactionManager(db)
    visualizer = Visualizer(db)

    import menus.add_menu
    import menus.view_menu
    import menus.edit_menu
    import menus.visualization_menu
    
    while True:
        print("\nMain Menu:")
        print("1. Add")
        print("2. View")
        print("3. Edit")
        print("4. Visualize")
        print("5. Exit")
        choice = input("Enter your choice (1/2/3/4/5): ").upper()

        if choice == "1":
            menus.add_menu.menu(income_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "2":
            menus.view_menu.menu(income_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "3":
            menus.edit_menu.menu(income_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "4":
            menus.visualization_menu.menu(income_manager, category_manager, budget_manager, transaction_manager, visualizer)

        elif choice == "5":
            print("Exiting...")
            break

        elif choice == "CLEAR":
            print("WARNING: THIS WILL DELETE ALL DATA FROM BUDGET.")
            choice = input("Continue? ").upper()
            if choice == "CONTINUE":
                clear_data(db)

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()