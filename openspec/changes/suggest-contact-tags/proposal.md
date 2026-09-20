## Why

Users can read contact notes but have no help choosing an appropriate relationship tag. A small, explicitly requested suggestion flow lets the workshop demonstrate how specifications, deterministic tests, and example-based evals address different aspects of an AI feature while preserving user ownership and control.

## What Changes

- Add a per-contact action that displays at most one suggested existing tag based only on that contact's stored note.
- Require authentication, CSRF protection, and an owner-scoped lookup before any provider call.
- Allow abstention when evidence is insufficient and show a recoverable message for provider failures or invalid output.
- Keep suggestions transient: requesting or viewing one never changes any contact data.
- Start with a clearly labeled, offline deterministic fake provider and an example-based evaluation runner with synthetic notes.
- Non-goals: applying or saving suggestions, editing contacts, multiple tags, new tag categories, live AI integration, batch processing, background jobs, CI, browser test infrastructure, or deployment.
- Proposed scope decisions for review: display only, one existing tag or abstention, and fake provider only. A live model and any explicit apply action require later changes.

## Capabilities

### New Capabilities

- `contact-tag-suggestions`: Owner-only, explicitly requested, transient suggestions with validated output and safe failure behavior.
- `tag-suggestion-evals`: Small reproducible synthetic evaluation set and runner that separate classification quality from application correctness.

### Modified Capabilities

None. There are no existing main specifications to modify.

## Impact

Implementation will touch Django contact views, URLs, templates, tests, and a small provider module, plus an eval dataset, management command, and workshop documentation. The existing Contact model, SQLite schema, standard authentication, and per-user list isolation remain the foundation. No additional runtime dependencies or migrations are anticipated. Fake-provider runs require no credentials or external services; live-model quality is not established by fake-provider results.
