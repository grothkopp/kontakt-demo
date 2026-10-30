## 1. Suggestion service and provider contract

- [ ] 1.1 Select the live demo provider/model, verify its current API documentation, and record the adapter and environment configuration in the design; keep one provider integration.
- [ ] 1.2 Add Django tests for the result contract: all three tags, insufficient evidence, invalid status/tag combinations, missing or oversized explanations, and provider errors.
- [ ] 1.3 Implement the suggestion service and validated result types, sending only company, role, and note with fixed tag definitions and instructions to abstain on weak or conflicting evidence.
- [ ] 1.4 Implement environment-based provider configuration, a 15-second timeout without automatic retries, and unavailable behavior when configuration is missing. Add any required dependency with uv and commit the updated lockfile.

## 2. Secure request and review flow

- [ ] 2.1 Add tests for authenticated, POST-only, CSRF-protected suggestion requests; foreign/missing contact IDs must fail before any provider invocation. Assert selected-contact-only payloads and no saved-tag changes.
- [ ] 2.2 Add the owner-scoped request route and view, bounded per-contact session state, result tokens, 15-minute expiry, and POST/redirect/GET. Replace previous pending results on every new request, including failures.
- [ ] 2.3 Add English Suggest tag controls and result panels to contact templates, with escaped explanation text and distinct suggested, already-matching, insufficient-evidence, and unavailable states. Preserve the active filter using local redirects.

## 3. Apply and dismiss

- [ ] 3.1 Add tests showing that Apply changes only the selected owner's tag and Dismiss makes no contact change or provider call; verify ownership, POST-only behavior, and CSRF for both actions.
- [ ] 3.2 Add tests for absent, forged, foreign-session, superseded, replayed, and expired result tokens, plus changes to input fields or current tag between request and Apply.
- [ ] 3.3 Implement Apply using the server-stored tag, snapshot validation, and a conditional update; consume accepted results and reject stale results with a request-again message.
- [ ] 3.4 Implement Dismiss and filter-preserving redirects. Verify accepted changes recalculate totals, remove rows that no longer match the filter, and provide a confirmation.

## 4. Browser coverage and evaluation

- [ ] 4.1 Extend the existing Playwright live-server tests with a fake provider to cover request/review/apply and request/dismiss, unchanged tags before acceptance, persisted tags after reload, and no extra provider call on refresh.
- [ ] 4.2 Add browser coverage for active-filter changes after Apply and unavailable/insufficient evidence without an Apply action; verify other users' contacts remain private.
- [ ] 4.3 Add a small fictional evaluation dataset for Customer, Partner, Lead, sparse information, conflicting relationships, and instruction-like notes, recording acceptable tag/abstention and evidence expectations.
- [ ] 4.4 Provide an explicitly invoked live evaluation command or documented procedure that reports classification/abstention and groundedness separately; do not run live provider calls in the default test suite or CI.

## 5. Documentation and verification

- [ ] 5.1 Update README with this branch's AI flow, note-as-history scope, tag definitions, provider environment variables, dependency setup, unavailable behavior, tests, and optional live evaluation instructions. Document that ordinary list/filter use does not call AI.
- [ ] 5.2 Confirm the existing PR-only workflow runs the new Django and Playwright tests with fakes and no provider secrets; retain one workflow run per PR push.
- [ ] 5.3 Run `uv run python manage.py test`, `uv run python manage.py check`, and `uv run python manage.py makemigrations --check --dry-run`; verify all tests pass and no schema migration is introduced.
- [ ] 5.4 Validate the OpenSpec artifacts, review the final diff for isolation and scope, and update the PR description with behavior and actual validation results. Check the latest commit's CI before declaring the PR ready.
