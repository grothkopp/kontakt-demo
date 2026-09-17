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
        self.assertContains(response, "Benutzername und Passwort passen nicht zusammen")
        response = self.client.post(reverse("login"), {
            "username": "anna", "password": "Workshop-2026!", "next": "https://example.org/",
        })
        self.assertRedirects(response, "/")

    def test_empty_account(self):
        user = get_user_model().objects.create_user(username="empty", password="Another-test-password!")
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertContains(response, "Noch keine Kontakte")
        self.assertEqual(response.context["contact_count"], 0)

    def test_filter_by_tag(self):
        self.client.login(username="anna", password="Workshop-2026!")
        response = self.client.get(reverse("contacts"), {"tag": "lead"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mila@morgenwerk.example")
        self.assertNotContains(response, "clara@studionord.example")
        self.assertNotContains(response, "jonas@formfeld.example")
