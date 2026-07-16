# Pure query helpers for Step 5 — Backend Connection.
# No Flask imports here; each function opens its own connection via get_db()
# and closes it before returning.

from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    return {
        "name": row["name"],
        "email": row["email"],
        "member_since": created_at.strftime("%B %Y"),
    }


def get_summary_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        if start_date and end_date:
            rows = conn.execute(
                "SELECT category, amount FROM expenses WHERE user_id = ? AND date BETWEEN ? AND ?",
                (user_id, start_date, end_date),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT category, amount FROM expenses WHERE user_id = ?", (user_id,)
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return {"total_spent": 0, "transaction_count": 0, "top_category": "—"}

    total_spent = 0.0
    category_totals = {}
    for row in rows:
        amount = row["amount"]
        total_spent += amount
        category_totals[row["category"]] = category_totals.get(row["category"], 0.0) + amount

    top_category = max(category_totals, key=category_totals.get)

    return {
        "total_spent": total_spent,
        "transaction_count": len(rows),
        "top_category": top_category,
    }


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    conn = get_db()
    try:
        if start_date and end_date:
            rows = conn.execute(
                """
                SELECT date, description, category, amount
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                LIMIT ?
                """,
                (user_id, start_date, end_date, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT date, description, category, amount
                FROM expenses
                WHERE user_id = ?
                ORDER BY date DESC, id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
    finally:
        conn.close()

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        }
        for row in rows
    ]


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        if start_date and end_date:
            rows = conn.execute(
                """
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (user_id, start_date, end_date),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT category, SUM(amount) as total
                FROM expenses
                WHERE user_id = ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (user_id,),
            ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    breakdown = []
    for row in rows:
        pct = int((row["total"] / grand_total) * 100)
        breakdown.append({"name": row["category"], "amount": row["total"], "pct": pct})

    remainder = 100 - sum(item["pct"] for item in breakdown)
    breakdown[0]["pct"] += remainder

    return breakdown
