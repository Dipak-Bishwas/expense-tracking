"""
Tests for Step 6 — Date Filter for Profile Page
(spec: .claude/specs/06-date-filter-profile-page.md)

Covers:
  - GET /profile?range=... behavior: default ("this-month") when the query
    param is missing, "last-month", "last-3-months", "all-time", and a
    bogus/invalid value falling back to the default without a 500.
  - Auth guard on /profile (unauthenticated -> redirect to /login).
  - database/queries.py helpers (get_summary_stats, get_recent_transactions,
    get_category_breakdown) accepting optional start_date/end_date kwargs
    while staying fully backward compatible when those args are omitted.

Expected values are derived from the seed data in database/db.py: the demo
user (demo@spendly.com / demo123) has 8 expenses, all dated in July 2026,
summing to INR 7,180.00 (350 + 600 + 150 + 2200 + 480 + 700 + 2500 + 200).
This is the corrected total per the task brief -- NOT the INR 346.24 figure
that appears in an older draft of the spec's Definition of Done section.

IMPORTANT -- real-DB safety:
`app.py` runs `init_db()` / `seed_db()` at *module import time* against
whatever `database.db.DB_PATH` currently points to. To guarantee the
developer's real `expense_tracker.db` is never touched by this suite (it has
already been accidentally wiped once during manual testing), we redirect
`database.db.DB_PATH` to a throwaway temp file *before* `app` is imported
below, and every test additionally monkeypatches DB_PATH to its own
tmp_path-backed file for full per-test isolation.

Time-coupling caveat: because the seed data's "current month" alignment is
baked into database/db.py as hardcoded 2026-07 dates (not derived from
datetime.today()), the "this-month" / "last-3-months" assertions below are
only valid while the suite is run during July 2026, matching the app's own
seed-data design assumption spelled out in the spec's Definition of Done
("seed data falls in the current month").
"""

import os
import tempfile
import uuid

import pytest

import database.db as db_module

_IMPORT_TIME_DB = os.path.join(
    tempfile.gettempdir(), f"spendly_test_import_{uuid.uuid4().hex}.db"
)
db_module.DB_PATH = _IMPORT_TIME_DB  # redirect BEFORE importing app.py

from app import app as flask_app  # noqa: E402  (must follow the DB_PATH patch above)
from database.db import init_db, seed_db  # noqa: E402
from database.queries import (  # noqa: E402
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
)

