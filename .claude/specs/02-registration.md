# Spec: Registration

## Overview
Wires up the `/register` route so visitors can actually create a Spendly
account. Right now `register.html` posts to `/register`, but the route
only renders the template — it doesn't accept `POST`, read form data, hash
the password, or write a row to `users`. This step makes account creation
real: validate the form, hash the password with werkzeug, insert the user
via `get_db()`, and start a session so the new user is signed in
immediately after registering. It's the first authenticated action in the
app and the foundation later steps (logout, profile, expenses) build on.

## Depends on
- Step 1 — Database Setup (`users` table, `get_db()`, `init_db()`)

## Routes
- `POST /register` — accept the registration form, validate input, create
  the user, start a session, redirect on success — public
- `GET /register` — unchanged, still renders the empty form — public

If no new routes: N/A — `/register` already exists as a GET route; this
step adds `POST` handling to it, no new endpoints are introduced.

## Database changes
No database changes. The existing `users` table (`id`, `name`, `email`,
`password_hash`, `created_at`) already has everything registration needs —
verified against `database/db.py`.

## Templates
- **Create:** none
- **Modify:** `templates/register.html` — no structural changes needed;
  it already renders `{{ error }}` inside `.auth-card` for failed
  submissions, so validation failures just need the route to pass an
  `error` string back into the template

## Files to change
- `app.py`
  - add `app.secret_key` (required for Flask sessions)
  - change `/register` to `methods=["GET", "POST"]`
  - on `POST`: read `request.form` (`name`, `email`, `password`), validate,
    hash the password, insert into `users`, set `session["user_id"]`,
    redirect to `/`
  - on validation failure or duplicate email: re-render `register.html`
    with an `error` message (200, not a redirect)

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` is already available via Flask.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash` /
  `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server even though the form has `required` attributes
  (name non-empty, valid email, password ≥ 8 characters — matches the
  existing placeholder text "Min. 8 characters")
- Treat duplicate email as a normal validation error shown in the
  existing `.auth-error` block, not a 500 — rely on the `UNIQUE` constraint
  and catch `sqlite3.IntegrityError` as a backup, don't pre-query as the
  only guard
- Don't touch `/login` or session-verification logic — that's a separate
  step

## Definition of done
- [ ] Submitting the register form with valid data creates a row in
      `users` with a hashed (not plaintext) password
- [ ] After successful registration, the browser has a session cookie and
      is redirected to `/`
- [ ] Submitting with an email that already exists re-renders
      `register.html` with an error message and does not create a
      duplicate row
- [ ] Submitting with a password under 8 characters, or a missing
      name/email, re-renders the form with an error and no row is created
- [ ] `GET /register` still renders the empty form with no errors
- [ ] App starts and runs with no errors (`python app.py`)
