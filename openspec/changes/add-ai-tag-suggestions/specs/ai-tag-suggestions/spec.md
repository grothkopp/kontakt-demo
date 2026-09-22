## ADDED Requirements

### Requirement: Suggestions are requested explicitly for one owned contact
The system SHALL offer a Suggest tag action for each owned contact. It MUST call OpenRouter only following an authenticated, CSRF-protected POST for that contact and MUST NOT change the contact while generating a suggestion. The provider input SHALL contain only that contact's company, role, current tag, and note, plus classification instructions and allowed tag values.

#### Scenario: Owner requests a suggestion
- **WHEN** the signed-in owner submits Suggest tag for a contact
- **THEN** the system requests a recommendation using that contact's allowed fields and leaves all contact fields unchanged

#### Scenario: Browsing is free of AI side effects
- **WHEN** a user opens, filters, or reloads the contact list or review page
- **THEN** no provider request or contact update occurs

#### Scenario: Request attempts to include another contact
- **WHEN** a request contains extra contact identifiers or field values
- **THEN** provider input is built from the owner-scoped database record, not those submitted values

### Requirement: Suggestions are constrained and explainable
The system SHALL accept only an allowed tag from the model choices, or null for insufficient evidence, with a nonempty explanation of at most 500 characters. It MUST reject malformed, incomplete, or unsupported responses and render explanations as escaped text. Prompt instructions MUST define Customer as explicit paid-relationship evidence, Partner as collaboration, and Lead as prospective business interest, preferring Customer when paid and partner evidence coexist. The current tag alone MUST NOT be treated as sufficient evidence, and field contents MUST be treated as data rather than instructions.

#### Scenario: Valid different-tag recommendation
- **WHEN** the provider returns a valid different tag with an explanation
- **THEN** the review displays the current tag, proposed tag, and explanation with Accept and Decline actions

#### Scenario: Evidence is insufficient
- **WHEN** the provider returns a valid null-tag response
- **THEN** the system displays its explanation, offers no Accept action, and leaves the contact unchanged

#### Scenario: Recommendation matches the existing tag
- **WHEN** the provider returns the current tag
- **THEN** the system displays “The current tag still fits.” and the explanation with a Dismiss action and no Accept action

#### Scenario: Output is invalid or contains markup
- **WHEN** a provider response has an unknown tag, extra fields, invalid types, missing or oversized explanation, or an incomplete completion
- **THEN** no actionable suggestion is created and the contact remains unchanged
- **AND** any valid explanation containing markup is displayed as text without executing or rendering that markup

### Requirement: Acceptance applies exactly the reviewed suggestion
The system MUST hold pending suggestions on the server and bind each to the requester, contact, proposed tag, and contact snapshot. Accept SHALL require an authenticated, CSRF-protected POST, revalidate ownership and the allowed tag, and update only the intended contact's tag. Acceptance and consumption of the pending suggestion MUST be atomic. Submitted tag or explanation values MUST NOT override the stored suggestion.

#### Scenario: Owner accepts a pending suggestion
- **WHEN** the owner accepts an unexpired suggestion for an unchanged contact
- **THEN** the stored proposed tag is applied once, the suggestion is consumed, all other contact fields and contacts remain unchanged, and no provider request occurs

#### Scenario: Acceptance payload is tampered with
- **WHEN** an acceptance POST includes a different proposed tag
- **THEN** that submitted tag cannot replace the server-held recommendation

#### Scenario: Acceptance is repeated or concurrent
- **WHEN** multiple requests attempt to accept the same suggestion
- **THEN** at most one succeeds and later attempts cannot perform another update

### Requirement: Decline dismisses without changing contact data
Decline SHALL use an authenticated, CSRF-protected POST to remove the pending suggestion and return to the contact list immediately. It MUST NOT change any contact or call the provider. A declined suggestion MUST NOT remain actionable through an old page or URL.

#### Scenario: Owner declines
- **WHEN** the owner declines a pending suggestion
- **THEN** the suggestion disappears, the current tag stays unchanged, and a later attempt to accept that suggestion is rejected

### Requirement: All suggestion actions preserve access controls
Request, review, accept, and decline MUST require authentication and scope records to the signed-in contact owner and suggestion requester. Foreign and nonexistent records MUST produce equivalent not-found behavior without provider calls or changes. Mutation endpoints MUST reject GET requests, and missing or invalid CSRF tokens MUST be rejected.

#### Scenario: Another user targets a contact or suggestion
- **WHEN** a signed-in user attempts any suggestion action on another user's record
- **THEN** no contact data or explanation is exposed, no provider request occurs, and no state changes

#### Scenario: Anonymous or forged request
- **WHEN** an anonymous user requests a suggestion action, or a mutation lacks a valid CSRF token, or an authenticated GET targets a mutation endpoint
- **THEN** the system requires login, rejects the CSRF violation, or rejects the HTTP method respectively, without a provider call or contact update

### Requirement: Pending suggestions cannot overwrite newer information
Suggestions MUST expire 15 minutes after creation. The system MUST reject generation results or acceptance if contact fields differ from the snapshot used to request the suggestion. A new suggestion request MUST invalidate the earlier pending suggestion for that requester/contact, even if generation fails. Only one pending suggestion per requester/contact SHALL remain actionable.

#### Scenario: Contact changes during generation or before acceptance
- **WHEN** contact data changes after the request snapshot is taken
- **THEN** the stale recommendation cannot be applied and the user is prompted to request a new suggestion

#### Scenario: Expired, deleted, or replaced suggestion
- **WHEN** a user tries to accept an expired suggestion, one whose contact was deleted, or one replaced by a new request
- **THEN** no contact changes and the old suggestion is no longer actionable

### Requirement: AI failures leave the application usable
Missing configuration, network timeout, refusal, provider error, unsupported model output, and validation errors MUST produce an English message without altering contact data. Provider calls SHALL use a 15-second timeout, bounded output, and no automatic retry. Credentials and raw provider payloads MUST NOT appear in pages or logs. Contact browsing and filtering MUST work without provider configuration.

#### Scenario: Provider is unavailable
- **WHEN** a suggestion request fails due to configuration, timeout, or provider error
- **THEN** the page reports unavailability, the contact remains unchanged, and the user can return to the list or explicitly retry

### Requirement: Suggestion actions preserve list and filter behavior
After accept or decline, the system SHALL return to the contact list with the selected tag filter preserved through a server-constructed local URL. It MUST recalculate displayed results and list counts and preserve owner-scoped account summaries. Acceptance SHALL show a confirmation even if the contact leaves the selected filter.

#### Scenario: Accepted tag no longer matches the filter
- **WHEN** the user accepts a new tag while returning to a filter for the old tag
- **THEN** the contact is absent from the filtered list, heading and footer match the remaining result count, account totals are correct, and a confirmation is visible

#### Scenario: Decline or malicious return URL
- **WHEN** a suggestion is declined or a submitted return value contains an external URL
- **THEN** the user returns only to the local contact list with valid filter context and no external redirect

### Requirement: Automated verification uses synthetic data and no live AI
Django and Playwright tests MUST use a deterministic fake at the provider boundary, require no API keys, and make no external AI calls. Coverage SHALL include all declared tag values, multiple owners, accept and decline flows, and failure cases. Live model quality evaluation SHALL be optional and separate from CI.

#### Scenario: Tests run without OpenRouter credentials
- **WHEN** the developer or CI runs the documented automated test commands without provider configuration
- **THEN** suggestion tests execute against synthetic responses alongside existing authentication, CSRF, and filter regression tests
