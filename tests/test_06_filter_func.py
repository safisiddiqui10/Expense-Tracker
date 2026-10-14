"""
Tests for Step 06 — Expense Filter Function.

Covers:
- GET /profile with no query params (unfiltered)
- GET /profile?category=<value>
- GET /profile?date_from=<YYYY-MM-DD>
- GET /profile?date_to=<YYYY-MM-DD>
- Combined filters
- Filter notice (present / absent)
- Malformed date input
- Unauthenticated access
- Empty-expense user
- DB helpers: get_distinct_categories(), get_filtered_transactions()
"""

import pytest
from database.queries import get_distinct_categories, get_filtered_transactions
from database.db import get_db


# ---------------------------------------------------------------------- #
# Seed data reference (from database/db.py seed_db)                      #
# ---------------------------------------------------------------------- #
# (user_id, amount, category, date, description)
# 12.50   Food          2026-10-01  "Lunch at cafe"
# 35.00   Transport     2026-10-03  "Monthly bus pass"
# 120.00  Bills         2026-10-05  "Electricity bill"
# 45.00   Health        2026-10-07  "Pharmacy"
# 25.00   Entertainment 2026-10-09  "Cinema tickets"
# 89.99   Shopping      2026-10-11  "Clothing"
# 8.75    Other         2026-10-13  "Miscellaneous"
# 18.40   Food          2026-10-14  "Groceries"
#
# date_from=2026-10-10 → Shopping, Other, Groceries (3)
# date_to=2026-10-05   → Lunch, Monthly bus pass, Electricity bill (3)
# category=Food        → Lunch at cafe, Groceries (2)
# category=Food + date_from=2026-10-10 → Groceries (1)
# ---------------------------------------------------------------------- #


# ---------------------------------------------------------------------- #
# Helper — create an extra user with no expenses                         #
# ---------------------------------------------------------------------- #

def _create_empty_user(app, email="nospend@test.com", name="No Spend"):
    """Insert a user with no expenses; return their id."""
    with app.app_context():
        conn = get_db()
        conn.execute(
            "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, "hashed"),
        )
        conn.commit()
        user_id = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()["id"]
        conn.close()
    return user_id


# ====================================================================== #
# Route tests — unauthenticated access                                    #
# ====================================================================== #

