import sqlite3
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


# 1. Database Initialization
def init_db():
  conn = sqlite3.connect("web_finance.db")
  cursor = conn.cursor()
  # Transactions Table
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            amount REAL,
            category TEXT,
            date TEXT,
            description TEXT
        )
    """)
  # Settings Table (Budget Limit ke liye)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value REAL
        )
    """)
  conn.commit()
  conn.close()


init_db()


# 2. Main Dashboard Route
@app.route("/")
def index():
  conn = sqlite3.connect("web_finance.db")
  cursor = conn.cursor()

  # All records history fetch karna
  cursor.execute(
      "SELECT id, date, type, amount, category, description FROM transactions"
      " ORDER BY date DESC, id DESC"
  )
  transactions = cursor.fetchall()

  # Total Income calculate karna
  cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
  total_inc = cursor.fetchone()[0] or 0.0

  # Total Expense calculate karna
  cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
  total_exp = cursor.fetchone()[0] or 0.0

  # Net Savings
  net_savings = total_inc - total_exp

  # Monthly Budget Limit Check
  cursor.execute(
      "SELECT value FROM settings WHERE key='monthly_budget'"
  )
  b_res = cursor.fetchone()
  budget_limit = b_res[0] if b_res else 0.0

  budget_alert = False
  if budget_limit > 0 and total_exp > budget_limit:
    budget_alert = True

  conn.close()

  return render_template(
      "index.html",
      transactions=transactions,
      income=total_inc,
      expense=total_exp,
      savings=net_savings,
      budget=budget_limit,
      budget_alert=budget_alert,
  )


# 3. Add Income / Expense Route
@app.route("/add", methods=["POST"])
def add_transaction():
  t_type = request.form["type"]
  amount = float(request.form["amount"])
  category = request.form["category"]
  date = request.form["date"]
  description = request.form["description"]

  conn = sqlite3.connect("web_finance.db")
  cursor = conn.cursor()

  # Low balance protection check
  if t_type == "Expense":
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    inc = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    exp = cursor.fetchone()[0] or 0.0
    current_balance = inc - exp

    if current_balance < amount:
      conn.close()
      return (
          f"<h3>Error: Insufficient Balance! (Current Balance: ₹{current_balance})</h3><a"
          " href='/'>Wapas Jayein</a>"
      )

  cursor.execute(
      "INSERT INTO transactions (type, amount, category, date, description)"
      " VALUES (?, ?, ?, ?, ?)",
      (t_type, amount, category, date, description),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


# 4. Set Budget Route
@app.route("/set_budget", methods=["POST"])
def set_budget():
  budget_val = float(request.form["budget"])
  conn = sqlite3.connect("web_finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_budget',"
      " ?)",
      (budget_val,),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


# 5. Delete Transaction Route
@app.route("/delete/<int:trans_id>")
def delete_transaction(trans_id):
  conn = sqlite3.connect("web_finance.db")
  cursor = conn.cursor()
  cursor.execute("DELETE FROM transactions WHERE id=?", (trans_id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


if __name__ == "__main__":
  app.run(host='0.0.0.0',port=5000,debug=True)