from django.contrib.auth import get_user_model
from django.test import TestCase


class FilterContractTests(TestCase):
    fixtures = ["demo"]

    def setUp(self):
        self.client.force_login(get_user_model().objects.get(username="anna"))

    def test_filtered_contacts_remain_private(self):
        response = self.client.get("/", {"tag": "customer"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "clara@studionord.example")
        self.assertNotContains(response, "david@kuestenwerk.example")
        self.assertNotContains(response, "lea@lichtblick.example")

    def test_result_count_matches_filtered_contacts(self):
        response = self.client.get("/", {"tag": "lead"})
        self.assertContains(response, "mila@morgenwerk.example")
        self.assertEqual(len(response.context["contacts"]), 1)
        self.assertEqual(response.context["contact_count"], 1)
        self.assertContains(response, 'Gefilterte Kontakte <span>1</span>')
        self.assertContains(response, '1 Kontakt <span>Dein Netzwerk.')