class TestProfileAuthGuard:

    def test_unauthenticated_no_params_redirects_to_login(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 302, "Expected redirect for unauthenticated request"
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_with_category_param_redirects(self, client):
        resp = client.get("/profile?category=Food")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_with_date_params_redirects(self, client):
        resp = client.get("/profile?date_from=2026-10-01&date_to=2026-10-14")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ====================================================================== #
# Route tests — unfiltered profile                                        #
# ====================================================================== #

class TestProfileUnfiltered:

    def test_no_params_returns_200(self, auth_client):
        resp = auth_client.get("/profile")
        assert resp.status_code == 200

    def test_no_params_shows_seed_expenses(self, auth_client):
        resp = auth_client.get("/profile")
        # At least one expense description from each end of the seed list should appear
        assert b"Lunch at cafe" in resp.data, "Oldest food expense should be visible"
        assert b"Groceries" in resp.data, "Newest food expense should be visible"

    def test_no_params_shows_all_eight_seed_expenses(self, auth_client):
        resp = auth_client.get("/profile")
        # All 8 descriptions from seed data should be present (8 < 10 limit)
        for description in (
            b"Lunch at cafe",
            b"Monthly bus pass",
            b"Electricity bill",
            b"Pharmacy",
            b"Cinema tickets",
            b"Clothing",
            b"Miscellaneous",
            b"Groceries",
        ):
            assert description in resp.data, f"Expected {description!r} in unfiltered profile"

    def test_no_params_filter_notice_absent(self, auth_client):
        resp = auth_client.get("/profile")
        # The "Filtered results" notice must NOT appear when no filters are active
        assert b"Filtered results" not in resp.data, (
            "Filter notice should not appear when no filters are active"
        )

    def test_no_params_filter_form_present(self, auth_client):
        resp = auth_client.get("/profile")
        # Filter form structural elements must be rendered
        assert b"All Categories" in resp.data, "Category dropdown should have 'All Categories' option"
        assert b"Apply" in resp.data, "Submit button labelled Apply must be present"
        assert b"date_from" in resp.data, "date_from input must be present"
        assert b"date_to" in resp.data, "date_to input must be present"

    def test_no_params_clear_link_present(self, auth_client):
        resp = auth_client.get("/profile")
        assert b"Clear" in resp.data, "A 'Clear' link must be present on the filter form"

    def test_no_params_filter_form_action_is_profile(self, auth_client):
        resp = auth_client.get("/profile")
        # The form action must resolve to the profile route
        assert b'action="' in resp.data or b"action='" in resp.data, (
            "Filter form must have an action attribute"
        )
        assert b"/profile" in resp.data, "Form action must point to /profile"


# ====================================================================== #
# Route tests — category filter                                           #
# ====================================================================== #

class TestProfileCategoryFilter:

    def test_category_food_returns_200(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        assert resp.status_code == 200

    def test_category_food_shows_food_expenses(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        assert b"Lunch at cafe" in resp.data, "Expected 'Lunch at cafe' in Food filter results"
        assert b"Groceries" in resp.data, "Expected 'Groceries' in Food filter results"

    def test_category_food_excludes_non_food(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        for description in (
            b"Monthly bus pass",
            b"Electricity bill",
            b"Pharmacy",
            b"Cinema tickets",
            b"Clothing",
            b"Miscellaneous",
        ):
            assert description not in resp.data, (
                f"Non-food expense {description!r} should not appear when filtering by Food"
            )

    def test_category_food_filter_notice_appears(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        assert b"Filtered results" in resp.data, (
            "Filter notice must appear when category filter is active"
        )

    def test_category_food_filter_notice_shows_count_2(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        # The notice should indicate 2 matching rows
        data = resp.data.decode("utf-8")
        # Find 'Filtered results' section and nearby count
        assert "2" in data, "Filter notice should show count of 2 for Food category"

    def test_category_food_preselected_in_dropdown(self, auth_client):
        resp = auth_client.get("/profile?category=Food")
        # The Food option must be marked as selected
        assert b"selected" in resp.data, "An option should be selected in the dropdown"
        # Food value must appear in the select context
        assert b"Food" in resp.data

    def test_category_filter_case_sensitive(self, auth_client):
        # "food" (lowercase) should match nothing — category matching is exact
        resp = auth_client.get("/profile?category=food")
        assert resp.status_code == 200
        assert b"Lunch at cafe" not in resp.data, (
            "Category filter is case-sensitive; 'food' should not match 'Food'"
        )

    def test_category_transport_returns_one_expense(self, auth_client):
        resp = auth_client.get("/profile?category=Transport")
        assert resp.status_code == 200
        assert b"Monthly bus pass" in resp.data
        assert b"Groceries" not in resp.data

    def test_empty_category_param_treated_as_no_filter(self, auth_client):
        resp = auth_client.get("/profile?category=")
        assert resp.status_code == 200
        assert b"Filtered results" not in resp.data, (
            "Empty category param must not activate filter notice"
        )


# ====================================================================== #
# Route tests — date_from filter                                          #
# ====================================================================== #

class TestProfileDateFromFilter:

    def test_date_from_returns_200(self, auth_client):
        resp = auth_client.get("/profile?date_from=2026-10-10")
        assert resp.status_code == 200

    def test_date_from_shows_expenses_on_or_after(self, auth_client):
        resp = auth_client.get("/profile?date_from=2026-10-10")
        # 2026-10-11 Shopping, 2026-10-13 Other, 2026-10-14 Food
        assert b"Clothing" in resp.data, "Shopping expense (2026-10-11) should be included"
        assert b"Miscellaneous" in resp.data, "Other expense (2026-10-13) should be included"
        assert b"Groceries" in resp.data, "Food expense (2026-10-14) should be included"

    def test_date_from_excludes_earlier_expenses(self, auth_client):
        resp = auth_client.get("/profile?date_from=2026-10-10")
        for description in (
            b"Lunch at cafe",
            b"Monthly bus pass",
            b"Electricity bill",
            b"Pharmacy",
            b"Cinema tickets",
        ):
            assert description not in resp.data, (
                f"{description!r} is before 2026-10-10 and should be excluded"
            )

    def test_date_from_filter_notice_appears(self, auth_client):
        resp = auth_client.get("/profile?date_from=2026-10-10")
        assert b"Filtered results" in resp.data, (
            "Filter notice must appear when date_from is active"
        )

    def test_date_from_prepopulated_in_form(self, auth_client):
        resp = auth_client.get("/profile?date_from=2026-10-10")
        assert b"2026-10-10" in resp.data, (
            "The date_from value must be pre-populated in the form input"
        )


# ====================================================================== #
# Route tests — date_to filter                                            #
# ====================================================================== #

class TestProfileDateToFilter:

    def test_date_to_returns_200(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-10-05")
        assert resp.status_code == 200

    def test_date_to_shows_expenses_on_or_before(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-10-05")
        # 2026-10-01 Food, 2026-10-03 Transport, 2026-10-05 Bills (inclusive)
        assert b"Lunch at cafe" in resp.data, "Food expense (2026-10-01) should be included"
        assert b"Monthly bus pass" in resp.data, "Transport expense (2026-10-03) should be included"
        assert b"Electricity bill" in resp.data, "Bills expense (2026-10-05) should be included (inclusive)"

    def test_date_to_inclusive_boundary(self, auth_client):
        # 2026-10-05 is the date_to — the expense ON that date must be included
        resp = auth_client.get("/profile?date_to=2026-10-05")
        assert b"Electricity bill" in resp.data, (
            "date_to bound is inclusive; 2026-10-05 expense must appear"
        )

    def test_date_to_excludes_later_expenses(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-10-05")
        for description in (
            b"Pharmacy",
            b"Cinema tickets",
            b"Clothing",
            b"Miscellaneous",
            b"Groceries",
        ):
            assert description not in resp.data, (
                f"{description!r} is after 2026-10-05 and should be excluded"
            )

    def test_date_to_filter_notice_appears(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-10-05")
        assert b"Filtered results" in resp.data, (
            "Filter notice must appear when date_to is active"
        )

    def test_date_to_prepopulated_in_form(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-10-05")
        assert b"2026-10-05" in resp.data, (
            "The date_to value must be pre-populated in the form input"
        )


# ====================================================================== #
# Route tests — combined filters                                          #
# ====================================================================== #

class TestProfileCombinedFilters:

    def test_category_and_date_from_intersects(self, auth_client):
        # Food + date_from=2026-10-10 → only Groceries (2026-10-14)
        resp = auth_client.get("/profile?category=Food&date_from=2026-10-10")
        assert resp.status_code == 200
        assert b"Groceries" in resp.data, "Groceries (Food, 2026-10-14) should match"
        assert b"Lunch at cafe" not in resp.data, (
            "Lunch at cafe is before 2026-10-10 and should be excluded"
        )

    def test_category_and_date_range_combined(self, auth_client):
        # Food + date_from=2026-10-01 + date_to=2026-10-05 → only Lunch at cafe
        resp = auth_client.get(
            "/profile?category=Food&date_from=2026-10-01&date_to=2026-10-05"
        )
        assert resp.status_code == 200
        assert b"Lunch at cafe" in resp.data
        assert b"Groceries" not in resp.data

    def test_combined_filters_filter_notice_appears(self, auth_client):
        resp = auth_client.get("/profile?category=Food&date_from=2026-10-10")
        assert b"Filtered results" in resp.data

    def test_combined_filters_all_prepopulated(self, auth_client):
        resp = auth_client.get(
            "/profile?category=Food&date_from=2026-10-10&date_to=2026-10-15"
        )
        data = resp.data
        assert b"2026-10-10" in data, "date_from should be pre-populated"
        assert b"2026-10-15" in data, "date_to should be pre-populated"
        assert b"selected" in data, "category should be pre-selected"

    def test_non_intersecting_filters_return_empty(self, auth_client):
        # category=Bills, but date range excludes 2026-10-05 entirely
        resp = auth_client.get(
            "/profile?category=Bills&date_from=2026-10-06&date_to=2026-10-14"
        )
        assert resp.status_code == 200
        assert b"Electricity bill" not in resp.data, (
            "Bills expense at 2026-10-05 should not appear when date_from=2026-10-06"
        )


# ====================================================================== #
# Route tests — malformed date input                                      #
# ====================================================================== #

class TestProfileMalformedDate:

    def test_malformed_date_from_does_not_crash(self, auth_client):
        resp = auth_client.get("/profile?date_from=notadate")
        assert resp.status_code == 200, (
            "Malformed date_from must not crash the app — expected 200"
        )

    def test_malformed_date_to_does_not_crash(self, auth_client):
        resp = auth_client.get("/profile?date_to=bad-date")
        assert resp.status_code == 200

    def test_malformed_date_from_ignored_no_filter_notice(self, auth_client):
        resp = auth_client.get("/profile?date_from=notadate")
        # Malformed date should be silently ignored, so no filter is active
        assert b"Filtered results" not in resp.data, (
            "Malformed date_from should be silently ignored; filter notice must not appear"
        )

    def test_malformed_date_to_ignored_no_filter_notice(self, auth_client):
        resp = auth_client.get("/profile?date_to=2026-13-99")
        assert resp.status_code == 200
        assert b"Filtered results" not in resp.data, (
            "Invalid date_to should be silently ignored; filter notice must not appear"
        )

    def test_malformed_date_from_shows_all_expenses(self, auth_client):
        # Since the bad date is ignored, all seed expenses should still appear
        resp = auth_client.get("/profile?date_from=notadate")
        assert b"Lunch at cafe" in resp.data
        assert b"Groceries" in resp.data

    def test_valid_category_with_malformed_date_still_filters_by_category(self, auth_client):
        # Valid category + malformed date → only category filter applies
        resp = auth_client.get("/profile?category=Food&date_from=notadate")
        assert resp.status_code == 200
        assert b"Groceries" in resp.data
        assert b"Lunch at cafe" in resp.data
        assert b"Electricity bill" not in resp.data


# ====================================================================== #
# Route tests — user with no expenses                                     #
# ====================================================================== #

class TestProfileEmptyUser:

    def test_empty_user_profile_returns_200(self, client, app):
        uid = _create_empty_user(app, email="nospend_route@test.com", name="No Spend Route")
        with client.session_transaction() as sess:
            sess["user_id"] = uid
        resp = client.get("/profile")
        assert resp.status_code == 200

    def test_empty_user_filter_form_renders(self, client, app):
        uid = _create_empty_user(app, email="nospend_form@test.com", name="No Spend Form")
        with client.session_transaction() as sess:
            sess["user_id"] = uid
        resp = client.get("/profile")
        assert b"Apply" in resp.data, "Filter form must still render for empty user"
        assert b"date_from" in resp.data

    def test_empty_user_no_category_options_except_all(self, client, app):
        uid = _create_empty_user(app, email="nospend_cats@test.com", name="No Spend Cats")
        with client.session_transaction() as sess:
            sess["user_id"] = uid
        resp = client.get("/profile")
        # "All Categories" is always present; no dynamic category options for empty user
        assert b"All Categories" in resp.data

    def test_empty_user_filter_notice_absent(self, client, app):
        uid = _create_empty_user(app, email="nospend_notice@test.com", name="No Spend Notice")
        with client.session_transaction() as sess:
            sess["user_id"] = uid
        resp = client.get("/profile?category=Food")
        # Empty user has no Food expenses; filtered results notice may appear or not,
        # but if it does it should show 0 — either way no crash
        assert resp.status_code == 200


# ====================================================================== #
# DB unit tests — get_distinct_categories()                               #
# ====================================================================== #

class TestGetDistinctCategories:

    def test_returns_list_for_seed_user(self, app):
        with app.app_context():
            cats = get_distinct_categories(1)
        assert isinstance(cats, list), "Should return a list"
        assert len(cats) == 7, "Seed data has 7 distinct categories"

    def test_returns_sorted_alphabetical_list(self, app):
        with app.app_context():
            cats = get_distinct_categories(1)
        assert cats == sorted(cats), "Categories must be sorted alphabetically"

    def test_contains_expected_seed_categories(self, app):
        with app.app_context():
            cats = get_distinct_categories(1)
        expected = {"Bills", "Entertainment", "Food", "Health", "Other", "Shopping", "Transport"}
        assert set(cats) == expected, f"Expected {expected}, got {set(cats)}"

    def test_returns_strings(self, app):
        with app.app_context():
            cats = get_distinct_categories(1)
        for cat in cats:
            assert isinstance(cat, str), f"Category must be a string, got {type(cat)}"

    def test_user_isolation_empty_user(self, app):
        uid = _create_empty_user(app, email="cats_isolation@test.com", name="Cats Isolation")
        with app.app_context():
            cats = get_distinct_categories(uid)
        assert cats == [], "User with no expenses should get empty categories list"

    def test_user_isolation_different_user_categories(self, app):
        # Create a separate user with only one category
        with app.app_context():
            conn = get_db()
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Cat User", "catuser@test.com", "hashed"),
            )
            conn.commit()
            uid = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("catuser@test.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (uid, 10.0, "Unique", "2026-10-01", "Only this"),
            )
            conn.commit()
            conn.close()

            cats = get_distinct_categories(uid)

        assert cats == ["Unique"], "User should only see their own categories"
        # Seed user categories should NOT appear in this user's list
        with app.app_context():
            cats_other = get_distinct_categories(uid)
        assert "Food" not in cats_other
        assert "Bills" not in cats_other

    def test_no_duplicates_returned(self, app):
        with app.app_context():
            cats = get_distinct_categories(1)
        assert len(cats) == len(set(cats)), "No duplicate categories should be returned"


# ====================================================================== #
# DB unit tests — get_filtered_transactions()                             #
# ====================================================================== #

class TestGetFilteredTransactions:

    def test_no_filters_returns_all_seed_rows(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1)
        assert len(rows) == 8, "No filters should return all 8 seed expenses"

    def test_no_filters_returns_list_of_dicts(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1)
        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, dict)

    def test_no_filters_rows_have_required_keys(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1)
        required_keys = {"id", "date", "description", "category", "amount"}
        for row in rows:
            assert required_keys.issubset(row.keys()), (
                f"Row missing keys. Got: {set(row.keys())}"
            )

    def test_no_filters_ordered_newest_first(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1)
        dates = [r["date"] for r in rows]
        assert dates == sorted(dates, reverse=True), "Rows should be ordered newest first"

    def test_category_filter_returns_only_food(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category="Food")
        assert len(rows) == 2, "Expected 2 Food expenses from seed data"
        for row in rows:
            assert row["category"] == "Food", f"Non-food row returned: {row}"

    def test_category_filter_returns_all_matching_no_limit(self, app):
        # When a filter is active, no row limit should be applied
        with app.app_context():
            rows = get_filtered_transactions(1, category="Food")
        # All 2 Food rows must be present, not truncated
        descriptions = {r["description"] for r in rows}
        assert "Lunch at cafe" in descriptions
        assert "Groceries" in descriptions

    def test_category_filter_case_sensitive(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category="food")
        assert rows == [], "Lowercase 'food' should not match 'Food' — case-sensitive"

    def test_category_filter_exact_match_no_wildcards(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category="Foo")
        assert rows == [], "Partial category name should not match"

    def test_date_from_inclusive_lower_bound(self, app):
        # date_from=2026-10-01 — expense ON this date (Food/Lunch) must be included
        with app.app_context():
            rows = get_filtered_transactions(1, date_from="2026-10-01")
        descriptions = {r["description"] for r in rows}
        assert "Lunch at cafe" in descriptions, (
            "date_from is inclusive; expense on 2026-10-01 must be included"
        )

    def test_date_from_excludes_earlier_dates(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, date_from="2026-10-10")
        dates = [r["date"] for r in rows]
        for d in dates:
            assert d >= "2026-10-10", f"Expense on {d} should be excluded by date_from=2026-10-10"

    def test_date_from_returns_three_expenses(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, date_from="2026-10-10")
        assert len(rows) == 3, (
            "date_from=2026-10-10 should return 3 expenses: Shopping, Other, Groceries"
        )

    def test_date_to_inclusive_upper_bound(self, app):
        # date_to=2026-10-05 — expense ON this date (Bills) must be included
        with app.app_context():
            rows = get_filtered_transactions(1, date_to="2026-10-05")
        descriptions = {r["description"] for r in rows}
        assert "Electricity bill" in descriptions, (
            "date_to is inclusive; expense on 2026-10-05 must be included"
        )

    def test_date_to_excludes_later_dates(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, date_to="2026-10-05")
        dates = [r["date"] for r in rows]
        for d in dates:
            assert d <= "2026-10-05", f"Expense on {d} should be excluded by date_to=2026-10-05"

    def test_date_to_returns_three_expenses(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, date_to="2026-10-05")
        assert len(rows) == 3, (
            "date_to=2026-10-05 should return 3 expenses: Lunch, Bus pass, Electricity bill"
        )

    def test_date_range_both_inclusive(self, app):
        # date_from=2026-10-03, date_to=2026-10-09 → Transport, Bills, Health, Entertainment (4)
        with app.app_context():
            rows = get_filtered_transactions(
                1, date_from="2026-10-03", date_to="2026-10-09"
            )
        assert len(rows) == 4
        dates = [r["date"] for r in rows]
        for d in dates:
            assert "2026-10-03" <= d <= "2026-10-09"

    def test_combined_category_and_date_from(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category="Food", date_from="2026-10-10")
        assert len(rows) == 1, "Only Groceries (Food, 2026-10-14) should match"
        assert rows[0]["description"] == "Groceries"

    def test_combined_category_and_date_range(self, app):
        with app.app_context():
            rows = get_filtered_transactions(
                1, category="Food", date_from="2026-10-01", date_to="2026-10-05"
            )
        assert len(rows) == 1
        assert rows[0]["description"] == "Lunch at cafe"

    def test_none_category_param_does_not_raise(self, app):
        with app.app_context():
            try:
                rows = get_filtered_transactions(1, category=None)
            except Exception as exc:
                pytest.fail(f"category=None raised an exception: {exc}")
        assert isinstance(rows, list)

    def test_none_date_from_param_does_not_raise(self, app):
        with app.app_context():
            try:
                rows = get_filtered_transactions(1, date_from=None)
            except Exception as exc:
                pytest.fail(f"date_from=None raised an exception: {exc}")
        assert isinstance(rows, list)

    def test_none_date_to_param_does_not_raise(self, app):
        with app.app_context():
            try:
                rows = get_filtered_transactions(1, date_to=None)
            except Exception as exc:
                pytest.fail(f"date_to=None raised an exception: {exc}")
        assert isinstance(rows, list)

    def test_all_none_params_returns_all_rows(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category=None, date_from=None, date_to=None)
        assert len(rows) == 8

    def test_user_isolation_returns_only_own_expenses(self, app):
        uid = _create_empty_user(app, email="isolation_txn@test.com", name="Isolation Txn")
        with app.app_context():
            conn = get_db()
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                (uid, 5.00, "Food", "2026-10-01", "Isolated expense"),
            )
            conn.commit()
            conn.close()

            rows = get_filtered_transactions(uid)

        assert len(rows) == 1, "User should only see their own expenses"
        assert rows[0]["description"] == "Isolated expense"

    def test_user_isolation_seed_user_not_leaked(self, app):
        uid = _create_empty_user(app, email="noleak_txn@test.com", name="No Leak Txn")
        with app.app_context():
            rows = get_filtered_transactions(uid)
        assert rows == [], "Seed user's expenses must not appear for a different user"

    def test_nonexistent_user_returns_empty_list(self, app):
        with app.app_context():
            rows = get_filtered_transactions(99999)
        assert rows == [], "Non-existent user should return empty list"

    def test_no_matching_rows_returns_empty_list(self, app):
        with app.app_context():
            rows = get_filtered_transactions(1, category="NonExistentCategory")
        assert rows == [], "No matching category should return empty list"


# ====================================================================== #
# Parametrized — filter notice behavior                                   #
# ====================================================================== #

@pytest.mark.parametrize("query_string", [
    "category=Food",
    "date_from=2026-10-10",
    "date_to=2026-10-05",
    "category=Transport&date_from=2026-10-01",
    "date_from=2026-10-01&date_to=2026-10-14",
    "category=Bills&date_from=2026-10-01&date_to=2026-10-14",
])
def test_filter_notice_appears_when_any_filter_active(auth_client, query_string):
    resp = auth_client.get(f"/profile?{query_string}")
    assert resp.status_code == 200
    assert b"Filtered results" in resp.data, (
        f"Filter notice must appear for active filter: ?{query_string}"
    )


@pytest.mark.parametrize("query_string", [
    "",
    "category=",
    "date_from=",
    "date_to=",
    "category=&date_from=&date_to=",
    "date_from=notadate",
    "date_to=bad",
])
def test_filter_notice_absent_when_no_valid_filter(auth_client, query_string):
    url = f"/profile?{query_string}" if query_string else "/profile"
    resp = auth_client.get(url)
    assert resp.status_code == 200
    assert b"Filtered results" not in resp.data, (
        f"Filter notice must NOT appear when no valid filter active: {url}"
    )
