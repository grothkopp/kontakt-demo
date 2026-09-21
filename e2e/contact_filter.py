"""Run explicitly with: uv run python manage.py test e2e.contact_filter."""
from contextlib import contextmanager
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright

from contacts.models import Contact


class ContactFilterBrowserTests(StaticLiveServerTestCase):
    password = "Synthetic-browser-password!"

    def setUp(self):
        self.users = []
        self.contacts = []
        for owner_index in range(3):
            owner = get_user_model().objects.create_user(
                username=f"browser-owner-{owner_index}", password=self.password,
            )
            self.users.append(owner)
            for tag_index, tag in enumerate(Contact.Tag.values):
                for index in range((0, 1, 3)[(owner_index + tag_index) % 3]):
                    marker = f"owner-{owner_index}-tag-{tag_index}-record-{index}"
                    self.contacts.append(Contact.objects.create(
                        owner=owner, tag=tag, name=f"Name {marker}",
                        company=f"Company {marker}", role=f"Role {marker}",
                        email=f"{marker}@example.test", note=f"Note {marker}",
                    ))
        self.users.append(get_user_model().objects.create_user(
            username="browser-empty-owner", password=self.password,
        ))

    @contextmanager
    def browser(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                yield browser
            finally:
                browser.close()

    def sign_in(self, page, user):
        page.goto(f"{self.live_server_url}/")
        page.get_by_label("Username", exact=True).fill(user.username)
        page.get_by_label("Password", exact=True).fill(self.password)
        page.get_by_role("button", name="Sign in").click()
        expect(page.get_by_role("heading", name="All contacts")).to_be_visible()

    def select_tag(self, page, tag):
        page.get_by_label("Tag", exact=True).select_option(tag)
        page.get_by_role("button", name="Filter", exact=True).click()
        page.wait_for_url(lambda url: parse_qs(urlsplit(url).query).get("tag", [""])[0] == tag)
        expect(page.get_by_label("Tag", exact=True)).to_have_value(tag)

    def assert_results(self, page, owner, tag=""):
        owned = [contact for contact in self.contacts if contact.owner_id == owner.pk]
        expected = [contact for contact in owned if not tag or contact.tag == tag]
        expected.sort(key=lambda contact: (contact.name, contact.pk))
        emails = page.locator('tbody a[href^="mailto:"]')
        expect(emails).to_have_count(len(expected))
        if expected:
            expect(emails).to_have_text([contact.email for contact in expected])
        else:
            expect(page.get_by_role("cell", name="No contacts in your workspace yet.")).to_be_visible()
        # Inspect the whole page to catch leaked fields outside the table too.
        expected_ids = {contact.pk for contact in expected}
        for contact in self.contacts:
            for field in ("name", "company", "role", "email", "note"):
                if contact.pk in expected_ids:
                    expect(page.locator("body")).to_contain_text(getattr(contact, field))
                else:
                    expect(page.locator("body")).not_to_contain_text(getattr(contact, field))
        label = "Filtered contacts" if tag else "All contacts"
        expect(page.get_by_role("heading", name=f"{label} {len(expected)}", exact=True)).to_be_visible()
        noun = "contact" if len(expected) == 1 else "contacts"
        expect(page.locator("footer.list-footer")).to_have_text(
            f"{len(expected)} {noun} Your network. Your overview."
        )
        overview = page.get_by_role("region", name="Contact overview")
        for label, count in (
            ("Contacts", len(owned)),
            ("Companies", len({contact.company for contact in owned})),
            ("Customers", sum(contact.tag == Contact.Tag.CUSTOMER for contact in owned)),
        ):
            card = overview.locator("div").filter(has=page.get_by_text(label, exact=True))
            expect(card.locator("strong")).to_have_text(f"{count:02d}")
        expect(page.locator(".nav-count")).to_have_text(str(len(owned)))

    def test_filter_all_tags_for_each_owner_and_empty_account(self):
        with self.browser() as browser:
            for owner in self.users:
                with browser.new_context() as context:
                    page = context.new_page()
                    self.sign_in(page, owner)
                    self.assert_results(page, owner)
                    for tag in Contact.Tag.values:
                        with self.subTest(owner=owner.username, tag=tag):
                            self.select_tag(page, tag)
                            self.assert_results(page, owner, tag)

    def test_filter_survives_reload_and_both_reset_controls_restore_all_contacts(self):
        owner = self.users[0]
        with self.browser() as browser, browser.new_context() as context:
            page = context.new_page()
            self.sign_in(page, owner)
            for tag in Contact.Tag.values:
                for reset in ("link", "all tags"):
                    with self.subTest(tag=tag, reset=reset):
                        self.select_tag(page, tag)
                        page.reload()
                        expect(page.get_by_label("Tag", exact=True)).to_have_value(tag)
                        self.assert_results(page, owner, tag)
                        if reset == "link":
                            page.get_by_role("link", name="Reset", exact=True).click()
                            page.wait_for_url(f"{self.live_server_url}/")
                        else:
                            self.select_tag(page, "")
                        self.assertFalse(parse_qs(urlsplit(page.url).query).get("tag"))
                        expect(page.get_by_label("Tag", exact=True)).to_have_value("")
                        expect(page.get_by_role("link", name="Reset", exact=True)).to_have_count(0)
                        self.assert_results(page, owner)

    def test_filter_deep_link_requires_login_and_preserves_selection(self):
        owner = self.users[1]
        with self.browser() as browser:
            for tag in Contact.Tag.values:
                with self.subTest(tag=tag), browser.new_context() as context:
                    page = context.new_page()
                    page.goto(f"{self.live_server_url}/?tag={tag}")
                    self.assertEqual(urlsplit(page.url).path, "/login/")
                    page.get_by_label("Username", exact=True).fill(owner.username)
                    page.get_by_label("Password", exact=True).fill(self.password)
                    page.get_by_role("button", name="Sign in").click()
                    page.wait_for_url(f"{self.live_server_url}/?tag={tag}")
                    expect(page.get_by_label("Tag", exact=True)).to_have_value(tag)
                    self.assert_results(page, owner, tag)
