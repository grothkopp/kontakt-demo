"""Browser coverage with a fake OpenRouter boundary; no API keys or calls."""
from contextlib import contextmanager
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright

from contacts.models import Contact
from contacts.suggestions import SuggestionUnavailable


class TagSuggestionBrowserTests(StaticLiveServerTestCase):
    password = "Synthetic-browser-password!"

    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="suggestion-owner", password=self.password)
        self.other = get_user_model().objects.create_user(username="other-owner", password=self.password)
        self.contact = Contact.objects.create(owner=self.owner, name="Taylor Demo",
            company="Example Company", role="Buyer", email="taylor@example.test", tag="lead", note="Purchased a plan.")
        self.foreign = Contact.objects.create(owner=self.other, name="Alex Demo",
            company="Other Company", role="Partner", email="alex@example.test", tag="partner", note="Private collaboration.")
        self.provider = self.enterContext(patch("contacts.suggestions.request_suggestion",
            return_value={"tag": "customer", "reason": "The note records a completed purchase."}))

    @contextmanager
    def page(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                with browser.new_context() as context:
                    yield context.new_page()
            finally:
                browser.close()

    def sign_in(self, page, user):
        page.goto(self.live_server_url)
        page.get_by_label("Username", exact=True).fill(user.username)
        page.get_by_label("Password", exact=True).fill(self.password)
        page.get_by_role("button", name="Sign in").click()
        expect(page.get_by_role("heading", name="All contacts 1", exact=True)).to_be_visible()

    def request(self, page):
        page.get_by_role("button", name=f"Suggest tag for {self.contact.name}", exact=True).click()
        expect(page.get_by_role("heading", name="Review tag suggestion", exact=True)).to_be_visible()

    def test_accept_updates_only_after_review_and_preserves_filter(self):
        with self.page() as page:
            self.sign_in(page, self.owner)
            page.get_by_label("Tag", exact=True).select_option("lead")
            page.get_by_role("button", name="Filter", exact=True).click()
            self.request(page)
            expect(page.locator("dd")).to_have_text(["Lead", "Customer"])
            expect(page.get_by_text("The note records a completed purchase.", exact=True)).to_be_visible()
            review_url = page.url
            page.reload()
            expect(page.get_by_role("button", name="Accept", exact=True)).to_be_visible()
            self.assertEqual(self.provider.call_count, 1)
            # A separate page shows that requesting has not changed the contact.
            other_page = page.context.new_page()
            other_page.goto(f"{self.live_server_url}/?tag=lead")
            expect(other_page.get_by_role("heading", name="Filtered contacts 1", exact=True)).to_be_visible()
            other_page.close()
            page.get_by_role("button", name="Accept", exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Tag updated to Customer for Taylor Demo.")
            expect(page.get_by_label("Tag", exact=True)).to_have_value("lead")
            expect(page.get_by_role("heading", name="Filtered contacts 0", exact=True)).to_be_visible()
            expect(page.locator(".list-footer")).to_have_text("0 contacts Your network. Your overview.")
            expect(page.locator(".nav-count")).to_have_text("1")
            page.reload()
            expect(page.get_by_role("heading", name="Filtered contacts 0", exact=True)).to_be_visible()
            page.get_by_label("Tag", exact=True).select_option("customer")
            page.get_by_role("button", name="Filter", exact=True).click()
            expect(page.get_by_role("heading", name="Filtered contacts 1", exact=True)).to_be_visible()
            self.assertEqual(page.goto(review_url).status, 404)
            self.assertEqual(self.provider.call_count, 1)
        self.contact.refresh_from_db()
        self.foreign.refresh_from_db()
        self.assertEqual(self.contact.tag, "customer")
        self.assertEqual(self.foreign.tag, "partner")

    def test_decline_dismisses_and_cannot_be_replayed(self):
        with self.page() as page:
            self.sign_in(page, self.owner)
            self.request(page)
            review_url = page.url
            page.get_by_role("button", name="Decline", exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Suggestion declined.")
            page.reload()
            expect(page.locator("tbody .tag")).to_have_text("Lead")
            self.assertEqual(page.goto(review_url).status, 404)
            self.assertEqual(self.provider.call_count, 1)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.tag, "lead")

    def test_nonactionable_results_and_provider_failure(self):
        cases = [("lead", "The current tag still fits."),
                 (None, "Not enough information to suggest a tag."),
                 ("unavailable", "Tag suggestions are unavailable right now.")]
        with self.page() as page:
            self.sign_in(page, self.owner)
            for tag, expected in cases:
                with self.subTest(tag=tag):
                    self.provider.side_effect = SuggestionUnavailable if tag == "unavailable" else None
                    self.provider.return_value = {"tag": tag, "reason": "No different relationship is established."}
                    page.get_by_role("button", name=f"Suggest tag for {self.contact.name}").click()
                    expect(page.get_by_role("status")).to_contain_text(expected)
                    expect(page.get_by_role("button", name="Accept", exact=True)).to_have_count(0)
                    expect(page.locator("tbody .tag")).to_have_text("Lead")
                    page.get_by_role("link", name="Dismiss", exact=True).click()
                    expect(page.get_by_role("status")).to_have_count(0)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.tag, "lead")

    def test_explanations_are_text_and_other_owner_cannot_review(self):
        self.provider.return_value = {"tag": "customer", "reason": "<script>window.aiExecuted = true</script>"}
        with self.page() as page:
            self.sign_in(page, self.owner)
            self.request(page)
            review_url = page.url
            expect(page.locator(".suggestion-reason")).to_have_text(self.provider.return_value["reason"])
            self.assertIsNone(page.evaluate("window.aiExecuted"))
            with page.context.browser.new_context() as other_context:
                other_page = other_context.new_page()
                self.sign_in(other_page, self.other)
                expect(other_page.get_by_text(self.contact.email, exact=True)).to_have_count(0)
                self.assertEqual(other_page.goto(review_url).status, 404)
                self.assertEqual(other_page.request.post(
                    f"{self.live_server_url}/contacts/{self.contact.pk}/suggest-tag/"
                ).status, 403)
            self.assertEqual(self.provider.call_count, 1)
