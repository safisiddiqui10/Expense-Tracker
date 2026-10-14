# Spec: Expense Filter Function

## Overview
Step 6 adds client-side and server-side filtering to the transaction history
table on the `/profile` page. Users can narrow the expense list by category
and/or date range without leaving the page. The filter values are submitted as
GET query parameters so that filtered views are bookmarkable and shareable. A
new DB helper processes the dynamic WHERE clause with parameterised queries; no
new tables or columns are required.

## Depends on
- Step 1: Database setup (`expenses` table and `get_db()` exist)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 5: Backend connection (`get_recent_transactions()` and `database/queries.py` exist)

## Routes
No new routes. The existing `GET /profile` route is extended to accept optional
query parameters:
- `category` — one of the known category values, or empty/absent for "all"
- `date_from` — ISO date string `YYYY-MM-DD`, inclusive lower bound
- `date_to` — ISO date string `YYYY-MM-DD`, inclusive upper bound

## Database changes
No database changes. The `expenses` table already has `category`, `date`,
`user_id`, `amount`, and `description`.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter form above the transaction table with:
    - A `<select>` for category (populated from the distinct categories in the
      database; first option is "All Categories")
    - Two `<input type="date">` fields for date range (`date_from`, `date_to`)
    - A Submit button labelled "Apply"
    - A "Clear" link that navigates back to `/profile` with no query params
  - Pre-populate the form inputs with the current query param values so the
    selected filters are visible after the form is submitted
  - When filters are active, show a small "Filtered results" notice above the
    table with the count of matching rows

## Files to change
- `app.py` — extend `profile()` to read `category`, `date_from`, `date_to`
  from `request.args` and pass them to the new DB helper; pass the filter
  values back to the template for pre-population
- `templates/profile.html` — add the filter form and "Filtered results" notice
- `database/queries.py` — add `get_filtered_transactions()` and
  `get_distinct_categories()`
- `static/css/profile.css` — add styles for the filter form and notice pill

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL; build the
  WHERE clause by appending `?` placeholders and collecting params into a list
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_filtered_transactions()` must fall back gracefully when any filter
  argument is `None` or an empty string — it must not raise an exception
- Date filtering is inclusive on both ends (`date >= date_from AND date <= date_to`)
- Category matching is case-sensitive and exact — no LIKE wildcards
- The route must not crash on invalid date strings; validate with a try/except
  around `datetime.strptime` and ignore malformed values
- The filter form must use `method="GET"` and `action="{{ url_for('profile') }}"`
  so filtered URLs remain bookmarkable
- `get_distinct_categories(user_id)` returns a sorted list of category strings
  for the logged-in user only
- Do not apply the 10-row `limit` when filters are active — return all matching
  rows so the count in the notice is accurate

## Definition of done
- [ ] Loading `/profile` with no query params shows the full unfiltered
  transaction list (up to 10 rows) — identical to Step 5 behaviour
- [ ] Selecting "Food" from the category dropdown and clicking Apply reloads the
  page showing only food expenses; the category select shows "Food" selected
- [ ] Setting `date_from` to `2026-10-10` and clicking Apply returns only
  expenses on or after that date; the date input shows `2026-10-10`
- [ ] Combining category and date range filters correctly intersects both
  constraints
- [ ] Clicking "Clear" navigates to `/profile` with no query params and shows
  the full unfiltered list
- [ ] The "Filtered results" notice appears when any filter is active and
  displays the correct row count
- [ ] The "Filtered results" notice does not appear when no filters are applied
- [ ] Passing a malformed date (e.g. `date_from=notadate`) does not crash the
  app — the filter is silently ignored
- [ ] A user with no expenses sees the empty-state message and an empty filter
  form with no category options selected
