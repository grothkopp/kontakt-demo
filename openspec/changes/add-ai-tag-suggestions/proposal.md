## Why

Users currently choose contact tags without assistance interpreting their notes and relationship information. An on-demand AI suggestion provides an explainable recommendation while keeping the user in control of every tag change, and demonstrates a bounded AI workflow in the local workshop app.

## What Changes

- Add a per-contact Suggest tag action using existing company, role, current tag, and note information; no new history source is required.
- Use OpenRouter to suggest one existing tag with a short explanation, or report insufficient evidence.
- Let the owner review the current and suggested tags and explicitly Accept or Decline. Only acceptance changes the stored tag; declining dismisses the suggestion.
- Handle unchanged recommendations, unavailable AI, invalid output, and stale suggestions without modifying contact data.
- Preserve authentication, CSRF protection, ownership isolation, and correct list filtering and counts after acceptance.
- Add deterministic service, view, and browser tests plus English setup and workshop documentation.

## Capabilities

### New Capabilities

- `ai-tag-suggestions`: Request, review, accept, or decline an owner-scoped AI tag suggestion based on existing contact information.

### Modified Capabilities

None. There are no existing OpenSpec capability specs to modify; the existing contact list and filter guarantees remain applicable.

## Impact

- Django views, routes, templates, and settings gain suggestion actions and OpenRouter configuration.
- A small service adapter handles prompt construction, provider calls, and response validation. Python dependencies, if added, use uv and update uv.lock.
- SQLite gains a pending suggestion record linked to its contact and requester so acceptance cannot trust a browser-supplied tag.
- OpenRouter requests occur only on explicit user actions; credentials stay on the server. Automated tests and CI use a fake provider and require no AI credentials.
- Existing contact data is retained. New interaction history, email/CRM imports, bulk tagging, automatic tagging, and production deployment are outside this change.
