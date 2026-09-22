from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import Contact


class ContactTests(TestCase):
    fixtures = ["demo"]

    def test_anonymous_visitors_must_log_in(self):
        response = self.client.get(reverse("contacts"))
        self.assertRedirects(response, "/login/?next=/")

    def test_each_user_only_sees_their_own_contacts(self):
        for username, count in [("anna", 3), ("ben", 3)]:
            with self.subTest(username=username):
                self.assertTrue(self.client.login(username=username, password="Workshop-2026!"))
                response = self.client.get(reverse("contacts"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["contact_count"], count)
                for contact in Contact.objects.all():
                    if contact.owner.username == username:
                        self.assertContains(response, contact.email)
                    else:
                        self.assertNotContains(response, contact.email)
                self.client.logout()

    def test_actual_login_logout_and_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("login"))
        payload = {"username": "anna", "password": "Workshop-2026!"}
        self.assertEqual(client.post(reverse("login"), payload).status_code, 403)
        payload["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
        self.assertRedirects(client.post(reverse("login"), payload), "/")
        self.assertEqual(client.get(reverse("logout")).status_code, 405)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)
        self.assertRedirects(client.post(reverse("logout"), {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        }), "/login/")
        self.assertRedirects(client.get("/"), "/login/?next=/")

    def test_invalid_password_and_external_redirect(self):
        response = self.client.post(reverse("login"), {"username": "anna", "password": "wrong"})
        self.assertContains(response, "The username and password do not match")
        response = self.client.post(reverse("login"), {
            "username": "anna", "password": "Workshop-2026!", "next": "https://example.org/",
        })
        self.assertRedirects(response, "/")

    def test_empty_account(self):
        user = get_user_model().objects.create_user(username="empty", password="Another-test-password!")
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertContains(response, "No contacts")
        self.assertEqual(response.context["contact_count"], 0)

    def test_filter_by_tag(self):
        self.client.login(username="anna", password="Workshop-2026!")
        response = self.client.get(reverse("contacts"), {"tag": "lead"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mila@morgenwerk.example")
        self.assertNotContains(response, "clara@studionord.example")
        self.assertNotContains(response, "jonas@formfeld.example")


class ContactFilterIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.users = [
            get_user_model().objects.create_user(username=username)
            for username in ("first", "second", "sparse", "empty")
        ]
        cls.contacts = []
        for user in cls.users:
            tags = Contact.Tag.values
            if user.username == "sparse":
                tags = [Contact.Tag.LEAD]
            elif user.username == "empty":
                tags = []
            for tag in tags:
                identifier = f"{user.username}-{tag}"
                cls.contacts.append(Contact.objects.create(
                    owner=user,
                    name=f"Name {identifier}",
                    company=f"Company {identifier}",
                    role=f"Role {identifier}",
                    email=f"{identifier}@example.test",
                    tag=tag,
                    note=f"Private note {identifier}",
                ))

    def assert_visible_contacts(self, user, params):
        response = self.client.get(reverse("contacts"), params)
        self.assertEqual(response.status_code, 200)
        selected_tag = params.get("tag", "")
        expected = [
            contact for contact in self.contacts
            if contact.owner_id == user.pk
            and (not selected_tag or contact.tag == selected_tag)
        ]
        # Verify both the data passed to the template and the rendered fields.
        with self.subTest(surface="context"):
            self.assertCountEqual(response.context["contacts"], expected)
        with self.subTest(surface="page"):
            for contact in self.contacts:
                assertion = self.assertContains if contact in expected else self.assertNotContains
                for field in ("name", "company", "role", "email", "note"):
                    assertion(response, getattr(contact, field))

    def test_tag_filters_preserve_contact_isolation_for_every_account(self):
        # Shared tags catch leaks; sparse/empty accounts catch foreign-only matches.
        for user in self.users:
            self.client.force_login(user)
            for tag in Contact.Tag.values:
                with self.subTest(user=user.username, tag=tag):
                    self.assert_visible_contacts(user, {"tag": tag})

    def test_unfiltered_and_unknown_tag_requests_preserve_contact_isolation(self):
        for user in self.users:
            self.client.force_login(user)
            for params in ({}, {"tag": ""}, {"tag": "unknown-tag"}):
                with self.subTest(user=user.username, params=params):
                    self.assert_visible_contacts(user, params)
