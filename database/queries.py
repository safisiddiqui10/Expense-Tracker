from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    name = row["name"]
    initials = "".join(w[0].upper() for w in name.split()[:2])
    created_at = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
    member_since = created_at.strftime("%B %Y")
    return {
        "name": name,
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary_stats(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
        "FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    top_row = conn.execute(
        "SELECT category, SUM(amount) AS cat_total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return {
        "total": round(row["total"], 2),
        "count": row["count"],
        "top_category": top_row["category"] if top_row else "—",
    }


def get_category_breakdown(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return []
    grand = sum(r["total"] for r in rows)
    result = [
        {
            "name": r["category"],
            "total": round(r["total"], 2),
            "pct": round(r["total"] / grand * 100),
        }
        for r in rows
    ]
    diff = 100 - sum(item["pct"] for item in result)
    if result and diff:
        result[0]["pct"] += diff
    return result
