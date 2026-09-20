## ADDED Requirements

### Requirement: Explicit authenticated request
The system SHALL offer a per-contact suggestion action through an authenticated, CSRF-protected POST. Viewing the contact list SHALL NOT invoke the provider.

#### Scenario: Ordinary list view
- **WHEN** a signed-in user opens the contact list
- **THEN** no suggestion provider call occurs and actions are shown only for their contacts

#### Scenario: Anonymous request
- **WHEN** an anonymous visitor submits a POST with valid CSRF data to the suggestion endpoint
- **THEN** they are redirected to login without any provider call

#### Scenario: Unsupported method
- **WHEN** a signed-in user makes a GET request to the suggestion endpoint
- **THEN** the response is 405 and the provider is not called

#### Scenario: Missing CSRF token
- **WHEN** a signed-in user submits a suggestion request without a valid CSRF token
- **THEN** the response is 403 and the provider is not called

### Requirement: Owner isolation before inference
The system MUST resolve a contact by ID and current owner before calling the provider. It SHALL pass only the selected contact's stored note as contact data. All response lists and counts SHALL remain owner-scoped.

#### Scenario: Foreign or nonexistent contact
- **WHEN** Anna posts a valid request for Ben's contact or a nonexistent contact ID
- **THEN** both requests return 404, reveal no contact details, and make zero provider calls

#### Scenario: Stored note is authoritative
- **WHEN** Anna requests a suggestion for her contact and includes forged note, owner, or tag fields
- **THEN** the provider receives only that contact's stored note and the response contains only Anna's contacts and counts

### Requirement: Validated transient suggestion
The system SHALL accept only an exact provider result with a single `tag` key whose value is customer, partner, lead, or null. It SHALL display a valid tag with its existing localized label separately from the saved tag. It MUST NOT persist suggestions or change any contact field on any request outcome.

#### Scenario: Valid suggestion
- **WHEN** the provider returns a valid tag for an owned contact
- **THEN** the response is 200 and displays the suggestion next to that contact while every contact's stored fields remain unchanged

#### Scenario: Same tag is suggested
- **WHEN** the provider returns the contact's current tag
- **THEN** the result remains a valid displayed suggestion and no write occurs

#### Scenario: Result lifetime
- **WHEN** the user opens the contact list with a new GET after receiving a suggestion
- **THEN** the prior suggestion is no longer displayed and the provider is not called

### Requirement: Abstention and safe failure
The system SHALL bypass the provider for empty or whitespace-only notes. Empty notes and valid null results SHALL display “No clear suggestion”. Timeouts, expected provider-service errors, and invalid output SHALL display a distinct recoverable English failure message without raw provider text or exception details. All these outcomes SHALL preserve every contact field.

#### Scenario: Empty note
- **WHEN** a user requests a suggestion for an owned contact whose note is empty or whitespace-only
- **THEN** the response is 200 with the abstention message and no provider call

#### Scenario: Valid abstention
- **WHEN** the provider returns an exact result with tag null
- **THEN** the response is 200 with the abstention message

#### Scenario: Provider failure
- **WHEN** a provider double raises a timeout or expected service error
- **THEN** the response is 200 with a retryable failure message and no saved data changes

#### Scenario: Invalid provider response
- **WHEN** the provider returns an unknown tag, a wrong type, a missing or extra key, or malformed content
- **THEN** the response shows the safe failure message without displaying raw output or changing saved data

### Requirement: Offline workshop mode
The initial implementation SHALL use a deterministic offline fake and visibly label its suggestions as demo output. No live provider or automatic apply action SHALL be enabled.

#### Scenario: Repeatable demo
- **WHEN** the same nonempty note is evaluated repeatedly using the fake
- **THEN** results are identical, no external requests or credentials are required, and the displayed result is identified as a demo
