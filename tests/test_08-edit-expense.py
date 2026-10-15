"""
Tests for Step 08 — Edit Expense feature.

Spec source: .claude/specs/08-edit-expense.md

Coverage:
- Unit: get_expense_by_id() — valid id+user, wrong user, non-existent id
- Unit: update_expense() — valid update verifies DB, wrong user_id leaves row unchanged
- Auth guards: GET and POST /expenses/<id>/edit while unauthenticated → 302 to /login
- GET /expenses/1/edit authenticated: 200, <form, "save changes", pre-filled amount
- GET /expenses/9999/edit authenticated: 404
- POST /expenses/1/edit authenticated: happy path → 302 to /profile, DB row updated
- POST ownership guard: second user cannot GET or POST user 1's expense → 404
- POST validation errors: invalid amount, category, date → 200 + error keyword in body
- Parametrized: invalid amounts, invalid categories, invalid date strings
- Empty description → 302 to /profile, DB description column=NULL
"""

import pytest
from database.queries import get_expense_by_id, update_expense
from database.db import get_db


# ============================================================== #
# Unit tests — get_expense_by_id() in database/queries.py        #
# ============================================================== #

class TestGetExpenseById:

    def test_valid_expense_id_correct_user_returns_dict_with_correct_id(self, app):
        """Valid expense_id + correct user_id → returns dict with id field matching."""
        with app.app_context():
            result = get_expense_by_id(1, 1)
        assert result is not None, (
            "get_expense_by_id must return a dict for a valid expense belonging to user 1"
        )
        assert result["id"] == 1, "Returned dict must have id == 1"

    def test_valid_expense_id_wrong_user_id_returns_none(self, app):
        """Valid expense_id + wrong user_id (999) → None (ownership enforced)."""
        with app.app_context():
            result = get_expense_by_id(1, 999)
        assert result is None, (
            "get_expense_by_id must return None when the expense does not belong to user_id"
        )

    def test_nonexistent_expense_id_returns_none(self, app):
        """Non-existent expense_id (9999) → None regardless of user_id."""
        with app.app_context():
            result = get_expense_by_id(9999, 1)
        assert result is None, (
            "get_expense_by_id must return None for an expense_id that does not exist"
        )


# ============================================================== #
# Unit tests — update_expense() in database/queries.py           #
# ============================================================== #

class TestUpdateExpense:

    def test_valid_call_updates_db_row(self, app):
        """Valid call → DB row reflects the new values (verified with raw get_db query)."""
        with app.app_context():
            update_expense(1, 1, 999.99, "Food", "2026-01-15", "Updated by step08 unit test")
            conn = get_db()
            row = conn.execute(
                "SELECT amount, category, date FROM expenses WHERE id = ? AND user_id = ?",
                (1, 1),
            ).fetchone()
            conn.close()

        assert row is not None, "Expense row must still exist after a valid update"
        assert float(row["amount"]) == 999.99, "Amount must be updated to 999.99 in the DB"
        assert row["category"] == "Food", "Category must reflect the updated value"
        assert row["date"] == "2026-01-15", "Date must reflect the updated value"

    def test_wrong_user_id_leaves_row_unchanged(self, app):
        """update_expense with wrong user_id → WHERE matches 0 rows; amount stays the same."""
        with app.app_context():
            # Capture current amount before the attempted wrong-user update
            conn = get_db()
            before_row = conn.execute(
                "SELECT amount FROM expenses WHERE id = ? AND user_id = ?",
                (1, 1),
            ).fetchone()
            conn.close()
            before_amount = float(before_row["amount"])

            # Attempt update with user_id=999 — should silently affect 0 rows
            update_expense(1, 999, 0.01, "Other", "2020-01-01", "Wrong user attempt")

            conn = get_db()
            after_row = conn.execute(
                "SELECT amount FROM expenses WHERE id = ? AND user_id = ?",
                (1, 1),
            ).fetchone()
            conn.close()

        assert float(after_row["amount"]) == before_amount, (
            "update_expense with wrong user_id must not modify the expense row in the DB"
        )


