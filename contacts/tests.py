from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .models import Contact


class ContactTests(TestCase):
    fixtures = ["demo"]

    def test_anonymous_visitors_must_log_in(self):
        response = self.client.get(reverse("contacts"))
        self.assertRedirects(response, "/login/?next=/")

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


class ContactFilterTests(TestCase):
    """Exercise ownership and result counts independently of the demo fixture."""

    @classmethod
    def setUpTestData(cls):
        cls.users = []
        cls.contacts = []
        # Rotate zero, one, and multiple matches across every declared tag.
        # Each tag is shared by owners, including when one owner has no matches.
        for owner_index in range(3):
            owner = get_user_model().objects.create_user(username=f"owner-{owner_index}")
            cls.users.append(owner)
            for tag_index, tag in enumerate(Contact.Tag.values):
                count = (0, 1, 3)[(owner_index + tag_index) % 3]
                for index in range(count):
                    marker = f"owner-{owner_index}-tag-{tag_index}-record-{index}"
                    cls.contacts.append(Contact.objects.create(
                        owner=owner,
                        tag=tag,
                        name=f"Name {marker}",
                        company=f"Company {marker}",
                        role=f"Role {marker}",
                        email=f"{marker}@example.test",
                        note=f"Note {marker}",
                    ))
        cls.users.append(get_user_model().objects.create_user(username="empty-owner"))

    def responses(self):
        # Both ways of requesting all tags must preserve the same guarantees.
        filters = [{}, {"tag": ""}] + [{"tag": tag} for tag in Contact.Tag.values]
        for owner in self.users:
            self.client.force_login(owner)
            owned = [contact for contact in self.contacts if contact.owner_id == owner.pk]
            for params in filters:
                selected_tag = params.get("tag", "")
                expected = [
                    contact for contact in owned
                    if not selected_tag or contact.tag == selected_tag
                ]
                response = self.client.get(reverse("contacts"), params)
                yield owner, params, owned, expected, response
            self.client.logout()

    def test_results_contain_exactly_the_matching_owned_contacts(self):
        for owner, params, owned, expected, response in self.responses():
            with self.subTest(owner=owner.username, params=params, surface="query results"):
                self.assertEqual(response.status_code, 200)
                actual_ids = [contact.pk for contact in response.context["contacts"]]
                self.assertCountEqual(actual_ids, [contact.pk for contact in expected])
            with self.subTest(owner=owner.username, params=params, surface="rendered rows"):
                self.assertContains(response, 'class="email"', count=len(expected))
            # Check every exposed field, not just one fixture email. This also
            # detects leaks elsewhere in the page, outside the result queryset.
            expected_ids = {contact.pk for contact in expected}
            for contact in self.contacts:
                with self.subTest(owner=owner.username, params=params, contact=contact.pk):
                    for field in ("name", "company", "role", "email", "note"):
                        assertion = (
                            self.assertContains if contact.pk in expected_ids
                            else self.assertNotContains
                        )
                        assertion(response, getattr(contact, field))

    def test_list_heading_counts_matching_owned_contacts(self):
        for owner, params, owned, expected, response in self.responses():
            with self.subTest(owner=owner.username, params=params):
                label = "Filtered contacts" if params.get("tag") else "All contacts"
                self.assertContains(
                    response,
                    f'<h2 id="list-title">{label} <span>{len(expected)}</span></h2>',
                    html=True,
                )

    def test_list_footer_counts_matching_owned_contacts(self):
        for owner, params, owned, expected, response in self.responses():
            with self.subTest(owner=owner.username, params=params):
                count = len(expected)
                noun = "contact" if count == 1 else "contacts"
                self.assertContains(
                    response,
                    f'<footer class="list-footer">{count} {noun} '
                    '<span>Your network. Your overview.</span></footer>',
                    html=True,
                )

    def test_account_summaries_remain_owner_scoped_and_unfiltered(self):
        for owner, params, owned, expected, response in self.responses():
            summaries = (
                ("Contacts", len(owned), "In your network"),
                ("Companies", len({contact.company for contact in owned}), "In your network"),
                ("Customers", sum(contact.tag == Contact.Tag.CUSTOMER for contact in owned),
                 "Existing relationships"),
            )
            for label, count, caption in summaries:
                with self.subTest(owner=owner.username, params=params, summary=label):
                    self.assertContains(
                        response,
                        f'<div><span>{label}</span><strong>{count:02d}</strong>'
                        f'<small>{caption}</small></div>',
                        html=True,
                    )
            with self.subTest(owner=owner.username, params=params, summary="sidebar"):
                self.assertContains(
                    response, f'<span class="nav-count">{len(owned)}</span>', html=True,
                )
