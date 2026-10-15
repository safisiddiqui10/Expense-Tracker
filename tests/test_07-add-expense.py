"""
Tests for Step 07 — Add Expense feature.

Spec source: .claude/specs/07-add-expense.md

Coverage:
- Unit: insert_expense() DB helper (valid args, description=None)
- Auth guards: GET and POST /expenses/add while unauthenticated
- GET /expenses/add authenticated: 200, form with POST, all 7 category options
- POST /expenses/add authenticated: happy path redirect and DB verification
- POST /expenses/add authenticated: empty description stored as NULL
- POST /expenses/add validation errors: each returns 200 with error message
- Parametrized: invalid amounts, invalid categories, invalid date strings
"""

import pytest
from database.queries import insert_expense
from database.db import get_db


# ============================================================== #
# Unit tests — insert_expense() in database/queries.py           #
# ============================================================== #

class TestInsertExpenseHelper:

    def test_insert_expense_valid_args_row_is_retrievable(self, app):
        """Valid args → row inserted and queryable from the DB."""
        with app.app_context():
            insert_expense(
                user_id=1,
                amount=50.0,
                category="Food",
                date="2026-03-20",
                description="Spec07 unit test lunch unique",
            )
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
                (1, "Spec07 unit test lunch unique"),
            ).fetchone()
            conn.close()

        assert row is not None, "insert_expense must create a row in the expenses table"
        assert float(row["amount"]) == 50.0, "Stored amount must equal 50.0"
        assert row["category"] == "Food", "Stored category must equal Food"
        assert row["date"] == "2026-03-20", "Stored date must equal 2026-03-20"

    def test_insert_expense_none_description_stores_null(self, app):
        """description=None → column stored as NULL in the DB."""
        with app.app_context():
            insert_expense(
                user_id=1,
                amount=15.0,
                category="Bills",
                date="2026-03-22",
                description=None,
            )
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses "
                "WHERE user_id = ? AND category = ? AND date = ? "
                "AND amount = ? AND description IS NULL",
                (1, "Bills", "2026-03-22", 15.0),
            ).fetchone()
            conn.close()

        assert row is not None, (
            "insert_expense with description=None must insert a row with a NULL description"
        )
        assert row["description"] is None, (
            "description column must be NULL, not an empty string or other value"
        )


# ============================================================== #
# Auth guards — unauthenticated access                           #
# ============================================================== #

class TestAddExpenseAuthGuard:

    def test_get_unauthenticated_returns_302(self, client):
        resp = client.get("/expenses/add")
        assert resp.status_code == 302, (
            "GET /expenses/add while logged out must return 302"
        )

    def test_get_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/expenses/add")
        location = resp.headers.get("Location", "")
        assert "/login" in location, (
            "GET /expenses/add while logged out must redirect to /login"
        )

    def test_post_unauthenticated_returns_302(self, client):
        resp = client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Auth guard test",
        })
        assert resp.status_code == 302, (
            "POST /expenses/add while logged out must return 302"
        )

    def test_post_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Auth guard test",
        })
        location = resp.headers.get("Location", "")
        assert "/login" in location, (
            "POST /expenses/add while logged out must redirect to /login"
        )


# ============================================================== #
# GET /expenses/add — authenticated                              #
# ============================================================== #

