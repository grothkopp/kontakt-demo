# Contact demo

This is a local workshop application, not a production deployment.
Keep the implementation small: Django templates, SQLite, standard Django auth.
Use uv for dependencies and commit uv.lock when dependencies change.
Run `uv run python manage.py test` and `uv run python manage.py check` after changes.
Preserve per-user contact isolation and CSRF protection. Do not introduce intentional
bugs unless a future task explicitly requests an isolated teaching example.
The main baseline has no filter. Workshop branches add separate features and checks.
Demo accounts are public fixtures; do not use real data or deploy them publicly.

Write all workshop-facing UI text, documentation, example notes and new specifications in English. Keep test selectors and expected messages consistent with the English UI.

## Tests

- Use Django's built-in `TestCase` and test client; keep app tests in
  `contacts/tests.py`. Avoid adding a test framework for coverage Django already provides.
- Add or extend tests for behavior changes. For bug fixes, first reproduce the bug
  with a regression test, then verify that the test passes with the fix. Cover the
  class of error rather than only the reported example; do not weaken assertions
  or skip failing tests to make CI pass.
- For contact queries and filters, test multiple users with overlapping tags,
  every supported tag, empty accounts, no matches, and empty or unknown filter
  values. Assert the expected contacts and absence of other users' data in both
  the template context and rendered page.
- Preserve coverage for authentication, safe redirects, and CSRF. Use
  `Client(enforce_csrf_checks=True)` when testing CSRF protection.
- Keep test data fictional and deterministic. Use the demo fixture for workshop
  flows and `setUpTestData` for focused scenarios; never rely on local `db.sqlite3`.
- Run `uv run python manage.py test` and `uv run python manage.py check` after
  changes. For model or migration changes, also run
  `uv run python manage.py makemigrations --check --dry-run` and include required
  migrations. Report commands and results, including any checks that could not run.
- Explicitly requested test-only workshop stages may leave regression tests
  failing. Report the expected failures and keep the implementation unchanged
  until a fix is requested; normal completed fixes must pass the checks.

## Documentation

- Keep `README.md` as the entry point for setup, demo accounts, reset instructions,
  checks, and project structure. Update it in the same change when these details
  or documented behavior change.
- Distinguish the `main` baseline from branch-specific workshop features. Describe
  only implemented behavior and make clear that backup branches are independent,
  not cumulative; do not imply every branch includes every workshop stage.
- Keep commands consistent with uv, `.python-version`, and `uv.lock`. Document
  dependency, migration, or fixture steps when a change requires them.
- Explain non-obvious constraints and decisions concisely. Avoid duplicating code
  or adding separate documents for small changes. Documentation-only changes do
  not need new automated tests.
- Keep shared agent rules in `AGENTS.md`; `CLAUDE.md` references this file.

## Commits and pull requests

- Keep changes focused on one feature or fix and exclude unrelated edits and local
  artifacts such as databases, generated secrets, and virtual environments.
- Use semantic commit messages and PR titles: `type: short imperative summary`,
  with an optional scope, for example `fix: preserve contact ownership` or
  `test: cover tag filter isolation`. Use `feat`, `fix`, `test`, `docs`, `ci`,
  `refactor`, or `chore` as appropriate.
- Use `sg/` for new branch names unless a different name is requested. Preserve
  the workshop's separation between the baseline and feature branches.
- PR descriptions should explain the problem, resulting behavior, relevant test
  coverage, and validation results. Include setup or migration steps and known
  limitations when relevant; keep the title and description aligned with the final diff.
- Keep the Django workflow triggered by `pull_request` so a PR branch push runs
  it once; do not add a duplicate `push` trigger. Verify referenced action releases
  exist when adding or updating CI actions.
- Before declaring a PR ready, check the latest commit's CI results. Clearly label
  intentionally failing test-only workshop stages instead of claiming they pass.
- Address actionable review feedback with regression coverage where appropriate.
  When replying, cite the fix commit and validation results; resolve a thread
  only after its concern has been addressed and verified.
