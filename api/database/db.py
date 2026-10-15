import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            SERIAL PRIMARY KEY,
            name          TEXT        NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT        NOT NULL,
            created_at    TIMESTAMP   DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          SERIAL  PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.close()
    conn.close()


def seed_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.close()
        return

    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
        ("Demo User", "demo@budgetly.com", generate_password_hash("demo123")),
    )
    user_id = cur.fetchone()[0]
    cur.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (%s, %s, %s, %s, %s)",
        [
            (user_id, 12.50,  "Food",          "2026-10-01", "Lunch at cafe"),
            (user_id, 35.00,  "Transport",     "2026-10-03", "Monthly bus pass"),
            (user_id, 120.00, "Bills",         "2026-10-05", "Electricity bill"),
            (user_id, 45.00,  "Health",        "2026-10-07", "Pharmacy"),
            (user_id, 25.00,  "Entertainment", "2026-10-09", "Cinema tickets"),
            (user_id, 89.99,  "Shopping",      "2026-10-11", "Clothing"),
            (user_id, 8.75,   "Other",         "2026-10-13", "Miscellaneous"),
            (user_id, 18.40,  "Food",          "2026-10-14", "Groceries"),
        ],
    )
    conn.commit()
    cur.close()
    conn.close()
