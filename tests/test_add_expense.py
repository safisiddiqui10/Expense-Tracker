"""
Tests for Step 07 — Add Expense Feature.

Covers:
- Unit tests: insert_expense DB helper (valid args, description=None)
- GET /expenses/add unauthenticated and authenticated
- POST /expenses/add unauthenticated, valid data, validation errors, no description
- Parametrized: invalid amounts, invalid categories, invalid date strings
"""

import pytest
from database.queries import insert_expense
from database.db import get_db


# ====================================================================== #
# Unit tests — insert_expense()                                           #
# ====================================================================== #

class TestInsertExpense:

    def test_insert_expense_valid_args_inserts_row(self, app):
        """insert_expense with valid args creates a row queryable from the DB."""
        with app.app_context():
            insert_expense(
                user_id=1,
                amount=50.0,
                category="Food",
                date="2026-03-20",
                description="Lunch unit test unique",
            )
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
                (1, "Lunch unit test unique"),
            ).fetchone()
            conn.close()

        assert row is not None, "insert_expense should have created a row in the expenses table"
        assert row["amount"] == 50.0, "Row amount should be 50.0"
        assert row["category"] == "Food", "Row category should be Food"
        assert row["date"] == "2026-03-20", "Row date should be 2026-03-20"
        assert row["description"] == "Lunch unit test unique"

    def test_insert_expense_none_description_stores_null(self, app):
        """insert_expense with description=None stores NULL in the expenses table."""
        with app.app_context():
            insert_expense(
                user_id=1,
                amount=25.0,
                category="Transport",
                date="2026-03-21",
                description=None,
            )
            conn = get_db()
            # Query by all other fields since description is NULL
            row = conn.execute(
                "SELECT * FROM expenses "
                "WHERE user_id = ? AND category = ? AND date = ? AND amount = ? "
                "AND description IS NULL",
                (1, "Transport", "2026-03-21", 25.0),
            ).fetchone()
            conn.close()

        assert row is not None, (
            "insert_expense with description=None should create a row in the expenses table"
        )
        assert row["description"] is None, (
            "description must be stored as NULL when None is passed to insert_expense"
        )


# ====================================================================== #
# Route tests — GET /expenses/add — unauthenticated                       #
# ====================================================================== #

class TestAddExpenseGetUnauthenticated:

    def test_get_unauthenticated_returns_302(self, client):
        resp = client.get("/expenses/add")
        assert resp.status_code == 302, (
            "Unauthenticated GET /expenses/add should redirect (302)"
        )

    def test_get_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/expenses/add")
        assert "/login" in resp.headers["Location"], (
            "Unauthenticated GET /expenses/add must redirect to /login"
        )


# ====================================================================== #
# Route tests — GET /expenses/add — authenticated                         #
# ====================================================================== #

class TestAddExpenseGetAuthenticated:

    def test_get_authenticated_returns_200(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert resp.status_code == 200, (
            "Authenticated GET /expenses/add should return 200"
        )

    def test_get_authenticated_contains_form_element(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"<form" in resp.data, "Response must contain a <form element"

    def test_get_authenticated_form_uses_post_method(self, auth_client):
        resp = auth_client.get("/expenses/add")
        # Method attribute must be POST (HTML is case-insensitive, check both)
        assert b"POST" in resp.data or b"post" in resp.data, (
            "Form must use method POST"
        )

    def test_get_authenticated_contains_food_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Food" in resp.data, "Category option 'Food' must be present"

    def test_get_authenticated_contains_transport_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Transport" in resp.data, "Category option 'Transport' must be present"

    def test_get_authenticated_contains_bills_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Bills" in resp.data, "Category option 'Bills' must be present"

    def test_get_authenticated_contains_health_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Health" in resp.data, "Category option 'Health' must be present"

    def test_get_authenticated_contains_entertainment_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Entertainment" in resp.data, "Category option 'Entertainment' must be present"

    def test_get_authenticated_contains_shopping_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Shopping" in resp.data, "Category option 'Shopping' must be present"

    def test_get_authenticated_contains_other_category(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"Other" in resp.data, "Category option 'Other' must be present"

    def test_get_authenticated_contains_amount_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"amount" in resp.data, "Form must contain an amount input field"

    def test_get_authenticated_contains_date_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"date" in resp.data, "Form must contain a date input field"

    def test_get_authenticated_contains_description_field(self, auth_client):
        resp = auth_client.get("/expenses/add")
        assert b"description" in resp.data, "Form must contain a description input field"


# ====================================================================== #
# Route tests — POST /expenses/add — unauthenticated                      #
# ====================================================================== #

class TestAddExpensePostUnauthenticated:

    def test_post_unauthenticated_returns_302(self, client):
        resp = client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        })
        assert resp.status_code == 302, (
            "Unauthenticated POST /expenses/add should redirect (302)"
        )

    def test_post_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch",
        })
        assert "/login" in resp.headers["Location"], (
            "Unauthenticated POST /expenses/add must redirect to /login"
        )


