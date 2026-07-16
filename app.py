import calendar
import sqlite3
from datetime import date

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"  # dev-only placeholder; replace with a config-driven secret later

with app.app_context():
    init_db()
    seed_db()


RANGE_OPTIONS = [
    ("this-month", "This month"),
    ("last-month", "Last month"),
    ("last-3-months", "Last 3 months"),
    ("all-time", "All time"),
]


def _month_bounds(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def resolve_date_range(range_key):
    valid_keys = {key for key, _ in RANGE_OPTIONS}
    if range_key not in valid_keys:
        range_key = "this-month"

    today = date.today()

    if range_key == "all-time":
        return range_key, None, None

    if range_key == "last-month":
        year, month = today.year, today.month - 1
        if month == 0:
            month, year = 12, year - 1
        start, end = _month_bounds(year, month)
    elif range_key == "last-3-months":
        month, year = today.month - 2, today.year
        while month <= 0:
            month += 12
            year -= 1
        start, _ = _month_bounds(year, month)
        _, end = _month_bounds(today.year, today.month)
    else:  # this-month
        start, end = _month_bounds(today.year, today.month)

    return range_key, start.isoformat(), end.isoformat()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")

        password_hash = generate_password_hash(password)

        conn = get_db()
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            conn.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with this email already exists.")
        finally:
            conn.close()

        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    active_range, start_date, end_date = resolve_date_range(request.args.get("range"))

    user_row = get_user_by_id(user_id)
    if user_row is None:
        session.clear()
        return redirect(url_for("login"))

    name_parts = user_row["name"].split()
    if len(name_parts) > 1:
        initials = (name_parts[0][0] + name_parts[-1][0]).upper()
    else:
        initials = name_parts[0][:2].upper()
    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "member_since": user_row["member_since"],
        "initials": initials,
    }

    stats = get_summary_stats(user_id, start_date=start_date, end_date=end_date)
    transactions = get_recent_transactions(user_id, start_date=start_date, end_date=end_date)

    categories = [
        {**category, "width": round(category["pct"] / 5) * 5}
        for category in get_category_breakdown(user_id, start_date=start_date, end_date=end_date)
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        active_range=active_range,
        range_options=RANGE_OPTIONS,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