# ============================================================== #
# Auth guards — GET unauthenticated                              #
# ============================================================== #

class TestEditExpenseGetUnauthenticated:

    def test_returns_302(self, client):
        resp = client.get("/expenses/1/edit")
        assert resp.status_code == 302, (
            "GET /expenses/1/edit while logged out must return 302"
        )

    def test_redirects_to_login(self, client):
        resp = client.get("/expenses/1/edit")
        location = resp.headers.get("Location", "")
        assert "/login" in location, (
            "GET /expenses/1/edit while logged out must redirect to /login"
        )


# ============================================================== #
# GET /expenses/1/edit — authenticated                           #
# ============================================================== #

class TestEditExpenseGetAuthenticated:

    def test_returns_200(self, auth_client):
        resp = auth_client.get("/expenses/1/edit")
        assert resp.status_code == 200, (
            "Authenticated GET /expenses/1/edit must return 200"
        )

    def test_response_contains_form_element(self, auth_client):
        resp = auth_client.get("/expenses/1/edit")
        assert b"<form" in resp.data, (
            "Response must contain a <form element"
        )

    def test_response_contains_save_changes_text(self, auth_client):
        """The submit button or page heading must say 'save changes' (case-insensitive)."""
        resp = auth_client.get("/expenses/1/edit")
        body = resp.data.decode("utf-8").lower()
        assert "save changes" in body, (
            "Response must contain the text 'save changes' (case-insensitive)"
        )

    def test_prefilled_amount_present_in_body(self, auth_client, app):
        """Form must be pre-filled: the current amount for expense 1 appears in the response."""
        with app.app_context():
            expense = get_expense_by_id(1, 1)
        # Convert the stored float to string as Jinja2/Python would render it
        amount_str = str(expense["amount"])
        resp = auth_client.get("/expenses/1/edit")
        body = resp.data.decode("utf-8")
        assert amount_str in body, (
            f"Response must contain the pre-filled amount value '{amount_str}'"
        )

    def test_nonexistent_expense_returns_404(self, auth_client):
        resp = auth_client.get("/expenses/9999/edit")
        assert resp.status_code == 404, (
            "GET /expenses/9999/edit must return 404 for a non-existent expense"
        )


# ============================================================== #
# Auth guards — POST unauthenticated                             #
# ============================================================== #

class TestEditExpensePostUnauthenticated:

    def test_returns_302(self, client):
        resp = client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Unauthenticated post test",
        })
        assert resp.status_code == 302, (
            "POST /expenses/1/edit while logged out must return 302"
        )

    def test_redirects_to_login(self, client):
        resp = client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Unauthenticated redirect test",
        })
        location = resp.headers.get("Location", "")
        assert "/login" in location, (
            "POST /expenses/1/edit while logged out must redirect to /login"
        )


# ============================================================== #
# POST /expenses/1/edit — happy path                             #
# ============================================================== #

class TestEditExpensePostHappyPath:

    def test_valid_post_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "55.55",
            "category": "Transport",
            "date": "2026-05-20",
            "description": "Step08 happy path A",
        })
        assert resp.status_code == 302, (
            "Valid POST /expenses/1/edit must return 302"
        )

    def test_valid_post_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "66.66",
            "category": "Bills",
            "date": "2026-06-15",
            "description": "Step08 happy path B",
        })
        location = resp.headers.get("Location", "")
        assert "/profile" in location, (
            "Valid POST /expenses/1/edit must redirect to /profile"
        )

    def test_valid_post_updates_db_row(self, auth_client, app):
        """After a valid POST, the DB row for expense 1 reflects the submitted values."""
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "77.77",
            "category": "Health",
            "date": "2026-07-10",
            "description": "Step08 DB verify update",
        })
        assert resp.status_code == 302, "Expected 302 before verifying DB state"

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT amount, category, date, description "
                "FROM expenses WHERE id = ? AND user_id = ?",
                (1, 1),
            ).fetchone()
            conn.close()

        assert row is not None, "Expense row must still exist in the DB after update"
        assert float(row["amount"]) == 77.77, "DB amount must equal submitted value 77.77"
        assert row["category"] == "Health", "DB category must equal submitted value"
        assert row["date"] == "2026-07-10", "DB date must equal submitted value"


