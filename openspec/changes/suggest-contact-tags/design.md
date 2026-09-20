## Context

The app has one owner-scoped contact list, standard Django authentication and CSRF middleware, a 240-character note, and a single tag chosen from customer, partner, and lead. There is no editing flow or AI integration. The workshop needs a small feature whose access guarantees can be tested independently of suggestion quality.

## Goals / Non-Goals

**Goals:** Display an explicitly requested suggestion for an owned contact; preserve all contact data; provide offline repeatability, failure tests, and inspectable example-based evals.

**Non-Goals:** Saving or applying suggestions, new tags, multi-tag classification, live provider integration, schema changes, JavaScript infrastructure, background processing, CI, or public deployment.

## Decisions

### Request and ownership boundary

Add a POST-only `/contacts/<int:pk>/suggest-tag/` route, protected by login, CSRF, and `never_cache`. Resolve the contact using both its primary key and `owner=request.user` before reading its note for the provider. Missing and foreign contacts return 404. The form carries only CSRF data; the route identifies the contact. Ignore client-supplied notes, owner IDs, or current tags.

After a successful lookup, render the existing list template with the usual owner-scoped contacts and one transient result keyed to the selected contact. Reuse list-context preparation to preserve counts and isolation. A plain GET of the list clears the result. A refresh of the POST can repeat an offline calculation but cannot change data. This keeps the flow smaller than a JSON API, JavaScript interaction, or persisted suggestion history.

### Provider and output contract

Use a small replaceable Python callable accepting only the stored note and returning exactly `{"tag": "customer"}`, `{"tag": "partner"}`, `{"tag": "lead"}`, or `{"tag": null}`. Validate the exact shape, type, and vocabulary in application code before rendering. Never render raw provider output or exception messages. Derive display labels from Contact.Tag and use ordinary template escaping. No generated explanation or confidence score is needed.

The default provider is a deterministic offline fake, clearly labeled in the UI as a demo. Use a few documented fixed note-to-result examples and abstain for unmatched notes; this is a test double, not a classifier quality claim. Use injected doubles for error and malformed-output tests. Empty or whitespace-only notes bypass the provider.

Handle timeout and expected provider-service errors with a retryable message; malformed output gets the same safe fallback. Distinguish these from valid abstention. The fake does no network I/O or sleeps, so there is no runtime network timeout to implement now. Any future live adapter must enforce a total five-second call budget, including retries, at its transport boundary before being enabled. Timeout handling is tested now using a double that raises a timeout, without adding threads or timers to this demo.

### Transient display only

Show “Tag vorschlagen” beside the note, and show the validated suggestion separately from the persisted tag. Show “Kein eindeutiger Vorschlag” for abstention and a German retry message for failure. A suggestion matching the current tag is still a valid result. There is no Apply button, save call, suggestion database field, session persistence, or shared result cache. Names, email addresses, company, current tag, owner identifiers, and other contacts are never passed to the provider.

### Eval design and category policy

Create 16 synthetic cases in a checked-in JSON dataset with stable IDs, note, expected tag or null, category, and split (development or held-out). Keep at least four held-out cases, not used in the fake's mapping or prompt development. Labels are manually reviewed before implementation. Interpret customer as explicit current purchase/use of our offering, partner as explicit collaboration/partnership, and lead as explicit commercial interest without purchase. Mere acquaintance, negated evidence, conflicting relationships, and instruction-only notes warrant abstention; do not infer relationships from a person's role or company.

Add an offline `uv run python manage.py eval_tag_suggestions` command using the same provider and output validator as the app. Report each case's expected and actual result and separate classification accuracy on labeled cases, abstention accuracy on null cases, instruction-case failures, and invalid/error counts, grouped by split. Record dataset version and provider identifier; future live runs also need model and prompt versions. Treat errors as failures, not abstention, and show N/A for empty metric denominators.

The fake establishes a reproducible baseline and demonstrates the runner; low held-out scores are expected and must remain visible. The command exits nonzero for invalid dataset, invalid output, or provider errors; semantic mismatches appear in the report rather than preventing the workshop from running. Unit tests check scoring with controlled outputs, not a hard-coded perfect fake score. Live-model thresholds and repeated-run policy require a future reviewed proposal; no live provider is enabled by this change. A general eval framework or model-based judge would add unnecessary scope.

## Risks / Trade-offs

- Fake-provider scores could be mistaken for model quality → label provider and report mode explicitly, include held-out cases, and document the limitation.
- Notes can contain instructions → treat notes as untrusted evidence, validate outputs, include instruction cases in evals; access control stays entirely in Django.
- Valid tags can still be wrong → display only, allow abstention, and evaluate semantics independently of schema checks.
- Synchronous live calls could block requests later → keep live integration out of scope and require the bounded transport timeout before adding it.
- A small dataset is not broad quality evidence → report counts and per-case outcomes, not only aggregate percentages.

## Migration Plan

No database migration or new dependency is anticipated. Implement locally, run the existing checks plus new tests and offline evals, and review the template flow with demo accounts. Rollback consists of reverting the route, provider, template, tests, eval assets, and documentation; contact data never changes. If implementation unexpectedly needs dependencies, use uv and commit uv.lock.

## Open Questions

No implementation-blocking question remains for this proposed scope. Display-only behavior, fake-only execution, the category policy, and the eval reporting policy are proposed decisions for human review before implementation. A live provider choice, live quality thresholds, and an explicit apply workflow are deferred to separate changes.