# ====================================================================== #
# Route tests — POST /expenses/add — authenticated, valid data            #
# ====================================================================== #

class TestAddExpensePostValid:

    def test_post_valid_data_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Lunch valid route test A",
        })
        assert resp.status_code == 302, (
            "Valid POST /expenses/add should redirect (302)"
        )

    def test_post_valid_data_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "77.5",
            "category": "Health",
            "date": "2026-04-01",
            "description": "Doctor visit valid route test B",
        })
        assert "/profile" in resp.headers["Location"], (
            "Valid POST /expenses/add must redirect to /profile"
        )

    def test_post_valid_data_row_inserted_in_db(self, auth_client, app):
        resp = auth_client.post("/expenses/add", data={
            "amount": "99.0",
            "category": "Shopping",
            "date": "2026-05-10",
            "description": "DB verify route test unique string",
        })
        assert resp.status_code == 302, "Expected redirect after valid POST"

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
                (1, "DB verify route test unique string"),
            ).fetchone()
            conn.close()

        assert row is not None, "A new expense row must exist in the DB after valid POST"
        assert float(row["amount"]) == 99.0, "Stored amount must match submitted value"
        assert row["category"] == "Shopping", "Stored category must match submitted value"
        assert row["date"] == "2026-05-10", "Stored date must match submitted value"


# ====================================================================== #
# Route tests — POST /expenses/add — validation errors                    #
# ====================================================================== #

class TestAddExpenseValidationErrors:

    def test_post_missing_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "No amount field",
        })
        assert resp.status_code == 200, (
            "Missing amount should re-render the form (200), not redirect"
        )

    def test_post_missing_amount_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "No amount field",
        })
        data = resp.data.decode("utf-8").lower()
        has_error = any(
            word in data
            for word in ("error", "invalid", "required", "amount", "positive")
        )
        assert has_error, (
            "Response body must contain an error message when amount is missing"
        )

    def test_post_amount_zero_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount",
        })
        assert resp.status_code == 200, (
            "amount=0 should re-render the form (200) — zero is not a valid positive amount"
        )

    def test_post_amount_zero_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount",
        })
        data = resp.data.decode("utf-8").lower()
        has_error = any(
            word in data
            for word in ("error", "invalid", "positive", "greater", "amount")
        )
        assert has_error, (
            "Response body must contain an error message when amount is 0"
        )

    def test_post_non_numeric_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount",
        })
        assert resp.status_code == 200, (
            "Non-numeric amount should re-render the form (200)"
        )

    def test_post_non_numeric_amount_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount",
        })
        data = resp.data.decode("utf-8").lower()
        has_error = any(
            word in data
            for word in ("error", "invalid", "numeric", "number", "amount")
        )
        assert has_error, (
            "Response body must contain an error message when amount is non-numeric"
        )

    def test_post_invalid_category_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "InvalidCategory",
            "date": "2026-03-20",
            "description": "Bad category",
        })
        assert resp.status_code == 200, (
            "Invalid category should re-render the form (200)"
        )

    def test_post_invalid_category_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "InvalidCategory",
            "date": "2026-03-20",
            "description": "Bad category",
        })
        data = resp.data.decode("utf-8").lower()
        has_error = any(
            word in data
            for word in ("error", "invalid", "category")
        )
        assert has_error, (
            "Response body must contain an error message when category is not in the fixed list"
        )

    def test_post_invalid_date_string_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Bad date",
        })
        assert resp.status_code == 200, (
            "Invalid date string should re-render the form (200)"
        )

    def test_post_invalid_date_string_has_error_message(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Bad date",
        })
        data = resp.data.decode("utf-8").lower()
        has_error = any(
            word in data
            for word in ("error", "invalid", "date")
        )
        assert has_error, (
            "Response body must contain an error message when date is not a valid YYYY-MM-DD string"
        )