# ============================================================== #
# Ownership guard — second user cannot edit user 1's expense     #
# ============================================================== #

class TestEditExpenseOwnershipGuard:

    def test_get_other_users_expense_returns_404(self, app):
        """A different user (user 2) must receive 404 on GET /expenses/1/edit."""
        with app.app_context():
            conn = get_db()
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Guard User GET", "guard_get@step08test.com", "placeholder"),
            )
            conn.commit()
            user_row = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                ("guard_get@step08test.com",),
            ).fetchone()
            user2_id = user_row["id"]
            conn.close()

        user2_client = app.test_client()
        with user2_client.session_transaction() as sess:
            sess["user_id"] = user2_id

        resp = user2_client.get("/expenses/1/edit")
        assert resp.status_code == 404, (
            "A user who does not own the expense must receive 404 on GET"
        )

    def test_post_other_users_expense_returns_404(self, app):
        """A different user (user 2) must receive 404 on POST /expenses/1/edit."""
        with app.app_context():
            conn = get_db()
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Guard User POST", "guard_post@step08test.com", "placeholder"),
            )
            conn.commit()
            user_row = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                ("guard_post@step08test.com",),
            ).fetchone()
            user2_id = user_row["id"]
            conn.close()

        user2_client = app.test_client()
        with user2_client.session_transaction() as sess:
            sess["user_id"] = user2_id

        resp = user2_client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Ownership guard post attempt",
        })
        assert resp.status_code == 404, (
            "A user who does not own the expense must receive 404 on POST"
        )


# ============================================================== #
# POST /expenses/1/edit — validation errors                      #
# ============================================================== #

class TestEditExpenseValidationErrors:

    def test_missing_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "Missing amount test",
        })
        assert resp.status_code == 200, (
            "Missing amount must re-render the form (200), not redirect"
        )

    def test_missing_amount_body_contains_error_keyword(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "category": "Food",
            "date": "2026-03-20",
            "description": "Missing amount error keyword",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "required", "amount", "positive"))
        assert has_error, "Response must contain an error keyword when amount is missing"

    def test_amount_zero_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount test",
        })
        assert resp.status_code == 200, (
            "amount=0 is not positive — form must be re-rendered (200)"
        )

    def test_amount_zero_body_contains_error_keyword(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Zero amount error keyword",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "positive", "greater", "amount"))
        assert has_error, "Response must contain an error keyword when amount is 0"

    def test_nonnumeric_amount_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount test",
        })
        assert resp.status_code == 200, (
            "Non-numeric amount must re-render the form (200)"
        )

    def test_nonnumeric_amount_body_contains_error_keyword(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-03-20",
            "description": "Non-numeric amount error keyword",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "numeric", "number", "amount"))
        assert has_error, "Response must contain an error keyword when amount is non-numeric"

    def test_invalid_category_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "NotACategory",
            "date": "2026-03-20",
            "description": "Invalid category test",
        })
        assert resp.status_code == 200, (
            "Invalid category must re-render the form (200)"
        )

    def test_invalid_category_body_contains_error_keyword(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "NotACategory",
            "date": "2026-03-20",
            "description": "Invalid category error keyword",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "category"))
        assert has_error, "Response must contain an error keyword when category is not in the valid list"

    def test_invalid_date_returns_200(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Invalid date test",
        })
        assert resp.status_code == 200, (
            "Invalid date string must re-render the form (200)"
        )

    def test_invalid_date_body_contains_error_keyword(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "50.0",
            "category": "Food",
            "date": "not-a-date",
            "description": "Invalid date error keyword",
        })
        body = resp.data.decode("utf-8").lower()
        has_error = any(kw in body for kw in ("error", "invalid", "date"))
        assert has_error, "Response must contain an error keyword when date is not a valid YYYY-MM-DD"


