import math
from datetime import datetime

from flask import Flask, render_template, session, redirect, url_for, request, abort, flash
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db
from database.queries import (
    get_user_by_id,
    get_filtered_transactions,
    get_distinct_categories,
    get_summary_stats,
    get_category_breakdown,
    insert_expense,
    get_expense_by_id,
    update_expense,
    delete_expense as db_delete_expense,
)

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

    user = get_user_by_id(session["user_id"])
    if user is None:
        abort(404)

    category = request.args.get("category", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            date_from = ""
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            date_to = ""

    filter_active = bool(category or date_from or date_to)

    expenses = get_filtered_transactions(
        session["user_id"],
        category or None,
        date_from or None,
        date_to or None,
    )

    stats = get_summary_stats(session["user_id"])
    categories = get_category_breakdown(session["user_id"])
    filter_categories = get_distinct_categories(session["user_id"])

    if category and category not in filter_categories:
        category = ""

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        stats=stats,
        categories=categories,
        filter_categories=filter_categories,
        filter_active=filter_active,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "POST":
        raw_amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        error = None
        amount = None

        try:
            amount = float(raw_amount)
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError
        except ValueError:
            error = "Amount must be a positive number."

        if not error and category not in VALID_CATEGORIES:
            error = "Please select a valid category."

        if not error:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                error = "Please enter a valid date (YYYY-MM-DD)."

        if error:
            return render_template(
                "add_expense.html",
                error=error,
                categories=VALID_CATEGORIES,
                form={"amount": raw_amount, "category": category,
                      "date": date_str, "description": description or ""},
            )

        insert_expense(session["user_id"], amount, category, date_str, description)
        return redirect(url_for("profile"))

    today = datetime.today().strftime("%Y-%m-%d")
    return render_template(
        "add_expense.html",
        categories=VALID_CATEGORIES,
        form={"amount": "", "category": "", "date": today, "description": ""},
        error=None,
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "POST":
        raw_amount  = request.form.get("amount", "").strip()
        category    = request.form.get("category", "").strip()
        date_str    = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip() or None

        error = None
        amount = None

        try:
            amount = float(raw_amount)
            if not math.isfinite(amount) or amount <= 0:
                raise ValueError
        except ValueError:
            error = "Amount must be a positive number."

        if not error and category not in VALID_CATEGORIES:
            error = "Please select a valid category."

        if not error:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                error = "Please enter a valid date (YYYY-MM-DD)."

        if error:
            form = {"amount": raw_amount, "category": category,
                    "date": date_str, "description": description or ""}
            return render_template("edit_expense.html", form=form,
                                   categories=VALID_CATEGORIES, error=error,
                                   expense_id=id)

        update_expense(id, session["user_id"], amount, category, date_str, description)
        flash("Expense updated successfully.", "success")
        return redirect(url_for("profile"))

    form = {
        "amount":      expense["amount"],
        "category":    expense["category"],
        "date":        expense["date"],
        "description": expense["description"] or "",
    }
    return render_template("edit_expense.html", form=form,
                           categories=VALID_CATEGORIES, error=None,
                           expense_id=id)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))
    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)
    db_delete_expense(id, session["user_id"])
    return redirect(url_for("profile"))


with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
