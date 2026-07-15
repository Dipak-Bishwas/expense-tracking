# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Spendly" — a Flask expense tracker built as a step-by-step learning project. The front-end shell (landing, auth pages, legal pages) is built out; the backend is a scaffold with most logic left as placeholders for the student to implement. Comments in the code mark the intended build order (e.g. `app.py` placeholder routes are annotated "Step 3", "Step 4", "Step 7", etc.) — when adding backend features, follow that same incremental, one-feature-per-step style rather than implementing everything at once.

## Commands

Run from the repo root, on Windows.

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python app.py          # runs the dev server on http://localhost:5001 (debug=True)

pytest                 # run tests (no test files exist yet — add them under a tests/ dir)
pytest path/to/test_file.py::test_name   # run a single test
```

There is no build step, linter, or formatter configured in this repo.

## Architecture

Standard Flask app, single module, no blueprints:

- **`app.py`** — the entire Flask app. All routes live here as `@app.route` view functions. Currently split into two groups:
  - Implemented GET routes that just `render_template(...)`: `/`, `/register`, `/login`, `/terms`, `/privacy`.
  - Placeholder routes that return a bare string ("coming in Step N"): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`. These are stubs — replace the string return with real logic (template render + DB calls) as each feature is built, don't add unrelated scaffolding while doing so.
  - The `login`/`register` templates already POST to `/login` and `/register`, but those routes don't yet accept `methods=["POST"]` or read `request.form` — that wiring is still to be done.

- **`database/db.py`** — intentionally empty scaffold. Per its header comment, this file is meant to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables with `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample dev data). No ORM is used — expect raw SQLite via the stdlib `sqlite3` module. The DB file (`expense_tracker.db`) is gitignored and created locally.

- **Templates (`templates/`)** — Jinja2, all extend `base.html`, which defines the shared nav/footer and named blocks: `title`, `head`, `content`, `scripts`. New pages should extend `base.html` and only fill in `content` (and `title`) unless they need extra `<head>`/script content.

- **`static/css/style.css`** — single stylesheet, no preprocessor/build step, organized as flat sections in page order (navbar → hero → stats/progress → buttons → features → CTA → auth forms → footer → legal pages → modal). Class names are BEM-ish but not strictly namespaced (e.g. `.hero-title`, `.auth-card`, `.btn-submit`); match the existing naming style for new components instead of introducing a new convention.

- **`static/js/main.js`** — vanilla JS, no bundler/framework. Currently just wires up the "How it works" video modal on the landing page. Add new behavior as additional `DOMContentLoaded` listeners in the same file unless it grows large enough to warrant splitting.

## Notes

- No authentication, sessions, or password hashing exist yet — `/login` and `/register` render forms only. When implementing, use `werkzeug.security` (`generate_password_hash`/`check_password_hash`), which is already a dependency via Flask.
- Currency is INR (₹), not USD — this app targets Indian users (footer copy: "Track every rupee", example email `nitish@example.com`). Use ₹ for any amounts, inputs, or formatting added to templates/JS/backend, and keep new UI copy consistent with that framing.
