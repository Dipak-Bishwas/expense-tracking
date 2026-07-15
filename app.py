import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"  # dev-only placeholder; replace with a config-driven secret later

with app.app_context():
    init_db()
    seed_db()


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

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "member_since": "March 2026",
        "initials": "DU",
    }
    stats = {
        "total_spent": 7180.00,
        "transaction_count": 8,
        "top_category": "Shopping",
    }
    transactions = [
        {"date": "2026-07-12", "description": "Miscellaneous", "category": "Other", "amount": 200.00},
        {"date": "2026-07-11", "description": "New shoes", "category": "Shopping", "amount": 2500.00},
        {"date": "2026-07-10", "description": "Dinner with friends", "category": "Food", "amount": 600.00},
        {"date": "2026-07-08", "description": "Movie tickets", "category": "Entertainment", "amount": 700.00},
        {"date": "2026-07-07", "description": "Pharmacy", "category": "Health", "amount": 480.00},
        {"date": "2026-07-05", "description": "Electricity bill", "category": "Bills", "amount": 2200.00},
        {"date": "2026-07-03", "description": "Metro card recharge", "category": "Transport", "amount": 150.00},
        {"date": "2026-07-02", "description": "Groceries", "category": "Food", "amount": 350.00},
    ]
    categories = [
        {"name": "Shopping", "amount": 2500.00, "percent": 35, "width": 35},
        {"name": "Bills", "amount": 2200.00, "percent": 31, "width": 30},
        {"name": "Entertainment", "amount": 700.00, "percent": 10, "width": 10},
        {"name": "Food", "amount": 950.00, "percent": 13, "width": 15},
        {"name": "Health", "amount": 480.00, "percent": 7, "width": 5},
        {"name": "Transport", "amount": 150.00, "percent": 2, "width": 5},
        {"name": "Other", "amount": 200.00, "percent": 2, "width": 5},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
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
