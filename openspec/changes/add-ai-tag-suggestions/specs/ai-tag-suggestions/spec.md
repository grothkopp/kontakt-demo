## ADDED Requirements

### Requirement: Suggestions are explicitly requested and owner scoped

The system SHALL offer Suggest tag for an authenticated user's contacts. Request, Apply, and Dismiss MUST use CSRF-protected POST actions and verify current ownership before provider access or modification. Missing and foreign contacts SHALL return 404 without invoking the provider.

#### Scenario: Viewing contacts does not invoke AI
- **WHEN** a user loads, filters, or reloads the contact list
- **THEN** the system SHALL make no AI request and SHALL leave saved tags unchanged

#### Scenario: Requesting a suggestion for an owned contact
- **WHEN** an authenticated user submits a valid Suggest tag request
- **THEN** the system SHALL make one bounded suggestion request for that owned contact and SHALL leave its saved tag unchanged

#### Scenario: Other user's contact is addressed directly
- **WHEN** a user submits Request, Apply, or Dismiss for a foreign or nonexistent contact ID
- **THEN** the system SHALL return 404, invoke no provider, and modify no contact

#### Scenario: Authentication and CSRF are enforced
- **WHEN** a caller is anonymous, uses GET for an action, or omits a valid CSRF token
- **THEN** the action SHALL be rejected or redirected to login as appropriate without an AI call or contact update

### Requirement: The existing note is the complete demo history

The system SHALL use only the selected contact's company, role, and existing note as model input data. It MUST NOT send other contacts, user/account data, names, email addresses, or the current tag, and MUST NOT retrieve external history. Notes SHALL be treated as untrusted descriptive data rather than instructions.

#### Scenario: Building the model input
- **WHEN** a suggestion is requested for one of several contacts owned by different users
- **THEN** the request SHALL contain only the selected contact's company, role, and note plus fixed task instructions

#### Scenario: Instruction-like history
- **WHEN** a note contains instructions to invent tags or expose other contacts
- **THEN** the service SHALL continue to enforce its fixed tag result contract and SHALL provide no other contacts or tools to the model

### Requirement: Suggestions are constrained and explainable

The system SHALL accept only Customer, Partner, or Lead with a nonempty explanation of at most 400 characters, or an insufficient-evidence result with no tag. Prompt instructions SHALL define Customer as an established client/purchasing relationship, Partner as established collaboration/referrals, and Lead as a prospective relationship or expressed interest. Explanations SHALL be grounded in the supplied data. Sparse information or conflicting relationship evidence SHALL permit abstention instead of an invented classification.

#### Scenario: Valid tag suggestion
- **WHEN** the provider returns a valid supported tag and explanation
- **THEN** the page SHALL show that suggestion and an escaped explanation for the selected contact while retaining the current saved tag

#### Scenario: Insufficient evidence
- **WHEN** the provider reports insufficient or conflicting evidence
- **THEN** the page SHALL explain that a tag cannot be suggested, offer no Apply action, and leave the saved tag unchanged

#### Scenario: Suggested tag already matches
- **WHEN** a valid suggestion equals the saved tag
- **THEN** the page SHALL identify it as already matching, offer no Apply action, and allow dismissal

### Requirement: Changes require accepting a valid pending suggestion

The system SHALL provide Apply suggestion and Dismiss for a changeable suggestion. Pending results MUST be bound to the requesting session, user, and contact, expire after 15 minutes, and be replaced by subsequent requests. Apply MUST use the server-stored validated tag rather than a client-submitted tag. Apply MUST reject results whose input fields or original tag have changed and MUST conditionally update only the matching contact snapshot.

#### Scenario: Applying a suggestion
- **WHEN** the owner applies an unexpired current suggestion against unchanged contact data
- **THEN** the system SHALL update only that contact's tag, consume the result, and retain all other fields and contacts

#### Scenario: Dismissing a suggestion
- **WHEN** the owner dismisses the current pending result
- **THEN** the panel SHALL disappear without an AI call or a contact update

#### Scenario: Forged or replayed result
- **WHEN** an Apply request contains a missing, altered, foreign-session, previously consumed, or superseded result token
- **THEN** the system SHALL reject it without updating any contact or trusting a submitted tag

#### Scenario: Stale or expired suggestion
- **WHEN** Apply is submitted after expiry or after relevant contact fields or the current tag change
- **THEN** the system SHALL leave the contact unchanged, clear the stale result, and ask the user to request a new suggestion

### Requirement: Failure leaves the application usable

Missing configuration, provider timeout/refusal, transport failure, or malformed results SHALL yield an English unavailable message and no applicable suggestion. The provider operation SHALL have a 15-second timeout and no automatic retries. The system MUST NOT expose credentials or raw provider errors in the UI, and generated text MUST be escaped.

#### Scenario: Invalid output or provider failure
- **WHEN** the provider returns an unsupported tag, an inconsistent result, missing/oversized explanation, refusal, timeout, or error
- **THEN** the user SHALL see an unavailable message, saved data SHALL remain unchanged, and no previous result SHALL remain applicable for that contact

#### Scenario: Missing provider configuration
- **WHEN** the app has no configured provider credentials or model
- **THEN** listing and filtering SHALL still work and Suggest tag SHALL report unavailability without a provider call

### Requirement: Suggestion actions integrate with tag filtering

Suggestion actions SHALL return to the local contact list with the active tag filter retained. Refresh after an action SHALL NOT repeat an AI call. Applying a tag SHALL update displayed totals and filtered rows using the existing owner-scoped behavior; totals SHALL continue to describe the full owned collection.

#### Scenario: Accepted tag no longer matches the filter
- **WHEN** a user applies Partner to a contact while viewing the Customer filter
- **THEN** the system SHALL retain the Customer filter, remove that contact from the visible rows, recalculate totals, and show an update confirmation

#### Scenario: Refresh after requesting
- **WHEN** the user refreshes the redirected page after requesting a suggestion
- **THEN** the page SHALL display the pending result without issuing another provider request

### Requirement: Automated tests do not depend on a live provider

Default Django and Playwright CI tests SHALL use controlled provider responses without external AI requests or provider credentials. A separate optional live evaluation SHALL use fictional inputs and report tag/abstention correctness and explanation grounding.

#### Scenario: Offline provider tests in CI
- **WHEN** the normal PR workflow runs without provider credentials
- **THEN** tests SHALL exercise successful suggestions, acceptance, dismissal, ownership boundaries, and failure handling using the fake provider

#### Scenario: Optional quality evaluation
- **WHEN** a developer explicitly runs the live evaluation with provider configuration
- **THEN** it SHALL assess fictional clear, sparse, ambiguous, and instruction-like examples independently of the deterministic application suite
