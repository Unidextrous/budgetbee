from datetime import datetime

def menu(income_manager, category_manager, budget_manager, transaction_manager, visualizer):
        print("Visualization Menu:")
        print("1. Bar Graph: Spending vs Budget")
        print("2. Line Graph: Cumulative Spending vs Budget Over Time")
        print("3. Pie Chart: ")
        choice = input("Enter your choice (1/2/3): ")

        try:
            if choice == "1":
                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                visualizer.visualize_bar(budget_manager, start_date, end_date)

            elif choice == "2":
                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                categories = category_manager.get_categories()
                if not categories:
                    print("No categories found. Please add at least one category first.")
                    return
                print(f"Available categories: {', '.join(set(categories))}")
                category = input("Enter the category (* for ALL): ").upper()
                
                visualizer.visualize_line(category, start_date, end_date)

            elif choice == "3":
                start_date_str = input("Enter the start date (YYYY-MM-DD): ")
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date_str = input("Enter the end date (YYYY-MM-DD): ")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                visualizer.visualize_pie(start_date, end_date)
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")