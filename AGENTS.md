# Contact demo

This is a local workshop application, not a production deployment.
Keep the implementation small: Django templates, SQLite, standard Django auth.
Use uv for dependencies and commit uv.lock when dependencies change.
Run `uv run python manage.py test` and `uv run python manage.py check` after changes.
Preserve per-user contact isolation and CSRF protection. Do not introduce intentional
bugs unless a future task explicitly requests an isolated teaching example.
The baseline has no tag filtering, CI workflows, or browser test suite yet.
Demo accounts are public fixtures; do not use real data or deploy them publicly.
