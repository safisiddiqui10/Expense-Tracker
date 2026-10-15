import pytest
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# Unit tests — get_user_by_id                                         #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_correct_fields(app):
    with app.app_context():
        user = get_user_by_id(1)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@budgetly.com"
    assert user["initials"] == "DU"
    assert user["member_since"]  # non-empty "Month YYYY" string


def test_get_user_by_id_nonexistent_returns_none(app):
    with app.app_context():
        assert get_user_by_id(99999) is None


# ------------------------------------------------------------------ #
# Unit tests — get_summary_stats                                      #
# ------------------------------------------------------------------ #

def test_get_summary_stats_seed_user(app):
    with app.app_context():
        stats = get_summary_stats(1)
    assert stats["total"] == pytest.approx(354.64, abs=0.01)
    assert stats["count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(app):
    with app.app_context():
        from database.db import get_db
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty User", "empty@test.com", "x"),
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        stats = get_summary_stats(new_id)

    assert stats["total"] == 0
    assert stats["count"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# Unit tests — get_recent_transactions                                #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_returns_newest_first(app):
    with app.app_context():
        txns = get_recent_transactions(1)
    assert len(txns) == 8
    dates = [t["date"] for t in txns]
    assert dates == sorted(dates, reverse=True)


def test_get_recent_transactions_keys(app):
    with app.app_context():
        txns = get_recent_transactions(1)
    first = txns[0]
    assert all(k in first for k in ("id", "date", "description", "category", "amount"))


def test_get_recent_transactions_no_expenses(app):
    with app.app_context():
        from database.db import get_db
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty2 User", "empty2@test.com", "x"),
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        txns = get_recent_transactions(new_id)
    assert txns == []


# ------------------------------------------------------------------ #
# Unit tests — get_category_breakdown                                 #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_ordered_by_amount(app):
    with app.app_context():
        cats = get_category_breakdown(1)
    assert len(cats) == 7
    totals = [c["total"] for c in cats]
    assert totals == sorted(totals, reverse=True)


def test_get_category_breakdown_pct_sums_to_100(app):
    with app.app_context():
        cats = get_category_breakdown(1)
    assert sum(c["pct"] for c in cats) == 100


def test_get_category_breakdown_keys(app):
    with app.app_context():
        cats = get_category_breakdown(1)
    first = cats[0]
    assert all(k in first for k in ("name", "total", "pct"))


def test_get_category_breakdown_no_expenses(app):
    with app.app_context():
        from database.db import get_db
        conn = get_db()
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty3 User", "empty3@test.com", "x"),
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        cats = get_category_breakdown(new_id)
    assert cats == []


# ------------------------------------------------------------------ #
# Route tests — GET /profile                                          #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_authenticated_returns_200(auth_client):
    resp = auth_client.get("/profile")
    assert resp.status_code == 200


def test_profile_shows_real_user_name(auth_client):
    resp = auth_client.get("/profile")
    assert b"Demo User" in resp.data


def test_profile_shows_real_user_email(auth_client):
    resp = auth_client.get("/profile")
    assert b"demo@budgetly.com" in resp.data


def test_profile_shows_rupee_symbol(auth_client):
    resp = auth_client.get("/profile")
    assert "₹".encode() in resp.data


def test_profile_correct_total(auth_client):
    resp = auth_client.get("/profile")
    assert b"354.64" in resp.data


def test_profile_top_category_bills(auth_client):
    resp = auth_client.get("/profile")
    assert b"Bills" in resp.data


def test_profile_transaction_count(auth_client):
    resp = auth_client.get("/profile")
    assert b"8" in resp.data


def test_profile_category_breakdown_present(auth_client):
    resp = auth_client.get("/profile")
    # All 7 seed categories should appear
    for cat in (b"Food", b"Transport", b"Bills", b"Health", b"Entertainment", b"Shopping", b"Other"):
        assert cat in resp.data
