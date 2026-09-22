## 1. Pending suggestion state

- [x] 1.1 Add the TagSuggestion model and additive migration with UUID, contact, requester, proposed tag, explanation, creation timestamp, and contact fingerprint; enforce one pending record per requester/contact.
- [x] 1.2 Implement snapshot/fingerprint and 15-minute expiry helpers; test changed fields, boundary expiry, replacement, and cascade deletion using synthetic contacts.

## 2. OpenRouter integration

- [x] 2.1 Add optional OPENROUTER_API_KEY and OPENROUTER_MODEL settings and a small HTTP adapter; add any dependency through uv and update uv.lock. Confirm the configured model supports the documented structured-output contract.
- [x] 2.2 Build the classification prompt from company, role, current tag, note, and model tag choices; include tag definitions, precedence, abstention, and treatment of field text as data.
- [x] 2.3 Implement the OpenRouter request with bearer authentication, required schema support, a 15-second timeout, bounded response size, and no automatic retries; validate tag/reason, completion status, explanation length, and extra fields.
- [x] 2.4 Add adapter tests for every tag, null, same-tag results, minimal provider input, malicious note text, refusal, invalid schemas, unsupported models, missing configuration, timeout, HTTP errors, and oversized responses. Ensure no live requests or secret/payload logging.

## 3. Request and review actions

- [x] 3.1 Add owner-scoped, login-required POST request and read-only review routes with CSRF protection; invalidate old pending records before generation and verify the snapshot again after the provider returns.
- [x] 3.2 Store only validated different-tag recommendations as pending records. Add transient feedback for insufficient evidence, same-tag recommendations, stale input, and provider failures without creating actionable suggestions.
- [x] 3.3 Add transactional accept logic that revalidates requester, ownership, tag, fingerprint, and expiry; update only the contact tag and consume the suggestion atomically, handling replay and SQLite contention safely.
- [x] 3.4 Add decline logic that consumes the pending suggestion without changing contacts or calling the provider. Reject foreign, missing, expired, or replaced identifiers consistently.
- [x] 3.5 Construct local return URLs from validated tag-filter context and add user feedback after acceptance or decline; preserve filtering and recompute list and account counts.

## 4. Workshop interface

- [x] 4.1 Add a Suggest tag form to each contact and an English review template showing contact identity, current tag, recommendation, and escaped explanation with Accept and Decline controls.
- [x] 4.2 Add clear unavailable, insufficient-evidence, and same-tag states with dismissal and no Accept action; use POST/redirect/GET so reloading never resubmits a provider request.
- [x] 4.3 Preserve keyboard-accessible labels, existing styling, and visible acceptance feedback when a contact leaves the active filter.

## 5. Behavior and security regression tests

- [x] 5.1 Add tests proving requests and declines never change contact data, acceptance applies only the server-held tag to the intended contact, other fields remain unchanged, and accept/decline do not call the provider.
- [x] 5.2 Cover all suggestion routes with anonymous users, multiple owners, forged contact/suggestion IDs, missing/invalid CSRF tokens, disallowed GET mutations, and attempted external redirects; assert unauthorized requests never call the provider.
- [x] 5.3 Cover changed contacts during generation and before acceptance, expiry, replacement including failed generation, deleted contacts, repeated/concurrent acceptance, and explanation escaping.
- [x] 5.4 Cover acceptance into and out of every declared tag filter, zero/one/multiple visible results, account summary changes, and unchanged behavior after decline or provider failure.

## 6. Browser tests and documentation

- [x] 6.1 Add Playwright request/review/accept and request/review/decline flows with a deterministic fake patched at the Django live-server provider boundary; verify persisted results after reload.
- [x] 6.2 Add browser scenarios for same-tag, insufficient-evidence, and unavailable responses, a second owner, escaped explanations, and acceptance removing a contact from the active filter with correct counts.
- [x] 6.3 Ensure the existing CI browser command includes the new suite or add an explicit suite command; tests must run without OpenRouter credentials or outbound AI requests.
- [x] 6.4 Document branch-specific setup, migrations, OPENROUTER_API_KEY and OPENROUTER_MODEL environment variables, compatible-model selection, transmitted fields, user review behavior, failure states, and rollback. Use synthetic examples and no committed secrets.
- [x] 6.5 Add a small documented set of synthetic classification examples for Customer, Partner, Lead, overlap, insufficient evidence, and instruction-like notes. Keep optional live evaluation separate from deterministic CI; report if no live model was evaluated.

## 7. Final verification

- [x] 7.1 Run `uv run python manage.py test`, `uv run python manage.py check`, and `uv run python manage.py makemigrations --check --dry-run`.
- [x] 7.2 Run the existing filter browser suite and the new suggestion browser suite using fake provider responses; verify the documented commands match CI.
- [x] 7.3 Review the final diff for migration/dependency consistency, secrets, generated artifacts, and unrelated changes; report validation and remaining live-model limitations in the PR description.
