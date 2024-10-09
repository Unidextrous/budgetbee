from datetime import datetime

# Import required modules and classes for database, account, category, transaction, budget, and visualization management
from database import Database
from account import AccountManager
from category import CategoryManager
from transaction import TransactionManager
from budget import BudgetManager
from visualization import Visualizer

# Import menus for different functionalities (add, view, edit, visualize)
import menus.add_menu
import menus.view_menu
import menus.edit_menu
import menus.visualization_menu

# Function to clear all data from the database (WARNING: Deletes all records)
def clear_data(db):
    with db.conn:
        db.conn.execute("DELETE FROM accounts")
        db.conn.execute("DELETE FROM categories")
        db.conn.execute("DELETE FROM transactions")
        db.conn.execute("DELETE FROM budgets")
        
# Main function: Entry point for the program
def main():
    try:
        db = Database() # Create a Database instance and connect to the database
        db.create_tables()  # Ensure all necessary tables are created
    except Exception as e:
        # Handle database connection errors
        print(f"Error connecting to the database: {e}")
        return
    
    # Initialize managers for accounts, categories, budgets, and transactions
    account_manager = AccountManager(db)
    category_manager = CategoryManager(db)
    budget_manager = BudgetManager(db)
    transaction_manager = TransactionManager(db, account_manager, category_manager, budget_manager)
    visualizer = Visualizer(db, budget_manager, transaction_manager)
    
    # Main loop to display the main menu and handle user choices
    while True:
        print("\nMain Menu:")
        print("1. Add")
        print("2. View")
        print("3. Edit")
        print("4. Visualize")
        print("5. Exit")
        choice = input("Enter your choice (1/2/3/4/5): ").upper()

        if choice == "1":
            # Call the Add/Set menu
            menus.add_menu.menu(account_manager, category_manager, transaction_manager, budget_manager)

        elif choice == "2":
            # Call the View menu
            menus.view_menu.menu(account_manager, category_manager, transaction_manager, budget_manager)

        elif choice == "3":
            # Call the Edit menu
            menus.edit_menu.menu(account_manager, category_manager, transaction_manager, budget_manager)

        elif choice == "4":
            # Call the Visualization menu
            menus.visualization_menu.menu(category_manager, transaction_manager, budget_manager, visualizer)

        elif choice == "5":
            # Exit the program
            print("Exiting...")
            break

        elif choice == "CLEAR":
            # Warning before clearing all data in the database
            choice = input("WARNING: THIS WILL DELETE ALL DATA. Type 'CONFIRM' to proceed: ").upper()
            if choice == "CONFIRM":
                clear_data(db)

        else:
            # Handle invalid input
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()