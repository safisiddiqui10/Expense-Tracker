import psycopg2.extras
from api.database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    name = row["name"]
    initials = "".join(w[0].upper() for w in name.split()[:2])
    member_since = row["created_at"].strftime("%B %Y")
    return {
        "name": name,
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, date, description, category, amount FROM expenses "
        "WHERE user_id = %s ORDER BY date DESC, id DESC LIMIT %s",
        (user_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_distinct_categories(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT DISTINCT category FROM expenses WHERE user_id = %s ORDER BY category",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["category"] for r in rows]


def get_filtered_transactions(user_id, category=None, date_from=None, date_to=None):
    clauses = ["user_id = %s"]
    params = [user_id]

    if category:
        clauses.append("category = %s")
        params.append(category)
    if date_from:
        clauses.append("date >= %s")
        params.append(date_from)
    if date_to:
        clauses.append("date <= %s")
        params.append(date_to)

    where = " AND ".join(clauses)
    limit_sql = " LIMIT 10" if len(clauses) == 1 else ""
    sql = (
        f"SELECT id, date, description, category, amount FROM expenses "
        f"WHERE {where} ORDER BY date DESC, id DESC{limit_sql}"
    )

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_summary_stats(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
        "FROM expenses WHERE user_id = %s",
        (user_id,),
    )
    row = cur.fetchone()
    cur.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = %s GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,),
    )
    top_row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "total": round(float(row["total"]), 2),
        "count": row["count"],
        "top_category": top_row["category"] if top_row else "—",
    }


def get_category_breakdown(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "WHERE user_id = %s GROUP BY category ORDER BY total DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return []
    grand = sum(r["total"] for r in rows)
    result = [
        {
            "name": r["category"],
            "total": round(float(r["total"]), 2),
            "pct": round(r["total"] / grand * 100),
        }
        for r in rows
    ]
    diff = 100 - sum(item["pct"] for item in result)
    if result and diff:
        result[0]["pct"] += diff
    return result


def insert_expense(user_id, amount, category, date, description):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (%s, %s, %s, %s, %s)",
        (user_id, amount, category, date, description),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, user_id, amount, category, date, description FROM expenses"
        " WHERE id = %s AND user_id = %s",
        (expense_id, user_id),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row is not None else None


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE expenses SET amount = %s, category = %s, date = %s, description = %s"
        " WHERE id = %s AND user_id = %s",
        (amount, category, date, description, expense_id, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_expense(expense_id, user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM expenses WHERE id = %s AND user_id = %s",
        (expense_id, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
