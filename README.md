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

This branch adds **display-only tag suggestions**. Click **Suggest tag** next to a
contact's note to see a transient suggestion, abstention, or retryable error.
Requests use authenticated, CSRF-protected POSTs and look up the contact by its
owner before passing only the stored note to the provider. No contact fields are
saved, and a fresh visit to the list clears the result.

The UI labels this as an **offline demo**. Its deterministic fake recognizes six
fixed example notes and abstains for other notes, including the baseline fixtures.
There is no live AI service, API key, generated explanation, or apply action.

```sh
uv run python manage.py eval_tag_suggestions
```

See [the eval guide](evals/README.md) for example notes, label meanings, acceptance
scenario/test links, the observed baseline, and prerequisites for future live-model
evaluation. Fake results demonstrate the eval machinery, not live-model quality.

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
redirects and the empty state. The filter branch adds a happy-path filter test.

## Project structure

- `contacts/models.py`: contacts and their owners.
- `contacts/views.py`: authenticated contact list.
- `contacts/tests.py`: Django tests.
- `config/urls.py`: contacts, sign-in and sign-out routes.
- `templates/` and `static/`: server-rendered interface and styling.
- `contacts/fixtures/demo.json`: repeatable synthetic demo data.

Use uv for Python dependencies. An optional external environment can be selected
with `UV_PROJECT_ENVIRONMENT` when the checkout lives inside a notes workspace.
The default `.venv` is suitable for normal standalone clones.

## OpenSpec (workshop backup)

Requires Node.js >=20.19. `.nvmrc` selects 20.20.2 for nvm users.
The app remains Python/Django; npm is only used for the OpenSpec CLI.

```sh
# Optional, if nvm is installed:
nvm use
npm ci
npm run openspec -- --version
npm run openspec -- list
```

OpenSpec **1.13.1** is pinned locally in `package-lock.json`. Initialization and
project context are committed in `openspec/config.yaml`, with agent integrations
in the repository. Restart your coding agent after checkout to load its commands
and skills. No global installation or repeated initialization is needed.

Start with this short prompt in Claude Code:

```text
/opsx:explore I'd like to add AI-powered tag suggestions based on a contact's notes.
Suggestions should only be available for the user's own contacts and must not change
anything automatically. Let's explore a simple approach that we can use to demonstrate
specs, tests and evals in the workshop.
```

Then use `/opsx:propose` to create the change. Review `proposal.md`,
`specs/<capability>/spec.md`, `design.md` and `tasks.md` under
`openspec/changes/<change>/` before implementing anything. This branch includes
the `suggest-contact-tags` artifacts and their offline implementation.

```sh
npm run openspec -- validate <change> --strict
```

Structural validation does not replace a review of the requirements. After review,
use `/opsx:apply`; archive the change only after verifying the implementation.
This backup starts from `main`, without the filter from the exercise PR.