class TestAddExpenseGetAuthenticated:

    def test_returns_200(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert resp.status_code == 200, (
            "Authenticated GET /expenses/add must return 200"
        )

    def test_response_contains_form_element(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"<form" in resp.data, (
            "Response must contain a <form element"
        )

    def test_form_method_is_post(self, auth_client):
        resp = auth_client.get("/expenses/add")
        body = resp.data.upper()
        assert b"POST" in body, (
            "The form method attribute must be POST"
        )

    def test_category_option_food(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Food" in resp.data, "Category option 'Food' must appear in the response"

    def test_category_option_transport(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Transport" in resp.data, "Category option 'Transport' must appear in the response"

    def test_category_option_bills(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Bills" in resp.data, "Category option 'Bills' must appear in the response"

    def test_category_option_health(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Health" in resp.data, "Category option 'Health' must appear in the response"

    def test_category_option_entertainment(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Entertainment" in resp.data, (
            "Category option 'Entertainment' must appear in the response"
        )

    def test_category_option_shopping(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Shopping" in resp.data, "Category option 'Shopping' must appear in the response"

    def test_category_option_other(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Other" in resp.data, "Category option 'Other' must appear in the response"

    def test_contains_amount_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"amount" in resp.data, "Form must contain an amount input field"

    def test_contains_date_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"date" in resp.data, "Form must contain a date input field"

    def test_contains_description_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"description" in resp.data, "Form must contain a description input field"


# ============================================================== #
# POST /expenses/add — happy path                                #
# ============================================================== #

class TestAddExpensePostHappyPath:

    def test_valid_post_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Spec07 happy path A",
        })
        assert resp.status_code == 302, (
            "Valid POST /expenses/add must return 302"
        )

    def test_valid_post_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "75.0",
            "category": "Transport",
            "date": "2026-04-05",
            "description": "Spec07 happy path B redirect check",
        })
        location = resp.headers.get("Location", "")
        assert "/profile" in location, (
            "Valid POST /expenses/add must redirect to /profile"
        )

    def test_valid_post_row_exists_in_db(self, auth_client, app):
        resp = auth_client.post("/expenses/add", data={
            "amount": "88.0",
            "category": "Shopping",
            "date": "2026-05-15",
            "description": "Spec07 DB verify unique string",
        })
        assert resp.status_code == 302, "Expected 302 after valid POST before checking DB"

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
                (1, "Spec07 DB verify unique string"),
            ).fetchone()
            conn.close()

        assert row is not None, "A new expense row must be inserted after a valid POST"
        assert float(row["amount"]) == 88.0, "Stored amount must match submitted value"
        assert row["category"] == "Shopping", "Stored category must match submitted value"
        assert row["date"] == "2026-05-15", "Stored date must match submitted value"


# ============================================================== #
# POST /expenses/add — no description (optional field)           #
# ============================================================== #

class TestAddExpensePostNoDescription:

    def test_empty_description_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "30.0",
            "category": "Other",
            "date": "2026-06-10",
            "description": "",
        })
        assert resp.status_code == 302, (
            "Empty description is optional — POST must still return 302"
        )

    def test_empty_description_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "42.0",
            "category": "Bills",
            "date": "2026-06-11",
            "description": "",
        })
        location = resp.headers.get("Location", "")
        assert "/profile" in location, (
            "POST with empty description must redirect to /profile"
        )

    def test_empty_description_stored_as_null_in_db(self, auth_client, app):
        resp = auth_client.post("/expenses/add", data={
            "amount": "60.0",
            "category": "Entertainment",
            "date": "2026-07-04",
            "description": "",
        })
        assert resp.status_code == 302, (
            "Expected 302 after valid POST with empty description"
        )

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses "
                "WHERE user_id = ? AND category = ? AND date = ? AND amount = ?",
                (1, "Entertainment", "2026-07-04", 60.0),
            ).fetchone()
            conn.close()

        assert row is not None, "Row must be inserted even when description is an empty string"
        assert row["description"] is None, (
            "description must be stored as NULL when blank string is submitted"
        )


# ============================================================== #
# POST /expenses/add — validation errors                         #
# ============================================================== #

