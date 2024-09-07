from datetime import datetime

from database import Database
from balance import BalanceManager
from category import CategoryManager
from transaction import TransactionManager
from budget import BudgetManager
from visualization import Visualizer

def clear_data(db):
    with db.conn:
        db.conn.execute("DELETE FROM categories")
        db.conn.execute("DELETE FROM budgets")
        db.conn.execute("DELETE FROM transactions")

def main():
    db = Database()
    db.create_tables()
    
    balance_manager = BalanceManager(db)
    category_manager = CategoryManager(db)
    budget_manager = BudgetManager(db)
    transaction_manager = TransactionManager(db)
    visualizer = Visualizer(db, budget_manager, transaction_manager)

    import menus.add_menu
    import menus.view_menu
    import menus.edit_menu
    import menus.visualization_menu
    
    while True:
        print("\nMain Menu:")
        print("1. Add/Set")
        print("2. View")
        print("3. Edit")
        print("4. Visualize")
        print("5. Exit")
        choice = input("Enter your choice (1/2/3/4/5): ").upper()

        if choice == "1":
            menus.add_menu.menu(balance_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "2":
            menus.view_menu.menu(balance_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "3":
            menus.edit_menu.menu(balance_manager, category_manager, budget_manager, transaction_manager)

        elif choice == "4":
            menus.visualization_menu.menu(category_manager, budget_manager, transaction_manager, visualizer)

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