import os
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright


class ContactBrowserTests(StaticLiveServerTestCase):
    fixtures = ["demo"]

    def setUp(self):
        # Each test gets its own browser context and Django test database fixtures.
        self.playwright = sync_playwright().start()
        self.addCleanup(self.playwright.stop)
        self.browser = self.playwright.chromium.launch(headless=os.getenv("HEADED") != "1")
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.addCleanup(self.save_trace)
        self.page = self.context.new_page()

    def save_trace(self):
        output = Path("output/playwright")
        output.mkdir(parents=True, exist_ok=True)
        self.context.tracing.stop(path=str(output / f"{self._testMethodName}.zip"))

    def login(self, username="anna"):
        self.page.goto(self.live_server_url)
        self.page.get_by_label("Benutzername").fill(username)
        self.page.get_by_label("Passwort").fill("Workshop-2026!")
        self.page.get_by_role("button", name="Anmelden", exact=True).click()
        expect(self.page.get_by_role("heading", name="Alle Kontakte 3")).to_be_visible()

    def filter(self, tag):
        self.page.get_by_label("Tag", exact=True).select_option(tag)
        self.page.get_by_role("button", name="Filtern", exact=True).click()

    def test_login_and_logout(self):
        self.login()
        self.page.get_by_role("button", name="Abmelden").click()
        expect(self.page.get_by_label("Passwort")).to_be_visible()
        self.page.goto(self.live_server_url)
        expect(self.page.get_by_label("Passwort")).to_be_visible()

    def test_unfiltered_contacts_are_private(self):
        self.login("ben")
        expect(self.page.locator('a[href^="mailto:"]')).to_have_count(3)
        expect(self.page.get_by_role("link", name="david@kuestenwerk.example")).to_be_visible()
        expect(self.page.get_by_role("link", name="clara@studionord.example")).to_have_count(0)

    def test_filtered_contacts_are_private(self):
        self.login()
        self.filter("customer")
        expect(self.page.get_by_role("link", name="clara@studionord.example")).to_be_visible()
        expect(self.page.get_by_role("link", name="david@kuestenwerk.example")).to_have_count(0)
        expect(self.page.get_by_role("link", name="lea@lichtblick.example")).to_have_count(0)

    def test_filtered_count_and_reset(self):
        self.login()
        self.filter("lead")
        expect(self.page.locator('a[href^="mailto:"]')).to_have_count(1)
        expect(self.page.get_by_role("heading", name="Gefilterte Kontakte 1")).to_be_visible()
        expect(self.page.locator(".list-footer")).to_have_text("1 Kontakt Dein Netzwerk. Dein Überblick.")
        self.page.get_by_role("link", name="Zurücksetzen").click()
        expect(self.page.get_by_role("heading", name="Alle Kontakte 3")).to_be_visible()
        expect(self.page.locator('a[href^="mailto:"]')).to_have_count(3)
