# feat: add reviewed AI tag suggestions

Users can request an OpenRouter tag recommendation from a contact's existing
company, role, current tag, and note, then review its explanation and explicitly
Accept or Decline. Only acceptance updates the contact. Insufficient evidence,
same-tag recommendations, invalid responses, and provider failures leave it unchanged.

Pending suggestions expire after 15 minutes and are bound to the requester and
contact snapshot. Ownership, CSRF, stale-record, and replay checks protect every
action. Returning to a filtered list preserves the filter and recalculates counts.
Transient feedback is also scoped to its owner across account switches.

Validation:

- All 24 Django tests pass, including provider validation, isolation, CSRF,
  expiry, stale records, replay, and concurrent acceptance.
- All 7 Playwright tests pass across the filter and suggestion suites with a fake
  provider; the review page was also visually inspected.
- Django system checks and migration consistency checks pass.
- The additive suggestion migration was applied successfully to the local database.
- CI is configured to include the new browser suite; the changes have not yet
  been pushed, so remote CI has not run for this implementation.

Setup requires OPENROUTER_API_KEY and an explicit compatible OPENROUTER_MODEL.
No runtime dependencies were added. Automated tests need neither credentials nor
AI credits. Live OpenRouter/model quality was not evaluated; the documentation
provides synthetic cases for optional manual evaluation. This remains a local
workshop app with synchronous provider requests and no new interaction history.
