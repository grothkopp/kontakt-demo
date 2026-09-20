"""Offline suggestion boundary. No contact objects or other user data enter here."""

from dataclasses import dataclass

from .models import Contact


PROVIDER_ID = "offline-fake-v1"
# Fixed development examples, not a language classifier. Unknown notes abstain.
DEMO_RESULTS = {
    "Hat unser Produkt gekauft und nutzt es seit Juni.": "customer",
    "Gemeinsames Partner-Webinar für November vereinbart.": "partner",
    "Interessiert am Angebot; noch keine Bestellung.": "lead",
    "Purchased our product and has used it since June.": "customer",
    "Agreed to co-host a partner webinar in November.": "partner",
    "Interested in our offer; has not ordered yet.": "lead",
}


class ProviderError(Exception):
    """An expected provider-service failure (never displayed to the user)."""


class InvalidOutput(ValueError):
    """The provider did not satisfy the exact result contract."""


def fake_provider(note):
    return {"tag": DEMO_RESULTS.get(note)}


def validate_output(output):
    if type(output) is not dict or set(output) != {"tag"}:
        raise InvalidOutput("Expected exactly one tag field.")
    tag = output["tag"]
    if tag is not None and (type(tag) is not str or tag not in Contact.Tag.values):
        raise InvalidOutput("Expected an existing tag or null.")
    return tag


@dataclass(frozen=True)
class Suggestion:
    tag: str | None = None
    error: str | None = None

    @property
    def label(self):
        return Contact.Tag(self.tag).label if self.tag is not None else None


def suggest_tag(note, *, provider=None):
    """Return validated data, abstention, or a safe error code without saving."""
    if not note.strip():
        return Suggestion()
    if provider is None:
        provider = fake_provider
    try:
        return Suggestion(tag=validate_output(provider(note)))
    except InvalidOutput:
        return Suggestion(error="invalid_output")
    except TimeoutError:
        return Suggestion(error="timeout")
    except ProviderError:
        return Suggestion(error="provider_error")
