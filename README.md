# kontakt.

This demo repository accompanies **Quality & Observability in Agentic Engineering**,
a workshop by **Stefan Grothkopp** at [Digitale Leute School](https://school.digitale-leute.de/).
We use a small contact app to explore requirements, automated tests, CI workflows,
evals and code review. Clone the repository to follow along live or revisit it later.

- [Digitale Leute](https://www.digitale-leute.de/)
- [Stefan Grothkopp](https://grothkopp.com/)
- [LinkedIn](https://www.linkedin.com/in/grothkopp/)

Python 3.13, Django 5.2, SQLite and uv. Server-rendered templates and local CSS.
The workshop UI, documentation, fixture notes and test expectations are in English.
Names of fictional people and companies remain unchanged.

## Clone and start

```sh
git clone https://github.com/grothkopp/kontakt-demo.git
cd kontakt-demo
uv sync --locked
uv run python manage.py migrate
uv run python manage.py loaddata demo
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/. Repository access is required to clone a private repository.

| Username | Password | Contacts | Customers |
| --- | --- | ---: | ---: |
| anna | Workshop-2026! | 3 | 1 |
| ben | Workshop-2026! | 3 | 2 |

These are intentionally public demo credentials, shown on the sign-in page.
Both accounts are regular Django users without admin privileges. All data is fictional.
The app is intended for local workshops, not production deployment.

## App and workshop stages

The baseline on `main` includes Django sign-in/sign-out, per-user contact lists,
summary counts, tags and notes. It has no contact editing, public API or AI feature.
The filter PR adds filtering. Separate backup branches provide CI, regression tests,
project rules, browser tests and OpenSpec. Backups are independent, not cumulative.
See the current branch's files and pull request for its exact scope.

## Data and reset

Schema migrations are in `contacts/migrations/`. The fixture in
`contacts/fixtures/demo.json` contains two users with hashed passwords and six contacts.
Load it explicitly after migrating; migrations do not create demo accounts automatically.

Run `uv run python manage.py loaddata demo` to restore the fixture records, including
passwords and English notes. This overwrites those records but does not remove any
additional records. After updating an existing checkout, run migrations and reload
the fixture to see translated notes in your local database.

For a complete local reset, stop the server, remove your local `db.sqlite3`, then
run migrations and load the fixture again. SQLite files, the virtual environment
and the generated local Django secret are excluded from Git.

## Checks

```sh
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

Tests use an isolated database and fixture data. The baseline tests cover sign-in
requirements, user isolation, authentication and CSRF, invalid credentials, safe
redirects and the empty state. The filter branch adds regression tests for every
tag, ownership isolation, result counts, and unchanged account summaries.

### Browser tests on the filter branch

The Playwright suite uses headless Chromium and Django's temporary test database
and live server. It creates synthetic accounts and contacts; no running development
server or loaded demo database is needed.

```sh
uv sync --locked
uv run playwright install chromium
uv run python manage.py test e2e.contact_filter
```

On Linux, use `uv run playwright install --with-deps chromium` to also install
browser system dependencies. Re-run browser installation after Playwright upgrades.
CI runs both the fast Django suite and this separate browser suite.

Browser tests sign in through the UI and cover every tag across multiple owners,
shared tags, empty accounts, zero/one/multiple matches, and displayed counts. They
also check reload persistence, the Reset link, All tags, and sign-in redirects
from filtered URLs. Browser tests are explicitly selected with the command above;
the default Django test command continues to run the fast suite.

## Project structure

- `contacts/models.py`: contacts and their owners.
- `contacts/views.py`: authenticated contact list.
- `contacts/tests.py`: Django tests.
- `e2e/contact_filter.py`: Playwright browser tests for the filter branch.
- `config/urls.py`: contacts, sign-in and sign-out routes.
- `templates/` and `static/`: server-rendered interface and styling.
- `contacts/fixtures/demo.json`: repeatable synthetic demo data.

Use uv for Python dependencies. An optional external environment can be selected
with `UV_PROJECT_ENVIRONMENT` when the checkout lives inside a notes workspace.
The default `.venv` is suitable for normal standalone clones.