# ====================================================================== #
# Route tests — POST /expenses/add — no description (optional field)      #
# ====================================================================== #

class TestAddExpenseNoDescription:

    def test_post_no_description_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "30.0",
            "category": "Other",
            "date": "2026-06-15",
            "description": "",
        })
        assert resp.status_code == 302, (
            "Empty description is optional — POST should still redirect (302)"
        )

    def test_post_no_description_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/add", data={
            "amount": "40.0",
            "category": "Bills",
            "date": "2026-06-16",
            "description": "",
        })
        assert "/profile" in resp.headers["Location"], (
            "Successful POST with no description must redirect to /profile"
        )

    def test_post_no_description_row_has_null_description(self, auth_client, app):
        resp = auth_client.post("/expenses/add", data={
            "amount": "55.0",
            "category": "Entertainment",
            "date": "2026-07-01",
            "description": "",
        })
        assert resp.status_code == 302, (
            "Expected redirect (302) for valid POST with empty description"
        )

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM expenses "
                "WHERE user_id = ? AND category = ? AND date = ? AND amount = ?",
                (1, "Entertainment", "2026-07-01", 55.0),
            ).fetchone()
            conn.close()

        assert row is not None, "Row must be inserted even when description is an empty string"
        assert row["description"] is None, (
            "description must be stored as NULL when a blank string is submitted"
        )


# ====================================================================== #
# Parametrized — invalid amount values all re-render the form             #
# ====================================================================== #

@pytest.mark.parametrize("bad_amount", [
    "",        # empty / missing value
    "0",       # zero — not positive
    "0.00",    # zero as float string
    "-10",     # negative
    "-0.01",   # negative fraction
    "abc",     # non-numeric string
    "1e999",   # overflow / Inf — not representable as positive finite float
    " ",       # whitespace only
])
def test_invalid_amount_rerenders_form(auth_client, bad_amount):
    resp = auth_client.post("/expenses/add", data={
        "amount": bad_amount,
        "category": "Food",
        "date": "2026-03-20",
        "description": "Parametrized amount test",
    })
    assert resp.status_code == 200, (
        f"amount={bad_amount!r} is invalid — form must be re-rendered (200), not redirected"
    )


# ====================================================================== #
# Parametrized — invalid category values all re-render the form           #
# ====================================================================== #

@pytest.mark.parametrize("bad_category", [
    "",                              # empty
    "food",                          # lowercase — category match is case-sensitive
    "FOOD",                          # uppercase
    "Groceries",                     # valid-looking but not in the fixed list
    "InvalidXYZ",                    # arbitrary string
    "'; DROP TABLE expenses; --",    # SQL injection attempt — parameterized queries handle safely
])
def test_invalid_category_rerenders_form(auth_client, bad_category):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0",
        "category": bad_category,
        "date": "2026-03-20",
        "description": "Parametrized category test",
    })
    assert resp.status_code == 200, (
        f"category={bad_category!r} is not in the fixed list — form must be re-rendered (200)"
    )


# ====================================================================== #
# Parametrized — invalid date strings all re-render the form              #
# ====================================================================== #

@pytest.mark.parametrize("bad_date", [
    "",              # empty
    "not-a-date",    # free text
    "2026-13-01",    # month 13 — impossible
    "2026-00-01",    # month 0 — impossible
    "2026-01-00",    # day 0 — impossible
    "20261301",      # missing dashes
    "01/01/2026",    # wrong separator format
    "2026/03/20",    # slashes instead of dashes
])
def test_invalid_date_rerenders_form(auth_client, bad_date):
    resp = auth_client.post("/expenses/add", data={
        "amount": "50.0",
        "category": "Food",
        "date": bad_date,
        "description": "Parametrized date test",
    })
    assert resp.status_code == 200, (
        f"date={bad_date!r} is not a valid YYYY-MM-DD date — form must be re-rendered (200)"
    )
