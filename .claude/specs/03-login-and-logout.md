# Spec: Login and Logout

## Overview
This step makes the login and logout flow fully functional. The existing `GET /login`
route is upgraded to also handle `POST` form submissions — validating credentials against
the database, starting a Flask session on success, and returning an error message on
failure. The stub `GET /logout` route is implemented to clear the session and redirect
to the landing page. This is the first step where the server maintains user state across
requests using Flask's signed-cookie session mechanism, which requires `app.secret_key`
to be configured.

---

## Depends on
- **Step 01 — Database Setup**: `users` table with `email` and `password_hash` columns
  must exist. `get_db()` from `database/db.py` must be available.
- **Step 02 — Registration**: At minimum, the seeded demo user (`demo@budgetly.com` /
  `demo123`) must be present so login can be tested without a working registration form.

---

## Routes

- `GET /login` — render login form — public
- `POST /login` — validate credentials, start session, redirect to `/profile` on success
  or re-render login with error message on failure — public
- `GET /logout` — clear session, redirect to `/` — public (no auth guard needed here)

---

## Database changes

No database changes. The `users` table (with `email` and `password_hash`) was established
in Step 01. Login reads from it; logout does not touch the database.

---

## Templates

- **Modify:** `templates/login.html`
  - Ensure the `<form>` action uses `url_for('login')` instead of the hardcoded `/login`
  - The `{% if error %}` block is already present — no structural change needed; just
    confirm it wires to the `error` variable the route passes on failure

- **Modify:** `templates/base.html`
  - Add a conditional nav block: when `session.user_id` is set, show a "Sign out" link
    (`url_for('logout')`) instead of "Sign in" / "Get started"

---

## Files to change

- `app.py` — add `SECRET_KEY`, update `login()` to accept POST, implement `logout()`
- `templates/login.html` — fix hardcoded action URL to use `url_for`
- `templates/base.html` — add session-aware nav links

---

## Files to create

No new files.

---

## New dependencies

No new pip packages. Uses:
- `flask.session` — already part of Flask
- `werkzeug.security.check_password_hash` — already installed

---

## Rules for implementation

- Set `app.secret_key` in `app.py` as a plain string (dev only — a fixed value is fine
  for this project stage; do not generate it dynamically or read from env)
- Import `session, redirect, url_for, request, flash` from Flask as needed
- The `POST /login` route must:
  1. Read `email` and `password` from `request.form`
  2. Look up the user with a parameterised query: `SELECT * FROM users WHERE email = ?`
  3. Verify the password with `check_password_hash(user['password_hash'], password)`
  4. On success: set `session['user_id']` and redirect to `url_for('profile')`
  5. On failure (no user found OR wrong password): re-render `login.html` with
     `error="Invalid email or password"` — never reveal which field is wrong
- The `GET /logout` route must call `session.clear()` and redirect to `url_for('landing')`
- All SQL must use parameterised queries (`?` placeholders) — never f-strings in SQL
- No SQLAlchemy or ORMs
- Passwords verified with `werkzeug.security.check_password_hash` only
- Use CSS variables — never hardcode hex values in any new styles
- All templates extend `base.html`
- After login, redirect to `url_for('profile')` (Step 4 will make that page useful;
  for now the stub return string is acceptable)

---

## Definition of done

- [ ] Visiting `/login` renders the login form (GET still works)
- [ ] Submitting the form with `demo@budgetly.com` / `demo123` redirects to `/profile`
- [ ] Submitting with a wrong password re-renders the login page with an error message
- [ ] Submitting with an unknown email also re-renders with the same generic error message
- [ ] After a successful login, `session['user_id']` is set to the user's database ID
- [ ] Visiting `/logout` clears the session and redirects to the landing page `/`
- [ ] After logout, `session['user_id']` is no longer set
- [ ] The nav bar shows "Sign out" when logged in and "Sign in"/"Get started" when logged out
- [ ] The login form `action` uses `url_for('login')` (not a hardcoded URL)
- [ ] No raw SQL uses string formatting — all queries use `?` placeholders
