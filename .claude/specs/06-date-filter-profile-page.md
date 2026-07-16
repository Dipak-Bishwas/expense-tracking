# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the profile page so a user can narrow the
summary stats, recent transactions, and category breakdown to a specific time
window (This month, Last month, Last 3 months, or All time) instead of always
seeing their entire expense history. The filter is chosen from a dropdown,
submitted as a GET query parameter on the existing `/profile` route, and
reflected back in the URL so the selection is shareable and survives a page
reload.

## Depends on
- Step 1: Database setup (`expenses` table with a `date` column)
- Step 3: Login / Logout (`session["user_id"]` is set on login)
- Step 5: Backend routes for profile page (`database/queries.py` helpers and
  the live `/profile` route this step extends)

## Routes
No new routes. The existing `GET /profile` route is modified to accept an
optional `range` query parameter, e.g. `GET /profile?range=last-month`.

## Database changes
No database changes. `expenses.date` is already stored as `YYYY-MM-DD` text
(see `database/db.py` seed data), which compares correctly against other
`YYYY-MM-DD` strings using standard SQL `BETWEEN` / `>=` / `<=` — no new
columns, tables, or a date library are needed.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter control (a `<select>` inside a `GET` form) above the summary
    stats grid, with options: This month, Last month, Last 3 months, All
    time. The option matching the active range is marked `selected`.
  - Add an empty-state row/message for "Recent transactions" and "Category
    breakdown" when the filtered range has no expenses (distinct from the
    existing all-time empty state, e.g. "No transactions in this period").

## Files to change
- `app.py` — `profile()` reads `request.args.get("range")`, resolves it to a
  `(start_date, end_date)` pair via a small helper, passes the pair to the
  three query functions, and passes the active range key back to the template
  so the dropdown can pre-select it
- `database/queries.py` — add optional `start_date` / `end_date` keyword
  arguments to `get_summary_stats`, `get_recent_transactions`, and
  `get_category_breakdown`; when both are provided, filter with
  `AND date BETWEEN ? AND ?`; when omitted, behave exactly as today (no
  filtering, preserving Step 5 behavior)
- `templates/profile.html` — add the filter dropdown and the two empty-state
  messages
- `static/css/style.css` — style the new filter control using existing CSS
  variables, matching the current form/button conventions
- `static/js/main.js` — add a `DOMContentLoaded` listener that submits the
  filter form when the dropdown value changes (progressive enhancement; a
  visible submit button remains the no-JS fallback)

## Files to create
No new files.

## New dependencies
No new dependencies. Range boundaries are computed with the stdlib
`datetime`/`calendar` modules already available via Python's standard
library.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Passwords hashed with werkzeug (unaffected by this step, listed per
  standing rule)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Date range math must use `YYYY-MM-DD` string boundaries so it composes
  with the existing `date BETWEEN ? AND ?` style used elsewhere in
  `database/queries.py`
- Default to "This month" when the `range` query parameter is missing or
  holds an unrecognized value — never raise an error for a bad value
- The active range must be reflected in the URL (`?range=...`) so it is
  bookmarkable and persists across a page reload
- Query helpers keep opening their own connection via `get_db()` and closing
  it before returning, matching the Step 5 pattern
- Existing callers/tests that invoke the query helpers without date
  arguments must continue to work unchanged (start/end stay optional,
  default `None` = no filtering)

## Definition of done
- [ ] Visiting `/profile` with no query string defaults to "This month" and
      the dropdown shows "This month" as selected
- [ ] Logging in as the seed user (demo@spendly.com / demo123) with the
      default "This month" filter shows all 8 seed transactions and
      ₹346.24 total (seed data falls in the current month)
- [ ] Selecting "Last month" updates the URL to `?range=last-month` and shows
      ₹0.00 total, 0 transactions, and the empty-state message (seed data has
      no expenses in the prior month)
- [ ] Selecting "All time" shows all 8 transactions and ₹346.24 total,
      matching Step 5's unfiltered totals
- [ ] Selecting "Last 3 months" includes the seed data and matches the "This
      month" totals for this dataset
- [ ] Category breakdown percentages still sum to 100% whenever the filtered
      range has expenses
- [ ] Visiting `/profile?range=bogus-value` does not error and falls back to
      the "This month" default
- [ ] Reloading the page after selecting a filter keeps the same filter
      selected (state comes from the URL, not client-side only)
