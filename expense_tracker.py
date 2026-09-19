import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================
# DATABASE CONNECTION
# ==========================================

conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL
)
""")

conn.commit()


# ==========================================
# ADD EXPENSE
# ==========================================

def add_expense():
    print("\n--- Add New Expense ---")

    date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()

    if date == "":
        date = datetime.today().strftime("%Y-%m-%d")

    # Validate date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date. Please use YYYY-MM-DD.")
        return

    category = input("Enter category (Food/Travel/Shopping/etc.): ").strip()

    description = input("Enter description: ").strip()

    try:
        amount = float(input("Enter amount: ₹"))
    except ValueError:
        print("Invalid amount.")
        return

    if amount <= 0:
        print("Amount must be greater than 0.")
        return

    cursor.execute("""
        INSERT INTO expenses (date, category, description, amount)
        VALUES (?, ?, ?, ?)
    """, (date, category, description, amount))

    conn.commit()

    print("Expense added successfully!")


# ==========================================
# VIEW ALL EXPENSES
# ==========================================

def view_expenses():

    cursor.execute("""
        SELECT id, date, category, description, amount
        FROM expenses
        ORDER BY date DESC, id DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        print("\nNo expenses found.")
        return

    print("\n---------------- ALL EXPENSES ----------------")
    print("{:<5} {:<12} {:<15} {:<25} {:>10}".format(
        "ID", "Date", "Category", "Description", "Amount"
    ))

    print("-" * 72)

    for row in rows:
        print("{:<5} {:<12} {:<15} {:<25} ₹{:>9.2f}".format(
            row[0],
            row[1],
            row[2],
            row[3][:25],
            row[4]
        ))


# ==========================================
# DELETE EXPENSE
# ==========================================

def delete_expense():

    view_expenses()

    try:
        expense_id = int(input("\nEnter expense ID to delete: "))
    except ValueError:
        print("Invalid ID.")
        return

    cursor.execute(
        "SELECT * FROM expenses WHERE id = ?",
        (expense_id,)
    )

    expense = cursor.fetchone()

    if expense is None:
        print("Expense not found.")
        return

    cursor.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()

    print("Expense deleted successfully!")


# ==========================================
# TOTAL EXPENSE
# ==========================================

def total_expense():

    cursor.execute("SELECT SUM(amount) FROM expenses")

    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    print("\nTotal money spent: ₹{:.2f}".format(total))


# ==========================================
# CATEGORY ANALYSIS
# ==========================================

def category_analysis():

    query = """
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("\nNo expense data available.")
        return

    print("\n--- Spending by Category ---")

    print(df.to_string(index=False))

    print("\nHighest spending category:")
    print(
        "{} - ₹{:.2f}".format(
            df.iloc[0]["category"],
            df.iloc[0]["total"]
        )
    )


# ==========================================
# MONTHLY ANALYSIS
# ==========================================

def monthly_analysis():

    query = """
        SELECT
            substr(date, 1, 7) AS month,
            SUM(amount) AS total
        FROM expenses
        GROUP BY month
        ORDER BY month
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("\nNo expense data available.")
        return

    print("\n--- Monthly Spending ---")

    print(df.to_string(index=False))


# ==========================================
# PIE CHART
# ==========================================

def category_chart():

    query = """
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("No data available for chart.")
        return

    plt.figure(figsize=(8, 6))

    plt.pie(
        df["total"],
        labels=df["category"],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Expense Distribution by Category")

    plt.tight_layout()

    plt.show()


# ==========================================
# MONTHLY BAR CHART
# ==========================================

def monthly_chart():

    query = """
        SELECT
            substr(date, 1, 7) AS month,
            SUM(amount) AS total
        FROM expenses
        GROUP BY month
        ORDER BY month
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        print("No data available for chart.")
        return

    plt.figure(figsize=(9, 5))

    plt.bar(
        df["month"],
        df["total"]
    )

    plt.xlabel("Month")
    plt.ylabel("Amount Spent")
    plt.title("Monthly Expense Analysis")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.show()


# ==========================================
# SEARCH BY CATEGORY
# ==========================================

def search_category():

    category = input("\nEnter category to search: ").strip()

    cursor.execute("""
        SELECT id, date, category, description, amount
        FROM expenses
        WHERE LOWER(category) = LOWER(?)
        ORDER BY date DESC
    """, (category,))

    rows = cursor.fetchall()

    if not rows:
        print("No expenses found for this category.")
        return

    print("\n--- {} Expenses ---".format(category))

    total = 0

    for row in rows:

        print(
            "ID: {} | {} | {} | ₹{:.2f}".format(
                row[0],
                row[1],
                row[3],
                row[4]
            )
        )

        total += row[4]

    print("\nTotal {} spending: ₹{:.2f}".format(category, total))


# ==========================================
# MAIN MENU
# ==========================================

def main():

    while True:

        print("\n====================================")
        print("       PERSONAL EXPENSE TRACKER")
        print("====================================")

        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Delete Expense")
        print("4. View Total Spending")
        print("5. Category Analysis")
        print("6. Monthly Analysis")
        print("7. Category Pie Chart")
        print("8. Monthly Bar Chart")
        print("9. Search Expense by Category")
        print("10. Exit")

        choice = input("\nEnter your choice (1-10): ").strip()

        if choice == "1":
            add_expense()

        elif choice == "2":
            view_expenses()

        elif choice == "3":
            delete_expense()

        elif choice == "4":
            total_expense()

        elif choice == "5":
            category_analysis()

        elif choice == "6":
            monthly_analysis()

        elif choice == "7":
            category_chart()

        elif choice == "8":
            monthly_chart()

        elif choice == "9":
            search_category()

        elif choice == "10":
            print("\nThank you for using Expense Tracker!")
            break

        else:
            print("Invalid choice. Please enter 1-10.")


# ==========================================
# START PROGRAM
# ==========================================

if __name__ == "__main__":

    try:
        main()

    finally:
        conn.close()