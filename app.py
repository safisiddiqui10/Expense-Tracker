from flask import Flask, render_template, session, redirect, url_for, request
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = 'spendly-dev-secret-key'


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register")
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))
        return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "October 2026",
    }

    expenses = [
        {"id": 1, "date": "2026-10-14", "description": "Groceries",       "category": "Food",          "amount": 18.40},
        {"id": 2, "date": "2026-10-13", "description": "Miscellaneous",    "category": "Other",         "amount": 8.75},
        {"id": 3, "date": "2026-10-11", "description": "Clothing",         "category": "Shopping",      "amount": 89.99},
        {"id": 4, "date": "2026-10-09", "description": "Cinema tickets",   "category": "Entertainment", "amount": 25.00},
        {"id": 5, "date": "2026-10-07", "description": "Pharmacy",         "category": "Health",        "amount": 45.00},
        {"id": 6, "date": "2026-10-05", "description": "Electricity bill", "category": "Bills",         "amount": 120.00},
        {"id": 7, "date": "2026-10-03", "description": "Monthly bus pass", "category": "Transport",     "amount": 35.00},
        {"id": 8, "date": "2026-10-01", "description": "Lunch at cafe",    "category": "Food",          "amount": 12.50},
    ]

    total = sum(e["amount"] for e in expenses)
    count = len(expenses)

    cat_totals = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]

    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "—"

    categories = [
        {"name": cat, "total": round(amt, 2), "pct": round(amt / total * 100) if total else 0}
        for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])
    ]

    stats = {"total": round(total, 2), "count": count, "top_category": top_category}

    return render_template("profile.html", user=user, expenses=expenses, stats=stats, categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
