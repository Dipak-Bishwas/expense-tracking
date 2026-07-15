# Spec: Login and Logout

## Overview
Wires up the `/login` route and turns the `/logout` placeholder into a real
route. Right now `login.html` posts to `/login`, but the route only accepts
`GET` and renders the template — it doesn't read form data, look up the
user, or verify the password. This step makes signing in real: read the
submitted email/password, look up the user by email, verify the password
with werkzeug, and start a session on success (mirroring the session set up
during registration). `/logout` moves from a placeholder string to clearing
that session and sending the user back to the landing page. Together with
registration, this completes the authentication loop that later steps
(profile, expenses) will require a logged-in session for.

## Depends on
- Step 1 — Database Setup (`users` table, `get_db()`)
- Step 2 — Registration (`app.secret_key`, session pattern: `session["user_id"]`,
  `session["user_name"]`, and seeded/registered users to log in as)

## Routes
- `POST /login` — accept the login form, verify credentials, start a
  session, redirect on success — public
- `GET /login` — unchanged, still renders the empty form — public
- `GET /logout` — clear the session and redirect to `/` — logged-in
  (visiting while already logged out is a harmless no-op redirect, not an
  error)

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`,
`password_hash`, `created_at`) already has everything login needs —
verified against `database/db.py`.

## Templates
- **Create:** none
- **Modify:** `templates/login.html` — no structural changes needed; it
  already renders `{{ error }}` inside `.auth-card` for failed submissions
  (same pattern as `register.html`), so validation failures just need the
  route to pass an `error` string back into the template

## Files to change
- `app.py`
  - change `/login` to `methods=["GET", "POST"]`
  - on `POST`: read `request.form` (`email`, `password`), look up the user
    by email via `get_db()`, verify the password with
    `check_password_hash`, set `session["user_id"]` and
    `session["user_name"]`, redirect to `/`
  - on invalid credentials: re-render `login.html` with a single generic
    error message (200, not a redirect) — don't reveal whether the email
    exists or the password was wrong
  - replace the `/logout` placeholder: clear the session (`session.clear()`)
    and redirect to `/`

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` (`check_password_hash`) is already
available via Flask.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords verified with werkzeug (`check_password_hash`) — never compare
  plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use one generic error message ("Invalid email or password.") for both
  "no such user" and "wrong password" cases — don't let the error reveal
  which one it was
- Don't touch `/register` or the `/profile`, `/expenses/*` placeholder
  routes — those are separate steps
- Don't add session-aware nav (e.g. showing "Logout"/"Profile" links in
  `base.html`) — registration already established sessions without
  touching nav, and that UI work belongs to the Profile step; logout can
  be exercised directly via `GET /logout`

## Definition of done
- [ ] Logging in with a valid seeded account (`demo@spendly.com` /
      `demo123`) sets a session cookie and redirects to `/`
- [ ] Logging in with a wrong password re-renders `login.html` with a
      generic error and no session is set
- [ ] Logging in with an email that doesn't exist re-renders `login.html`
      with the same generic error (indistinguishable from a wrong
      password)
- [ ] Visiting `/logout` after logging in clears the session and redirects
      to `/`; visiting a protected action afterward behaves as logged out
- [ ] `GET /login` still renders the empty form with no errors
- [ ] App starts and runs with no errors (`python app.py`)
