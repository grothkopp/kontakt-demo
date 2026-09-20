# Contact demo

## Scope and structure
This is a local workshop app, not a production deployment. Keep changes small.
Use Django templates, SQLite, standard Django authentication and local CSS.
Avoid a frontend framework, extra services, or new dependencies without a concrete need.

- `config/`: settings and URL routing.
- `contacts/models.py`, `views.py`: contact data and request handling.
- `contacts/tests.py`, `contacts/test_*.py`: Django tests.
- `contacts/migrations/`: schema changes; never edit an applied migration.
- `contacts/fixtures/demo.json`: synthetic Anna/Ben demo data.
- `templates/` and `static/`: interface and styling.
- `e2e/` and `.github/workflows/`: browser tests and automation when present.
- `openspec/`: requirements and change artifacts when initialized.

## Plan before implementation
Read the relevant code and tests first. Clarify ambiguous acceptance criteria.
Describe observable behavior and failure cases before implementing a feature.
When a change has OpenSpec artifacts, review its proposal, specs, design and tasks
before coding; keep implementation and artifacts consistent.
Do not install or initialize missing workshop stages as an unrelated side effect.

## Test requirements
Every new or changed feature needs automated tests for its behavior and relevant
negative or boundary cases. For a bug fix, first reproduce the bug with a failing
regression test, then fix it. Never weaken an assertion to obtain a green result.
Use two users for access-control tests. Test filtered as well as unfiltered paths.
Test displayed result counts, empty results, invalid input and authentication
where the change affects them. Add browser coverage for important user journeys
when the E2E suite is available; browser tests complement Django tests.
Use isolated fixtures and deterministic tests; never rely on the developer database.

## Security and data
Scope contact access to the authenticated owner, including filtered requests.
Keep Django authentication, CSRF protection, template escaping and safe redirects.
Demo accounts have public passwords: use synthetic data and local/test environments.
Never commit credentials, databases, logs containing contact data, or local secrets.
Do not introduce deliberate bugs unless explicitly requested for an isolated exercise.

## Dependencies and verification
Use uv, commit `uv.lock` with dependency changes and verify locked installs.
Run after changes:

```sh
uv sync --locked
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

If the E2E backup is present, also run:

```sh
uv sync --locked --group e2e
uv run --group e2e python -m playwright install chromium
uv run --group e2e python manage.py test e2e.browser_tests
```

Report what actually ran and any failures or unverified behavior. A green suite
only proves its assertions, not overall correctness. Review the diff for unrelated
changes. Keep PRs focused, explain behavior and verification, and leave merging
to the human reviewer. Do not silently repair intentional workshop examples.

Write all workshop-facing UI text, documentation, example notes and new specifications in English. Keep test selectors and expected messages consistent with the English UI.
