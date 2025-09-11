# BudgetBee — MVP Design Doc 🐝💛

## 1. Goal / Purpose
BudgetBee is a lightweight budgeting app for Dex and Tonya.  
The goal of this MVP is to provide a simple, shared way to track income, expenses, and category budgets together, without the complexity of a full public-facing app.

---

## 2. Core Features (Must-Haves)
- **Add Transactions**  
  - Input: amount, category, date, description, who logged it.  
  - Stored locally in a single database.  

- **View Transactions**  
  - List view of recent expenses and income.  
  - Filter by category or date.  

- **Shared Totals**  
  - Show current balance (income – expenses).  
  - Show per-category totals.  

- **Monthly Budgets**  
  - Each category has a set monthly budget goal.  
  - Show progress vs. budget (e.g. $150 of $300 spent on Groceries).  

---

## 3. Out of Scope (Not-Yet Features)
- User accounts / logins.  
- Multi-device sync / cloud hosting.  
- Automatic bank imports.  
- Recurring transactions.  
- Fancy charts/graphs.  
- Public release & distribution.  

---

## 4. Tech Stack & Approach
- **Language/Framework:** Python with Kivy (desktop/mobile app).
- **Database:** SQLite (lightweight, easy to set up).  
- **Frontend:** Minimal HTML/CSS if Flask; simple UI widgets if Kivy.  
- **Data Location:** Local database file stored on Dex’s machine (backed up manually if needed).  

---

## 5. User Flow
1. **Open App** → Homepage shows current balance + budget summary.  
2. **Add Transaction** → Fill out form (amount, category, date, description, who).  
3. **See Update** → Totals & progress bars update immediately.  
4. **Browse Transactions** → Scroll through past entries, filter if needed.  
5. **End of Month** → Review spending by category vs. goals.  

---

## 6. Success Criteria
- Dex and Tonya can log all income/expenses quickly without confusion.  
- At a glance, they can see how much is left in each budget category.  
- The app runs reliably on Dex’s machine without internet dependency.  

---

## 7. Future Ideas
- Add charts/visualizations.  
- Export to CSV/Google Sheets.  
- Sync across devices.  
- Make it available for public use.

This way, you’ve got a clear boundary: you’re only building what’s in section 2 right now, and everything in section 3 is officially “not your problem yet.” 🐝

Would you like me to also draft the README.md so it pairs nicely with this, or do you want to keep that minimal until you’ve got the MVP working?