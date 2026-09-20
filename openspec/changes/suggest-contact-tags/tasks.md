## 1. Review the proposed contract

- [x] 1.1 Review proposal, design, and both specs with the workshop owner before implementation; record any adjustments to display-only scope, fake-only execution, category meanings, and eval reporting policy.

## 2. Add the provider boundary

- [x] 2.1 Add the note-only provider contract, deterministic offline fake with documented example mappings, and exact output validator for one existing tag or null.
- [x] 2.2 Add service handling for empty notes, abstention, invalid responses, timeouts, and expected provider errors; expose safe result states without raw provider content.
- [x] 2.3 Test the “Empty note”, “Valid abstention”, “Invalid provider response”, “Provider failure”, and “Repeatable demo” scenarios with controlled doubles and no network access.

## 3. Add the owner-only display flow

- [x] 3.1 Add the login-protected, CSRF-protected POST route with owner-scoped lookup before inference and no-cache responses; reuse owner-scoped list context.
- [x] 3.2 Add the per-contact form and transient English result messages to the template, including visible demo labeling and no apply/save action.
- [x] 3.3 Test “Ordinary list view”, “Anonymous request”, “Unsupported method”, and “Missing CSRF token”; use a client with CSRF enforcement for rejection and successful submission.
- [x] 3.4 Test “Foreign or nonexistent contact” for both demo users, assert zero provider calls and no leaked contact details, and test “Stored note is authoritative” with forged form fields and owner-scoped response counts.
- [x] 3.5 Test “Valid suggestion”, “Same tag is suggested”, and “Result lifetime”; reload every contact from the database and compare all fields across success, abstention, error, invalid-output, and rejected-request paths.

## 4. Add inspectable evals

- [x] 4.1 Create and manually review 16 synthetic cases with stable IDs, version, expected tag/null, categories, and development/held-out splits; reserve at least four held-out cases and cover the “Reviewable labeling policy” and “Instruction-only note” scenarios.
- [x] 4.2 Add the offline eval management command using the shared provider and validator, per-case results, split metrics, provider/dataset identity, and documented exit behavior.
- [x] 4.3 Test “Repeated fake run”, “Wrong valid prediction”, and “Invalid input or failed evaluation” using controlled outputs, including N/A denominators and errors counted as failures; do not assert a perfect fake classification score.
- [x] 4.4 Run the dataset through the fake, inspect and document the baseline including held-out failures, and explain why it is not live-model quality evidence. Keep live-provider enablement outside this change and document the later eval, threshold, versioning, and timeout requirements.

## 5. Verify and document the workshop flow

- [x] 5.1 Update README with the suggestion flow, offline demo limitation, eval command, label policy, and links between acceptance scenarios, tests, and evals.
- [x] 5.2 Run `uv run python manage.py test`, `uv run python manage.py check`, and `uv run python manage.py makemigrations --check --dry-run`; run the offline eval command and inspect the output.
- [x] 5.3 Manually review the local template flow with Anna and Ben, including transient results and unchanged saved tags; no browser test framework is required.
- [x] 5.4 Validate the completed change with `npm run openspec -- validate suggest-contact-tags --strict` and review the final diff against the agreed scope.