class TestAddExpenseValidationErrors:

    def test_missing_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "Missing amount test",
        })
        assert resp.status_code == 200, (
            "Missing amount must re-render the form (200), not redirect"
        )

    def test_missing_amount_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "Missing amount test",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "required", "amount", "positive"))
        assert has_error, (
            "Response must contain an error keyword when amount is missing"
        )

    def test_amount_zero_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount test",
        })
        assert resp.status_code == 200, (
            "amount=0 is not positive — form must be re-rendered (200)"
        )

    def test_amount_zero_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount test",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "positive", "greater", "amount"))
        assert has_error, (
            "Response must contain an error keyword when amount is 0"
        )

    def test_non_numeric_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount test",
        })
        assert resp.status_code == 200, (
            "Non-numeric amount must re-render the form (200)"
        )

    def test_non_numeric_amount_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount test",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "numeric", "number", "amount"))
        assert has_error, (
            "Response must contain an error keyword when amount is non-numeric"
        )

    def test_invalid_category_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "NotACategory",
            "date": "2026-03-20",
            "description": "Invalid category test",
        })
        assert resp.status_code == 200, (
            "Invalid category must re-render the form (200)"
        )

    def test_invalid_category_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "NotACategory",
            "date": "2026-03-20",
            "description": "Invalid category test",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "category"))
        assert has_error, (
            "Response must contain an error keyword when category is not in the fixed list"
        )

    def test_invalid_date_string_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Invalid date test",
        })
        assert resp.status_code == 200, (
            "Invalid date string must re-render the form (200)"
        )

    def test_invalid_date_string_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Invalid date test",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "date"))
        assert has_error, (
            "Response must contain an error keyword when date is not a valid YYYY-MM-DD string"
        )


# ============================================================== #
# Parametrized — invalid amount values                           #
# ============================================================== #

@pytest.mark.parametrize("bad_amount", [
    "",        # empty string — missing value
    "0",       # exactly zero — not positive
    "0.00",    # zero as float string
    "-5",      # negative integer
    "-0.01",   # negative fraction
    "abc",     # non-numeric string
    "1e999",   # overflow → Inf, not a finite positive float
    "   ",     # whitespace only
])
def test_invalid_amount_rerenders_form(auth_client, bad_amount):
    resp = auth_client.post("/expenses/add", data={
        "amount": bad_amount,
        "category": "Food",
        "date": "2026-03-20",
        "description": "Parametrized bad amount",
    })
    assert resp.status_code == 200, (
        f"amount={bad_amount!r} is not a valid positive number — "
        "form must be re-rendered (200)"
    )


# ============================================================== #
# Parametrized — invalid category values                         #
# ============================================================== #

@pytest.mark.parametrize("bad_category", [
    "",                            # empty string
    "food",                        # lowercase — match is case-sensitive
    "FOOD",                        # uppercase
    "Groceries",                   # plausible but not in the fixed list
    "InvalidXYZ",                  # arbitrary string
    "'; DROP TABLE expenses; --",  # SQL injection — parameterized queries must handle safely
])
def test_invalid_category_rerenders_form(auth_client, bad_category):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0",
        "category": bad_category,
        "date": "2026-03-20",
        "description": "Parametrized bad category",
    })
    assert resp.status_code == 200, (
        f"category={bad_category!r} is not in the fixed list — "
        "form must be re-rendered (200)"
    )


# ============================================================== #
# Parametrized — invalid date strings                            #
# ============================================================== #

@pytest.mark.parametrize("bad_date", [
    "",              # empty string
    "not-a-date",   # free-form text
    "2026-13-01",   # month 13 — impossible
    "2026-00-01",   # month 0 — impossible
    "2026-01-00",   # day 0 — impossible
    "20260320",     # missing dashes — YYYYMMDD format
    "01/01/2026",   # US slash-separated format
    "2026/03/20",   # slash-separated instead of dash
])
def test_invalid_date_rerenders_form(auth_client, bad_date):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0",
        "category": "Food",
        "date": bad_date,
        "description": "Parametrized bad date",
    })
    assert resp.status_code == 200, (
        f"date={bad_date!r} is not a valid YYYY-MM-DD date — "
        "form must be re-rendered (200)"
    )
