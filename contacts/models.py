import uuid
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.db import models


class Contact(models.Model):
    class Tag(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PARTNER = "partner", "Partner"
        LEAD = "lead", "Lead"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    email = models.EmailField()
    tag = models.CharField(max_length=20, choices=Tag.choices)
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class TagSuggestion(models.Model):
    """A short-lived recommendation; only explicit acceptance changes a contact."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="tag_suggestions")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    proposed_tag = models.CharField(max_length=20, choices=Contact.Tag.choices)
    explanation = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["contact", "requester"], name="one_pending_tag_suggestion",
        )]

    def is_expired(self, now=None):
        return (now or timezone.now()) >= self.created_at + timedelta(minutes=15)
