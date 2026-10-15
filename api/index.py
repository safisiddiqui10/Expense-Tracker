import math
import os
from datetime import datetime

import psycopg2.extras

from flask import Flask, jsonify, session, request
from werkzeug.security import check_password_hash, generate_password_hash

from api.database.db import get_db, init_db, seed_db
from api.database.queries import (
    get_user_by_id,
    get_filtered_transactions,
    get_distinct_categories,
    get_summary_stats,
    get_category_breakdown,
    insert_expense,
    get_expense_by_id,
    update_expense,
    delete_expense,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "Budgetly-dev-secret-key")

if os.environ.get("VERCEL"):
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def require_auth():
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401
    return None


# ------------------------------------------------------------------ #
# Auth endpoints                                                       #
# ------------------------------------------------------------------ #

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user_row = cursor.fetchone()
    cursor.close()
    db.close()

    if not user_row or not check_password_hash(user_row["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user_row["id"]
    user = get_user_by_id(user_row["id"])
    return jsonify(user), 200


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "Name is required."}), 400
    if not email:
        return jsonify({"error": "Email is required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        db.close()
        return jsonify({"error": "An account with that email already exists."}), 400

    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
        (name, email, generate_password_hash(password)),
    )
    new_id = cursor.fetchone()["id"]
    db.commit()
    cursor.close()
    db.close()

    session["user_id"] = new_id
    user = get_user_by_id(new_id)
    return jsonify(user), 201


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True}), 200


@app.route("/api/auth/me", methods=["GET"])
def api_me():
    guard = require_auth()
    if guard:
        return guard
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return jsonify({"error": "User not found"}), 401
    return jsonify(user), 200


# ------------------------------------------------------------------ #
# Profile / dashboard                                                  #
# ------------------------------------------------------------------ #

@app.route("/api/profile", methods=["GET"])
def api_profile():
    guard = require_auth()
    if guard:
        return guard

    user = get_user_by_id(session["user_id"])
    if user is None:
        return jsonify({"error": "User not found"}), 404

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

    return jsonify({
        "user": user,
        "expenses": expenses,
        "stats": stats,
        "categories": categories,
        "filter_categories": filter_categories,
        "filter_active": filter_active,
        "category": category,
        "date_from": date_from,
        "date_to": date_to,
    }), 200


# ------------------------------------------------------------------ #
# Expenses CRUD                                                        #
# ------------------------------------------------------------------ #

def _validate_expense(data):
    raw_amount = str(data.get("amount") or "").strip()
    category = (data.get("category") or "").strip()
    date_str = (data.get("date") or "").strip()
    description = (data.get("description") or "").strip() or None

    try:
        amount = float(raw_amount)
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError
    except ValueError:
        return None, None, None, None, "Amount must be a positive number."

    if category not in VALID_CATEGORIES:
        return None, None, None, None, "Please select a valid category."

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None, None, None, None, "Please enter a valid date (YYYY-MM-DD)."

    return amount, category, date_str, description, None


@app.route("/api/expenses", methods=["POST"])
def api_add_expense():
    guard = require_auth()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    amount, category, date_str, description, error = _validate_expense(data)
    if error:
        return jsonify({"error": error}), 400

    insert_expense(session["user_id"], amount, category, date_str, description)
    return jsonify({"ok": True}), 201


@app.route("/api/expenses/<int:expense_id>", methods=["GET"])
def api_get_expense(expense_id):
    guard = require_auth()
    if guard:
        return guard

    expense = get_expense_by_id(expense_id, session["user_id"])
    if expense is None:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify(expense), 200


@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def api_update_expense(expense_id):
    guard = require_auth()
    if guard:
        return guard

    existing = get_expense_by_id(expense_id, session["user_id"])
    if existing is None:
        return jsonify({"error": "Expense not found"}), 404

    data = request.get_json(silent=True) or {}
    amount, category, date_str, description, error = _validate_expense(data)
    if error:
        return jsonify({"error": error}), 400

    update_expense(expense_id, session["user_id"], amount, category, date_str, description)
    return jsonify({"ok": True, "message": "Expense updated successfully."}), 200


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def api_delete_expense(expense_id):
    guard = require_auth()
    if guard:
        return guard

    existing = get_expense_by_id(expense_id, session["user_id"])
    if existing is None:
        return jsonify({"error": "Expense not found"}), 404

    delete_expense(expense_id, session["user_id"])
    return jsonify({"ok": True}), 200


# ------------------------------------------------------------------ #
# Startup                                                              #
# ------------------------------------------------------------------ #

with app.app_context():
    init_db()
    seed_db()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
