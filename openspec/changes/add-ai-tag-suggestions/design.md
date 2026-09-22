## Context

The app uses Django templates, SQLite, standard authentication, and CSRF middleware. Each contact belongs to one user and has a name, company, role, email, tag, and note. The filter operates on owner-scoped contacts; its list counts differ from account totals. There is no interaction timeline. The user selected OpenRouter and confirmed that existing information is sufficient and suggestions must be accepted or declined.

## Goals / Non-Goals

**Goals:** Provide an explicit, explainable, owner-scoped suggestion and review flow; persist a tag change only on acceptance; keep provider failures harmless; preserve filtering and summaries; make automated tests deterministic.

**Non-Goals:** New contact history, external enrichment, email/CRM integrations, bulk or automatic tagging, background workers, streaming, a general chat interface, production deployment, or a permanent suggestion audit log.

## Decisions

### 1. Small synchronous OpenRouter adapter

Create a service boundary in `contacts` that accepts a contact snapshot and returns a validated tag/reason or an insufficient-evidence result. Use a server-side HTTP request to `https://openrouter.ai/api/v1/chat/completions` with bearer authentication. Read `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from the environment; require an explicit model ID rather than a moving default. Use a model supporting JSON-schema structured output, request required parameter support, and validate the response locally regardless of provider guarantees. Use a small HTTP client installed with uv if needed; avoid an agent framework or tools.

Use a 15-second network timeout, no automatic retries, and bounded response size (64 KiB) and explanation length (500 characters). Missing configuration, refusals, incomplete completions, unsupported schema, HTTP errors, and malformed output produce a friendly unavailable message and no pending suggestion. Normal browsing never requires credentials.

References: [OpenRouter quickstart](https://openrouter.ai/docs/quickstart), [structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs). Confirm the chosen model supports these options during implementation; no live request is required for CI.

Alternative: a background queue would avoid holding a request open but adds unnecessary infrastructure for this local demo.

### 2. Limited evidence and a clear classification contract

Send only company, role, current tag, and note. Name and email are not needed to classify a relationship and stay local. Never send other contacts or account data. The existing note is the only narrative history; do not fabricate a timeline. Supply tag values from `Contact.Tag.choices` and instruct the model to treat field contents as data, not instructions.

Define Customer as explicit evidence of a purchase or paid relationship, Partner as explicit collaboration without clearer customer evidence, and Lead as explicit prospective business interest. If evidence supports both Customer and Partner, prefer Customer; if evidence is insufficient or contradictory, abstain. A current tag alone is not evidence. This is a proposed demo classification policy, documented with synthetic examples.

The response contract is `{tag: allowed_tag_or_null, reason: nonempty_string}` with no extra fields. Null means insufficient evidence. Explain the decision from supplied evidence; do not invent facts or emit confidence percentages. Render explanations as escaped text, never trusted HTML. A same-tag response shows “The current tag still fits.” with a Dismiss action and no Accept button.

### 3. Server-held pending suggestions

Add `TagSuggestion` with a UUID primary key, contact foreign key (cascade delete), requester foreign key, proposed tag, explanation, creation timestamp, and a fingerprint of the contact fields at request time. Only different-tag, validated recommendations create pending records. Enforce one pending suggestion per requester/contact with a uniqueness constraint. A new request invalidates the previous pending record before generating a replacement, including when the replacement fails. Keep the provider call outside database transactions.

Suggestions expire after 15 minutes. Check the fingerprint again after generation and at acceptance; a changed contact requires a fresh request. Re-fetch and check ownership at every action. Delete pending records on accept or decline; reject expired or missing records. Expired records can be removed lazily on requests. This supports reloads and avoids trusting hidden tag fields. Session-only storage was considered but offers weaker concurrent review handling; signed browser payloads complicate replay prevention.

Accept in a short SQLite transaction: re-read the pending record and owner-scoped contact, validate expiry and fingerprint, update only the tag, then delete the pending record atomically. Concurrent or repeated requests must never apply a consumed suggestion twice; handle contention as a retryable user message. The browser supplies a suggestion ID, not an authoritative tag or explanation.

### 4. Template forms and explicit review

Add POST-only, login-required, CSRF-protected request, accept, and decline routes; use a separate read-only review GET after requesting via POST/redirect/GET. GET never calls OpenRouter or changes tags. The review page displays the contact identity, current tag, proposed tag, and explanation with Accept and Decline buttons. Decline returns to the list immediately and dismisses the suggestion.

Carry only the selected tag as return context and construct the list URL server-side; do not accept arbitrary redirect URLs. After acceptance, return to the list with that filter and recompute all counts; the contact disappears if its new tag no longer matches. Show an English confirmation so the disappearance is understandable. Accept and Decline never call OpenRouter. Missing or foreign records return the same not-found behavior.

### 5. Deterministic verification

Mock the provider at the service boundary in Django tests and patch the same boundary for the Playwright live server. Exercise each allowed tag, multiple owners, empty and conflicting evidence, same-tag output, provider errors, tampered IDs, invalid output, expiry, stale records, repeated submission, and escaped explanations. Assert no tag writes on request, failure, or decline and no provider calls on browsing, accept, decline, or unauthorized requests. Keep existing authentication, CSRF, filter, and summary tests.

Add synthetic classification examples for optional manual model evaluation. Ordinary test runs verify software behavior with fakes; they do not claim to prove live model accuracy.

## Risks / Trade-offs

- Plausible but wrong recommendations → evidence-based explanation, abstention guidance, explicit human acceptance, and synthetic evaluation examples.
- Contact notes containing instructions → separate instructions from field data, no tools, strict output validation, and no autonomous writes.
- Provider cost or latency → explicit requests only, small input/output, timeout, no automatic retries, no background generation.
- Provider/model variation → explicit configurable model, required schema support, local validation, and documented compatibility check.
- Changes while a suggestion is open → fingerprint and expiry checks before applying; atomic consumption.
- External data handling → transmit only the chosen contact's limited fields; keep credentials and raw payloads out of logs; document that requests go through OpenRouter and its selected provider.
- Pending records add a migration → additive table only; no changes to existing contact fields or fixture data.

## Migration Plan

1. Add the pending-suggestion model and migration; update uv.lock if an HTTP dependency is added.
2. Add optional environment configuration, service, routes, templates, tests, and documentation.
3. Run Django migrations and automated suites using fakes. Configure a compatible OpenRouter model and key only for an optional local smoke test with synthetic data.
4. Roll back feature code and reverse the new migration if needed; this removes pending suggestions only. Tags explicitly accepted by users remain ordinary contact data and are not automatically reverted.

## Open Questions

No blocking product questions remain. The operator selects a compatible `OPENROUTER_MODEL` at setup; model choice is configuration, not hardcoded behavior. Immediate dismissal on decline, 15-minute expiry, and the tag precedence above are proposal defaults that can be adjusted before implementation.
