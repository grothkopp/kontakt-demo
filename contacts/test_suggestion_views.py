from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Contact
from .suggestions import ProviderError


class SuggestionViewTests(TestCase):
    fixtures = ["demo"]

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.provider_patch = patch("contacts.suggestions.fake_provider", return_value={"tag": "lead"})
        self.provider = self.provider_patch.start()
        self.addCleanup(self.provider_patch.stop)
        self.before = self.snapshot()
        self.addCleanup(self.assert_unchanged)

    def snapshot(self):
        return list(Contact.objects.order_by("pk").values())

    def assert_unchanged(self):
        self.assertEqual(self.snapshot(), self.before)

    def sign_in(self, username="anna"):
        self.client.force_login(get_user_model().objects.get(username=username))
        self.client.get(reverse("contacts"))

    def post(self, pk=1, **data):
        return self.client.post(reverse("suggest_contact_tag", args=[pk]), {
            **data, "csrfmiddlewaretoken": self.client.cookies["csrftoken"].value,
        })

    def test_list_and_get_do_not_request_suggestions(self):
        self.sign_in()
        response = self.client.get(reverse("contacts"))
        self.assertContains(response, 'class="suggestion-form"', count=3)
        for contact in Contact.objects.filter(owner__username="ben"):
            self.assertNotContains(response, reverse("suggest_contact_tag", args=[contact.pk]))
        response = self.client.get(reverse("suggest_contact_tag", args=[1]))
        self.assertEqual(response.status_code, 405)
        self.provider.assert_not_called()

    def test_anonymous_with_valid_csrf_redirects_to_login(self):
        self.client.get(reverse("login"))
        response = self.post()
        self.assertRedirects(response, "/login/?next=/contacts/1/suggest-tag/")
        self.provider.assert_not_called()

    def test_csrf_rejected_before_provider(self):
        self.sign_in()
        url = reverse("suggest_contact_tag", args=[1])
        for data in ({}, {"csrfmiddlewaretoken": "invalid"}):
            self.assertEqual(self.client.post(url, data).status_code, 403)
        self.provider.assert_not_called()

    def test_foreign_and_missing_contacts_are_not_sent_to_provider(self):
        for username, foreign_pk in (("anna", 4), ("ben", 1)):
            self.sign_in(username)
            for pk in (foreign_pk, 99999):
                with self.subTest(username=username, pk=pk):
                    response = self.post(pk)
                    self.assertEqual(response.status_code, 404)
                    for contact in Contact.objects.all():
                        self.assertNotContains(response, contact.email, status_code=404)
                        self.assertNotContains(response, contact.note, status_code=404)
        self.provider.assert_not_called()

    def test_stored_note_and_owner_scoped_response(self):
        for username in ("anna", "ben"):
            self.sign_in(username)
            owned = Contact.objects.filter(owner__username=username)
            selected = owned.first()
            self.provider.reset_mock()
            response = self.post(selected.pk, note="forged", owner=999, tag="partner")
            self.provider.assert_called_once_with(selected.note)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["contact_count"], owned.count())
            self.assertEqual(response.context["customer_count"], owned.filter(tag="customer").count())
            self.assertEqual(response.context["company_count"], len(set(owned.values_list("company", flat=True))))
            for contact in Contact.objects.all():
                if contact.owner.username == username:
                    self.assertContains(response, contact.email)
                else:
                    self.assertNotContains(response, contact.email)
                    self.assertNotContains(response, contact.note)
            self.assertIn("no-store", response.headers["Cache-Control"])

    def test_valid_and_same_tag_results_are_transient(self):
        self.sign_in()
        for tag in ("customer", "partner", "lead"):
            with self.subTest(tag=tag):
                self.provider.return_value = {"tag": tag}
                response = self.post()
                self.assertContains(response, "Demo suggestion:", count=1)
                self.assertEqual(response.context["suggestion"].tag, tag)
                self.assertContains(response, 'class="tag tag-customer">Customer</span>')
                self.assertContains(response, "Nothing is saved")
                self.assert_unchanged()
        self.provider.reset_mock()
        response = self.client.get(reverse("contacts"))
        self.assertNotContains(response, "Demo suggestion:")
        self.provider.assert_not_called()

    def test_abstention_and_failures_do_not_expose_raw_output(self):
        self.sign_in()
        cases = [({"tag": None}, None, "No clear suggestion"),
                 ({"tag": "<script>private-detail</script>"}, None, "Suggestion unavailable"),
                 ({"tag": "lead", "reason": "private-detail"}, None, "Suggestion unavailable"),
                 (None, TimeoutError("private-detail"), "Suggestion unavailable"),
                 (None, ProviderError("private-detail"), "Suggestion unavailable")]
        for output, error, message in cases:
            with self.subTest(output=output, error=error):
                self.provider.return_value = output
                self.provider.side_effect = error
                response = self.post()
                self.assertContains(response, message)
                self.assertNotContains(response, "private-detail")
                self.assert_unchanged()

    def test_empty_note_skips_provider(self):
        self.sign_in()
        for note in ("", " \t "):
            Contact.objects.filter(pk=1).update(note=note)
            self.before = self.snapshot()  # Test setup, not a request mutation.
            response = self.post()
            self.assertContains(response, "No clear suggestion")
            self.assert_unchanged()
        self.provider.assert_not_called()

    def test_note_and_accessible_button_label_are_escaped(self):
        Contact.objects.filter(pk=1).update(note="<script>alert(1)</script>", name='Name " <b>')
        self.before = self.snapshot()
        self.sign_in()
        response = self.post()
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>")
        self.assertContains(response, "Name &quot; &lt;b&gt;")
