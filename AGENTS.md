# Contact demo

This is a local workshop application, not a production deployment.
Keep the implementation small: Django templates, SQLite, standard Django auth.
Use uv for dependencies and commit uv.lock when dependencies change.
Preserve per-user contact isolation and CSRF protection. Do not introduce intentional
bugs unless a future task explicitly requests an isolated teaching example.
The main baseline has no filter. Workshop branches add separate features and checks.
Demo accounts are public fixtures; do not use real data or deploy them publicly.

Write all workshop-facing UI text, documentation, example notes and new specifications in English. Keep test selectors and expected messages consistent with the English UI.

## Tests

- Run `uv run python manage.py test` and `uv run python manage.py check` after changes. Report the results and any checks that could not be run.
- Add or adapt tests for behavior changes and bug fixes. For bug fixes, first confirm that a regression test fails for the reported reason, then verify it passes with the fix.
- Test the underlying behavior across relevant cases rather than only the reported example. Cover multiple users, shared tag values, empty accounts, and zero, one, and multiple results where applicable. Derive tag cases from the model choices.
- Preserve coverage for authentication, per-user data isolation, and CSRF protection. Check rendered output as well as result membership when user-visible data or counts change.
- Keep tests deterministic and independent of execution order or external services. Use synthetic data; create dedicated test data when demo fixtures do not cover the required cases.
- Do not weaken assertions, skip failing tests, or mark regressions as expected failures to make CI pass. Commit intentionally failing tests only when explicitly requested for a workshop step, and explain the expected failures.

## Documentation

- Update the relevant documentation when setup commands, dependencies, demo behavior, or workshop steps change. Keep examples consistent with the implemented English UI.
- Clearly identify branch-specific features and prerequisites so workshop instructions do not imply that every feature exists on the main baseline.
- Keep instructions concise and reproducible. Verify documented commands where practical, and distinguish implemented behavior from planned exercises or known limitations.
- Use only public demo credentials and synthetic contact data in examples. Never include secrets, real personal data, or instructions to deploy the demo accounts publicly.

## Pull requests

- Keep each PR focused on one feature, fix, or explicit workshop step. Avoid unrelated refactoring and dependency changes.
- Use semantic commit messages and PR titles, such as `feat:`, `fix:`, `test:`, `docs:`, or `ci:`.
- Describe the problem, the resulting behavior, and the validation performed. Call out known limitations and any intentionally failing workshop tests.
- Review the final diff and CI results before declaring a PR ready. Include `uv.lock` whenever dependencies change, and exclude generated files, local databases, and secrets.
- Address review findings with regression coverage where appropriate. When asked to reply to review comments, explain the change and validation, and resolve a thread only after its finding is addressed and verified.
- Do not merge a PR or publish the application unless explicitly requested.