SEED_TOTAL = 7180.00
SEED_TRANSACTION_COUNT = 8
SEED_TOP_CATEGORY = "Shopping"  # highest single-category total: 2500.00


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app wired to a fresh, isolated per-test SQLite file."""
    db_path = str(tmp_path / "test_expense_tracker.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    flask_app.config.update({"TESTING": True})
    init_db()
    seed_db()
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """A test client logged in as the seeded demo user."""
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    return client


@pytest.fixture
def seeded_user_id(app):
    """The demo user's id in the current test's isolated DB."""
    conn = db_module.get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, "seed_db() should have created the demo user"
    return row["id"]


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestProfileAuthGuard:
    def test_profile_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Unauthenticated /profile should redirect, not render"
        assert "/login" in response.headers["Location"], "Unauthenticated /profile should redirect to /login"


# ------------------------------------------------------------------ #
# GET /profile?range=... — default / missing / bogus values          #
# ------------------------------------------------------------------ #

class TestProfileDefaultRange:
    def test_profile_no_range_param_defaults_to_this_month(self, auth_client):
        response = auth_client.get("/profile")
        assert response.status_code == 200

        assert b'value="this-month" selected>' in response.data, (
            "With no ?range= query string, the 'This month' option must be pre-selected"
        )
        assert "&#8377;7,180.00".encode() in response.data, "Default range should show the full seed total"
        assert b'<span class="stat-value">8</span>' in response.data, "Default range should show all 8 seed transactions"
        assert b'<span class="stat-value">Shopping</span>' in response.data, "Top category for the full seed set should be Shopping"

    @pytest.mark.parametrize(
        "bogus_range",
        [
            "bogus-value",
            "",
            "THIS-MONTH",
            "this_month",
            "next-month",
            "'; DROP TABLE expenses; --",
            "<script>alert(1)</script>",
            "a" * 500,
        ],
    )
    def test_profile_bogus_range_falls_back_to_default_without_error(self, auth_client, bogus_range):
        response = auth_client.get(f"/profile?range={bogus_range}")
        assert response.status_code == 200, "An unrecognized range value must never raise a server error"
        assert b'value="this-month" selected>' in response.data, (
            "An unrecognized range value must fall back to the 'This month' default"
        )
        assert "&#8377;7,180.00".encode() in response.data


# ------------------------------------------------------------------ #
# GET /profile?range=... — each supported range option                #
# ------------------------------------------------------------------ #

class TestProfileRangeOptions:
    def test_profile_last_month_shows_zero_total_and_empty_state(self, auth_client):
        response = auth_client.get("/profile?range=last-month")
        assert response.status_code == 200

        assert b'value="last-month" selected>' in response.data, "Selecting Last month must mark it selected in the dropdown"
        assert "&#8377;0.00".encode() in response.data, "Last month has no seed expenses, so total should be INR 0.00"
        assert b'<span class="stat-value">0</span>' in response.data, "Last month should show 0 transactions"
        assert b"No transactions in this period." in response.data, "Empty recent-transactions state must be shown"
        assert b"No expenses in this period." in response.data, "Empty category-breakdown state must be shown"

    def test_profile_all_time_matches_this_month_totals(self, auth_client):
        response = auth_client.get("/profile?range=all-time")
        assert response.status_code == 200

        assert b'value="all-time" selected>' in response.data
        assert "&#8377;7,180.00".encode() in response.data, "All time should match Step 5's unfiltered total"
        assert b'<span class="stat-value">8</span>' in response.data
        assert b'<span class="stat-value">Shopping</span>' in response.data

    def test_profile_last_3_months_matches_this_month_totals(self, auth_client):
        response = auth_client.get("/profile?range=last-3-months")
        assert response.status_code == 200

        assert b'value="last-3-months" selected>' in response.data
        assert "&#8377;7,180.00".encode() in response.data, "Last 3 months should include all seed data for this dataset"
        assert b'<span class="stat-value">8</span>' in response.data

    def test_profile_range_state_comes_from_url_not_session(self, auth_client):
        """Selecting a filter must not 'stick' server-side; a later request
        with no query string must revert to the This month default, proving
        the active range is derived purely from the URL."""
        filtered = auth_client.get("/profile?range=last-month")
        assert b'value="last-month" selected>' in filtered.data

        reload_same_url = auth_client.get("/profile?range=last-month")
        assert b'value="last-month" selected>' in reload_same_url.data, (
            "Reloading the same URL must keep the same filter selected"
        )

        no_query_string = auth_client.get("/profile")
        assert b'value="this-month" selected>' in no_query_string.data, (
            "A subsequent request with no ?range= must default to This month, "
            "not remember the previous selection server-side"
        )


# ------------------------------------------------------------------ #
# database/queries.py — backward compatibility (no date args)         #
# ------------------------------------------------------------------ #

class TestQueryHelpersBackwardCompatibility:
    def test_get_summary_stats_without_date_args_matches_legacy_behavior(self, seeded_user_id):
        stats = get_summary_stats(seeded_user_id)
        assert stats["total_spent"] == pytest.approx(SEED_TOTAL)
        assert stats["transaction_count"] == SEED_TRANSACTION_COUNT
        assert stats["top_category"] == SEED_TOP_CATEGORY

    def test_get_recent_transactions_without_date_args_matches_legacy_behavior(self, seeded_user_id):
        transactions = get_recent_transactions(seeded_user_id)
        assert len(transactions) == SEED_TRANSACTION_COUNT

    def test_get_recent_transactions_positional_limit_still_works(self, seeded_user_id):
        """Step 5 callers used get_recent_transactions(user_id, limit) positionally;
        adding start_date/end_date after limit must not break that call shape."""
        transactions = get_recent_transactions(seeded_user_id, 3)
        assert len(transactions) == 3

    def test_get_category_breakdown_without_date_args_matches_legacy_behavior(self, seeded_user_id):
        breakdown = get_category_breakdown(seeded_user_id)
        assert len(breakdown) == 7, "Seed data spans 7 distinct categories"
        total_pct = sum(item["pct"] for item in breakdown)
        assert total_pct == 100, "Category percentages must sum to 100% when the range has expenses"

    def test_query_helpers_no_data_user_return_empty_defaults_without_date_args(self, seeded_user_id):
        """A user with no expenses at all (unfiltered) should get the same
        empty-state shape the helpers have always returned (Step 5 behavior)."""
        unknown_user_id = seeded_user_id + 9999
        stats = get_summary_stats(unknown_user_id)
        assert stats["total_spent"] == 0
        assert stats["transaction_count"] == 0

        assert get_recent_transactions(unknown_user_id) == []
        assert get_category_breakdown(unknown_user_id) == []


# ------------------------------------------------------------------ #
# database/queries.py — new start_date / end_date filtering            #
# ------------------------------------------------------------------ #

class TestQueryHelpersDateRangeFiltering:
    def test_get_summary_stats_with_date_range_filters_expenses(self, seeded_user_id):
        # Groceries (07-02, 350), Metro (07-03, 150), Electricity (07-05, 2200)
        stats = get_summary_stats(seeded_user_id, start_date="2026-07-01", end_date="2026-07-05")
        assert stats["total_spent"] == pytest.approx(350.00 + 150.00 + 2200.00)
        assert stats["transaction_count"] == 3

    def test_get_recent_transactions_with_date_range_filters_expenses(self, seeded_user_id):
        transactions = get_recent_transactions(
            seeded_user_id, start_date="2026-07-01", end_date="2026-07-05"
        )
        assert len(transactions) == 3
        dates = [tx["date"] for tx in transactions]
        assert dates == sorted(dates, reverse=True), "Recent transactions must stay ordered by date desc"
        assert all("2026-07-01" <= d <= "2026-07-05" for d in dates)

    def test_get_category_breakdown_with_date_range_filters_expenses_and_sums_to_100(self, seeded_user_id):
        breakdown = get_category_breakdown(
            seeded_user_id, start_date="2026-07-01", end_date="2026-07-05"
        )
        names = {item["name"] for item in breakdown}
        assert names == {"Food", "Transport", "Bills"}
        assert sum(item["pct"] for item in breakdown) == 100

    def test_get_summary_stats_with_date_range_no_matches_returns_zero(self, seeded_user_id):
        stats = get_summary_stats(seeded_user_id, start_date="2026-06-01", end_date="2026-06-30")
        assert stats["total_spent"] == 0
        assert stats["transaction_count"] == 0

    def test_get_recent_transactions_with_date_range_no_matches_returns_empty_list(self, seeded_user_id):
        transactions = get_recent_transactions(
            seeded_user_id, start_date="2026-06-01", end_date="2026-06-30"
        )
        assert transactions == []

    def test_get_category_breakdown_with_date_range_no_matches_returns_empty_list(self, seeded_user_id):
        breakdown = get_category_breakdown(
            seeded_user_id, start_date="2026-06-01", end_date="2026-06-30"
        )
        assert breakdown == []

    def test_date_range_boundaries_are_inclusive(self, seeded_user_id):
        """start_date == end_date == an expense's exact date must include it,
        matching BETWEEN semantics used elsewhere in database/queries.py."""
        stats = get_summary_stats(seeded_user_id, start_date="2026-07-02", end_date="2026-07-02")
        assert stats["total_spent"] == pytest.approx(350.00)
        assert stats["transaction_count"] == 1

    def test_get_summary_stats_with_date_range_covering_all_seed_data_matches_unfiltered(self, seeded_user_id):
        filtered = get_summary_stats(seeded_user_id, start_date="2026-07-01", end_date="2026-07-31")
        unfiltered = get_summary_stats(seeded_user_id)
        assert filtered == unfiltered, "A range covering the full seed month must match the unfiltered result"
