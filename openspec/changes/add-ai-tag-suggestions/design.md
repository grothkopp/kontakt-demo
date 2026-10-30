## Context

The workshop app uses Django templates, SQLite, standard authentication, and a contact list with a GET tag filter. Contacts have a required Customer, Partner, or Lead tag and one optional 240-character `note`. The user confirmed that this note is the complete description/history for the demo. There is no general contact editing UI or existing AI integration.

The new flow must preserve the recently tested owner isolation. Existing Django tests and a Playwright live-server test run in one PR workflow. No provider account or model has been selected.

## Goals / Non-Goals

**Goals:**

- Request a suggestion for one owned contact, review an explanation, and explicitly apply or dismiss it.
- Use existing fields and a small provider adapter, with deterministic tests and no paid CI calls.
- Keep the current tag unchanged on request, dismissal, insufficient evidence, and failure.

**Non-Goals:**

- Separate history storage, external enrichment, multi-label or new tags, automatic tagging, general editing, bulk operations, background jobs, durable suggestion audit history, or production infrastructure.

## Decisions

### 1. Existing note and minimal input

Send company, role, and note for the selected contact. Omit name, email, current tag, user identity, and other contacts: these are unnecessary for the relationship decision, and the current tag could bias the output. No database migration is needed. A dated interaction model would exceed the agreed demo scope.

Use explicit prompt definitions: Customer means evidence of purchasing/using a service or an established client relationship; Partner means evidence of an established collaboration or referral relationship; Lead means evidence of a prospective relationship or expressed interest without an established customer/partner relationship. A title, company name, or absence of history is not sufficient by itself. When relationships overlap without a clear primary relationship, return insufficient evidence instead of assuming a priority. Notes are untrusted data, not instructions; the model receives no tools or retrieval access.

### 2. Small server-side provider boundary

Add a service such as `contacts/tag_suggestions.py` exposing a single suggestion operation with a typed, validated result. Implement one real provider adapter, selected and documented at implementation time, plus an injected fake for tests. Avoid a multi-provider framework. Credentials and model selection are environment configuration; credentials never enter templates or Git. The README names the exact configuration once the adapter is selected.

The result contract has status `suggested` with one existing tag and a nonempty explanation of at most 400 characters, or status `insufficient_evidence` with no tag and a short reason. Reject unknown tags, inconsistent status/tag combinations, missing explanation, oversized output, and malformed responses. Provider refusal and transport errors produce an unavailable result, never a fallback tag. Use a 15-second request timeout and no automatic retries for the demo.

Without configuration, listing and filtering still work; a suggestion request returns an English unavailable message without contacting a provider. CI patches the service boundary and needs no credentials. Real-provider quality checks are a separate, explicitly invoked activity.

### 3. Django form actions and temporary session state

Add authenticated, POST-only routes for requesting, applying, and dismissing a suggestion under a contact ID. Use standard CSRF-protected forms and POST/redirect/GET so refresh does not repeat an AI call. Resolve the contact with both primary key and owner before inspecting pending state or calling the provider; foreign and missing contacts return the same 404.

Render a Suggest tag button beside each contact and, after a successful request, a panel showing the suggested label, explanation, Apply suggestion, and Dismiss. Escape all generated text. Insufficient evidence and failure panels have no Apply button. A suggestion equal to the current tag is displayed as already matching and also has no Apply button. The existing tag remains visible throughout.

Store at most one pending result per contact in the server-side session, keyed by contact ID. Include a random result token, creation time, owner ID, the current tag, and a fingerprint of the input fields. Expire results after 15 minutes. A new request invalidates the previous result even if the new request fails. Hidden form fields contain the result token and filter value, not an authoritative tag or explanation.

The server rechecks ownership, token, expiry, and contact snapshot on Apply. A stale result is cleared with a message asking the user to request another suggestion. A valid Apply uses a conditional update against the saved snapshot so intervening edits cannot be overwritten; then consume the pending result. Dismiss consumes the matching result without writing to Contact or calling the provider. Reject missing, tampered, replayed, or superseded tokens without modifying any contact. A database model for suggestions would add unnecessary persistence for this ephemeral flow.

Preserve the active tag query through actions using a locally constructed contacts URL, never an arbitrary redirect URL. After Apply, recalculate list and summary data. If the changed tag no longer matches the active filter, the contact disappears from that list and an English confirmation explains the update.

### 4. Tests and evaluation

Extend Django coverage with injected provider responses for all three tags, insufficient evidence, already-matching tags, errors, and invalid output. Assert request payload isolation, no writes before Apply, authorization and CSRF on each action, and rejection of stale/tampered results. Include multiple users and contacts with overlapping tags.

Extend the existing Playwright suite with a controlled provider response to test Suggest → review → Apply and Suggest → Dismiss, saved-tag behavior after reload, filter behavior after Apply, and an unavailable/insufficient state. Reuse Django's isolated live server and the existing PR-only workflow; do not call an external model in CI.

Create a small fictional evaluation set containing clear Customer/Partner/Lead cases, sparse descriptions, contradictory relationships, and instruction-like notes. Store expected tag or abstention plus supporting evidence, not exact generated sentences. An optional live evaluation reports correct classification/abstention and whether the explanation is supported, separately from deterministic application tests.

## Risks / Trade-offs

- Ambiguous relationship language or hallucinated explanations → permit abstention, define tag semantics, evaluate groundedness, and require explicit acceptance.
- Notes attempting to redirect the model → separate instructions from input data, supply no tools, validate output, and test adversarial examples. Prompt text alone is not a security boundary.
- Cross-user disclosure or unauthorized updates → owner-scoped reads before provider calls and again on Apply/Dismiss, with direct-ID regression tests.
- Slow/unavailable provider → bounded synchronous timeout and a recoverable error. A worker queue is unnecessary for the workshop's small request volume.
- Stale browser tabs or repeated form submissions → session-bound result tokens, expiry, snapshot validation, and consumption after use. This is a local demo, not a distributed concurrency guarantee.
- Model quality varies → deterministic CI verifies application contracts; separate live evaluations assess suggestion quality without pretending mocks measure it.

## Migration Plan

No contact schema or fixture migration. Add provider dependency only if needed, using uv and committing the lockfile. Document environment configuration and the existing browser installation steps. Deploy only as a local workshop branch. Rollback removes the suggestion UI/routes/adapter and session keys; already accepted tags remain ordinary contact data and must not be silently reverted.

## Open Questions

- Which provider/account and model should the live demo use? Resolve when implementing the real adapter, verify that provider's current API, and document required environment variables. The UI contract, fake-provider tests, and lack-of-configuration behavior are independent of that choice.
