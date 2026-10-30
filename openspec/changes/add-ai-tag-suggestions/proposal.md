## Why

Users can filter contacts by tag but have no help deciding which tag fits a relationship. An on-demand AI suggestion can interpret the contact's details and existing note while keeping the user in control of any tag change.

## What Changes

- Add a per-contact **Suggest tag** action using the existing description/history in `Contact.note`, together with the contact's company and role.
- Suggest Customer, Partner, or Lead with a short explanation; report insufficient or conflicting evidence instead of inventing a relationship.
- Show **Apply suggestion** and **Dismiss**. Requesting or dismissing a suggestion never changes the saved tag; applying explicitly updates only the selected contact.
- Preserve owner isolation, authentication, CSRF protection, and the existing tag filter. Handle missing AI configuration, timeouts, and invalid responses without changing contact data.
- Add deterministic Django and Playwright coverage with a fake provider, plus a small optional live evaluation set and setup documentation.

## Capabilities

### New Capabilities

- `ai-tag-suggestions`: Request, review, apply, and dismiss a tag suggestion grounded in the current user's contact information and note.

### Modified Capabilities

None. No existing OpenSpec capability specifications are present.

## Impact

- Contacts views, URL routes, templates, and minimal styling gain the suggestion flow; a small server-side adapter handles AI requests and validates results.
- Django sessions hold temporary suggestions; SQLite and the existing contact schema remain unchanged.
- Provider credentials and model configuration come from the server environment. Any chosen SDK dependency must be managed with uv and committed in `uv.lock`.
- Tests, CI, and README gain coverage and instructions; default CI requires neither provider credentials nor paid AI calls.

## Non-goals

No separate history model, external email/calendar integration, free-form tags, bulk suggestions, automatic tagging, general contact editing, background workers, or production deployment. The existing note is the complete demo history.