# ============================================================== #
# Parametrized — invalid amount values                           #
# ============================================================== #

@pytest.mark.parametrize("bad_amount", [
    "",       # empty string — missing value
    "0",      # exactly zero — not positive
    "-5",     # negative integer
    "abc",    # non-numeric string
    "inf",    # infinity — not a finite positive float
])
def test_invalid_amount_rerenders_form(auth_client, bad_amount):
    resp = auth_client.post("/expenses/1/edit", data={
        "amount": bad_amount,
        "category": "Food",
        "date": "2026-03-20",
        "description": "Parametrized bad amount",
    })
    assert resp.status_code == 200, (
        f"amount={bad_amount!r} is invalid — form must be re-rendered (200), not redirect"
    )


# ============================================================== #
# Parametrized — invalid category values                         #
# ============================================================== #

@pytest.mark.parametrize("bad_category", [
    "",                            # empty string
    "Invalid",                     # plausible but not in the fixed list
    "food",                        # lowercase — match is case-sensitive
    "FOOD",                        # uppercase — match is case-sensitive
    "Other!",                      # punctuation variant
])
def test_invalid_category_rerenders_form(auth_client, bad_category):
    resp = auth_client.post("/expenses/1/edit", data={
        "amount": "50.0",
        "category": bad_category,
        "date": "2026-03-20",
        "description": "Parametrized bad category",
    })
    assert resp.status_code == 200, (
        f"category={bad_category!r} is not in VALID_CATEGORIES — "
        "form must be re-rendered (200), not redirect"
    )


# ============================================================== #
# Parametrized — invalid date strings                            #
# ============================================================== #

@pytest.mark.parametrize("bad_date", [
    "",              # empty string
    "2026-13-01",   # month 13 — impossible
    "not-a-date",   # free-form text
    "01/01/2026",   # US slash-separated format — not YYYY-MM-DD
])
def test_invalid_date_rerenders_form(auth_client, bad_date):
    resp = auth_client.post("/expenses/1/edit", data={
        "amount": "50.0",
        "category": "Food",
        "date": bad_date,
        "description": "Parametrized bad date",
    })
    assert resp.status_code == 200, (
        f"date={bad_date!r} is not a valid YYYY-MM-DD date — "
        "form must be re-rendered (200), not redirect"
    )


# ============================================================== #
# POST — empty description stored as NULL                        #
# ============================================================== #

class TestEditExpenseNoDescription:

    def test_empty_description_returns_302(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "33.33",
            "category": "Other",
            "date": "2026-08-20",
            "description": "",
        })
        assert resp.status_code == 302, (
            "POST with empty description must return 302 — blank description is optional"
        )

    def test_empty_description_redirects_to_profile(self, auth_client):
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "44.44",
            "category": "Shopping",
            "date": "2026-09-05",
            "description": "",
        })
        location = resp.headers.get("Location", "")
        assert "/profile" in location, (
            "POST with empty description must redirect to /profile"
        )

    def test_empty_description_stored_as_null_in_db(self, auth_client, app):
        """Empty description string submitted in form → description column stored as NULL."""
        resp = auth_client.post("/expenses/1/edit", data={
            "amount": "22.22",
            "category": "Entertainment",
            "date": "2026-09-15",
            "description": "",
        })
        assert resp.status_code == 302, "Expected 302 before checking DB description value"

        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT description FROM expenses WHERE id = ? AND user_id = ?",
                (1, 1),
            ).fetchone()
            conn.close()

        assert row is not None, "Expense row must exist after update"
        assert row["description"] is None, (
            "An empty description string submitted in the form must be stored as NULL in the DB"
        )
