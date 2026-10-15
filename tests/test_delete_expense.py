"""Tests for Step 09 — Delete Expense."""

import pytest
from database.queries import delete_expense, get_expense_by_id
from database.db import get_db


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _insert_test_expense(app, user_id=1):
    """Insert a throwaway expense and return its id."""
    with app.app_context():
        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, 1.00, "Other", "2026-01-01", "step09 throwaway"),
        )
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
    return new_id


# ------------------------------------------------------------------ #
# Unit tests — delete_expense()                                       #
# ------------------------------------------------------------------ #

class TestDeleteExpenseUnit:

    def test_valid_call_removes_row(self, app):
        expense_id = _insert_test_expense(app, user_id=1)
        with app.app_context():
            delete_expense(expense_id, 1)
            result = get_expense_by_id(expense_id, 1)
        assert result is None

    def test_wrong_user_leaves_row_unchanged(self, app):
        expense_id = _insert_test_expense(app, user_id=1)
        with app.app_context():
            delete_expense(expense_id, 999)
            result = get_expense_by_id(expense_id, 1)
        assert result is not None
        with app.app_context():
            delete_expense(expense_id, 1)

    def test_nonexistent_id_raises_no_error(self, app):
        with app.app_context():
            delete_expense(99999, 1)  # must not raise


# ------------------------------------------------------------------ #
# GET → 405                                                           #
# ------------------------------------------------------------------ #

class TestDeleteGetMethodNotAllowed:

    def test_get_returns_405(self, client):
        resp = client.get("/expenses/1/delete")
        assert resp.status_code == 405


# ------------------------------------------------------------------ #
# POST — unauthenticated                                              #
# ------------------------------------------------------------------ #

class TestDeleteUnauthenticated:

    def test_returns_302_to_login(self, client):
        resp = client.post("/expenses/1/delete")
        assert resp.status_code == 302
        assert "/login" in resp.headers.get("Location", "")


# ------------------------------------------------------------------ #
# POST — authenticated, happy path                                    #
# ------------------------------------------------------------------ #

class TestDeleteAuthenticated:

    def test_redirects_to_profile(self, auth_client, app):
        expense_id = _insert_test_expense(app, user_id=1)
        resp = auth_client.post(f"/expenses/{expense_id}/delete")
        assert resp.status_code == 302
        assert "/profile" in resp.headers.get("Location", "")

    def test_row_removed_from_db(self, auth_client, app):
        expense_id = _insert_test_expense(app, user_id=1)
        auth_client.post(f"/expenses/{expense_id}/delete")
        with app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT id FROM expenses WHERE id = ?", (expense_id,)
            ).fetchone()
            conn.close()
        assert row is None

    def test_nonexistent_expense_returns_404(self, auth_client):
        resp = auth_client.post("/expenses/99999/delete")
        assert resp.status_code == 404


# ------------------------------------------------------------------ #
# POST — ownership guard                                              #
# ------------------------------------------------------------------ #

class TestDeleteOwnershipGuard:

    def test_other_user_gets_404_and_row_survives(self, app):
        expense_id = _insert_test_expense(app, user_id=1)

        with app.app_context():
            conn = get_db()
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Guard User", "guard_del@step09.test", "placeholder"),
            )
            conn.commit()
            row = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                ("guard_del@step09.test",),
            ).fetchone()
            user2_id = row["id"]
            conn.close()

        user2_client = app.test_client()
        with user2_client.session_transaction() as sess:
            sess["user_id"] = user2_id

        resp = user2_client.post(f"/expenses/{expense_id}/delete")
        assert resp.status_code == 404

        with app.app_context():
            result = get_expense_by_id(expense_id, 1)
        assert result is not None

        with app.app_context():
            delete_expense(expense_id, 1)
