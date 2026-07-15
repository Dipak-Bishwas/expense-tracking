# Students will write this file in Step 1 — Database Setup
# This file should contain:
#   get_db()   — returns a SQLite connection with row_factory and foreign keys enabled
#   init_db()  — creates all tables using CREATE TABLE IF NOT EXISTS
#   seed_db()  — inserts sample data for development

import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "expense_tracker.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()

    existing = conn.execute("SELECT id FROM users LIMIT 1").fetchone()

    if existing is None:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        conn.executemany(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (user_id, 350.00, "Food", "2026-07-02", "Groceries"),
                (user_id, 600.00, "Food", "2026-07-10", "Dinner with friends"),
                (user_id, 150.00, "Transport", "2026-07-03", "Metro card recharge"),
                (user_id, 2200.00, "Bills", "2026-07-05", "Electricity bill"),
                (user_id, 480.00, "Health", "2026-07-07", "Pharmacy"),
                (user_id, 700.00, "Entertainment", "2026-07-08", "Movie tickets"),
                (user_id, 2500.00, "Shopping", "2026-07-11", "New shoes"),
                (user_id, 200.00, "Other", "2026-07-12", "Miscellaneous"),
            ],
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_db()
    print("Database initialized and seeded.")
